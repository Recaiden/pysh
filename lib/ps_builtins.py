''' ps_builtins - defines all the pyshell builtin commands
    by Mike Miller 2004-2005
    released under the GNU public license, (GPL) version 2
'''
import sys, os, string, shutil
import subprocess as sp
sub  = sp.Popen

from cmdbase import *
import ps_lib
from ps_cfg import *
import ansi

# Utility Functions
#____________________________________________________________________
def print_commands(commands=[]):
    'print all built-in commands'
    
    width = 15
    print 'Built-in commands:\n'
#    print commands
    
    if commands:
        cmdlist = []
        for cmd in commands:
            cmdlist.append('_%s' % cmd)
    else:
        cmdlist = po.keywords
#    print cmdlist
    
    import textwrap
    for kw in cmdlist:
#        print 'kw:', kw
        if not kw in po.keywords: return
        if po.color:
            print po.colors['keyword'] % kw[1:].ljust(width),
        else:
            print kw[1:].ljust(width),

        #try:
        doc = string.split(globals()[kw].__doc__, '\n')[0]
        if len(doc) > 64:

            lines = textwrap.wrap(doc, 64)
            print lines[0]
            for line in lines[1:]:
                print ' ' * (width + 5), line
        else: print doc
        #except: pass
    print


#____________________________________________________________________
def del_confirm(command, args):
    '''user confirmation helper function'''

    ps_lib.msg('warning', 'Multiple file or folder deletion, including the use of glob characters\n' + \
         '\t  is potentially very dangerous.\n')

    answer = ''
    if po.color:     print ' ', po.colors['keyword'] % command, string.join(args), '\n'
    else:            print ' ', command, string.join(args), '\n'
    try:
        if po.color: answer = raw_input('  Please confirm the command [%s,%s]: '
                        % (po.colors['yes'] % 'yes', po.colors['no'] % 'NO') )
        else:        answer = raw_input('  Please confirm the command [yes,NO]: ')
        print
    except (KeyboardInterrupt, EOFError):
        print; return False

    answer = string.lower(answer)
    if answer == 'y' or answer == 'yes':    return True
    else:                                   return False

#____________________________________________________________________
def dlprogress(count, blocksize, totalsize):
    '''print the progress of a downloaded file.
    See reporthook on urlretrieve in urllib'''
    
    pcnt = count * blocksize * 100.0 / totalsize
    
    # nice to use a graph from ansi module here
    data = [
        ('%', pcnt,     ansi.grey, ansi.bluebg, False),     # Used
        ('-', 100-pcnt, ansi.grey, ansi.greenbg, False),    # free
        ]
    print '\r        ',
    ansi.bargraph(data, 50, po.color)
    print '  %2d %%  ' % pcnt,
    
    if po.opts.debug:
        print
        print '\rcount:', count, '\tblocksize:', blocksize, '\ttotal:', totalsize,
    sys.stdout.flush()
#____________________________________________________________________
def print_variable(name, value, vtype='string', padding=-15, istty=True,
    truncate=False):
    'pretty print name, value pairs, such as env vars or alias'
    
    if truncate:
        strlength = (ansi.getTermSize()[0] - 6 + padding)
        if len(value) > strlength:
            value = value[:strlength] + '...'
    
    template = '%%%ss%%s%%s' % padding
    if po.color and istty:
        print template % \
            (name, po.colors['identifier'] % ' = ', po.colors[vtype] % value)
    else:
        print template % (name, ' = ', value)
        
#____________________________________________________________________
def print_variables(vars, vtype='string', istty=True, truncate=False):
    'pretty print a dictionary of values, such as env vars or aliases'
    
    names = vars.keys()
    names.sort()
    padding=-10
    for item in names:  # get longest name
        length = len(item)
        if length > padding: padding = length
    
    for item in names:  # print with correct padding
        print_variable(item, vars[item], padding=-padding, istty=istty, truncate=truncate)
        

#____________________________________________________________________
def runcmd(name, args):
    'Run a command object'
    
    args.insert(0, name[1:])
    obj = globals()[name]( args )
    #obj.run()  # not needed anymore


#____________________________________________________________________
# Built-in Commands

#____________________________________________________________________
class _alias(ConsoleAppBase):
    '''create and remove aliases (command substitutions)
    
    alias [-h] [name] [value]
    
    alias                   # Print table of current aliases
    alias -h                # Print help text
    alias name              # Print aliases that start with 'name'
    alias name = value...   # Set alias 'name' to 'value'
    alias name=value...     # "
    alias name value...     # "
    alias name=             # Delete an alias
    
    An alias can be used to substitute a series of commands by a single word.'''
    # Triple quotes should end at end of line, so options arent spaced by two lines
    
    def run(self):
        
        del self.args[0] # remove name, arg[0], for compatibility

        if len(self.args) < 1:              # No args, pretty print list
            aliases = po.aliases.keys()
            if len(aliases) == 0 and self.opts.verbose:
                ps_lib.msg('info', 'No aliases set.')
            else:
                aliases.sort()
                print_variables(po.aliases, istty=self.istty)
    
        elif '=' in self.args[0]:
            name, value = self.args[0].split('=', 1) #split on first = only
    
            if len(self.args) > 1:   # alias name= something; there is stuff after the equal sign
                value = value + ' ' + string.join(self.args[1:])
                po.aliases[name] = value
            else:            # there may be stuff... if not, delete alias
                if value:     # alias name=something;
                    po.aliases[name] = value
                else:        # alias name=; delete alias
                    if po.aliases.has_key(name):  del po.aliases[name]
                    else:
                        ps_lib.msg('error', 'this alias does not exist.'); print
                        return self.ERR_DNE
        else:
            if len(self.args) > 1:   # alias name text; create an alias
                if self.args[1] == '=': del self.args[1]                # alias name = text;
                if self.args[1].startswith('='): self.args[1] = self.args[1][1:] # alias name =text;
                name, value = self.args[0], string.join(self.args[1:])
                po.aliases[name] = value
            else:   # alias name; just print out the alias, if it exists
                srch_results = {}
                for var in po.aliases:
                    if string.count(var.lower(), self.args[0].lower()):
                        srch_results[var] = po.aliases[var]
                if srch_results:  print_variables(srch_results, istty=self.istty)
                elif self.opts.verbose:
                    ps_lib.msg('warning', 'an alias containing "%s" does not exist.'
                        % self.args[0])
                    return self.ERR_ARGS

