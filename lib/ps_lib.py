''' ps_lib - library of utility functions for pyshell use.
    by Mike Miller 2004-2005
    released under the GNU public license, (GPL) version 2
'''
import string, sys, os, glob, threading, keyword, atexit, subprocess, optparse
import ansi
from ps_cfg import *
#if sys.platform == 'win32':
#    import winsound
#    readline = False
#elif os.name == 'posix':
#    winsound = False
#    import readline
#
# should move to capabilities obj
try:                import winsound
except ImportError: winsound = None
try:                import readline
except ImportError: readline = None
    

#___Common Funciones______________________________________________________________

def background_job(linelist, started=False):
    '''run a command in the background and check on it in a separate thread.
    This implementation needs to be replaced.
    '''
    if started == False:  # start this puppy again in a new thread
       # shortcut to make a new thread
       t = threading.Timer(0, background_job, [linelist], {'started': True})
       t.start()
       return

    line = string.join(linelist)
    try:
        #child = sp.Popen(linelist, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT, close_fds=True)
        child = subprocess.Popen(linelist, close_fds=True)
        thisjob = [child.pid, line, child.stdin, child.stdout, child.stderr]
        po.jobs.append(thisjob)
        print; msg('info','job: %s' % thisjob)

        print_prompt()
        sys.stdout.flush()

        returncode = child.wait()  # what should I do with return code on a background process?
        print; msg('info','job \'%s\' complete.' % line)
        po.jobs.remove(thisjob)
    except OSError, why:
        msg('error', str(why)); print

    print_prompt()
    sys.stdout.flush()

#____________________________________________________________________
def print_prompt():
    if po.color: print eval_str(po.colorprompt).replace('\001','').replace('\002',''),
    else:        print eval_str(po.prompt),  # get prompt

#____________________________________________________________________
def beep(btype='Info'):
    'beep the console, beep the console'

    if po.audio:
       if    btype == 'Info':                       # nice boop
           if winsound: winsound.Beep(100, 20)
           else: pass # what to do?
       elif  btype == 'Debug': pass
       else:                                        # Annoying error Beeeep!
          if winsound: winsound.Beep(800, 80)
          else: sys.stdout.write('\a')

#____________________________________________________________________
def code_char(char):
    'convert chars in line to decimal %007 format, if necessary'
    ex = po.sym_expansion

    if   char == '\\':  char = '%s092' % ex
    elif char == "'":   char = '%s039' % ex
    elif char == '"':   char = '%s034' % ex
    elif char == 'a':   char = '%s007' % ex
    elif char == 'b':   char = '%s008' % ex
    elif char == 'f':   char = '%s012' % ex
    elif char == 'n':   char = '%s010' % ex
    elif char == 't':   char = '%s009' % ex
    elif char == '' :   char = '%s000' % ex
    else:
       char = '%s%03u' % (ex, ord(char))

    return char # or several

#____________________________________________________________________
def cmd_substition(fragment):
    '''execute any sub-commands inside back-ticks (acute accents) and replace
    the expression with the output of the command'''

    tokens = fragment.split('`')
    length = len(tokens)
    destlist = []
    if length == 0: return ''
    import subprocess
    sp = subprocess

    for i, token in enumerate(tokens):  # there may be several `x` substitutions
        if i % 2: # this is a command
            output = sp.Popen(token.split(), stdout=sp.PIPE).communicate()[0]
            destlist.append(output.rstrip())
        else: # a regular string.
            destlist.append(token)

    return string.join(destlist, '')


