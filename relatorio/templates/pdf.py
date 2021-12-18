# This file is part of relatorio.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import os
import shutil
import subprocess
import tempfile
from io import BytesIO

import genshi
import genshi.output
from genshi.template import NewTextTemplate

from relatorio.reporting import MIMETemplateLoader
from relatorio.templates.base import RelatorioStream

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
