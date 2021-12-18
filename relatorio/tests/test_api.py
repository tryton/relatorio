# This file is part of relatorio.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import os
import unittest

from relatorio.reporting import (
    DefaultFactory, MIMETemplateLoader, Report, ReportRepository, _absolute,
    _guess_type)


class StubObject(object):

    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


class TestRepository(unittest.TestCase):

    def test_register(self):
        "Testing the registration"
        reporting = ReportRepository()
        reporting.add_report(StubObject, 'text/plain',
                             os.path.join('templates', 'test.tmpl'),
                             description='Test report')

        self.assertTrue(StubObject in reporting.classes)
        self.assertTrue('default' in reporting.classes[StubObject].ids)
        self.assertTrue(
            'text/plain' in reporting.classes[StubObject].mimetypes)

        report, mime, desc = reporting.classes[StubObject].ids['default']
        self.assertEqual(mime, 'text/plain')
        self.assertEqual(desc, 'Test report')
        self.assertEqual(report.mimetype, 'text/plain')
        self.assertTrue(report.fpath.endswith(os.path.join('templates',
                                                       'test.tmpl')))

        report2, name = (reporting.classes[StubObject]
                         .mimetypes['text/plain'][0])
        self.assertEqual(name, 'default')
        self.assertEqual(report, report2)

    def test_mimeguesser(self):
        self.assertEqual(_guess_type('application/pdf'), 'pdf')
        self.assertEqual(_guess_type('text/plain'), 'text')
        self.assertEqual(_guess_type('text/xhtml'), 'markup')
        self.assertEqual(
            _guess_type('application/vnd.oasis.opendocument.text'), 'oo.org')

    def abspath_helper(self, path):
        return _absolute(path)

    def test_absolute(self):
        "Test the absolute path calculation"
        self.assertEqual("/home/nicoe/python/mock.py",
            _absolute("/home/nicoe/python/mock.py"))

        our_dir, _ = os.path.split(__file__)
        # We use this because me go up by two frames
        new_path = self.abspath_helper(os.path.join('brol', 'toto'))
        self.assertEqual(os.path.join(our_dir, 'brol', 'toto'), new_path)


class TestReport(unittest.TestCase):

    def setUp(self):
        self.loader = MIMETemplateLoader()
        our_dir, _ = os.path.split(__file__)
        self.report = Report(os.path.join(our_dir, 'templates', 'test.tmpl'),
                             'text/plain', DefaultFactory(), self.loader)

    def test_report(self):
        "Testing the report generation"
        a = StubObject(name='OpenHex')
        self.assertEqual(self.report(o=a).render(), 'Hello OpenHex.\n')

    def test_factory(self):
        "Testing the data factory"
        class MyFactory:
            def __call__(self, o, time, y=1):
                d = dict()
                d['o'] = o
                d['y'] = y
                d['time'] = time
                d['func'] = lambda x: x + 1
                return d

        our_dir, _ = os.path.split(__file__)
        report = Report(os.path.join(our_dir, 'templates', 'time.tmpl'),
                        'text/plain', MyFactory(), self.loader)

        a = StubObject(name='Foo')
        self.assertEqual(report(o=a, time="One o'clock").render(),
            "Hi Foo,\nIt's One o'clock to 2 !\n")
        self.assertEqual(report(o=a, time="One o'clock", y=4).render(),
            "Hi Foo,\nIt's One o'clock to 5 !\n")
        self.assertRaises(TypeError, report, a)


class TestReportInclude(unittest.TestCase):

    def test_include(self):
        our_dir = os.path.dirname(__file__)
        template_path = os.path.join(our_dir, 'templates')
        relative_report = Report(os.path.join(template_path, 'include.tmpl'),
                                 'text/plain')
        self.assertEqual(relative_report().render(), 'Another Hello.\n\n')
