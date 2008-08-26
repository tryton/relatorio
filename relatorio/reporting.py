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

import os, sys
import warnings

import pkg_resources
from genshi.template import TemplateLoader

def _absolute(path):
    "Compute the absolute path of path relative to the caller file"
    if os.path.isabs(path):
        return path
    caller_fname = sys._getframe(2).f_globals['__file__']
    caller_dir = os.path.dirname(caller_fname)
    return os.path.abspath(os.path.join(caller_dir, path))

def _guess_type(mime):
    """
    Returns the codename used by relatorio to identify which template plugin
    it should use to render a mimetype
    """
    mime = mime.lower()
    major, stype = mime.split('/', 1)
    if major == 'application':
        if 'opendocument' in stype:
            return 'oo.org'
        else:
            return stype
    elif major == 'text':
        if stype in ('xml', 'html', 'xhtml'):
            return 'markup'
        else:
            return 'text'


class MIMETemplateLoader(TemplateLoader):
    """This subclass of TemplateLoader use mimetypes to search and find
    templates to load.
    """

    factories = {}

    mime_func = [_guess_type]

    def get_type(self, mime):
        "finds the codename used by relatorio to work on a mimetype"
        for func in reversed(self.mime_func):
            codename = func(mime)
            if codename is not None:
                return codename

    def load(self, path, mime):
        "returns a template object based on path"
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

    @classmethod
    def load_template_engines(cls):
        """loads template engines found via PEAK's pkg_resources"""
        for entrypoint in pkg_resources.iter_entry_points(
                                        'relatorio.templates.engines'):
            try:
                engine = entrypoint.load()
                if hasattr(engine, 'id_function'):
                    cls.add_factory(entrypoint.name, engine, engine.id_function)
                else:
                    cls.add_factory(entrypoint.name, engine)
            except ImportError:
                warnings.warn('We were not able to load %s. You will not '
                              'be able to use its functonlities' %
                              entrypoint.module_name)


class Report:
    """Report is a simple interface on top of a rendering template.
    """

    def __init__(self, path, mimetype, factory, loader):
        self.fpath = path
        self.mimetype = mimetype
        self.data_factory = factory
        self.tmpl_loader = loader
        self.filters = []

    def __call__(self, **kwargs):
        template = self.tmpl_loader.load(self.fpath, self.mimetype)
        data = self.data_factory(**kwargs)
        return template.generate(**data).filter(*self.filters)

    def __repr__(self):
        return '<relatorio report on %s>' % self.fpath


class DefaultFactory:
    """This is the default factory used by relatorio.
    
    It just returns a copy of the data it receives"""

    def __call__(self, **kwargs):
        data = kwargs.copy()
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
        """adds a report to the repository.

        You will be able to find the report via 
            - the class it is working on
            - the mimetype it outputs
            - the name of the report
        
        You also have the opportunity to define a specific data_factory.
        """
        if data_factory is None:
            data_factory = self.default_factory
        reports = self.reports.setdefault(klass, {})
        report = Report(_absolute(template_path), mimetype, data_factory(),
                        self.loader)
        reports[report_name] = report, mimetype
        reports.setdefault(mimetype, []).append((report_name, report))

