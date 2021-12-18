# This file is part of relatorio.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import genshi.core
from genshi.template import MarkupTemplate, NewTextTemplate

from relatorio.reporting import MIMETemplateLoader

__metaclass__ = type


class RelatorioStream(genshi.core.Stream):
    "Base class for the relatorio streams."

    def render(self, method=None, encoding='utf-8', out=None, **kwargs):
        "calls the serializer to render the template"
        return self.serializer(
            self.events, method=method, encoding=encoding, out=out)

    def serialize(self, method='xml', **kwargs):
        "generates the bitstream corresponding to the template"
        return self.render(method, **kwargs)

    def __or__(self, function):
        "Support for the bitwise operator"
        return RelatorioStream(self.events | function, self.serializer)


MIMETemplateLoader.add_factory('text', NewTextTemplate)
MIMETemplateLoader.add_factory('markup', MarkupTemplate)
