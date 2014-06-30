''' ps_init - initialize the python shell,
    by Mike Miller 2004-2005
    released under the GNU public license, (GPL) version 2
'''
import sys, os, glob, time, string
from optparse import OptionParser

import ansi, openanything, ps_builtins, ps_lib, ps_interpreter, ps_interactive
from ps_cfg import *
po.namespace['po'] = po                         # make avaliable to user
po.namespace['pi'] = pi

import subprocess as sp
stdio = (sys.stdin, sys.stdout, sys.stderr)     # save for later
sub  = sp.Popen
call = sp.call
sigintreceived = False

#find builtin commands automatically
po.keywords = []
for name in dir(ps_builtins):  # filter junk
    if (name[0] == '_') and (name[1] <> '_'):
        po.keywords.append(name)

# Parse command line and/or provide help
parser = OptionParser(usage='%prog [options] [script.psl | URL]', version=pi.version)
parser.add_option('-c', '--cmd', dest='command',          #bogus
               help='Execute supplied command(s) and exit.', metavar='"echo foo"')
parser.add_option('-d', '--debug',
               action='store_true', dest='debug', default=False,
               help='Print too much information to the console')
parser.add_option('-f', '--faststart',
               action='store_true', dest='faststart', default=False,
               help='Do not execute startup files')
parser.add_option('-v', '--verbose',
               action='store_true', dest='verbose', default=True,
               help='Print extra information to the console')
po.opts, po.args = parser.parse_args()

if po.opts.debug:
    #ps_lib.msg('debug', 'ps_builtins namespace: %s' % po.keywords)
    ps_lib.msg('debug', 'command line: options=%s \nargs=%s' % (po.opts, po.args) )

# Initialize some environment vars...
os.environ['SHELL'] = sys.argv[0]       # or maybe sys.executable
os.environ['PWD'] = os.getcwd()         # needed for default prompt on login shell
import socket
os.environ['HOSTNAME'] = socket.gethostname()  # needed for prompt on login shell

# some platform dependent code
if sys.platform == 'win32':
     #os.system('cmd /c title %s' % ps_lib.eval_str(po.title))
    # set title (doesnt work - reset on exit of cmd)
    pass
    readline = False
    
elif os.name == 'posix':

    #import curses                                      # term routines
    import readline                                     # line editor
    import rlcompleter                                  # tab completion
    #print 'delims', readline.get_completer_delims()
    readline.parse_and_bind('tab: complete')
    readline.set_completer_delims('\r\n`~!@#$%^&*()-=+[{]}\|;:\'",<>? ')
    readline.set_completer(
            ps_interactive.ps_completer(po.namespace).complete
        )
    ansi.xtermTitle(ps_lib.eval_str(po.title))          # set title, bug!

    # Register the signal handlers
    def termsize_change(signum, frame):
        x, y = ansi.getTermSize()
        if x:  os.environ['COLUMNS'] = str(x)
        if y:  os.environ['LINES']   = str(y)
    termsize_change(None, None) # once to set environment

    def sighandler(signum, frame):
        '''Clean and tidy shutdown when killed.'''
        if po.opts.debug: ps_lib.msg('debug', 'Signal %s received.' % signum)
        #print 'removing:', readline.remove_history_item(readline.get_current_history_length()-1)
        # how to clear the line buffer?  there doesn't seem to be a function to do it.
        print
        readline.redisplay()
        if signum == signal.SIGINT: sigintreceived = True

    # Register the signal handlers
    import signal
    signal.signal(signal.SIGWINCH,  termsize_change)
    #signal.signal(signal.SIGTERM,   termhandler)
    signal.signal(signal.SIGINT,    sighandler)
    #signal.signal(signal.SIGQUIT,  termhandler)
    #signal.signal(signal.SIGHUP,   termhandler)
    #del signal


# clean up
del name, parser, socket
# remove python help strings for exiting, and dir, they clash with our commands
del __builtins__['quit'], __builtins__['exit']


