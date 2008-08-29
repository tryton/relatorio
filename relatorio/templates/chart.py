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

from cStringIO import StringIO

import yaml
import genshi
import genshi.output
from genshi.template import NewTextTemplate

from relatorio.templates import RelatorioStream

import pycha
import pycha.pie
import pycha.line
import pycha.bar

PYCHA_TYPE = {'pie': pycha.pie.PieChart,
              'vbar': pycha.bar.VerticalBarChart,
              'hbar': pycha.bar.HorizontalBarChart,
              'line': pycha.line.LineChart,
             }
_encode = genshi.output.encode

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

    def __call__(self, stream):
        yml = StringIO(_encode(self.text_serializer(stream)))
        chart_yaml = yaml.load(yml.read())
        chart_info = chart_yaml['chart']
        chart = PYCHA_TYPE[chart_info['type']](chart_yaml['options'])
        chart.addDataset(chart_info['dataset'])
        return chart.render()