#____________________________________________________________________
class _cd(ConsoleAppBase):
    '''change current folder
    
    cd [-h] [folder]
    
    cd              # Move to the home folder (~)
    cd bin          # Move to bin
    cd -h           # Print help text

    The cd command changes the current working folder to another.'''

    def run(self):
                
        if len(self.args) > 2:
            print ('error', 'too many parameters.'); print
            return self.ERR_ARGS
        try:
            if len(self.args) == 1:     os.chdir(os.path.expanduser('~'))
            else:                       os.chdir(self.args[1])
            os.environ['PWD'] = os.getcwd()
            
        except OSError, why:
            ps_lib.msg('error', str(why) ); print
            return self.ERR_OS
_changefolder = _cd
#____________________________________________________________________
class _bg(ConsoleAppBase):
    '''Send a suspended task into the background - not quite implemented yet.
    
    bg
    bg -h
    
    bg sends a suspended task to the background.  Not implemented yet.'''

    def run():
        
        if po.jobs:
            job = po.jobs[-1]
            pid = job[0]
            # what to do with stio?
            signal(['cont', pid])
        else:
            ps_lib.msg('error', 'No jobs at this time.'); print
            return self.ERR_DNE


#____________________________________________________________________
class _cls(ConsoleAppBase):
    '''Clear the console or terminal screen
    
    cls [-h]
    
    cls         # clear screen
    cls -h      # Print this useless help text
    
    cls clears the console or terminal screen.'''
    
    def run(self):
                    
        if sys.platform == 'win32': return os.system('cls')    # Oh, so cheesy
        elif os.name == 'posix':    return os.system('clear')
            #print ''
            #print '\f'
        print
        
_clear = _cls
#____________________________________________________________________
class _copy(ConsoleAppBase):
    '''copy a file or folder
    
    copy [-h] [source] [destination]
    
    copy <source> <destination>     # Copy a file to destination file or folder
    copy <sources> <dest_folder/>   # Copy files to a folder
    copy <source>                   # Copy file to current folder[.] implied
    copy <URL> <destination>        # Copy remote file to destination file, fd.
    copy -h                         # Print help text
    
    copy copies files and folders to another location.'''

    def run(self):
    
        # remove name, arg[0], for compatibility
        del self.args[0]
        
        #   figure out what to do with args
        destisdir = False
        if len(self.args) == 0:                      # no self.args print usage
            ps_lib.msg('error', 'this command requires additional arguments')
            print; print self.usage; print
            return self.ERR_ARGS
        if len(self.args) == 1:                      # source only, copy to current f
            sources, dst = self.args[0], '.'
            destisdir = True
        else:                                   # 2 or more self.args
            sources, dst = self.args[0:-1], self.args[-1]
            if os.path.isdir(dst): destisdir = True
    
        # Convert to list if not
        type = globals()['__builtins__']['type'] # clash with type builtin
        if type(sources) is str:
            sources = [sources]

        if len(sources) > 1 and not destisdir:
            ps_lib.msg('error', 'when moving multiple files, last argument must be a directory.')
            print self.usage; print; return self.ERR_ARGS
    
        # check for urls, using urlparse
        import urlparse
        for src in sources:
        
            if self.opts.verbose:
                if po.color:
                    print 'Copying %s  -->  %s ...' \
                        % ( po.colors['string'] % src,
                            po.colors['string'] % dst),
                else:
                    print 'Copying "%s"  -->  "%s" ...' % (src, dst),
            
            urltype = urlparse.urlparse(src)[0]
            if urltype in ['http', 'ftp', 'gopher', 'file']:
                import urllib
                if urltype == 'file':  # convert to regular path and cont normally
                    #src = src[7:]
                    src = src.split(':', 1)[1]  # split once, take second chunk
                    #if src.startswith('//') == '/': src = src[1:]
                    while '//' in src: src = src.replace('//', '/')
                    pos = src.find('?')  # clip cgi params
                    if pos <> -1: src = src[:pos]
                    src = urllib.url2pathname(src)
                    # normalize path for os, continue below
                else:
                    class DownloadError(Exception): pass
                    try:
                        if os.path.isdir(dst):
                            fname = os.path.basename(urlparse.urlparse(src)[2])
                            if not fname: fname = 'index.html'
                            dst = os.path.join(dst, fname)
                        print
                        #urllib.urlretrieve(src, dst, _dlprogress) # report_hook()
                        ps_lib.download(src, dst, report_hook=dlprogress)
                        print;  continue
                    except IOError, why:
                        ps_lib.msg('error', str(why)); print
                        return self.ERR_IO
                    except DownloadError, why:
                        print; ps_lib.msg('error', str(why)); print
                        return self.ERR_RESM
                    except Exception, why:
                        print;  ps_lib.msg('info', str(why)); print
                        return self.ERR_UNKN
            # do copy
            try:
                if os.path.isdir(src):       # if folder, use copy tree
                    dirdst = dst + os.sep + os.path.basename(src)
                    if os.path.exists(dirdst):
                        ps_lib.msg('error', 'destination folder %s must not exist.' % dirdst)
                        print;  po.status = 2
                        continue
                    else:
                        shutil.copytree(src, dirdst, symlinks=True)
                else:
                    shutil.copy(src, dst)
                if self.opts.verbose:  print 'done'
            except IOError, why:
                print; ps_lib.msg('error', str(why) ); print
                return self.ERR_IO
            except Exception, why:
                print;  ps_lib.msg('error', str(why) )
                return self.ERR_UNKN
