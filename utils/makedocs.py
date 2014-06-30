#!/bin/env python
'''Create builtins.html doc page listing the syntax of all the builtin commands. '''
import sys, os, os.path, string

# find builtin commands automatically
sys.path += [os.path.normpath(os.getcwd() + '/lib')]
#print sys.path
import ps_builtins
import ps_cfg
version = ps_cfg.pi.version
commands = []
for name in dir(ps_builtins):  # filter junk
    if (name[0] == '_') and (name[1] <> '_'):
        commands.append(name)

# open files for writing
outfile = file('builtins.html', 'w')
sys.stdout = outfile

# print titles
print '''
<html>
    <title>Pyshell Builtins, Version: %s</title>
    <meta name="GENERATOR" content="makedocs.py">
    <!-- This document auto-generated, don't bother to edit. -->
<body>
<h1>Pyshell Built-in Commands, Version: %s</h1>
''' % (version, version)

# print quick access header
print '<a name="top">[</a>'
for cmd in commands:
    func = getattr(ps_builtins, cmd)
    print '<a href="#%s">%s</a> | '.replace('%s', cmd[1:])
print ''']\n
<p>Note:  many of these commands are aliases to others.\n\n<pre>'''

# print commands
for cmd in commands:
    print '-' * 50
    func = getattr(ps_builtins, cmd)
    print '<h3><a name="%s">%s</a></h3>'.replace('%s', cmd[1:])
    print string.join(string.split(func.__doc__, '\n')[2:], '\n')
    print '\n(<a href="#top">top</a>)'

print '''
</pre>
</body><html>
'''
# clean up
sys.stdout = sys.__stdout__
outfile.close()
