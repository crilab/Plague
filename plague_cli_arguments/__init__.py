import argparse
import os

def type_threshold (threshold):
    try:
        t = int(threshold)
    except ValueError:
        raise argparse.ArgumentTypeError('invalid integer')

    if t < 0:
        raise argparse.ArgumentTypeError('THRESHOLD is less than 0')
    elif 100 < t:
        raise argparse.ArgumentTypeError('THRESHOLD is more than 100')

    return t / 100

def type_folder (path):
    if os.path.isfile(path):
        raise argparse.ArgumentTypeError('not a directory')

    if not path.endswith('/'):
        path += '/'

    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError('directory not found')

    return path

def type_folder_reports (path):
    path = type_folder(path)

    if len(os.listdir(path)):
        raise argparse.ArgumentTypeError('the reports directory must be empty')

    return path

def get():
    parser = argparse.ArgumentParser(
        description='A Python 3 plagiarism checker.',
        epilog='A plagiarism report will be generated if any THRESHOLD is exceeded.'
    )

    parser.add_argument(
        'SUBMISSIONS',
        type = type_folder,
        help = 'folder containing student submissions to be checked for plagiarism'
    )

    parser.add_argument(
        'REPORTS',
        type = type_folder_reports,
        help = 'folder to which reports should be written'
    )

    parser.add_argument(
        '--archive',
        metavar = 'FOLDER',
        type = type_folder,
        help = 'folder with archived submissions; plagiarism detection is not performed between two archived submissions'
    )

    parser.add_argument(
        '-c',
        metavar = 'THRESHOLD',
        type = type_threshold,
        default = 0.5,
        help = 'minimum percentage (0 - 100) of matching comments (default: 50)'
    )

    parser.add_argument(
        '-t',
        metavar = 'THRESHOLD',
        type = type_threshold,
        default = 0.5,
        help = 'minimum percentage (0 - 100) of matching tokens (default: 50)'
    )

    parser.add_argument(
        '-v',
        metavar = 'THRESHOLD',
        type = type_threshold,
        default = 0.9,
        help = 'minimum percentage (0 - 100) of matching variable names (default: 90)'
    )

    args = parser.parse_args()

    return {
        'paths': {
            'submissions': args.SUBMISSIONS,
            'reports': args.REPORTS,
            'archive': args.archive
        },
        'thresholds': {
            'comments': args.c,
            'tokens': args.t,
            'variables': args.v
        }
    }