_cp = _copy
#____________________________________________________________________
class _dir(ConsoleAppBase):
    '''print a listing of the current folder
    
    dir [file | folder]
    
    necessary for windows, posix should use an alias to "ls -l" instead.
    ? could windows use "cmd /c dir" ?'''
    
    def run(self):

        # remove name, arg[0], for compatibility
        del self.args[0]

        if len(self.args) < 1:
            self.args = [os.getcwd()]
        for item in self.args:
            try:
                result = os.listdir(item)
                print '\nListing of: "%s"\n' % item.replace('\\','/')
                for item in result:
                    print item
            except Exception, why:
                ps_lib.msg('error', str(why)); print
                return self.ERR_AXSD
        print
_ll = _dir
#____________________________________________________________________
class _deltree(ConsoleAppBase):
    '''devastates file(s) and folder(s)
    
    deltree [-h] [-f] <files>
    
    deltree file1       # Delete file or folder and everything it contains
    deltree -f file1    # Delete and don't ask for confirmation
    deltree foo bar     # Delete foo and bar
    deltree -h          # Print help text
    
    deltree wipes out files and whole folders, use with caution.'''

    def register_opts(self):
        
        self.parser.add_option('-f', '--force',  action='store_true',
            dest='force', default=False, help='don\'t ask for confirmation')

    def run(self):

        del self.args[0]  # get rid of command name
        if len(self.args) < 1:
            ps_lib.msg('error', 'this command needs at least one parameter, \n' + \
                '          the name(s) of the folder(s) (or files) to be removed.')
            print self.usage; print
            return self.ERR_ARGS
    
        if not self.opts.force and not del_confirm('deltree', self.args):
            return self.USR_RJCT
        
        for obj in self.args:
    
            if self.opts.verbose:
                if po.color:    print 'Removing %s ...' % po.colors['string'] % obj,
                else:           print 'Removing "%s" ...' % obj,
            try:
                if os.path.isdir(obj):  shutil.rmtree(obj)
                else:                   os.remove(obj)
                if self.opts.verbose:  print 'done'
            except Exception, why:
                return self.ERR_AXSD;    print
                ps_lib.msg('error', '%s: %s' % (obj, str(why)) ); print
        print
    
_rd = _deltree
#____________________________________________________________________
class _echo(ConsoleAppBase):
    '''displays messages to the console
    
    echo [-h | -n] [messages...]
    
    echo            # Prints a blank line
    echo foo        # Prints msg
    echo -n foo     # Prints msg without carriage return/new line (\\n)
    echo -h foo     # Prints help message
    
    echo displays messages to the console.
    '''
    
    def register_opts(self):
        
        self.parser.add_option('-n', '--nocr',  action='store_true',
            dest='nocr', default=False, help='print msg without carriage return/new line')

    def run(self):
        if len(self.args) > 1:
            
            # a smarter join here that recognizes '' as null
            output = self.args[1]
            for arg in self.args[2:]:
                output = '%s %s' % (output, arg)
            print output,
    
        if not self.opts.nocr:  print

#____________________________________________________________________
class _erase(ConsoleAppBase):
    '''deletes files, use with caution
    
    erase [-h | -f] [files...]
    
    erase <file>       # Remove file
    erase *.txt        # Remove all files ending in .txt, after confirmation
    erase -f file1     # Remove files without confirmation
    
    erase deletes files, never to be seen again.  Use with caution.
    ? should there be an erase and a deltree?
    ? deltree more powerful, but dangerous '''
    
    def register_opts(self):
        
        self.parser.add_option('-f', '--force',  action='store_true',
            dest='force', default=False, help='don\'t ask for confirmation')

    def run(self):
        
        if len(self.args) < 1:
            ps_lib.msg('error', 'this command needs at least one parameter, \n' + \
                '\tthe name of the file (or files) to be removed.')
            print; print self.usage; print
            return self.ERR_ARGS
    
        # special case for delete command and unglobbing:
        confirm = not self.opts.force  # lame but compatible
        if po.wasunglobbed and confirm and not del_confirm('erase', self.args[1:]):
            return self.USR_RJCT
    
        for obj in self.args[1:]:
            if self.opts.verbose:
                if po.color:    print 'Removing %s ...' % po.colors['string'] % obj,
                else:           print 'Removing "%s" ...' % obj,
            try:
                os.remove(obj)
                if self.opts.verbose:  print 'done'
            except OSError, why:
                print;  ps_lib.msg('error', '%s: %s' % (obj, str(why)) ); print
                return self.ERR_OS; print
_rm = _erase

