import html
import os

def split_and_escape (source):
    source = [line for line in source.split('\n')]

    for i in range(len(source)):
        source[i] = [html.escape(char) for char in source[i]]

    return source

def generate(checks, thresholds, reports_path, self_path, other_path, match_count):
    source = {
        'self': split_and_escape(checks['source']['self']),
        'other': split_and_escape(checks['source']['other']),
    }

    def add_span(source_name, position, class_name, match_id):
        source[source_name][position['start'][0]][position['start'][1]] = f'<span class="{class_name}" data-mid="{match_id}">' + source[source_name][position['start'][0]][position['start'][1]]
        source[source_name][position['end'][0]][position['end'][1] - 1] += '</span>'

    match_id = 0

    # GENERATING SUMMARY

    summary = ''
    for check_name in checks['matches']:
        check_matches = len(checks['matches'][check_name])
        check_total = checks['counters'][check_name]

        if check_total == 0:
            continue

        if check_name in thresholds:
            if thresholds[check_name] <= check_matches / check_total:
                class_name = 'threshold_alert'
            else:
                class_name = 'threshold_ok'
        else:
            class_name = 'threshold_unknown'

        summary += f'<div class="{class_name}">{check_name}<br>{check_matches} / {check_total}</div>'

    # VARIABLE MATCHING

    matching_variables = ''
    for var_name in checks['matches']['variables']:
        matching_variables += f'<div class="variable" data-mid="{match_id}">{var_name}</div>'
        for source_name in checks['matches']['variables'][var_name]:
            for match in checks['matches']['variables'][var_name][source_name]:
                add_span(
                    source_name,
                    match,
                    '',
                    match_id
                )
        match_id += 1

    # TOKEN MATCHING

    for match in checks['matches']['tokens']:
        for source_name in match['position']:
            add_span(
                source_name,
                match['position'][source_name],
                'match block',
                match_id
            )
        match_id += 1

    # COMMENT MATCHING

    for match in checks['matches']['comments']:
        for source_name in match['position']:
            add_span(
                source_name,
                match['position'][source_name],
                'match comment',
                match_id
            )
        match_id += 1

    # ASSEMBLING SOURCES

    for name in source:
        for i in range(len(source[name])):
            source[name][i] = ''.join(source[name][i])
        source[name] = '\n'.join(source[name])

    # CREATING HTML OUT OF TEMPLATE

    template_path = os.path.join(
        os.path.dirname(__file__),
        'template.html'
    )

    with open(template_path) as f:
        html = f.read() % (
            summary,
            matching_variables,
            self_path,
            source['self'],
            other_path,
            source['other']
        )

    output_path = os.path.join(reports_path, self_path + '.' + str(match_count) + '.html')

    os.makedirs(
        '/'.join(output_path.split('/')[:-1]),
        exist_ok=True
    )

    with open(output_path, 'w') as f:
        f.write(html)
