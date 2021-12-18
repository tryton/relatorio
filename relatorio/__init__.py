"""
relatorio
=========

A templating library which provides a way to easily output all kind of
different files (odt, ods, png, svg, ...). Adding support for more filetype is
easy: you just have to create a plugin for this.

relatorio also provides a report repository allowing you to link python objects
and report together, find reports by mimetypes/name/python objects.
"""
from . import templates
from .reporting import MIMETemplateLoader, Report, ReportRepository

__version__ = '0.10.1'
__all__ = ['MIMETemplateLoader', 'ReportRepository', 'Report', 'templates']
