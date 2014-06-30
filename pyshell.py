#!/bin/env python
''' pyshell - a python based interactive shell that needs a lot of work.
    by Mike Miller 2004-2006
    This file kept intentionally short to speed loading.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
'''

import sys
if (sys.version_info[0]*10 + sys.version_info[1]) < 24:
    print 'Error: pyshell requires python 2.4 or greater.'; sys.exit(1)

# Check how we were excecuted
import os, os.path
dirname = os.path.abspath(os.path.dirname(sys.argv[0])) + os.sep
sys.path += [dirname + 'lib', dirname + 'utils']     # find our files
os.environ['PATH'] += os.pathsep + dirname + 'utils' # a bug here, adds on every exec
os.environ['PYSHELL_OPTIONS'] = dirname + 'conf/options/'.replace('/', os.sep)

import ps_lib
import ps_main

# check for config files and folders and install if they don't exist
ps_lib.check_config()

# Start up pyshell
ps_main.startup()