#____________________________________________________________________
def download(srcpath, destpath, report_hook=None, resume=True):
    '''Download a file from a URL, resuming if desired.
    Throws DownloadError if resume fails '''

    import urllib, os.path

    def resumefile():

        if po.opts.verbose: print 'Resuming file ...'
        class DownloadError(Exception): pass
        class URLOpener(urllib.FancyURLopener):
            ''' Create sub-class in order to overide error 206.  This error means a
                partial file is being sent,  which is ok in this case.  Do nothing with this error.
            '''
            def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
                pass
            def http_error_416(self, url, fp, errcode, errmsg, headers, data=None):
                # REQUESTED_RANGE_NOT_SATISFIABLE
                raise DownloadError, 'Local file equal or larger than remote.' + headers
                return
        Urlclass = URLOpener()

        existSize = os.path.getsize(destpath)
        outputFile = open(destpath,'ab')
        Urlclass.addheader('Range','bytes=%s-' % (existSize))
        opener = Urlclass.open(srcpath)

        # sanity checks
        length = int(opener.headers['Content-length'])
        if po.opts.verbose:
            print 'existing size:', existSize
            print 'remaining:', length
            print 'total:', length + existSize

        # download file
        blocksize = 8192
        count = existSize / blocksize
        
        while True:
            data = opener.read(blocksize)
            if not data:  break
            outputFile.write(data)
            count = count + 1
            if report_hook: report_hook(count, blocksize, existSize + length)

        # clean up
        opener.close()
        outputFile.close()

    def retrieve():
        if report_hook:  urllib.urlretrieve(srcpath, destpath, report_hook)
        else:            urllib.urlretrieve(srcpath, destpath)

    # Get file
    if os.path.exists(destpath) and os.path.getsize(destpath) <> 0:

        if resume:  resumefile()
        else:       retrieve()

    else:
        retrieve()


#____________________________________________________________________
def escape_line(line):
    '''look thru line for quotage.  return the string checked and escaped'''
    isquoted, iscmd = False, False
    i = 0

    newline = ''
    while i < len(line):
       char = line[i]
       if char == '#': break  # comment, duh
       if char == '\\' and i+1 < len(line):
          if isquoted == "'":  pass
             #char = code_char(char, kind='full')
          elif isquoted == '"':
             i = i + 1   # skip to next, dumping backslash
             char = code_char(line[i])
          else:
             i = i + 1   # skip to next, dumping backslash
             char = code_char(line[i])
       # experiment, if everything escaped, why do we need quotes?
       elif char in pi.sym_quotes:
          if not isquoted:
             isquoted = char            # new one
             i = i + 1;                 # next char
             if line[i] == isquoted:    # if next is same it is null
                isquoted = False        # reset, found second
                char = code_char('')
                #print 'found!'
                #i = i + 1;              # next, next char
             else: continue
          elif isquoted == char:
             isquoted = False       # reset, found second
             i = i + 1; continue    # without adding the quote
          else:  char = code_char(char)  # different type of quote, but quoted, ignore

       elif char in pi.sym_metachars:
          if isquoted == "'": char = code_char(char)
          elif char is '`':   iscmd = not iscmd

       elif char in pi.sym_splitchars or char in pi.sym_globchars or char == '~':
          if isquoted:  char = code_char(char)
          elif char is ' ' and iscmd:   char = code_char(char)

          #else:
          #    if i > 0 and line[i-1] not in string.whitespace:
       # else: a normal char, leave unchanged for now
       newline = newline + char
       i = i + 1

    if isquoted:   # we have an odd number of top level quotes
       raise ValueError('unbalanced quotes')
    return newline

#____________________________________________________________________
def eval_str(string, replacehome=True):
    'return a string built from executing python code'
    try:
        if po.opts.debug: msg('debug','exec_str:' + string + ':')
        if replacehome: result = eval(string).replace(os.path.expanduser('~'),'~')
        else:           result = eval(string)
        return result
    except Exception, why:
        mesg = '%s: %s' %  (type(why), str(why))
        msg('error', 'Eval String: ' + mesg); print
        return msg


