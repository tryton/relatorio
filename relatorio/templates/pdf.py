###############################################################################
#
# Copyright (c) 2007, 2008 OpenHex SPRL. (http://openhex.com) All Rights
# Reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
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

__metaclass__ = type

import os
import shutil
import tempfile
import subprocess
from cStringIO import StringIO

import genshi
import genshi.output
from genshi.template import Template as GenshiTemplate, NewTextTemplate

TEXEXEC_PATH = '/usr/bin/texexec'
_encode = genshi.output.encode


class Template(NewTextTemplate):

    def __init__(self, source, filepath=None, filename=None, loader=None,
                 encoding=None, lookup='strict', allow_exec=True):
        if source is None:
            source = open(filepath, 'r').read()
        super(Template, self).__init__(source, filepath, filename, loader,
                                       encoding, lookup, allow_exec)
    def generate(self, *args, **kwargs):
        generated = super(Template, self).generate(*args, **kwargs)
        return PDFStream(generated, PDFSerializer())


class PDFStream(genshi.core.Stream):

    def __init__(self, content_stream, serializer):
        self.events = content_stream
        self.serializer = serializer

    def render(self, method=None, encoding='utf-8', out=None, **kwargs):
        return self.serializer(self.events)

    def serialize(self, method, **kwargs):
        return self.render(method, **kwargs)

    def __or__(self, function):
        return PDFStream(self.events | function, self.serializer)


class PDFSerializer:

    def __init__(self):
        self.working_dir = tempfile.mkdtemp(prefix='relatorio')
        self.tex_file = os.path.join(self.working_dir, 'report.tex')
        self.pdf_file = os.path.join(self.working_dir, 'report.pdf')
        self.text_serializer = genshi.output.TextSerializer()

    def __call__(self, stream):
        tex_file = open(self.tex_file, 'w')
        tex_file.write(_encode(self.text_serializer(stream)))
        tex_file.close()

        p = subprocess.check_call([TEXEXEC_PATH, '--purge', 'report.tex'],
                                  cwd=self.working_dir)

        pdf = StringIO()
        pdf.write(open(self.pdf_file, 'r').read())

        shutil.rmtree(self.working_dir, ignore_errors=True)
        return pdf

