#!/usr/bin/python
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

pathAdding = os.pathsep + dirname + 'utils'
if pathAdding not in os.environ['PATH']:
    os.environ['PATH'] += pathAdding # a bug here, adds on every exec
os.environ['PYSHELL_OPTIONS'] = dirname + 'conf/options/'.replace('/', os.sep)

import ps_lib
import ps_main

# check for config files and folders and install if they don't exist
ps_lib.check_config()

# Start up pyshell
try: 
#This exists becuase if you do cd ` then you get an exception. This fixes that....a better solution would be to change all the parsing to something that accounts for that
    ps_main.startup()
except IndexError as e:
    sys.stderr.write("An index error returned!")
    ps_main.startup()
