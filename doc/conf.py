# This file is part of relatorio.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import os


def get_info():
    import subprocess
    import sys

    module_dir = os.path.dirname(os.path.dirname(__file__))

    info = dict()

    result = subprocess.run(
        [sys.executable, 'setup.py', '--name', '--description'],
        stdout=subprocess.PIPE, check=True, cwd=module_dir)
    info['name'], info['description'] = (
        result.stdout.decode('utf-8').strip().splitlines())

    result = subprocess.run(
        [sys.executable, 'setup.py', '--version'],
        stdout=subprocess.PIPE, check=True, cwd=module_dir)
    info['version'] = result.stdout.decode('utf-8').strip()

    return info


info = get_info()

html_theme = 'sphinx_book_theme'
html_theme_options = {
    'repository_provider': 'gitlab',
    'repository_url': 'https://code.tryton.org/relatorio',
    'repository_branch': 'branch/default',
    'use_source_button': True,
    'use_edit_page_button': True,
    'use_repository_button': True,
    'use_download_button': False,
    'path_to_docs': 'doc',
    }
html_title = info['description']
master_doc = 'index'
project = info['name']
release = version = info['version']
default_role = 'ref'
highlight_language = 'none'
extensions = [
    'sphinx_copybutton',
    'sphinx.ext.intersphinx',
    ]
intersphinx_mapping = {
    'python': ('https://docs.python.org/', None),
    }

del get_info, info
