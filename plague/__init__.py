import tokenize
import builtins
import keyword
import copy

# EXCEPTIONS

class ParseError (Exception):
    pass

# CLASSES

class Token:
    def __init__ (self, token):
        self.token = token

    def get_string (self):
        return self.token.string

    def get_type (self):
        return tokenize.tok_name[self.token.type]

    def __iter__ (self):
        d = {
            'type': self.get_type(),
            'string': self.get_string()
        }
        for key in d:
            yield (key, d[key])

    def get_position (self):
        return {
            'start': [
                self.token.start[0] - 1,
                self.token.start[1]
            ],
            'end': [
                self.token.end[0] - 1,
                self.token.end[1]
            ]
        }

    def compare (self, other):
        if self.get_type() != other.get_type():
            return False

        properties = {
            'is_var': False
        }
        if self.is_var():
            properties['is_var'] = True
            properties['matching_names'] = self.get_string() == other.get_string()
        else:
            if self.get_string() != other.get_string():
                return False

        return {
            'properties': properties,
            'position': {
                'self': self.get_position(),
                'other': other.get_position()
            }
        }

    def is_var (self):
        if self.get_type() == 'NAME':
            if keyword.iskeyword(self.get_string()) or self.get_string() in dir(builtins):
                return False
            return True
        return False

class Line:
    def __init__ (self, line):
        self.line = line
        self.tokens = []
        self.block = Block()

    def __len__ (self):
        return len(self.tokens)

    def __iter__ (self):
        d = {
            'line': self.line,
            'tokens': [dict(token) for token in self.tokens]
        }

        if len(self.block):
            d['block'] = list(self.block)

        for key in d:
            yield (key, d[key])

    def __getitem__ (self, index):
        return self.tokens[index]

    def add_token (self, token):
        self.tokens.append(token)

    def is_type (self, *types):
        for t in types:
            if self[0].get_string() == t:
                return True
        return False

    def compare (self, other):
        tokens = len(self)
        if len(other) < tokens:
            tokens = len(other)

        self_delta = len(self) - tokens
        other_delta = len(other) - tokens

        matches = []

        strict_format = False # set to true if line has nonmatching variable names
        start_index = 0
        while start_index < tokens:
            if result := self[start_index].compare(other[start_index]):
                if result['properties']['is_var'] and not result['properties']['matching_names']:
                    strict_format = True
                matches.append(result)
            else:
                break
            start_index += 1

        if start_index < 2 or strict_format and start_index != tokens:
            matches = []
        else:
            end_index = tokens - 1
            while start_index <= end_index:
                if result := self[end_index + self_delta].compare(other[end_index + other_delta]):
                    matches.append(result)
                else:
                    break
                end_index -= 1

        return matches

