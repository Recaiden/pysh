#!/bin/env python
''' pyshell.py - Main loop for the python shell
    by Mike Miller 2004-2005
    released under the GNU public license, (GPL) version 2
'''

from ps_init import *

def process_file(source):
    '''main input loop'''

    if source:  infile = openanything.opn(source)   # given URL, File, filename, string
    else:       infile = ps_interactive.getinput()  # given nada, interactive session

    # get a "line" from stream, function takes loops into account already
    for line in ps_interpreter.getline(infile):
        if not line: break      # EOF - not sure if this is needed
        line = line.rstrip()    # needed when from file
        ispipe = []             # reset pipe check

        # check for string literals, escape chars, comments, quotes, and balance
        try:  eline = ps_lib.escape_line(line)
        except ValueError: # pass
            ps_lib.msg('error', 'unbalanced quotes'); print
            po.status = 1
            #return None
            continue
        if po.opts.debug:  ps_lib.msg('debug',  'escaped statement: %s' % eline)

        # check for multiple statements in same line
        # lines is a list of tuples, that contain statements, and their mode, ";&|" etc
        srclines = ps_lib.line_split(eline)
        if po.opts.debug:  ps_lib.msg('debug',  'multiple lines: %s' % srclines)

        # check for history substitution
        destlines = []
        for i, (statement, contmode) in enumerate(srclines):
            if statement[0] == '!':
                hist_sub = None
                if statement[1] == '!':
                    hist_sub = readline.get_history_item(readline.get_current_history_length()-1)
                elif statement[1] == '$':
                    hist_sub = readline.get_history_item(
                        readline.get_current_history_length()-1).split()[-1]
                else:
                    hist_sub = ps_lib.search_hist( statement[1:] )
                if hist_sub:
                    if readline: readline.replace_history_item(readline.get_current_history_length()-1, hist_sub)
                    destlines.append( (hist_sub, contmode) )
                    if po.opts.debug: ps_lib.msg('debug',  'history substitution: ' + hist_sub)
                    if po.opts.verbose: print hist_sub
                else:
                    destlines.append( ('', contmode) )
            else: destlines.append( (statement, contmode) )
        srclines = destlines

        # check to see if split line contains aliases that need to be split
        # into multiple lines too, this is inefficient
        destlines = []
        for i, (statement, contmode) in enumerate(srclines):

            linelist = statement.split()
            # expand aliaases, only once - check first word
            linelist, po.alias_expanded = ps_lib.expand_aliases(linelist)

            if po.alias_expanded:  # split again
                newstatement = string.join(linelist + [contmode])
                newlines = ps_lib.line_split(newstatement)
                destlines = destlines + newlines
                if po.opts.debug:  ps_lib.msg('debug',  'new lines: %s' % newlines)
            else:
                destlines.append( (statement, contmode) )
        if po.opts.debug:  ps_lib.msg('debug',  'destlines: %s' % destlines)


        # excecute each statement in possibly compound line
        for statement, contmode in destlines:

            linelist = statement.split()
            if po.opts.debug: ps_lib.msg('debug',  'linelist: %s' % linelist)

            # checken Sie para redirection, error out if it fails for any reason
            detours = [ None, None, None, None ]
            if pi.sym_rout in statement or pi.sym_rin in statement:
                linelist, detours = ps_lib.examine_redir(linelist, stdio)
                if po.status:  # there was an error
                    if po.opts.debug: ps_lib.msg('debug', 'should continue:%s' %
                        ps_lib.should_continue(contmode))
                    if ps_lib.should_continue(contmode):  continue
                    else:                                break

            # try to figure out what this statement is, return tuple of (type, subtype, data)
            linetype = ps_lib.examine_type(linelist, po.namespace, checkaliases=False)
            if po.opts.debug: ps_lib.msg('debug',  'statement type: ' + str(linetype))
            
            if linetype[0] == 'python':
                try:
                    if po.alias_expanded:
                        statement = string.join(linelist)
                    else:
                        statement = line    # the original line read from file
                    if po.opts.debug:
                        ps_lib.msg('debug','** Executing python stm:%s:' % statement)
                    exec(statement) in po.namespace
                except Exception, why:
                    ps_lib.msg('error', str(why) ); print
                    continue

            elif linetype[0] == 'inconclusive':
                ps_lib.msg('error', "The command '%s' cannot be found." % statement.split()[0])
                print

            else:   # pyshell OR system - have been combined.
                linelist = ps_interpreter.interpret(linelist, po.namespace)

                if po.opts.debug:  ps_lib.msg('debug',
                        '** Executing pyshell or system call: %s' % string.join(linelist) )
                try:
                    if contmode == pi.sym_contback:     # & char
                        ps_lib.background_job(linelist)

                    elif contmode == pi.sym_pipe:       # | char
                        if ispipe: # pipe already started
                            if linetype[0] == 'system':
                                newobj = sub(linelist, stdin=ispipe[-1].stdout, stdout=sp.PIPE)
                            else:
                                cmdclass = getattr(ps_builtins, '_%s' % linelist[0])
                                newobj = cmdclass(linelist, verbose=po.opts.verbose, stdin=ispipe[-1].stdout, stdout=sp.PIPE)
                        else:     # start pipe
                            if linetype[0] == 'system':
                                newobj = sub(linelist, stdout=sp.PIPE)
                            else:
                                cmdclass = getattr(ps_builtins, '_%s' % linelist[0])
                                newobj = cmdclass(linelist, verbose=po.opts.verbose, stdout=sp.PIPE)
                        ispipe.append(newobj)
                    else:  # run the command            # ; char
                        sigintreceived = False
                        if ispipe:  # we're at the end of a pipe, because contmode
                                    # is not "|" and there is a pipe
                            if linetype[0] == 'system': # just let end of pipe print to stdio
                                childp = sub(linelist, stdin=ispipe[-1].stdout,
                                        stdout=detours[1], stderr=detours[2])
                            else:
                                cmdclass = getattr(ps_builtins, '_%s' % linelist[0])
                                childp = cmdclass(linelist, verbose=po.opts.verbose, stdin=ispipe[-1].stdout,
                                        stdout=detours[1], stderr=detours[2])
                            ispipe.append(childp)
                        else: # never was a pipe, exec it
                            if linetype[0] == 'system':
                                childp = sub(linelist, stdin=detours[0],
                                    stdout=detours[1], stderr=detours[2])
                            else:  # probaly shouldn't fork on a standalone pyshell command
                                cmdclass = getattr(ps_builtins, '_%s' % linelist[0])
                                childp = cmdclass(linelist, verbose=po.opts.verbose,
                                    stdin=detours[0], stdout=detours[1],
                                    stderr=detours[2], fork=False)  # new obj # stdio? here

                        while True:  # the reason we poll and not wait is so user can interrupt
                            #print 'polling.... status:',
                            status = childp.poll()
                            #print status
                            if status <> None:  # finished
                                po.status = status
                                break
                            if sigintreceived:
                                if ispipe: # should I kill beg to end, or end to beg?
                                    for proc in ispipe[:-1]:  os.kill(proc.pid, 2)
                                os.kill(childp.pid, 2)
                                po.status = -2
                            time.sleep(.2) # cut the machine some slack, but still seem responsive

                except OSError, why:
                    ps_lib.msg('error', str(why)); print

            # reset stdio
            sys.stdin, sys.stdout, sys.stderr = stdio
            for detour in detours:
                if detour: detour.close()

            if po.opts.debug:
                ps_lib.msg('debug', 'should continue:%s' % ps_lib.should_continue(contmode))
                ps_lib.msg('debug', '-' * 72)
            if not ps_lib.should_continue(contmode): break

    if hasattr(infile, 'close'): infile.close()


#____________________________________________________________________
def startup():
    # don't know a better way to do this yet
    po.process_file = process_file

    ps_lib.atexit.register(sys.stdout.write, '\n') # schedule a newline on exit
    # string, file, or interactive?
    if  po.opts.command:
        if po.opts.debug:  ps_lib.msg('debug',  'Running from string: ' + po.opts.command)
        process_file(po.opts.command)

    elif len(po.args) > 0:
        filename = po.args[0]
        if po.opts.debug:  ps_lib.msg('debug',  'Running from file: ', filename)
        # put shell args into variables for scripts
        po.namespace['*'] = ''
        for i, arg in enumerate(po.args):
            po.namespace[str(i)] = arg
            po.namespace['*'] += arg + ' '
        process_file(filename)
    else:
        if not po.opts.faststart:
            # load inititalization files: history, system wide, login time, every time init
            sysconf = '/etc/pyshell/system_login.psl'
            if not os.access(sysconf, os.R_OK): sysconf = 'system_login.psl'
            ps_lib.load_init_files( ['history', sysconf, 'login.psl', 'logout.psl'] )

        process_file(None)     # 'interactive',
