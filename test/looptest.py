#!/bin/env python
import string, StringIO
namespace = { 'a': 5, 'b': 6 }
branch_words = ('if', 'for', 'while')
infile = file('loop.txt')

def line_exec(line):
    print 'exec:', line

def getinput(infile, mode='line'):

        line = infile.readline()
        #print 'debug: line:%r  mode:=%s' % (line, mode)
        if   mode == 'line':
            if line.isspace():  return True     # blank line, continue
            if not line:        return False    # null line, EOF, break

       # elif mode == 'block':


        elif mode == 'skip':
            if line and not line.isspace():
                print '     skipping line:%r' % line
                while getinput(infile, mode='skip'): pass # get until false
                return False
            else: 
                print '     blank:%r' % line
                return False

        line = line.rstrip()
        linelist = line.split()
        firstword = linelist[0]

        if linelist[0] in branch_words:
            # evaluate branch
            # IF = if true, read and execute until branch ends
            if firstword == 'if':
                test = string.join(linelist[1:])[:-1]  # ditch :
                print 'debug test:{%s}' % test,
                try: test = eval(test, namespace)
                except Exception, why:  
                    print 'error:', why
                    return False
                #print test
                if test:    getinput(infile)
                else:       getinput(infile, mode='skip')
                
            elif firstword == 'while':
                test = string.join(linelist[1:])[:-1]  # ditch :
                print 'debug test:{%s}' % test,
                try: test = eval(test, namespace)
                except Exception, why:  
                    print 'error:', why
                    return False

                if test:    
                    # get the block, and then exec block
                    # exec 'while test: getinput(infile)' in namespace
                else:   getinput(infile, mode='skip')

        else:   # exec statement normally
            yield line
            
        return True  # do again

while True:
    
    #success = getinput(infile)
    #if not success: break
    for line in getinput(infile):
        line_exec(line)

infile.close()