#____________________________________________________________________
def examine_type(linelist, namespc, checkaliases=True):
    'guess the line type by first word and other attributes'

    word = linelist[0]

    # magnum p.i. - pyshell command?   category   linetype    comment
    if word in pi.branch_words:         return ('pyshell', 'loop_keyword', word)
    if ('_' + word) in po.keywords:     return ('pyshell', 'keyword', '')
    if '=' in word:                     return ('pyshell', 'env', word[1:])
    if checkaliases and word in po.aliases:
                                        return ('pyshell', 'alias', po.aliases[word])
    if word.startswith('#'):            return ('comment', '', 'skip')
    if word.startswith(po.sym_expansion):
                                        return ('pyshell', 'variable', '')

    # Python checks
    if word in keyword.kwlist:          return ('python', 'keyword', '')
    if word.startswith('"'):            return ('python', 'docstring', '')
    if word.startswith("'"):            return ('python', 'docstring', '')

    # if  an absolute or relative path
    if '/' in word:                     return ('system', 'executable', word)

    if namespc:
        # look for variables and attributes--strip off any punctuation at end
        newword = ''
        for char in word:  # check for junk
           if char in string.letters or char in string.digits or char in '.':
              newword = newword + char
           else: break  # colonectomy
        #word = newword
        # maybe look for neword instead

        # look for existing objects
        if newword in namespc and len(linelist) == 1:
                                        return ('python', 'variable', newword)
        if newword in globals()['__builtins__']:
                                        return ('python', 'builtin', newword)
        # extended namespace check
        if '.' in newword:
           try:
              current = ''
              for item in string.split(word, '.'):
                 if current:    current = vars(current)[item]
                 else:          current = namespc[item]
              return ('python', 'attribute', '') # if we made it here it is a valid variable
           except KeyError:
              pass  # didn't find it

    if (len(linelist) > 1 and
        linelist[1] == '='):            return ('python', 'declaration', '') # set a var=

    # this is the most expensive, do last.
    fullpath = find_in_sys_path(word)
    if fullpath:    # handle spaces in path and conv \ to /
       fullpath = fullpath.replace(' ', '%032').replace('\\','/') # escape somewhere else
       return ('system', 'executable', fullpath)
    # still couldn't find it
    return  ('inconclusive', '-', 'not found')


#____________________________________________________________________
def examine_redir(linelist, stdio):
    'check statement for i/o redirection.'

    newlist = []
    length = len(linelist)
    detours = [None, None, None, None]
    shouldcontinue = True
    symbol_table = [
        (0, pi.sym_rin_here,    'h'),
        (0, pi.sym_rin,         'r'),
        (2, pi.sym_rerr_app,    'a'),
        (2, pi.sym_rerr,        'w'),
        (1, pi.sym_rout_app,    'a'),
        (1, pi.sym_rout,        'w')#,
        #(3, pi.sym_routerr_app, 'a'),
        #(3, pi.sym_routerr,     'w')
        ]  # longer strings need to be checked first
    i = 0
    while i < length:
        token = linelist[i]
        found = False
        for fd, symbol, mode in symbol_table:
            if symbol in token:
                found = True
                if len(token) > len(symbol):    # check if token has anything else attached
                    #print 'token:%s is longer than symbol' % token
                    before, after = token.split(symbol)

                    if before: newlist.append(before) # previous text should be retuned
                    if after: detours[fd] = (after, mode)
                    else: # after (filename) is next token
                        i = i + 1
                        detours[fd] = (linelist[i], mode)
                        break
                else:  # if equal size, next token should be filename
                    #print 'token:%s is symbol' % token
                    i = i + 1
                    detours[fd] = (linelist[i], mode)
                    break
        if not found:
            #print 'no symbols in token:%s, appending' % token
            newlist.append(token)
        i = i + 1

    if po.opts.debug:
        msg('debug', 'ex <<redr>>: %s / input:%s / output:%s / err:%s' %
            (newlist, detours[0], detours[1], detours[2]) )

    try:
        for i, detour in enumerate(detours):
            #print 'detour: ', detour
            filestr, line = '', ''
            # convert each to file obj if not null
            if detour:
                thefile, mode = detour[0], detour[1]
                if i == 0 and mode == 'h':
                    while line.strip() <> thefile:
                        line = sys.stdin.readline()
                        filestr = filestr + line
                    #import StringIO, wont work because it doesn't have fileno()
                    #detours[0] = StringIO.StringIO(filestr)
                    import tempfile
                    fd, path = tempfile.mkstemp()
                    fileobj = os.fdopen(fd, 'w')
                    fileobj.write(filestr);  fileobj.close()
                    detours[0] = file(path, 'r')  # reopen for reading
                    os.unlink(path)
                else:
                    detours[i] = file(thefile, mode)
                if   i == 0:  sys.stdin  = detours[i]
                elif i == 1:  sys.stdout = detours[i]
                elif i == 2:  sys.stderr = detours[i]
    except IOError, why:   # major clean up time
        msg('error', str(why) )
        po.status = int( string.split(str(why))[1][:-1] )

        sys.stdin, sys.stdout, sys.stderr = stdio
        for fobj in detours:
            if fobj and hasattr(fobj, 'close'): fobj.close()
        #detours[0] = detours[1] = detours[2] = detours[3] = None
        detours = [None, None, None, None]

    return newlist, detours


