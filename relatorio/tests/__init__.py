# This file is part of relatorio.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import sys
import os
import unittest

here = os.path.dirname(__file__)


def test_suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for fn in os.listdir(here):
        if fn.startswith('test') and fn.endswith('.py'):
            modname = 'relatorio.tests.' + fn[:-3]
            __import__(modname)
            module = sys.modules[modname]
            suite.addTests(loader.loadTestsFromModule(module))
    return suite


def main():
    suite = test_suite()
    runner = unittest.TextTestRunner()
    runner.run(suite)


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))))
    main()
