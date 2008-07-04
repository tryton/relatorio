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

__revision__ = "$Id: pdf.py 1 2008-07-04 14:31:52Z nicoe $"
__metaclass__ = type

from cStringIO import StringIO
from trml2pdf import parseString

from genshi.template import Template as GenshiTemplate, MarkupTemplate


class PDFTemplate(GenshiTemplate):

    def __init__(self, source, filepath=None, filename=None, loader=None,
                 encoding=None, lookup='strict', allow_exec=True):
        self.content_template = MarkupTemplate(source, filepath, filename,
                                               loader, encoding, lookup,
                                               allow_exec)

    def _parse(self, source, encoding):
        pass
    
    def _prepare(self, stream):
        return []

    def generate(self, *args, **kwargs):
        pdf = StringIO()
        pdf.write(str(parseString(self.content_template.generate(*args,
                                                                 **kwargs))))
        return pdf.getvalue()