#____________________________________________________________________
def expand_aliases(linelist):
    'Expand alias from first word of line, and return result. '

    #linelist = line.split()
    if len(linelist) < 1: return [''], False
    firstword = linelist[0]
    previous, expanded = '', False

    while firstword in po.aliases:

        if firstword == previous: break # don't expand same more than once
        del(linelist[0])                # get rid of original word
        linelist = po.aliases[firstword].split() + linelist # insert alias at 0

        # now swap to new values to prepare for next loop
        previous = firstword
        firstword = linelist[0]
        expanded = True

        if po.opts.debug:
            msg('debug', 'exp alias: %s' % string.join(linelist) )

    #return string.join(linelist), expanded
    return linelist, expanded


#____________________________________________________________________
def expand_braces(token):
    'Look thru string looking for braces to expand, and return result. '

    before, after, result = '', '', ''
    # minimal checking for errors because the { } chars must exist before getting here
    i = token.index('{');  j = token.index('}')
    if j < i: return token # bogus

    #check for var subst char %, and stop if so. This is variable substitution.
    try:
       if token[i-1] == po.sym_expansion: return token
    except IndexError: pass

    before = token[:i];    meat = token[i+1:j];    after = token[j+1:]
    for item in meat.split(','):
       result = '%s%s%s%s ' % (result, before, item, after)
    return result.rstrip() # remove last space


#____________________________________________________________________
def expand_escapes(token):
    'Look thru string looking for escape sequences to expand, and return result. '

    varchars = string.ascii_letters + string.digits + '_-.'
    result, i = '', 0
    length = len(token)
    while i < length:
        char = token[i]
        if char == po.sym_expansion:
            var = ''
            if token[i+1:i+2] == po.sym_expansion:      # next char is same '%'
                result = result + char
                i = i + 2
                continue
            else:                                       # bare pysh var or
                i = i + 1                               # escape char syntax
                char = token[i:i+1]
                if char in string.digits:               # %9
                    digit = 1
                    while char and char in string.digits:  # max three digits
                        if digit == 4: break            # go up to 3
                        var = var + char
                        i = i + 1
                        char = token[i:i+1]
                        digit = digit + 1
                    #print 'debug: var:', var
                    #print 'getvar: {%s}' % getvar(var, {})
                    result += getvar(var, {})           # replace sequence
                    #print 'result: {%s}' % result
                    if char: continue
                else:                                   # bare pysh var
                    while char and char in varchars:
                        var = var + char
                        i = i + 1
                        char = token[i:i+1]
                    result = result + getvar(var, namespace)
                    if char: continue
        else:                                           # regular char, just
            result = result + char                      # append to result
        i = i + 1
    if po.opts.debug:  msg('debug', 'exp escapes: [%s] has expanded to [%s]:  ' % (token, result) )
    return result


#____________________________________________________________________
def expand_vars(token, namespace):
    'Look thru string looking for variables to expand, and return result. '

    #if po.sym_expansion not in token:  return token  #'%' not needed, checking beforehand
    varchars = string.ascii_letters + string.digits + '_-.'
    result, i = '', 0
    length = len(token)
    while i < length:
        char = token[i]
        if char == po.sym_expansion:
            var = ''
            if token[i+1:i+2] == po.sym_expansion:      # next char is same '%'
                result = '%s%%%%' % result
                i = i + 2
                continue
            elif token[i+1:i+2] == '{':                 # bracketed for env
                token = token[i+2:]
                length = len(token)
                try:
                    i = token.index('}')
                    var = token[:i]
                    if var in os.environ:
                        result = result + os.environ[var]
                    i = i + 1
                except ValueError:
                    result = result + token
                    i = length - 1
                continue
            elif token[i+1:i+2] == '(':                 # bracketed for pysh
                token = token[i+2:]
                length = len(token)
                try:
                    i = token.index(')')
                    var = token[:i]
                    result = result + getvar(var, namespace)
                except ValueError:
                    result = result + token
                    i = length - 1
            else:                                       # bare pysh var or
                i = i + 1                               # escape char syntax
                char = token[i:i+1]
                if char == '*':                         # %* in script
                    result = result + getvar(char, namespace)
                    i = i + 1
                elif char in string.digits:             # %123 esc skip
                    result = '%s%%%s' % (result, char)  # % was chopped
                    i = i + 1
                    continue
                else:                                   # bare pysh var
                    while char and char in varchars:
                        var = var + char
                        i = i + 1
                        char = token[i:i+1]
                    result = result + getvar(var, namespace)
                    if char: continue
        else:                                           # regular char, just
            result = result + char                      # append to result
        i = i + 1
    if po.opts.debug:  msg('debug', 'exp var: [%s] has expanded to [%s]:  ' % (token, result) )
    return result