class Block:
    def __init__ (self, path=False):
        self.lines = []

        self.comments = []
        self.tokens = 0
        self.variables = {}

        self.newline = True
        self.indent = False

        if path:
            with open(path) as f:
                try:
                    self.source = f.read()
                except UnicodeDecodeError as e:
                    raise ParseError('unable to decode source') from None
                f.seek(0)
                try:
                    for token in tokenize.generate_tokens(f.readline):
                        self.add_token(token)
                except tokenize.TokenError as e:
                    raise ParseError('TokenError ' + str(e)) from None

    def __len__ (self):
        return len(self.lines)

    def __bool__ (self):
        return bool(len(self))

    def __iter__ (self):
        for line in self.lines:
            yield dict(line)

    def __getitem__ (self, index):
        return self.lines[index]

    def add_token (self, token):
        t = Token(token)

        if not t.get_type() in ['NL', 'COMMENT', 'NEWLINE', 'ENDMARKER', 'INDENT', 'DEDENT']:
            self.tokens += 1

        if t.get_type() in ['NL']: # Tokens to ignore
            return True

        if t.get_type() == 'COMMENT': # Memorize all comments
            self.comments.append(t)
            return True

        if t.is_var(): # Memorize all variables
            var_name = t.get_string()
            if not var_name in self.variables:
                self.variables[var_name] = []
            self.variables[var_name].append(t)

        if self.indent: # Forward the token to block if indent
            if not self.lines:
                raise ParseError('double indentation detected on row ' + str(token.start[0]))
            if self.lines[-1].block.add_token(token): # Cancel execution if block accepts the token
                return True

        if t.get_type() == 'NEWLINE' or t.get_type() == 'ENDMARKER':
            self.newline = True
        elif t.get_type() == 'INDENT':
            self.indent = True
        elif t.get_type() == 'DEDENT':
            if self.indent:
                self.indent = False
            else:
                return False
        else:
            if self.newline:
                line = token.line
                self.lines.append(Line(line))
                self.newline = False
            self.lines[-1].add_token(t)

        return True

    def list_sublocks (self, block_type):
        blocks = []
        for line in self.lines:
            if line.is_type(block_type):
                blocks.append(line)
        return blocks

    def compare_comments (self, other):
        matches = []

        for sc in self.comments:
            for oc in other.comments:
                if match := sc.compare(oc):
                    matches.append(match)

        return matches

    def compare_sublocks (self, other, block_type):
        matches = []
        candidate_matches = []

        self_sublocks = self.list_sublocks(block_type)
        other_sublocks = other.list_sublocks(block_type)

        for si in range(len(self_sublocks)):
            self_sublock = self_sublocks[si]
            for oi in range(len(other_sublocks)):
                other_sublock = other_sublocks[oi]

                line_matches = self_sublock.compare(other_sublock)
                block_matches = self_sublock.block.compare(other_sublock.block)

                candidate_matches.append({
                    'self': {
                        'sublock': self_sublock,
                        'index': si
                    },
                    'other': {
                        'sublock': other_sublock,
                        'index': oi
                    },
                    'matches': line_matches + block_matches
                })

        candidate_matches.sort(key=lambda x: (-len(x['matches']), x['self']['index'], x['other']['index']))

        occupied_sublocks = []

        for cm in candidate_matches:
            if not (cm['self']['sublock'] in occupied_sublocks or cm['other']['sublock'] in occupied_sublocks):
                matches += cm['matches']
                occupied_sublocks.append(cm['self']['sublock'])
                occupied_sublocks.append(cm['other']['sublock'])

        return matches

    def compare_variables (self, other):
        matching = {}

        for name in self.variables:
            for other_name in other.variables:
                if name == other_name:
                    matching[name] = {
                        'self': [],
                        'other': []
                    }

                    for variable in self.variables[name]:
                        matching[name]['self'].append(variable.get_position())

                    for variable in other.variables[name]:
                        matching[name]['other'].append(variable.get_position())

        return matching

    def compare (self, other):
        # Block matching
        match_pairs = [[] for i in range(len(other))]

        for si in range(len(self)):
            line_self = self[si]
            if line_self.is_type('class', 'def'):
                continue
            for oi in range(len(other)):
                line_other = other[oi]
                if line_other.is_type('class', 'def'):
                    continue

                match_pair = {
                    'self_line': si,
                    'matches': line_self.compare(line_other)
                }

                if line_self.block and line_other.block:
                    match_pair['matches'] += line_self.block.compare(line_other.block)

                if len(match_pair['matches']):
                    match_pairs[oi].append(match_pair)

        def search(self_line, other_line):
            best_matches = []

            def analyze(candidate_matches):
                nonlocal best_matches
                if len(best_matches) < len(candidate_matches):
                    best_matches = candidate_matches

            if other_line == len(match_pairs):
                return best_matches

            for match in match_pairs[other_line]:
                if self_line <= match['self_line']:
                    candidate_matches = search(
                        match['self_line'] + 1,
                        other_line + 1
                    )
                    candidate_matches += match['matches']
                    analyze(candidate_matches)

            analyze(
                search(
                    self_line,
                    other_line + 1
                )
            )

            return best_matches

        token_matches = search(0, 0)

        # Sublock matching
        for block_type in ['class', 'def']:
            token_matches += self.compare_sublocks(other, block_type)

        # This needs to be done better
        if hasattr(self, 'source') and hasattr(other, 'source'):
            return {
                'source': {
                    'self': self.source,
                    'other': other.source
                },
                'counters': {
                    'comments': max(
                        len(self.comments),
                        len(other.comments)
                    ),
                    'tokens': max(
                        self.tokens,
                        other.tokens
                    ),
                    'variables': max(
                        len(self.variables),
                        len(other.variables)
                    )
                },
                'matches': {
                    'comments': self.compare_comments(other),
                    'tokens': token_matches,
                    'variables': self.compare_variables(other)
                }
            }

        return token_matches
