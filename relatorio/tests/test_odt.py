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

__revision__ = "$Id: test_odt.py 1 2008-07-04 14:31:52Z nicoe $"

import os
from cStringIO import StringIO

import lxml.etree
from nose.tools import *
from genshi.template import MarkupTemplate

from mimetypes.odt import OOTemplate, NS


class TestOOTemplating(object):

    def setup(self):
        thisdir = os.path.dirname(__file__)
        filepath = os.path.join(thisdir, 'test.odt')
        self.oot = OOTemplate(file(filepath), filepath)

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