#____________________________________________________________________
class _evalps(ConsoleAppBase):
    '''evaluate a string from a command substitution as a new command line
    
    evalps [-h] <statement>
    
    evalps `dircolors -c /etc/DIR_COLORS`   # evaluate line
    evalps -h                               # Print this message
    
    evalps evaluates a string from a command substitution as a new command line.'''
    
    def run(self):
        
        if len(self.args) < 1:
            ps_lib.msg('error', 'this command needs at least one parameter, \n' + \
                '\ta statement to be executed.')
            print; print self.usage; print
            return self.ERR_ARGS
    
        import ps_main
        ps_main.process_file(string.join(self.args[1:]))

#____________________________________________________________________
class _exit(ConsoleAppBase):
    '''quit the command shell and return to parent

    exit [-h] [status]

    exit        # Quit
    exit 7      # Quit returning 7 to parent process
    exit -h     # Print this message
    
    exit quits the python shell (pyshell) and returns to the parent process.'''
    
    def run(self):
        status = 0
        if len(self.args) > 1:
            try:  status = int(self.args[1])
            except ValueError, why:
                ps_lib.msg('error', '"%s":  Number given must be a decimal integer.'
                    % self.args[1]); print
                return self.ERR_ARGS
        
        sys.exit(status)
_quit = _exit
#____________________________________________________________________
class _fg(ConsoleAppBase):
    '''bring a command to the foreground -

    not sure how to do this yet ;) NO WORKO.'''

    def run(self):

        del self.args[0]    # delete cmdlet name
        if len(self.args) > 0:
            try:
                number = int(self.args[0]) - 1
                job = po.jobs[number]
                #thisjob = (child.pid, line, child.stdin, child.stdout, child.stderr)
                zero, one, two = job[2], job[3], job[4]
                job[2], job[3], job[4] = sys.stdin, sys.stdout, sys.stderr

                if zero: zero.close()
                if one:  one.close()
                if two:  two.close()

            except Exception, why:
                ps_lib.msg('error', str(why)); print
        else:
            ps_lib.msg('error', 'This command needs one parameter, \n' + \
                'the name of the job to be brought forward.')
            print; print self.usage; print
            po.status = 1

#____________________________________________________________________
class _help(ConsoleAppBase):
    '''provides additional information and interactive help

    Please enter one of the following for more information.  Items in [brackets]
    are optional.  Usage: help <topic> [options]

    Pyshell:
    help  intro     [browser]   About pyshell
          cmddocs   [browser]   built-in commands documentation
          commands  [command]   list of built-in pyshell commands [or one]
          
    Python:
    help  tutorial  [browser]   launch python tutorial in a web browser
          modules               list all available python modules
          topics                list python topics
          keywords              list python reserved words
          help                  python interactive help
          
          [topic]               help on a module, keyword, or topic

    Search:
    help  apropos   [query]     search for an appropriate pyshell command
          modules   [query]     search for an appropriate python module'''

    def run(self):
        
        pi = po.namespace['pi']
        print '\n', pi.name, pi.version, ' Help Center'
        
        docfile = ''
        del self.args[0]
        if len(self.args) < 1:
            print self.usage; print
            return self.ERR_ARGS

        if   self.args[0] == 'commands':    print_commands(self.args[1:])
        elif self.args[0] == 'intro':       docfile = 'README.html'
        elif self.args[0] == 'cdmdocs':     docfile = 'builtins.html'
        elif self.args[0] == 'keywords':    help(self.args[0])
        elif self.args[0] == 'modules':     help(string.join(self.args))
        elif self.args[0] == 'topics':      help(string.join(self.args))
        elif self.args[0] == 'tutorial':
            print '\nExecuting Browser\n'
            docfile = '/usr/share/doc/python-docs-2.4.2/html/tut/tut.html'

        elif self.args[0] == 'apropos':

            if len(self.args) < 2:
                ps_lib.msg('error','Need keyword(s) to search for')
                return
            print
            for kw in po.keywords:
                doc = string.split(globals()[kw].__doc__, '\n')[0]
                if string.lower(self.args[1]) in doc:  # case insensitive
                    print_commands([kw[1:]])
            print
        else:  # help on a topic
            print
            help(string.join(self.args))

        if docfile:
            try:
                if len(self.args) > 1:
                    sub([self.args[1], docfile])
                    print [self.args[1], docfile]
                else:
                    sub(['prefapp', '-m', 'view', '-o', os.environ['PYSHELL_OPTIONS'], docfile])
            except Exception, why:
                print str(why)
                sub(['/usr/bin/firefox', docfile])



#____________________________________________________________________
class _history(ConsoleAppBase):
    '''print previously entered commands, enter search terms as parameters

    history [-h] [search terms]

    history         # Print complete history
    history foo     # Print only commands containing foo
    history -h      # Print help text

    history allows you to search and print your command history.
    '''

    def run(self):
        
        search = None
        del self.args[0]
        if self.args: search = string.join(self.args)
        try:
            import readline
            for i in range( readline.get_current_history_length() ):
                item = readline.get_history_item(i)
                if item:
                    if search:
                        if string.count(item, search):
                            print '  %04d  ' % i, item
                    else:   print '  %04d  ' % i, item
    
        except ImportError:
            msg = ('''Readline and history are not available on this platform (%s)
                or site.  Try using the arrow keys to access command history.'''
                % sys.platform )
            ps_lib.msg('error', msg); print
            return self.ERR_NA
_hist = _history
#____________________________________________________________________
class _jobs(ConsoleAppBase):
    '''list and manipulate child processes
    
    '''
    def run(self):
        print
        if len(po.jobs) == 0:
            print '  jobs: no jobs'
            return 0
        else:
            for i, job in enumerate(po.jobs):
                print '  [%s]  %s' % (i+1, job[1])
        print

