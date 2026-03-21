# This file is part of relatorio.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import os


def get_info():
    import json
    import subprocess

    module_dir = os.path.dirname(os.path.dirname(__file__))

    info = dict()

    metadata_cmd = 'python -m build --quiet --metadata'
    metadata = subprocess.check_output(
        metadata_cmd, shell=True, encoding='utf-8', cwd=module_dir).strip()
    metadata = json.loads(metadata)
    info['name'] = metadata['name']
    info['description'] = metadata['summary']
    info['version'] = metadata['version']

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