#____________________________________________________________________
def find_in_sys_path(program):
    '''Find a program on the system path to execute.  This is a simple, dos-like
    implementation that checks the entire path every time and does no caching.
    Bonus is that you don't have to rehash after modifying path.'''

      #  optimize this
    if sys.platform == 'win32':
       try:    pathexts = os.environ['pathext'].split(os.pathsep) + ['']
       except:   pathexts = ['.COM', '.EXE', '']

    if not os.environ.has_key('PATH'): return None
    for folder in os.environ['PATH'].split(os.pathsep):

       if sys.platform == 'win32':
          for ext in pathexts:  # check for every executable extension
             progext = ('%s%s' % (program, ext)).lower()
             if os.access(folder, os.R_OK) and progext in os.listdir(folder):
                # file should end in a executable path extension
                if '.' + progext.split('.')[-1].upper() in pathexts[:-1]:
                    return os.path.join(folder, progext)
       else:  # unix or like
          if os.access(folder, os.R_OK) and program in os.listdir(folder):
             path = os.path.join(folder, program)
             if os.access(path, os.X_OK):
                return os.path.join(folder, program)
    # else, not found
    return None

#____________________________________________________________________
def getinputline(infile):
    'return a line or two from the input file - is this obsolete?'

    previousline, line = '', ''
    isloop = False
    while True:
       if po.runmode == 'file':
          line = infile.readline()
          if line.isspace():  continue
          if line == '':    break # EOF
       elif po.runmode == 'interactive':
          if previousline:    prompt = 'more> '
          else:
                #prompt = process_prompt()
                prompt = exec_str(po.prompt)
                ansi.xtermTitle(exec_str(po.title))
          try:           line = raw_input(prompt)
          except EOFError:    break #sys.exit(1) # ^Z
          except KeyboardInterrupt:
             print;       continue
          if line.isspace():  line = ''  # make sure line is true
          if line == '' and not previousline: continue
       else:  return infile # string passed from -c " "

       # check if we need more input
       if   line and line[-1] == '\\':                # get more
             previousline = previousline + line[:-1]
             continue
       elif line and line.split()[0] in pi.branch_words:    # get more
             previousline = previousline + line
             isloop = True
             continue
       elif line and isloop:                       # spaces for auto indent
             previousline = previousline + '\n' + line
             continue
       else: # line is nada '', and a previous line exists
          isloop = False
          if previousline:
             line = previousline + line
             previousline = ''

       if po.opts.debug:
          if po.runmode == 'file':   msg('debug', 'file:%s> %s' % (infile.name, line) )
          else:                     msg('debug', '%s> %s' % (po.runmode, line) )

       return line
    return None

#____________________________________________________________________
def getvar(var, namespace):
    'return the value of a variable by name'
    result = ''
    try: # to expand
       if len(var) == 3 and var[0] in string.digits:
          # is an escaped char, not a name
            try:
                tmp = chr(int(var))
                #print 'getvar: character is: {%s}' % tmp
                if tmp == '\x00':   result = result + ''
                else:               result = result + tmp
            except (ValueError, TypeError): pass

       elif var in namespace:  # regular python variable
          result = result + str(namespace[var])

       elif '.' in var: # check to see if var is an object w/ attribs
          current = ''
          for item in string.split(var, '.'):
             if not current:  current = namespace[item]
             else:        current = vars(current)[item]
          result = result + str(current)
       else: raise KeyError
    except KeyError:  pass         # we couldn't find it (keyerror),
                          # return nada so user knows var DNE
    #print 'getvar: result: {%s}' % result
    return result


