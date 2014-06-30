''' ps_cfg - configuration options
    by Mike Miller 2004-2005
    released under the GNU public license, (GPL) version 2
'''
import sys, os
import ansi
import ps_lib

# Declare execution defaults, and wrap in nice package
# names starting with "_" are not copied to other namespaces by default
class _python_shell_info:
    '''This object holds unchangeable information about pyshell.'''
    
    version = 0.91
    branch_words        = ['if', 'for', 'while', 'def']
    name = 'Pyshell'
    pform = (os.name, sys.platform)  # name, platform
    # name - 'posix', 'nt', 'mac', 'os2', 'ce', 'java', 'riscos'.
    # platform - e.g. 'sunos5', 'linux2', 'win32'
    
    # envirionment capabilities
    caps = { 'daudio': False, 'readline': False, 'term': False, 'color': False }  # not implemented yet

    sym_contchars       = ['|','||','&','&&',';','(',')','\n']
    sym_globchars       = ['*','?', '[', ']']
    sym_metachars       = ['%','\\', '`', '{', '}']
    sym_splitchars      = ['|','&',';','<','>','\t',' '] # ,'(',')'

    sym_cmdsub          =  '`'
    sym_cont            = ';'
    sym_contback        =  '&'
    sym_contfail        = '||'
    sym_contsuccess     = '&&'
    sym_loopsplit       = ':'
    sym_pipe            = '|'
    sym_quotes          = '\'"'
    sym_rerr            = '>e>'
    sym_rerr_app        = '>e>>'
    sym_rin             = '<'
    sym_rin_here        ='<<'
    sym_rout            = '>'
    sym_rout_app        = '>>'
    sym_routerr         = '>3>'
    sym_routerr_app     = '>3>>'

    def __setattr__(self, name, value):
        ps_lib.msg('warning', 'The item %s cannot be changed.' % name)
        print

pi = _python_shell_info()


class _python_shell_options:
    '''This object holds dynamic information about pyshell.'''

    def __init__(self):

        self.opts, self.args = None, None  # later from optionparser
        self.wasunglobbed = False
        self.alias_expanded = False
        self.sym_expansion = '%'
        self.audio = True
        self.status = 0
        self.aliases = {}
        self.jobs = []
        self.keywords = []  # filled in later
        #self.completion_case = False  # unimplemented
        
        # avoid clash with dir builtin command..., and copy common modules
        self.namespace = { 'pdir': globals()['__builtins__']['dir'],
            'os': os, 'sys': sys }

        # user settings
        self.configpath = '~/.pyshell'
        if os.name == 'nt':  # w32 console can't handle colors
            self.prompt = '"%(username)s@%(computername)s:%(pwd)s> " % os.environ'
            self.title = '"%(username)s@%(computername)s:%(pwd)s" % os.environ'
            self.title = '"%(USERNAME)s@%(COMPUTERNAME)s " % os.environ'
            self.color = False
        elif os.name == 'posix':
            self.title = '"%(USER)s@%(HOSTNAME)s:%(PWD)s" % os.environ'
            self.prompt = '"%(USER)s@%(HOSTNAME)s:%(PWD)s> " % os.environ'
            if os.getuid() == 0:
                self.colorprompt = '(po.colors["root/input"] % "%(USER)s@%(HOSTNAME)s:" + po.colors["folder/input"] % "%(PWD)s> ") % os.environ'
            else:
                self.colorprompt = '("%(USER)s@%(HOSTNAME)s:" + po.colors["folder/input"] % "%(PWD)s> ") % os.environ' # color, but probs

            if os.isatty(sys.stdout.fileno()):  self.color = True
            else:                               self.color = False
            self.colors = {
                'string': ansi.forange, 'int': ansi.fgreen, 'keyword': ansi.fbblue,
                'identifier': ansi.fbold, 'folder': ansi.fbyellow, 'blank': '%s',
                'Debug':ansi.fblue, 'Info':ansi.fgreen, 'Warning':ansi.fbyellow,
                'Error':ansi.fred, 'Critical':ansi.fbred,
                'folder/input': ansi.yellowprompt, 'root/input': ansi.redprompt,
                'yes': ansi.fbgreen, 'no': ansi.fbred
                }

po = _python_shell_options()

