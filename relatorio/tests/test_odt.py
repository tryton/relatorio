# -*- encoding: utf-8 -*-
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

__revision__ = "$Id: test_odt.py 19 2008-07-17 00:11:51Z nicoe $"

import os
from cStringIO import StringIO

import lxml.etree
from nose.tools import *
from genshi.template import MarkupTemplate
from genshi.filters import Translator

from templates.odt import Template, NS

def pseudo_gettext(string):
    catalog = {'Mes collègues sont:': 'My collegues are:',
               'Bonjour,': 'Hello,',
               'Je suis un test de templating en odt.': 
                'I am an odt templating test',
               'Felix da housecat': unicode('Félix le chat de la maison',
                                            'utf8'),
              }
    return catalog.get(string, string)


class TestOOTemplating(object):

    def setup(self):
        thisdir = os.path.dirname(__file__)
        filepath = os.path.join(thisdir, 'test.odt')
        self.oot = Template(file(filepath), filepath)
        self.data = {'first_name': 'Trente',
                     'last_name': unicode('Møller', 'utf8'),
                     'ville': unicode('Liège', 'utf8'),
                     'friends': [{'first_name': 'Camille', 
                                  'last_name': 'Salauhpe'},
                                 {'first_name': 'Mathias',
                                  'last_name': 'Lechat'}],
                     'hobbies': ['Music', 'Dancing', 'DJing'],
                     'animals': ['Felix da housecat', 'Dog eat Dog']}

    def test_init(self):
        assert_true(isinstance(self.oot.content_template, MarkupTemplate))

    def test_directives(self):
        xml = '''<a xmlns="urn:a" xmlns:text="%s">
        <text:placeholder>&lt;foo&gt;</text:placeholder>
        </a>''' % NS['text']
        parsed = self.oot.add_directives(xml) 
        root = lxml.etree.parse(StringIO(xml)).getroot()
        root_parsed = lxml.etree.parse(StringIO(parsed)).getroot()
        eq_(root_parsed[0].attrib['{http://genshi.edgewall.org/}replace'], 
            'foo')

    def test_generate(self):
        stream = self.oot.generate(**self.data)
        rendered = stream.events.render()
        assert 'Bonjour,' in rendered
        assert 'Trente' in rendered
        assert 'Møller' in rendered
        assert 'Dog eat Dog' in rendered
        assert 'Felix da housecat' in rendered

    def test_filters(self):
        stream = self.oot.generate(**self.data)
        translated = stream.filter(Translator(pseudo_gettext))
        content_xml = translated.events.render()
        assert "Hello," in content_xml
        assert "I am an odt templating test" in content_xml
        assert 'Felix da housecat' not in content_xml
        assert 'Félix le chat de la maison' in content_xml
