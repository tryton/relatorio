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


import os
import re
from cStringIO import StringIO

import lxml.etree
from nose.tools import *
import genshi
from genshi.filters import Translator
from genshi.core import PI
from genshi.template.eval import UndefinedError

from templates.opendocument import Template, GENSHI_EXPR

def pseudo_gettext(string):
    catalog = {'Mes collègues sont:': 'My collegues are:',
               'Bonjour,': 'Hello,',
               'Je suis un test de templating en odt.': 
                'I am an odt templating test',
               'Felix da housecat': unicode('Félix le chat de la maison',
                                            'utf8'),
               'We sell stuffs': u'On vend des brols',
              }
    return catalog.get(string, string)


class TestOOTemplating(object):

    def setup(self):
        thisdir = os.path.dirname(__file__)
        filepath = os.path.join(thisdir, 'test.odt')
        self.oot = Template(file(filepath), filepath)
        self.data = {'first_name': u'Trente',
                     'last_name': unicode('Møller', 'utf8'),
                     'ville': unicode('Liège', 'utf8'),
                     'friends': [{'first_name': u'Camille', 
                                  'last_name': u'Salauhpe'},
                                 {'first_name': u'Mathias',
                                  'last_name': u'Lechat'}],
                     'hobbies': [u'Music', u'Dancing', u'DJing'],
                     'animals': [u'Felix da housecat', u'Dog eat Dog'],
                     'images': [(file(os.path.join(thisdir, 'one.jpg')),
                                 'image/jpeg'),
                                (file(os.path.join(thisdir, 'two.png')),
                                 'image/png')],
                     'oeuf': file(os.path.join(thisdir, 'egg.jpg')),
                     'footer': u'We sell stuffs'}

    def test_init(self):
        "Testing the correct handling of the styles.xml and content.xml files"
        ok_(isinstance(self.oot.stream, list))
        eq_(self.oot.stream[0], (PI, ('relatorio', 'content.xml'), None))
        ok_((PI, ('relatorio', 'content.xml'), None) in self.oot.stream)

    def test_directives(self):
        "Testing the directives interpolation"
        xml = '''<b:a xmlns:b="urn:b" xmlns:text="%s" xmlns:draw="urn:draw"
        xmlns:table="urn:table" xmlns:office="urn:office"
        xmlns:xlink="urn:xlink">
        <text:a xlink:href="relatorio://foo">foo</text:a>
        </b:a>''' % 'urn:text'
        parsed = self.oot.add_directives(xml) 
        root = lxml.etree.parse(StringIO(xml)).getroot()
        root_parsed = lxml.etree.parse(parsed).getroot()
        eq_(root_parsed[0].attrib['{http://genshi.edgewall.org/}replace'], 
            'foo')

    def test_styles(self):
        "Testing that styles get rendered"
        stream = self.oot.generate(**self.data)
        rendered = stream.events.render()
        ok_('We sell stuffs' in rendered)

        dico = self.data.copy()
        del dico['footer']
        stream = self.oot.generate(**dico)
        assert_raises(UndefinedError, lambda: stream.events.render())

    def test_generate(self):
        "Testing that content get rendered"
        stream = self.oot.generate(**self.data)
        rendered = stream.events.render()
        ok_('Bonjour,' in rendered)
        ok_('Trente' in rendered)
        ok_('Møller' in rendered)
        ok_('Dog eat Dog' in rendered)
        ok_('Felix da housecat' in rendered)

    def test_filters(self):
        "Testing the filters with the Translator filter"
        stream = self.oot.generate(**self.data)
        translated = stream.filter(Translator(pseudo_gettext))
        translated_xml = translated.events.render()
        ok_("Hello," in translated_xml)
        ok_("I am an odt templating test" in translated_xml)
        ok_('Felix da housecat' not in translated_xml)
        ok_('Félix le chat de la maison' in translated_xml)
        ok_('We sell stuffs' not in translated_xml)
        ok_('On vend des brols' in translated_xml)

    def test_images(self):
        "Testing the image replacement directive"
        stream = self.oot.generate(**self.data)
        rendered = stream.events.render()
        styles_idx = rendered.find('<?relatorio styles.xml?>')
        tree = lxml.etree.parse(StringIO(rendered[25:styles_idx]))
        root = tree.getroot()
        images = root.xpath('//draw:frame', namespaces=self.oot.namespaces)
        eq_(len(images), 3)
        eq_(images[0].attrib['{%s}name' % self.oot.namespaces['draw']],
            "image: (oeuf, 'image/png')")
        eq_(images[1].attrib['{%s}name' % self.oot.namespaces['draw']],
            'image: img')
        eq_(images[1].attrib['{%s}width' % self.oot.namespaces['svg']],
            '1.732cm')
        eq_(images[1].attrib['{%s}height' % self.oot.namespaces['svg']],
            '1.513cm')
        eq_(images[2].attrib['{%s}width' % self.oot.namespaces['svg']],
            '1.732cm')
        eq_(images[2].attrib['{%s}height' % self.oot.namespaces['svg']],
            '1.513cm')

    def test_regexp(self):
        "Testing the regexp used to find relatorio tags"
        regexp = re.compile(GENSHI_EXPR)
        group = regexp.match('for each="foo in bar"').groups()
        eq_(group, ('for each="foo in bar"', None, 'for', ' each="foo in bar"',
                    'each', 'foo in bar'))
        group = regexp.match('foreach="foo in bar"').groups()
        eq_(group, ('foreach="foo in bar"', None, None, None, None, None))
        group = regexp.match('/for').groups()
        eq_(group, ('/for', '/', 'for', '', None, None))
        group = regexp.match('/for ').groups()
        eq_(group, ('/for ', '/', 'for', '', None, None))
        group = regexp.match('formatLang("en")').groups()
        eq_(group, ('formatLang("en")', None, None, None, None, None))