#____________________________________________________________________
class _md(ConsoleAppBase):
    '''create a folder
    
    md [-h] [-p] <folder_name>
    
    md foo          # Creates the folder foo
    md foo/bar      # Creates the folder foo with a subfolder bar
    md -p foo/bar   # Same, for compatibility
    md -h           # Print help text
    
    md creates folders.'''
    
    def run(self):

        del self.args[0] # name
        while '-p' in self.args: self.args.remove('-p') # compatibility
        
        if len(self.args) < 1:
            ps_lib.msg('error', 'this command requires additional arguments')
            print self.usage; return self.ERR_ARGS
        
        try:
            for folder in self.args:
                if self.opts.verbose:
                    if po.color:    print 'creating: "%s" ...' % po.colors['string'] % folder,
                    else:           print 'creating: "%s" ...' % folder,
                os.makedirs(folder)
                if self.opts.verbose: print '  done'
                
        except OSError, why:
            print; ps_lib.msg('error', str(why)); print
            return self.ERR_OS
    
_makefolder = _mkdir = _md
#____________________________________________________________________
class _move(ConsoleAppBase):
    '''move a file or folder
    
    move [-h] <source> [destination]
    
    # todo: change below to examples
    move [-h]                       # Print help text
    move <source> <destination>     # move a file to destination file or folder
    move <sources> <dest_folder/>   # move files to a folder
    move <source>                   # move file to current folder[.] implied
    move <URL> <destination>        # move remote file to destination file, fd.
    
    Move moves files from one location to another.  If the files to be moved are
    on the same filesystem, they are simply renamed.  Otherwise, move copies
    files and folders to the destination, then removes the originals.'''
    
    def register_opts(self):
        
        self.parser.add_option('-g', '--progress',  action='store_true',
            dest='progress',
            help='show progress bar if copy will take a long time -- NOT IMPLEMENTED')

    def run(self):

        del self.args[0]  # get rid of command name for compatibility
    #   figure out what to do with self.args
        destisdir = False
        if len(self.args) == 0:                 # no self.args print usage
            ps_lib.msg('error', 'this command requires additional arguments')
            print self.usage; print; return self.ERR_ARGS
        if len(self.args) == 1:                 # source only, move to current f
            sources, dst = self.args[0], '.'
            destisdir = True
        else:                                   # 2 or more self.args
            sources, dst = self.args[0:-1], self.args[-1]
            if os.path.isdir(dst): destisdir = True
    
        # Convert to list if not
        type = globals()['__builtins__']['type'] # clash with type builtin
        if type(sources) is str:
            sources = [sources]
            
        if len(sources) > 1 and not destisdir:
            ps_lib.msg('error', 'when moving multiple files, last argument must be a directory.')
            print self.usage; print; return self.ERR_ARGS
    
        while dst in sources:  # needs smarter comparison to check real paths etc.
            ps_lib.msg('warning', 'omitting:%s' % dst)
            sources.remove(dst)
    
        for src in sources:
        
            if self.opts.verbose:
                if po.color:
                    print 'moving %s  -->  %s ...' \
                        % ( po.colors['string'] % src,
                            po.colors['string'] % dst),
                else:
                    print 'moving "%s"  -->  "%s" ...' % (src, dst),
            # do move
            try:
                shutil.move(src, dst)
                if self.opts.verbose:  print 'done'
            except IOError, why:
                print;  ps_lib.msg('error', str(why) )
                print; return self.ERR_IO
            except Exception, why:
                print;  ps_lib.msg('error', str(why) )
                print; return self.ERR_UNKN

_ren = _mv = _move #mv = move
#____________________________________________________________________
class _pause(ConsoleAppBase):
    '''wait for user to hit a key
    
    pause           # Wait for a key press
    pause [-h]      # Print help text
    
    pause waits until a user hits a key. (Only Enter key on posix for now)'''
    
    def run(self):

        if sys.platform == 'win32':
            print 'Press a key to continue. ',
            import msvcrt
            msvcrt.getch()
        elif os.name == 'posix': #pass
            print 'Press ENTER to continue. ',
            #import curses
            #curses.initscr().getch()
            # hmmm, clears screen and fucks up terminal, what to do?
            raw_input()
        print
#____________________________________________________________________
class _path(ConsoleAppBase):
    '''print or modify the execution path
    
    path [-h] [-p <VAR>] [set | pre | add | del] [path or path_fragment]
    
    path                        # Print execution path
    path set /fldr/             # Set path to /fldr/
    path pre /fldr/             # Prepend current path with /fldr/
    path add /fldr/             # Append current path with /fldr/
    path del /fldr/             # Remove /fldr/ from path
    path -h                     # Print help text
    path -u XPATH add /fldr/    # Manipulate another environment var., named XPATH
    
    path is a helpful utility to manipulate the execution path.'''
    
    def register_opts(self):
        
        self.parser.add_option('-u', '--usevar',  action='store', metavar='VAR',
            dest='usevar', default='PATH', help='specify another variable instead of PATH')

    def run(self):
        del self.args[0] # name
        var = self.opts.usevar
        
        def printpath():
            if os.environ.has_key(var):
                if po.color:
                    pathlist = os.environ[var].split(os.pathsep)
                    for i, folder in enumerate(pathlist):
                        pathlist[i] = po.colors['string'] % folder
                    print string.join(pathlist, os.pathsep)
                else:
                    print os.environ[var]
    
        if len(self.args) == 0:                      # pretty print path
            printpath()
            return
        elif len(self.args) == 2:                    # run command on path
            cmd, value = self.args[0], self.args[1]
            if   cmd == 'set':  os.environ[var] = value
            elif cmd == 'add':
                os.environ[var] = os.environ[var] + os.pathsep + value
    
            elif cmd == 'pre':
                os.environ[var] = value + os.pathsep + os.environ[var]
    
            elif cmd == 'del':
                pathlist = os.environ[var].split(os.pathsep)
                if not value in pathlist:
                    ps_lib.msg('error', '"%s" not in path' % value); print
                    po.status = 1; return
                while value in pathlist:
                    if self.opts.verbose: print 'Removing %s' % value
                    pathlist.remove(value)
                os.environ[var] = string.join(pathlist, os.pathsep)
            else:
                ps_lib.msg('error', 'unknown command:  "%s".' % cmd); print
                return self.ERR_ARGS
            if self.opts.verbose: printpath()         # pretty print new path
        else:
            ps_lib.msg('error', 'incorrect number of arguments')
            print self.usage; print
            return self.ERR_ARGS

