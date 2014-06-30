#   ansilib, a library of common console color functions for freedom desk
#   (C)2005, Mike Miller.  Released under the GPL, version 2.

import sys
import os

# Lifted from ipython
#    NoColor = ''  # for color schemes in color-less terminals.
#    Normal = '\001\033[0m\002'   # Reset normal coloring
#    _base  = '\001\033[%sm\002'  # Template for all other colors
#
#    color_templates = (
#        ("Black"       , "0;30"),
#        ("Red"         , "0;31"),
#        ("Green"       , "0;32"),
#        ("Brown"       , "0;33"),
#        ("Blue"        , "0;34"),
#        ("Purple"      , "0;35"),
#        ("Cyan"        , "0;36"),
#        ("LightGray"   , "0;37"),
#        ("DarkGray"    , "1;30"),
#        ("LightRed"    , "1;31"),
#        ("LightGreen"  , "1;32"),
#        ("Yellow"      , "1;33"),
#        ("LightBlue"   , "1;34"),
#        ("LightPurple" , "1;35"),
#        ("LightCyan"   , "1;36"),
#        ("White"       , "1;37"),  )
#

# A list of ansi escape sequences.

fred        = '[00;31m%s[00m'
fbred       = '[01;31m%s[00m'
fgreen      = '[00;32m%s[00m'
fbgreen     = '[01;32m%s[00m'
forange     = '[00;33m%s[00m'
fbyellow    = '[01;33m%s[00m'
fblue       = '[00;34m%s[00m'
fbblue      = '[01;34m%s[00m'
fpurple     = '[00;35m%s[00m'
fbpurple    = '[01;35m%s[00m'
fcyan       = '[00;36m%s[00m'
fbcyan      = '[01;36m%s[00m'
fgrey       = '[00;37m%s[00m'
fwhite      = '[01;37m%s[00m'
#fgrey       = '[00;38m%s[00m'
#fwhite      = '[01;38m%s[00m'

redrev      = '[00;05;37;41m%s[00m'
grerev      = '[00;05;37;42m%s[00m'
yelrev      = '[01;05;37;43m%s[00m'

fbold       = '[01m%s[00m'

# Readline encoded escape sequences:
greenprompt = '\001[01;32m\002%s\001[00m\002'
yellowprompt= '\001[01;33m\002%s\001[00m\002'
redprompt   = '\001[01;31m\002%s\001[00m\002'



#fg
red         = '31'
green       = '32'
orange      = '33'
blue        = '34'
purple      = '35'
cyan        = '36'
grey        = '37'

#bg
redbg       = '41'
greenbg     = '42'
orangebg    = '43'
bluebg      = '44'
purplebg    = '45'
cyanbg      = '46'
greybg      = '47'
blackbg     = '47'

# misc
underline   = '38'
underline   = '48'
bold        = '01'
norm        = '00'


def colorstart(fgcolor, bgcolor, weight):
    '''Begin a text style.'''
    if weight == True:  weight = bold
    else:               weight = norm
    if bgcolor == None:  bgcolor = 'm'
    sys.stdout.write('[%s;%s;%sm' % (weight, fgcolor, bgcolor))


def colorend(cr=False):
    '''End color styles.  Resets to default terminal colors.'''
    sys.stdout.write('[00m')
    if cr: sys.stdout.write('\n')
    sys.stdout.flush()


def cprint(text, fg=grey, bg=blackbg, w=norm, cr=False):
    '''Print a string in a specified color style and then return to normal.
    def cprint(text, fg=white, bg=blackbg, w=norm, cr=True):'''
    colorstart(fg, bg, w)
    sys.stdout.write(text)
    colorend(cr)



def bargraph(data, maxwidth, incolor, minwidth=None):
#   data =  [ ('%', pcnt, ansi.grey, ansi.bluebg, False), ... ]
#    if (uw + cw + fw) > graphwidth: # truncate if too big
#        fw = graphwidth - uw - cw

    threshold = 100.0 / (maxwidth * 2) # if smaller than one half of one char wide
    position = 0
    begpcnt = data[0][1] * 100
    endpcnt = data[-1][1] * 100

    if len(data) < 1: return        # Nada to do
    maxwidth = maxwidth - 2         # because of brackets
    datalen = len(data)

    # Print left bracket in correct color:
    #print '1st %:', begpcnt
    if incolor and not (begpcnt == 0 and endpcnt == 0):
        if begpcnt < threshold: lbkcolor = data[1][3] #greenbg # needs fix
        else:                   lbkcolor = data[0][3] #redbg
        cprint('[', data[0][2], lbkcolor, None, None)
    else:   sys.stdout.write('[')
    
    
    for i, part in enumerate(data):
        # unpack data
        char, pcnt, fgcolor, bgcolor, bold = part
        width = int( round(pcnt/100.0 * maxwidth, 0) )
        position = position + width

        #and graph
        if incolor and not ( fgcolor == None or bgcolor == None):
            cprint(char * width, fgcolor, bgcolor, bold, False)
        else:  # print kept putting in extra spaces
            sys.stdout.write(char * width)

    if minwidth:
        if position < maxwidth:
            print ' ' * (maxwidth - position),
    
    # Print right bracket in correct color:
    if incolor and not (begpcnt == 0 and endpcnt == 0):
        if endpcnt < threshold: lbkcolor = data[0][3] #redbg
        else:                   lbkcolor = data[1][3] #greenbg
        cprint(']', data[-1][2], lbkcolor, None, None)
        #print 'Lst %:', endpcnt
    else:    sys.stdout.write(']')
 
        

# -------------------------------------------------------------------
# modified from gentoo portage "output" module
# Copyright 1998-2004 Gentoo Foundation
def xtermTitle(mystr):
    if os.environ.has_key("TERM") and sys.stderr.isatty():
        term=os.environ["TERM"]
        legal_terms = ["xterm","Eterm","aterm","rxvt","screen","kterm","rxvt-unicode"]
        if term in legal_terms:
            sys.stderr.write("\x1b]2;"+str(mystr)+"\x07")
            sys.stderr.flush()

#def xtermTitleReset():
    #if os.environ.has_key("TERM"):
        #myt=os.environ["TERM"]
        #xtermTitle(os.environ["TERM"])
# -------------------------------------------------------------------
#____________________________________________________________________
# from avkutil.py - Andrei Kulakov <ak@silmarill.org>
def getTermSize():
    '''Return terminal size as tuple (width, height).'''

    import struct, fcntl, termios
    x, y = 0, 0
    try:
        y, x = struct.unpack('hhhh', fcntl.ioctl(0,
            termios.TIOCGWINSZ, '\000'*8))[0:2]
    except IOError: pass
    return x, y

