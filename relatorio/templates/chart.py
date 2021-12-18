# This file is part of relatorio.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from io import BytesIO, StringIO

import genshi
import genshi.output
from genshi.template import NewTextTemplate

from relatorio.reporting import MIMETemplateLoader
from relatorio.templates.base import RelatorioStream

try:
    import cairo
    import pycha
    import pycha.bar
    import pycha.line
    import pycha.pie
    import yaml

    PYCHA_TYPE = {'pie': pycha.pie.PieChart,
                  'vbar': pycha.bar.VerticalBarChart,
                  'hbar': pycha.bar.HorizontalBarChart,
                  'line': pycha.line.LineChart,
                 }
except ImportError:
    yaml = cairo = None
    PYCHA_TYPE = {}
_encode = genshi.output.encode

__metaclass__ = type


class Template(NewTextTemplate):
    "A chart templating object"

    def generate(self, *args, **kwargs):
        generated = super(Template, self).generate(*args, **kwargs)
        return RelatorioStream(generated, CairoSerializer())

    @staticmethod
    def id_function(mimetype):
        "The function used to return the codename."
        if mimetype in ('image/png', 'image/svg'):
            return 'chart'


class CairoSerializer:

    def __init__(self):
        self.text_serializer = genshi.output.TextSerializer()

    def __call__(self, stream, method=None, encoding='utf-8', out=None):
        if not PYCHA_TYPE:
            raise NotImplementedError
        if out is None:
            result = BytesIO()
        else:
            result = out
        yml = StringIO(_encode(self.text_serializer(stream)))
        chart_yaml = yaml.load(yml.read())
        chart_info = chart_yaml['chart']
        chart_type = chart_info['output_type']
        if chart_type == 'png':
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,
                                         chart_yaml['options']['width'],
                                         chart_yaml['options']['height'])
        elif chart_type == 'svg':
            surface = cairo.SVGSurface(result, chart_yaml['options']['width'],
                                       chart_yaml['options']['height'])
        else:
            raise NotImplementedError

        chart = PYCHA_TYPE[chart_info['type']](surface, chart_yaml['options'])
        chart.addDataset(chart_info['dataset'])
        chart.render()

        if chart_type == 'png':
            surface.write_to_png(result)
        elif chart_type == 'svg':
            surface.finish()

        if out is None:
            return result


MIMETemplateLoader.add_factory('chart', Template, Template.id_function)
