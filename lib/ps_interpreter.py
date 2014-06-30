''' ps_interpreter - pyshell commandps_interpreter.interpreter, by Mike Miller 2004-2005
    by Mike Miller 2004-2005
    released under the GNU public license, (GPL) version 2
'''
import os, sys, string
from StringIO import StringIO
import ps_lib, ps_builtins
from ps_cfg import *


def interpret(linelist, namespace):
    '''This function takes a statement and processes it, replacing various syntax
    and variables with their values.  The expanded statement is then returned.
    '''
    po.wasunglobbed = False
    destlist = []              # destination for our processing

    # lets check each word for expansions
    for token in linelist:
        if po.opts.debug: ps_lib.msg('debug', 'token:%s' % token)

        # Brace expansion: echo sp{1,2,3}a  > sp1a sp2a sp3a
        if '{' in token and '}' in token:
            token = ps_lib.expand_braces(token)
            if po.opts.debug: ps_lib.msg('debug', '{} exp:%s' % token)

        # tilde expansion
        if token[0] == '~':
         token = os.path.expanduser(token)
         if po.opts.debug: ps_lib.msg('debug', '~ exp:%s' % token)

        # check for any variables to expand '%var'
        if po.sym_expansion in token:
            token = ps_lib.expand_vars(token, po.namespace)
        # look for null args just expanded:
        if token == '\x00': token = ''

        # do command expansion in  `...`
        if pi.sym_cmdsub in token:
            try:
                # here expand escape sequences. like removing quotes
                if po.sym_expansion in token:
                    token = ps_lib.expand_escapes(token)
                token = ps_lib.cmd_substition(token)
            except NameError, why:  # not found, halt all processing
                ps_lib.msg('error', str(why)); print
                return
        
        # more word splitting
        tokens = token.split()
        
        # check to see if it needs unglobbage
        for tokinho in tokens:
            globresults = ps_lib.unglob_token(tokinho)
            if globresults:  # glob results probably don't need expansion, or they wouldnt work
                destlist = destlist + globresults   # globs already list
                po.wasunglobbed = True
            else:  # here expand escape sequences. like removing quotes
                if po.sym_expansion in tokinho:
                    tokinho = ps_lib.expand_escapes(tokinho)
                destlist.append(tokinho)

    return destlist



def getline(infile, mode='line'):

    for line in infile:
        if po.opts.debug: ps_lib.msg('debug', 'line:%r  mode:=%s' % (line, mode) )
        if   mode == 'line':
            if line.isspace():  continue        # blank line, continue
            else:
                if line.strip().startswith('#'): continue
            if not line:  raise StopIteration   # null line, EOF, break

        elif mode == 'block':
            if line:
                if line.isspace():  # blank line ends the block
                    #print '     blank:%r' % line
                    raise StopIteration
                else:
                    #print '     grabbing line:%r' % line
                    if line.strip().startswith('#'): continue
                    yield line; continue
            else:  raise StopIteration

        elif mode == 'skip':
            if line:
                if line.isspace():  raise StopIteration
                else:               continue
            else:                   raise StopIteration

        line = line.rstrip()
        linelist = line.split()
        firstword = linelist[0]

        if linelist[0] in pi.branch_words:  # evaluate branch
            # IF = if true, read and execute until branch ends
            if firstword == 'if':
                teststr = string.join(linelist[1:])[:-1]  # ditch :
                #print 'debug test:{%s}' % test,
                #test = eval(teststr, po.namespace)
                try: test = eval(teststr, po.namespace)
                except Exception, why:
                    ps_lib.msg('error', 'SyntaxError: ' + str(why))
                    if hasattr(infile, 'close'): raise StopIteration # if a real file stop
                    for line in getline(infile, mode='skip'): pass
                    continue
                if po.opts.debug: ps_lib.msg('debug', '%s (%s)' % (teststr, test) )
                if test:    getline(infile)
                else:
                    for line in getline(infile, mode='skip'): pass
                
            elif firstword == 'while':
                teststr = string.join(linelist[1:])[:-1]  # ditch :
                #print 'debug test:{%s}' % teststr,
                #test = eval(teststr, po.namespace)
                try: test = eval(teststr, po.namespace)
                except Exception, why:
                    ps_lib.msg('error', 'SyntaxError: ' + str(why))
                    if hasattr(infile, 'close'): raise StopIteration # if a real file stop
                    for line in getline(infile, mode='skip'): pass
                    continue
                if po.opts.debug: ps_lib.msg('debug', '%s (%s)' % (teststr, test) )
                if test:
                    # get the block, and then exec block
                    block = []
                    for line in getline(infile, mode='block'):
                        block.append(line)
                    #print 'debug: Block:', repr(block)
                    break2 = False
                    while test:
                        #import time; time.sleep(1)
                        for line in block:
                            firstword = line.split()[0]
                            if firstword == 'break':
                                break2 = True
                                break # get out
                            yield line
                        if break2: break
                        test = eval(teststr, po.namespace)
                else:
                    for line in getline(infile, mode='skip'): pass
            elif firstword == 'for':
                var, items = linelist[1], string.join(linelist[3:])[:-1]  # ditch :
                # get the block, and then exec block
                block = []
                for line in getline(infile, mode='block'):
                    block.append(line)
                #print 'debug: Block:', repr(block)
                break2 = False
                try:
                    for item in eval(items, po.namespace):
                        po.namespace[var] = item
                        for line in block:
                            firstword = line.split()[0]
                            if firstword == 'break':
                                break2 = True
                                break # get out
                            yield line
                        if break2: break
                except NameError, why:
                    ps_lib.msg('error', 'NameError: ' + str(why))
                    if hasattr(infile, 'close'): raise StopIteration # if a real file stop
                
            elif firstword == 'def':
                pass
        else:   # exec statement normally
            yield line
