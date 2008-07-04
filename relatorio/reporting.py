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

__revision__ = "$Id: reporting.py 1 2008-07-04 14:31:52Z nicoe $"
__metaclass__ = type

import os, sys
import warnings
from cStringIO import StringIO
from genshi.template import MarkupTemplate, TextTemplate
from genshi.template import TemplateLoader

from mimetypes.odt import Template as OOTemplate
from mimetypes.pdf import Template as PDFTemplate

def _absolute(path):
    "Compute the absolute path of path relative to the caller file"
    if os.path.isabs(path):
        return path
    caller_fname = sys._getframe(2).f_globals['__file__']
    dir = os.path.dirname(caller_fname)
    return os.path.abspath(os.path.join(dir, path))

def _guess_type(mime):
    mime = mime.lower()
    type, stype = mime.split('/', 1)
    if type == 'application':
        if 'opendocument' in stype:
            return 'oo.org'
        else:
            return stype
    elif type == 'text':
        if stype in ('xml', 'html', 'xhtml'):
            return 'markup'
        else:
            return 'text'


class MIMETemplateLoader(TemplateLoader):
    """This subclass of TemplateLoader use mimetypes to search and find
    templates to load.
    """

    factories = {'pdf': PDFTemplate,
                 'oo.org': OOTemplate,
                 'text': TextTemplate,
                 'markup': MarkupTemplate}

    mime_func = [_guess_type]

    def get_type(self, mime):
        for func in reversed(self.mime_func):
            t = func(mime)
            if t is not None:
                return t

    def load(self, path, mime):
        rtype = self.get_type(mime)
        return super(MIMETemplateLoader, self).load(path,
                                                    cls=self.factories[rtype])

    @classmethod
    def add_factory(cls, abbr_mimetype, template_factory, id_function=None):
        """adds a template factory to the already known factories"""
        if abbr_mimetype in cls.factories:
            warnings.warn('You are overriding an already defined link.')
        cls.factories[abbr_mimetype] = template_factory
        if id_function is not None:
            cls.mime_func.append(id_function)


class Report:
    """Report is a simple interface on top of a rendering template.
    """
    
    def __init__(self, path, mimetype, factory, loader):
        self.fpath = path
        self.mimetype = mimetype
        self.data_factory = factory
        self.tmpl_loader = loader

    def __call__(self, obj, **kwargs):
        template = self.tmpl_loader.load(self.fpath, self.mimetype)
        data = self.data_factory(obj, **kwargs)
        return StringIO(str(template.generate(**data)))


class DefaultFactory:

    def __call__(self, obj, **kwargs):
        data = {}
        data['o'] = obj
        data['args'] = kwargs
        return data


class ReportRepository:
    """ReportRepository stores the report definition associated to objects.

    The report are indexed in this object by the object class they are working
    on and the name given to it by the user.
    """
    
    def __init__(self, datafactory=DefaultFactory):
        self.reports = {}
        self.default_factory = datafactory
        self.loader = MIMETemplateLoader(auto_reload=True)

    def add_report(self, klass, mimetype, template_path, data_factory=None,
                   report_name='default'):
        if data_factory is None:
            data_factory = self.default_factory
        reports = self.reports.setdefault(klass, {})
        report = Report(_absolute(template_path), mimetype, data_factory(),
                        self.loader)
        reports[report_name] = mimetype, report
        reports.setdefault(mimetype, []).append((report_name, report))

