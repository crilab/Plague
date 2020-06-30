#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'plague',
    author = 'Christian Åberg',
    description = 'A plagiarism checker for Python 3',
    packages = [
        'plague',
        'plague_html_report',
        'plague_cli_arguments'
    ],
    package_data = {
        'plague_html_report': [
            'template.html'
        ]
    },
    scripts = [
        'scripts/plague'
    ],
    classifiers = [
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ]
)