#____________________________________________________________________
class _prompt(ConsoleAppBase):
    '''print or change the command prompt
    
    prompt [-h] [value]
    
    prompt 'pyshell> '      # Set prompt
    prompt -h               # Print help text

    Prompt is a helpful utility to manipulate the command prompt.'''
    
    def run(self):
    
        if len(self.args) < 2:
            if po.color:  print po.colorprompt
            else:         print po.prompt
            return

        prompt = string.join(self.args[1:])
        if self.opts.verbose: print 'Setting prompt to: ', prompt
        if po.color:    po.prompt = prompt
        else:           po.colorprompt = prompt
        
        
#____________________________________________________________________
class _pwd(ConsoleAppBase):
    '''print the working folder
    
    pwd [-h]
    
    pwd             # Print the current folder
    pwd -h          # Print help text
    
    pwd prints working folder.'''
#    pwd -r          # Print the fully resolved current folder
#    def register_opts(self):
        
#        self.parser.add_option('-r', '--resolvelinks',  action='store_true',
#            dest='resolve', default=False,
#            help='resolve links to find the true location of the current folder.')

    def run(self):
        
        folder = os.getcwd().replace('\\','/')  # Windows backslashes blow
        #if self.opts.resolve:
        #    result = os.readlink(folder)  # no worky
        #else:                   print folder
        print folder
        
_cwd = _currentfolder = _pwd
#____________________________________________________________________
class _py(ConsoleAppBase):
    '''execute a python statement, or a function using pyshell syntax.

    py [-h] [-q] [python_statement]
    
    py a = 5                # exec "a = 5" in python
    py -Q dude holmes       # Quote statement, i.e.  dude('holmes', 'homey')
    py -Q  write dude.{a,b,c}.jpg
                            # write('dude.a.jpg', 'dude.b.jpg', 'dude.c.jpg')
    py -h                   # Print help text
    
    The py command can execute a python statement, or a function using pyshell
    syntax and/or expansions.'''
    
    def register_opts(self):
        
        self.parser.add_option('-Q', '--quote',  action='store_true',
            dest='quote', default=False,
            help='quote given parameters for python')

    def run(self):
                
        del self.args[0]
        modify = False
        if self.opts.quote:  modify = True
    
        if len(self.args) > 1:
            if modify:
                statement = self.args[0] + '('
                for arg in self.args[1:]:
                    statement = "%s'%s', " % (statement, arg)
                if statement.endswith(', '): statement = statement[:-2]
                statement = statement + ')'
            else:
                statement = string.join(self.args)
            if po.opts.debug:  ps_lib.msg('debug',  'py executing:%s:' % statement)
            try:     exec(statement) in po.namespace # needs to execute in main namespace
            except Exception, why:
                ps_lib.msg('error', str(why) ); print
                return self.ERR_UNKN
        else:
            ps_lib.msg('error', 'this command requires additional arguments')
            print self.usage; print; return self.ERR_ARGS
        
        
        

#____________________________________________________________________
class _setenv(ConsoleAppBase):
    '''set or print variables in the environment
    
    setenv [-h] [-t] [name] [value]
    
    setenv                  # Print complete environment
    setenv foo              # Print variables containing foo in their name
    setenv DAY Mon          # Set DAY = Mon
    setenv DAY=Mon          # "
    setenv DAY = Mon        # "
    setenv DAY=             # Delete DAY
    
    setenv is a helpful utility to manipulate environment variables.  It accepts
    quite a few different syntax variations.'''

    def register_opts(self):
        
        self.parser.add_option('-t', '--truncate',  action='store_true',
            dest='truncate', default=False,
            help='Truncate variable to screen length.')

    def run(self):
    
        del self.args[0] # compatibility
        variables = os.environ.keys(); variables.sort()
        if   len(self.args) == 0:                            # No self.args, print everything
                print_variables(os.environ, istty=self.istty, truncate=self.opts.truncate)
        elif len(self.args) == 1:                            # one arg
            if '=' in self.args[0]:
                name, value = self.args[0].split('=', 1)
                if value:
                    os.environ[name] = value            # name=value, set it
                    if self.opts.verbose:  print_variable(name, os.environ[name], istty=self.istty)
                else:                                   # name=, remove
                    if self.opts.verbose: print 'Deleting: ', name
                    try: del os.environ[name]
                    except KeyError:
                        ps_lib.msg('error', '%s was not found.' % name); print
                        return self.ERR_DNE
            else:                                       # print, filtering output
                srch_results = {}
                for var in os.environ:
                    if string.count(var.lower(), self.args[0].lower()):
                        srch_results[var] = os.environ[var]
                if srch_results:  print_variables(srch_results, istty=self.istty, truncate=self.opts.truncate)
                elif self.opts.verbose:
                    ps_lib.msg('warning',
                        'an environment variable containing "%s" does not exist.'
                        % self.args[0])
                    return self.ERR_DNE
        else:                                           # length is 2 or greater
            if self.args[1] == '=':                          # if second param is standalone =
                if len(self.args) > 2:                       # additional self.args are set
                    name, value = self.args[0], string.join(self.args[2:])
                    os.environ[name] = value
                    if self.opts.verbose:  print_variable(name, os.environ[name], istty=self.istty, truncate=self.opts.truncate)
                else:                                   # no more self.args, delete
                    name = self.args[0]
                    if self.opts.verbose: print 'Deleting: ', name
                    try: del os.environ[self.args[0]]
                    except KeyError:
                        ps_lib.msg('error', '%s was not found.' % name); print
                        return self.ERR_DNE
            else:
                name, value = self.args[0], string.join(self.args[1:])
                if '=' in name:
                    name, extra = name.split('=', 1)
                    if extra: value = extra + ' ' + value