#____________________________________________________________________
def check_config():
    '''Install configuration files into proper locations.
        check conf directories and create if they do not exist'''
        
    import fromipy, shutil
    # user config
    dirname = '.pyshell'
    homedir = fromipy.get_home_dir()
    confdir = os.path.join(homedir, dirname)
    #print confdir, '/home/mgmiller/.pyshell'
    try:
        if not os.access(confdir, os.F_OK):
            
            print 'pyshell:  installing user configuration files into %s\n' % confdir
            shutil.copytree('conf', confdir)
            
        #system wide config
        if os.name == 'posix':
            conffile = confdir + '/system_login.psl'  # still user confdir
            confdir = '/etc/pyshell'  # new confdir
        
            if not os.access(confdir, os.F_OK):
                if os.getuid() == 0:  # root
                    print 'pyshell:  installing system configuration files into %s' % confdir
                    os.makedirs(confdir)
                    if os.access(conffile, os.R_OK):  shutil.move(conffile, confdir)
                else:
                    msg('warning', 'Pyshell must be run as root once to install the system wide config in /etc/pyshell/.  Alternatively create the folder, and copy conf/system_login.psl there.')
                print
    except Exception, why:
        msg('error', 'Could not install initialization files: %s' % str(why))
        print
# check config files

#____________________________________________________________________
def line_split(line):
    '''split command line into several sub commands if needed.  Returns a list
    of tuples, that contain each (line, continuation mode)'''

    length = len(line)
    lines = []
    mark = 0
    skipchar = False
    for i, char in enumerate(line):
       if skipchar:
          skipchar = False;  continue
       if char in [pi.sym_cont, pi.sym_contback, pi.sym_pipe]: #, pi.sym_loopsplit]:
          delimeter = char
          if i+1 < length:
             if ( line[i:i+2] == pi.sym_contsuccess or
                line[i:i+2] == pi.sym_contfail ):
                #print 'found double!'
                delimeter = line[i:i+2] # two chars
                skipchar = True

          if delimeter == pi.sym_loopsplit: delimeter = pi.sym_contsuccess
          lines.append(  (line[mark:i].strip(), delimeter) )
          mark = i + len(delimeter)  # new begining

       elif char == '\n':
          if line[mark:i] == '' or line[mark:i].isspace():    continue
          lines.append(  (line[mark:i].strip(), pi.sym_cont) )
          mark = i + len(char)  # new begining

       else:
          if i+1 == length:  # if last char
             #if line[mark:].split() == []: break  # if only whitespace stop
             if line[mark:].isspace(): break  # clip empty cmd from end
             # no more delimeters, append the rest of line
             lines.append( (line[mark:].strip(), pi.sym_cont) )
    return lines


#____________________________________________________________________
def load_init_files(initfiles):
    'process the initialization files'

    for filename in initfiles:

        filename = os.path.expanduser( os.path.join(po.configpath, filename) )
        if po.opts.debug: msg('warning', 'processing filename:%s:' % filename)

        if os.access(filename, os.R_OK):
            if   filename.endswith('history'):
               if readline: readline.read_history_file(filename)
            elif filename.endswith('out.psl'):  atexit.register(po.process_file, filename)
            else:                               po.process_file(filename)

        if filename.endswith('history'):  # should really check at shutdown
            if os.access(filename, os.W_OK) and readline:
                atexit.register(readline.write_history_file, filename)

