###############################################################################
#
# Copyright (c) 2015 Cedric Krier.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
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