#                if '=' in value:
#                    extra, value = value.split('=', 1) # extra tossed
#                    if extra: ps_lib.msg('warning', 'extra: "%s" tossed.' % extra)
                if value.startswith('='): value = value[1:] # fix bug at setenv LS_COLORS no=00:fi...

                if value and not value.isspace():
                    os.environ[name] = value
                    if self.opts.verbose:
                        print_variable(name, os.environ[name], istty=self.istty,
                            truncate=self.opts.truncate)
                else:
                    try: del os.environ[name]
                    except KeyError:
                        ps_lib.msg('error', '%s was not found.' % name); print
                        return self.ERR_DNE
                    
#____________________________________________________________________
class _signal(ConsoleAppBase):
    '''send a signal to process
    
    signal <SIGNAME|name|#|list> <pid1> [pid2..]
    
    signal term 1103        # tell 1103 to quit. If it doesn't work, try kill
    signal SIGTERM 1103     # propeller-head equivalent
    signal 15  1103         # "
    signal kill 1103        # brutal last resort
    signal list             # list the various available signals
    signal -h               # Print help text

    signal sends signals to processes on posix based systems
    '''
 
    def run(self):
   
        import signal
        del self.args[0]
        if len(self.args) == 0:
            ps_lib.msg('error', 'this command requires additional arguments')
            print self.usage; return self.ERR_ARGS
    
        elif len(self.args) == 1 and self.args[0] == 'list':
            info = '''
         #  Name   Default Action    Comment
         -  ----   --------------    -------
         1  hup         terminate    Terminal disconnected (hang up)
         2  int         terminate    Interrupt from keyboard (^C)
         3  quit             core    Quit from keyboard (^D?)
         4  ill              core    Illegal instruction, you be ill'n
         5  trap             stop    Halt for debugger breakpoint
         6  iot              core    A.k.a. sigabrt, abnormal exit
         7  bus              core    Bus error, dump may fail
         8  fpe              core    Floating point exception
         9  kill        terminate    Brutal immediate kill, cannot be blocked
        10  usr1        terminate    Available to processed
        11  segv             core    Invalid memory reference
        12  usr2        terminate    Available to processes
        13  pipe        terminate    Wrote to a pipe with no readers
        14  alrm        terminate    Real timer clock
        15  term        terminate    Graceful exit
        16  stkflt         ignore    Coprocessor stack error, may not be avail
        17  chld           ignore    Child process stopped or terminated
        18  cont           resume    Continue if suspended (^Q)
        19  stop             stop    Suspend execution, can't be blocked (^S)
        20  tstp             stop    Suspend from tty
        21  ttin             stop    Background process requires input
        22  ttou             stop    Background process requires output
        23  urg            ignore    Urgent condition on socket
        24  xcpu             core    Cpu time limit exceeded
        25  xfsz             core    File size limit exceeded
        26  vtalrm      terminate    Virtual timer clock
        27  prof        terminate    Profile timer clock
        28  winch          ignore    Terminal window changed size
        29  poll        terminate    I/o now possible
        30  pwr            ignore    Power lost, may exit on some systems
        31  sys              core    Bad system call
            '''
            if po.color:
                info = info.replace('terminate ',  po.colors['Error'] % 'terminate ')
                info = info.replace('core',         po.colors['Critical'] % 'core')
                info = info.replace('resume',       po.colors['Info'] % 'resume')
                info = info.replace('stop ',        po.colors['Warning'] % 'stop ')
                print info
        else:
            sigtext, pids, i = self.args[0], self.args[1:], 0
            try:
                for i, pid in enumerate(pids):
                    pids[i] = int(pid)
            except ValueError:
                ps_lib.msg('error', 'Cannot convert process id (%s) to number.' % pids[i]); print
                return self.ERR_VALU
        
            try:
                signum = int(sigtext)
            except ValueError: # not a number, normalize text
                sigtext = sigtext.upper()
                if not sigtext.startswith('SIG'): sigtext = 'SIG%s' % sigtext
                if hasattr(signal, sigtext): signum = getattr(signal, sigtext)
                else:
                    ps_lib.msg('error', 'Cannot find signal:' % sigtext); print
                    return self.ERR_DNE
    
            if po.opts.debug: ps_lib.msg('debug', 'sigtext:%s, signum:%s, pid:%s' % (sigtext, signum, pid)); print
    
            try:
                for pid in pids:
                    if self.opts.verbose: print 'Sending signal %s to %s.' % (sigtext, pid)
                    os.kill(pid, signum)    # send signal, not necessarily kill ;)
            except OSError, why:            # no such process
                ps_lib.msg('error', str(why) ); print
                return self.ERR_OS
