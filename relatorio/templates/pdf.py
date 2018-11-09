###############################################################################
#
# Copyright (c) 2014 Cedric Krier.
# Copyright (c) 2007, 2008 OpenHex SPRL. (http://openhex.com) All Rights
# Reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import os
import shutil
import tempfile
import subprocess
from io import BytesIO

import genshi
import genshi.output
from genshi.template import NewTextTemplate

from relatorio.templates.base import RelatorioStream
from relatorio.reporting import MIMETemplateLoader

__metaclass__ = type

TEXEXEC = 'texexec'
_encode = genshi.output.encode


class Template(NewTextTemplate):

    def generate(self, *args, **kwargs):
        generated = super(Template, self).generate(*args, **kwargs)
        return RelatorioStream(generated, PDFSerializer())


class PDFSerializer:

    def __init__(self):
        self.text_serializer = genshi.output.TextSerializer()

    def __call__(self, stream, method=None, encoding='utf-8', out=None):
        if out is None:
            result = BytesIO()
        else:
            result = out
        working_dir = tempfile.mkdtemp(prefix='relatorio')
        tex_file = os.path.join(working_dir, 'report.tex')
        pdf_file = os.path.join(working_dir, 'report.pdf')

        with open(tex_file, 'w') as fp:
            fp.write(_encode(self.text_serializer(stream)))

        subprocess.check_call([TEXEXEC, '--purge', 'report.tex'],
                              cwd=working_dir)

        with open(pdf_file, 'r') as fp:
            result.write(fp.read())

        shutil.rmtree(working_dir, ignore_errors=True)

        if out is None:
            return result


MIMETemplateLoader.add_factory('pdf', Template)