#____________________________________________________________________
def msg(mtype, message):
    'send a message in a standard format to the console'

    mtype = mtype.title()
    if hasattr(po, 'colors'):  colors = po.colors

    if mtype == 'Error' or mtype == 'Critical':
        if po.color:
            print >> sys.stderr, '\n   ', colors[mtype] % mtype + ': ',
            print >> sys.stderr, message
        else:
            print >> sys.stderr, '\n  ' + mtype + ':  ' + message
        beep(mtype)
    elif mtype == 'Warning':
        if po.color:    print colors[mtype] % mtype + ':  ' + message # no beep
        else:           print mtype + ':  ' + message # no beep
        beep(mtype)
    elif mtype == 'Debug':
        if po.color:    print colors[mtype] % mtype + ':  ' + message # no beep
        else:           print mtype + ':  ' + message # no beep
    elif mtype == 'Info':
        if po.color:    print colors[mtype] % mtype + ':  ' + message # no beep
        else:           print mtype + ':  ' + message # no beep
    else:
        print >> sys.stderr, mtype + ':  ' + message

#____________________________________________________________________
def search_hist(query):
    'Search history from rear to find a statement that fits'

    if readline:
        #import readline
        for i in range( readline.get_current_history_length()-1, -1, -1 ):
            item = readline.get_history_item(i)
            if item and item.startswith(query):
                    return item

    else:
        msg = ('''Readline and history are not available on this platform (%s)
            or site.  Try using the arrow keys to access command history.'''
            % pform )
        ps_lib.msg('error', msg); print
    
        return None

#____________________________________________________________________
def should_continue(contmode):
    'decide whether to continue to the next stmt on a multiple stmt line.'

    # if compound command line check what to do next
    if (contmode == pi.sym_cont or
        contmode == pi.sym_contback or
        contmode == pi.sym_pipe):           return True # ;| &
    elif (contmode == pi.sym_contsuccess
        and po.status == 0):                return True # &&
    elif (contmode == pi.sym_contfail
        and po.status <> 0):                return True # ||
    # stop processing statements on this line
    else:                                   return False


#____________________________________________________________________
def unescape(token, namespace, mode='var'):
    ' Look thru string looking for variables to expand, and return result. '

    #if po.sym_expansion not in token:  return token  #'%' not needed, checkin beforehand
    if po.opts.debug:  print 'ev: token has %:  ', token

    varchars = string.ascii_letters + string.digits + '_-.'
    result, i = '', 0
    length = len(token)
    while i < length:
       char = token[i]
       if char == po.sym_expansion:
          if token[i+1:i+2] == po.sym_expansion: # next char is same '%'
             result = result + char
             i = i + 2
             print result, i
             continue
          elif token[i + 1:i + 2] == '{':    # this variable is bracketed for env
             token = token[i+2:]
             length = len(token)
             try:
                i = token.index('}')
                var = token[:i]
                if var in os.environ:
                    result = result + os.environ[var]
                i = i + 1
             except ValueError:
                result = result + token
                i = length - 1
             continue
          var = ''
          if   token[i+1:i+2] == '(':    # this variable is bracketed for py
             token = token[i+2:]
             length = len(token)
             try:
                i = token.index(')')
                var = token[:i]
                result = result + getvar(var, namespace)
             except ValueError:
                result = result + token
                i = length - 1
          else:                    # this variable is bare, python var
             i = i + 1              # or escape char syntax, grab 3 #'s
             char = token[i:i+1]
             if char == '*':  # bug with positional params
                result = result + getvar(char, namespace)
                i = i + 1
             elif char in string.digits:  # bug with positional script params
                digit = 1
                while char and char in string.digits:  # max three digits
                    var = var + char
                    if digit == 4: break  # go up to 3
                    i = i + 1
                    char = token[i:i+1]
                    digit = digit + 1

                if mode == 'unescape' or len(var) < 3:
                       result += getvar(var, namespace)#regular var
                else:    result += '%' + var  # var mode skip esc char
                if char: continue
             else:
                while char and char in varchars:
                    var = var + char
                    i = i + 1
                    char = token[i:i+1]
                result = result + getvar(var, namespace)
                if char: continue
       else:
          result = result + char
       i = i + 1
    return result


#____________________________________________________________________
def unglob_token(token):
    'unglob a string, if it needs it'
    unglobbed = []
    for char in [ '*', '?', '[', ']']:
       if char in token:           # if glob char do unglob
          unglobbed = glob.glob(token)
          if po.opts.debug:  msg('debug',  'uglob:%s  to:%s' % (token, unglobbed) )
          break

#    if unglobbed: return unglobbed
#    else:        return False
    return unglobbed