_sig = _signal
#____________________________________________________________________
class _source(ConsoleAppBase):
    '''executes a file in the current shell
    
    source <file>
    
    source file.psl     # Run file.psl
    source -h           # Print help text
    
    source executes commands from a file specified on the command line.'''
    
    def run(self):
        
        if (len(self.args) < 2):
            ps_lib.msg('error', 'This command needs at least one parameter, \n' + \
                '            the name of the file to be executed.'); print
            print self.usage; print
            return self.ERR_ARGS
    
        for filename in self.args[1:]:
            if os.access(filename, os.F_OK): po.process_file(filename)
            else:
                ps_lib.msg('error', 'File "%s" cannot be found.' % filename)
                print

#____________________________________________________________________
class _trash(ConsoleAppBase):
    '''puts files in the system trash can
    
    trash <files>
    
    trash foo           # Run file.psl
    trash -h            # Print help text
    
    trash moves files to the trash bin, where they can be later removed
    or restored.
    
    Bug:    if files are on another filesystem, they will be copied
            to the one with the home folder.'''
    
    def run(self):

        del self.args[0] # del name
        if len(self.args) < 1:
            ps_lib.msg('error', 'This command needs at least one parameter, \n' + \
                '            the name(s) of the file (or files) to be removed.')
            print self.usage; print
            return self.ERR_ARGS

        # special case for delete command and unglobbing:
        if po.wasunglobbed and not _del_confirm('trash', self.args): return

        # try with move builtin
        if sys.platform == 'win32': dst = '\\recycler'
        elif os.name == 'posix':    dst = os.path.expanduser('~/.Trash')
        else:
            print 'OS not supported.'
            return self.ERR_NA
    
        self.args.append(dst)
        runcmd('_move', self.args)

_dele = _trash
#____________________________________________________________________
class _type(ConsoleAppBase):
    '''displays text from stdin or files from the command line
    
    type <files>
    
    type foo
    type -h
    
    type displays files from the command line.
    '''

    def run(self):
        
        del self.args[0]
        if (len(self.args) < 1):
            ps_lib.msg('error', 'This command needs at least one parameter, \n' + \
                '            the name(s) of the file (or files) to be printed.')
            print self.usage; print
            return self.ERR_ARGS
    
        for filename in self.args:
            try:
                if filename == '-':
                    for line in sys.stdin:          print line,
                else:
                    for line in file(filename):     print line, #.upper(),
            except IOError, why:
                ps_lib.msg('error', str(why) ); print
                return self.ERR_IO
        print
_cat = _type
#____________________________________________________________________
class _ver(ConsoleAppBase):
    '''print the version of the current python shell
        
    ver [-h]
    
    ver         # Print version info
    ver -h      # Print help text
    
    ver prints the version of the current python shell.'''
    
    def run(self):
            
        pi = po.namespace['pi']
        ps_lib.msg('Info', '%s %s (Python: %s)' % (pi.name, pi.version, sys.version.split()[0]) )
        print
        
 #____________________________________________________________________
#____________________________________________________________________
class _vars(ConsoleAppBase):
    '''prints the currently available variables
    
    vars [-h]
    
    vars        # Print current variables
    vars -h     # Print help text
    
    vars prints the currently available variables.'''
    
    def run(self):
            
        # prepare
        type = globals()['__builtins__']['type'] # clash with type builtin
        info = ''
        if pi.caps['term']: maxwidth = ansi.getTermSize()[0] - 26
        else:               maxwidth = 78
        vars = po.namespace.keys()
        vars.sort()
        for var in ['pdir', 'po', 'pi', 'os', 'sys','__builtins__']:
            vars.remove(var)
            vars.insert(0, var)
        
        padding = 5  # find longest var
        for var in vars:
            length = len(var)
            if length > padding: padding = length
        
        for var in vars:

            vartype = type(po.namespace[var])
            reprstr = repr(po.namespace[var])
            format = 'blank'
            
            if vartype is dict and len(reprstr) > (maxwidth + 3):
                value = reprstr
                value = value[:maxwidth] + '...'
            else: value = po.namespace[var]
        
            if   vartype is str: format = 'string'
            elif vartype is int: format = 'int'
        
            if po.color:
                print_variable(var, value, vtype=format, istty=self.istty, padding=-padding)
            else:           info = '%s\n    %-15.15s = %s' % (info, var, value)

        #ps_lib.msg('Info', info)
        print
#____________________________________________________________________
class _which(ConsoleAppBase):
    '''returns the types and locations of commands
    
    which [-h] <name>
    
    which foo       # Print type and/or location of foo
    which -i foo    # Print complete info about foo
    which -h        # Print help text
    
    which returns the types and locations of commands.'''
    
    def register_opts(self):
        
        self.parser.add_option('-i', '--info', action='store_true',
            default=False, dest='info', help='show print extra info')

    def run(self):
        
        del self.args[0]
        if len(self.args) < 1:
            ps_lib.msg('error','this command requires at least one parameter')
            print self.usage;  print; return self.ERR_ARGS
    
        #if self.args[0] == '-n': del self.args[0] # no banner
        #else:
        if self.opts.info:
            print
            print '%-13s %-13s %-13s %s\n' % ('Command', 'Type', 'Category', 'Value')
    
        for command in self.args:
            typ, stype, comment = ps_lib.examine_type([command], {})
            if self.opts.info:
                print '%-13s %-13s %-13s %s' % (command, typ, stype, comment)
                print
            else:
                if typ == 'system': print comment
                else:
                    print '%-13s %-13s %-13s %s' % (command, typ, stype, comment)
