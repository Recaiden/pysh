#!/bin/env python
import string
from StringIO import StringIO

def line_exec(line):
    #print 'exec:', line
    exec line.strip() in namespace

def getinput(infile, mode='line'):

    #while True:
        #line = infile.readline()
    for line in infile:
        #print 'debug: line:%r  mode:=%s' % (line, mode)
        if   mode == 'line':
            if line.isspace():  
                #print 'yielding None!'
                #yield None; 
                continue              # blank line, continue
            else: 
                if line.strip().startswith('#'): continue
            if not line:  raise StopIteration     # null line, EOF, break

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
                if line.isspace():  # blank line ends the block
                    #print '     blank:%r' % line
                    raise StopIteration
                else:
                    #print '     skipping line:%r' % line
                    #for line in getinput(infile, mode='skip'):  pass
                    yield None; continue
            else:  raise StopIteration

        line = line.rstrip()
        linelist = line.split()
        firstword = linelist[0]

        if linelist[0] in branch_words:  # evaluate branch
            # IF = if true, read and execute until branch ends
            if firstword == 'if':
                teststr = string.join(linelist[1:])[:-1]  # ditch :
                #print 'debug test:{%s}' % test,
                try: test = eval(teststr, namespace)
                except Exception, why:  
                    print 'error:', why
                    raise StopIteration
                if ps.opts.debug: ps.msg('debug', '%s (%s)' % (teststr, test) )
                if test:    getinput(infile)
                else:       
                    for line in getinput(infile, mode='skip'): pass
                
            elif firstword == 'while':
                teststr = string.join(linelist[1:])[:-1]  # ditch :
                #print 'debug test:{%s}' % teststr,
                try: test = eval(teststr, namespace)
                except Exception, why:  
                    print 'error:', why
                    raise StopIteration
                if ps.opts.debug: ps.msg('debug', '%s (%s)' % (teststr, test) )
                if test:
                    # get the block, and then exec block
                    block = ''
                    for line in getinput(infile, mode='block'):
                        block = block + line
                    #print 'debug: Block:', repr(block)
                    break2 = False
                    while test:                    
                        for line in getinput(StringIO(block), mode='line'):
                            firstword = line.split()[0]
                            if firstword == 'break': 
                                break2 = True
                                break # get out
                            yield line
                        if break2: break
                        test = eval(teststr, namespace)
                else:
                    for line in getinput(infile, mode='skip'): pass
            elif firstword == 'for':
                var, items = linelist[1], string.join(linelist[3:])[:-1]  # ditch :
                # get the block, and then exec block
                block = ''
                for line in getinput(infile, mode='block'):
                    block = block + line
                #print 'debug: Block:', repr(block)
                break2 = False
                for item in eval(items):
                    namespace[var] = item
                    for line in getinput(StringIO(block), mode='line'):
                        firstword = line.split()[0]
                        if firstword == 'break': 
                            break2 = True
                            break # get out
                        yield line
                    if break2: break
            
        else:   # exec statement normally
            yield line




if __name__ == '__main__':

    namespace = { 'a': 5, 'b': 6 }
    branch_words = ('if', 'for', 'while')
    infile = file('loop2.txt')
    
    
    for line in getinput(infile):
        if line: line_exec(line)
    
    infile.close()
