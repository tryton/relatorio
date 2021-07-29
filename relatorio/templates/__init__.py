# This file is part of relatorio.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
plugins = ['base', 'opendocument', 'pdf', 'chart']

for name in plugins:
    __import__('relatorio.templates.%s' % name)
