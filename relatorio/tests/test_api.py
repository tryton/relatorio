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

__revision__ = "$Id: test_api.py 1 2008-07-04 14:31:52Z nicoe $"

import os
from nose.tools import *

from reporting import (ReportRepository, Report, MIMETemplateLoader,
                       DefaultFactory, _absolute)

class StubObject(object):

    def __init__(self, **kwargs):
        for key, val in kwargs.iteritems():
            setattr(self, key, val)


class TestRepository(object):

    def test_register(self):
        "Testing the registration"
        reporting = ReportRepository()
        reporting.add_report(StubObject, 'text/plain', 
                             os.path.join('templates', 'test.tmpl'))

        assert_true(StubObject in reporting.reports)
        assert_true('default' in reporting.reports[StubObject])
        assert_true('text/plain' in reporting.reports[StubObject])

        mime, report = reporting.reports[StubObject]['default']
        eq_(mime, 'text/plain')
        eq_(report.mimetype, 'text/plain')
        assert_true(report.fpath.endswith(os.path.join('templates', 
                                                       'test.tmpl')))

        name, report2 = reporting.reports[StubObject]['text/plain'][0]
        eq_(name, 'default')
        eq_(report, report2)

    def test_absolute(self):
        "Test the absolute path calculation"
        our_dir, _ = os.path.split(__file__)
        new_path = _absolute(os.path.join('brol', 'toto'))
        eq_(os.path.join(our_dir, 'brol', 'toto'), new_path)


class TestReport(object):

    def setup(self):
        self.loader = MIMETemplateLoader()
        our_dir, _ = os.path.split(__file__)
        self.report = Report(os.path.join(our_dir, 'templates', 'test.tmpl'),
                             'text/plain', DefaultFactory(), self.loader)

    def test_report(self):
        "Testing the report generation"
        a = StubObject(name='OpenHex')
        eq_(self.report(a).getvalue(), 'Hello OpenHex.\n')

    def test_factory(self):
        "Testing the data factory"
        class MyFactory:
            def __call__(self, obj, time, y=1):
                d = dict()
                d['o'] = obj
                d['y'] = y
                d['time'] = time
                d['func'] = lambda x: x+1
                return d

        our_dir, _ = os.path.split(__file__)
        report = Report(os.path.join(our_dir, 'templates', 'time.tmpl'),
                        'text/plain', MyFactory(), self.loader)

        a = StubObject(name='Foo')
        eq_(report(a, time="One o'clock").getvalue(), 
            "Hi Foo,\nIt's One o'clock to 2 !\n")
        eq_(report(a, time="One o'clock", y=4).getvalue(), 
            "Hi Foo,\nIt's One o'clock to 5 !\n")
        assert_raises(TypeError, report, a) 

