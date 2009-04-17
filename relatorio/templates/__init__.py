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

import traceback
import warnings

plugins = ['base', 'opendocument', 'pdf', 'chart']

for name in plugins:
    try:
        __import__('relatorio.templates.%s' % name)
    except Exception, e:
        warnings.warn("Unable to load plugin '%s', you will not be able "
                      "to use it" % name)
        print
        print 'Original traceback:'
        print '-------------------'
        traceback.print_exc()
        print
