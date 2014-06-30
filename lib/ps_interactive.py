''' ps_interactive - interactive functionality masquerading as an input file.
    by Mike Miller 2004-2005
    released under the GNU public license, (GPL) version 2
'''
import os, string, glob, keyword
import ansi, ps_lib
from ps_cfg import *
try:
     import readline
     import rlcompleter
except ImportError:
     readline = False


def getinput():
    'a generator function that returns a line or two from an interactive session.'

    previousline, line = '', ''
    isloop = False
    while True:

        if previousline:  prompt = 'more> '
        else:
            if po.color:    prompt = ps_lib.eval_str(po.colorprompt)
            else:           prompt = ps_lib.eval_str(po.prompt)
            ansi.xtermTitle(ps_lib.eval_str(po.title))
        try:
            line = raw_input(prompt)    # get input from user
        except EOFError:                # sys.exit(1) or ^Z, ^D
            raise StopIteration
            break
        except KeyboardInterrupt:       # ^C ( now caught earlier)
            print;  continue

        if line.isspace():  line = ''   # make sure blank line is false
        if not line and not previousline: continue  # just an enter hit, I think

        # check if we need more input
        if line:
            if isloop:
                #previousline = previousline + '    ' + line + '\n'
                previousline = previousline + line + '\n'
                continue
            if line.split()[0] in pi.branch_words:  #ps_lib.
                isloop = True
                previousline = previousline + line + '\n'
                continue
            if line[-1] == '\\':
                # get more
                previousline = previousline + line[:-1]
                continue

        else: # line is nada '', and a previous line exists, end extended line
            isloop = False
            if previousline:
                line = previousline + ' ' # keeep from triggering EOF downstream
                previousline = ''

        if po.opts.debug: ps_lib.msg('debug', `line`)
        if '\n' in line:
            for item in line.split('\n'):
                #print 'yielding:', `item`
                yield item
            #yield ''
        else:
            yield line

if readline:
    class ps_completer(rlcompleter.Completer):
        def complete(self, text, index):
            '''Return the next possible completion for 'text'.
            This function is called successively with index == 0, 1, 2, ...
            which returns each match until they run out and then returns None
            as a signal to readline to stop.
            '''
            try:
                if index == 0:              # on first call, find our matches
                    self.matches = []
                    for kw in po.keywords:              # try pyshell keywords
                        if kw.startswith(text):
                            self.matches.append(kw)
                    for kw in keyword.kwlist:           # python keywords
                        if kw.startswith(text):
                            self.matches.append(kw)
                    if '.' in text:                     # python namespace
                        # these need to check for nulls or be at end
                        try: matches = self.attr_matches(text)
                        except Exception: matches = None  # which exception?
                        if matches: self.matches += matches
                    else:
                        matches = self.global_matches(text)
                        if matches: self.matches += matches
           
                    # check where in the command line we are. necessary to
                    # find out if we should search for executable or document.
                    # This needs to take lines with multiple statements into account.
                    start = readline.get_begidx(); pos = 0
                    if start == 0:                      # simple case
                        findmode = 'executable'
                    else:               # if whitespace in front, find real start
                        for i, char in enumerate(readline.get_line_buffer()):
                            if char not in string.whitespace:
                                pos = i; break
                        if start == pos:
                            findmode = 'executable'
                        else:
                            findmode = 'document'       # else do document mode
           
                    #then search filesystem
#                    if text[0] == '~':
#                        text = os.path.expanduser(text)
                    if findmode == 'executable':
                        if os.environ.has_key('PATH'):
                            for folder in os.environ['PATH'].split(os.pathsep):
                                matches = \
                                    glob.glob(os.path.join(folder, text) + '*')
                                #print matches
                                for match in matches:
                                    self.matches += [os.path.basename(match)]
                        else:   self.matches += glob.glob(text + '*')
                    else: # document
                        matches = glob.glob(text + '*')
                        for match in matches:
                            if os.path.isdir(match): match = match + '/'
                            self.matches += [match]
                    if po.opts.debug:
                        print; ps_lib.msg('debug', 'matches: %s' % self.matches)
           
                return self.matches[index]
           
            except IndexError:
                return None
            except Exception, why:
                print '\nps_completer err:', str(why)
                return None
