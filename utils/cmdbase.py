import sys, os, string, optparse, subprocess, traceback, pickle


#____________________________________________________________________
class cmd_parser(optparse.OptionParser):
    '''The option parser needs to be overridden to keep it from making pyshell
    exit on error!!  Instead we raise ValueError and the client program can catch it.'''

    def exit(self, status=0, msg=None):
        if msg:
            sys.stderr.write(msg)
        #sys.exit(status)
        raise ValueError

#____________________________________________________________________
class ConsoleAppBaseOrig:
    '''
    This is the base class that all pyshell based commands are derived from--
    functionality added here will be inherited by all.
    Interface the modeled after subprocess module.
    '''
     # how to come up with standard exit codes?
    ERR_ARGS    = 1     # argument error
    ERR_DNE     = 2     # Object does not exist
    ERR_SHNE    = 3     # Obj should not exist already
    ERR_IO      = 4     # Input/Output error
    ERR_RESM    = 5     # Resume download error
    ERR_OS      = 6     # OS error
    ERR_AXSD    = 7     # Access denied
    ERR_UNKN    = 8     # Unknown errror
    ERR_NA      = 9     # Service Not Available
    ERR_VALU    = 10    # Parameter has incorrect value, eg a char when int needed
    
    USR_RJCT    = 30    # Confirmation rejected by user
    
    PIPE        = -1    # like subprocess
   
    def __init__(self, args, stdin=None, stdout=None, stderr=None, verbose=False):
        
        self.opts, self.args = None, args
        self.name = args[0]
        self.istty = os.isatty(sys.stdout.fileno())
#        if stdin:  sys.stdin  = stdin
#        if stdout: sys.stdout = stdout
#        if stderr: sys.stderr = stderr
        self.stdin  = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pid = None
        self.returncode = None
        
        #self.status = 0
        self.usage = string.join(string.split(self. __doc__, '\n')[1:], '\n')
        
        # Argument Processing
        self.parser = cmd_parser(usage=self.usage)  # build parser
        self.parser.add_option('-v', '--verbose',  action='store_true',
            dest='verbose', default=verbose, help='Enable verbose output.')
        self.parser.add_option('-q', '--quiet',  action='store_false',
            dest='verbose', default=verbose, help='Disable verbose output.')

        try: # see if object needs to register parameters with option parser
            register_opts_func = getattr(self, 'register_opts')
            register_opts_func()
        except AttributeError:  pass
        # Option parser
        try:  self.parse_args(args)
        except ValueError:
            self.run = self.newline # on error or help (-h), defeat run() function
            
    def newline(self):
        print

    def parse_args(self, args):
        
        self.opts, self.args = self.parser.parse_args(self.args)

#    def register_opts(self):  # do not implement in base class
#        pass

#    def reset_io(self):  # not correct
#        self.stdin  = sys.stdin
#        self.stdout = sys.stdout
#        self.stdout = sys.stdout
#
#    def set_io(self, stdin=None, stdout=None, stderr=None):
#        if stdin:  sys.stdin  = stdin
#        if stdout: sys.stdout = stdout
#        if stderr: sys.stderr = stderr

    def run(self):  # override this with desired behavior
        pass

    def fork(self):
        pid = os.fork()
        if pid == 0: # child
            try: self.run()
            finally:  os._exit(113)  # don't run atexit routines
        else:       # parent gets pid of child
            return


#____________________________________________________________________
class ConsoleAppBase(subprocess.Popen):
    '''
    This is the base class that all pyshell based commands are derived from--
    functionality added here will be inherited by all.
    Interface derived from the subprocess module.
    '''
    
    if True:  # so I can fold this
        # how to come up with standard exit codes?
        ERR_ARGS    = 1     # argument error
        ERR_DNE     = 2     # Object does not exist
        ERR_SHNE    = 3     # Obj should not exist already
        ERR_IO      = 4     # Input/Output error
        ERR_RESM    = 5     # Resume download error
        ERR_OS      = 6     # OS error
        ERR_AXSD    = 7     # Access denied
        ERR_UNKN    = 8     # Unknown errror
        ERR_NA      = 9     # Service Not Available
        ERR_VALU    = 10    # Parameter has incorrect value, eg a char when int needed
        
        USR_RJCT    = 30    # Confirmation rejected by user
        
        PIPE        = -1    # like subprocess
    

    def __init__(self, args, bufsize=0, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=False, shell=False,
                 cwd=None, env=None, universal_newlines=False,
                 startupinfo=None, creationflags=0,
                 verbose=False, fork=True):  #new
        
        # do stuff
        self.opts, self.args = None, args
        self.name = args[0]
        self.usage = string.join(string.split(self. __doc__, '\n')[1:], '\n')
        
        # Argument Processing
        self.parser = cmd_parser(usage=self.usage)  # build parser
        self.parser.add_option('-v', '--verbose',  action='store_true',
            dest='verbose', default=verbose, help='enable verbose output.')
        self.parser.add_option('-q', '--quiet',  action='store_false',
            dest='verbose', default=verbose, help='disable verbose output.')

        try: # see if object needs to register parameters with option parser
            register_opts_func = getattr(self, 'register_opts')
            register_opts_func()
        except AttributeError:  pass
        # Option parser
        try:  self.parse_args(args)
        except ValueError:
            # on error or help (-h), defeat run() function, and print \n
            self.run = self.newline
        
        # run supa-class:
        #super(ConsoleAppBase2, self).__init__(self,args,**kw)
        subprocess._cleanup()

        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.pid = None
        self.returncode = None
        self.universal_newlines = universal_newlines

        # Input and output objects. The general principle is like
        # this:
        #
        # Parent                   Child
        # ------                   -----
        # p2cwrite   ---stdin--->  p2cread
        # c2pread    <--stdout---  c2pwrite
        # errread    <--stderr---  errwrite
        if fork:
            (p2cread, p2cwrite,
             c2pread, c2pwrite,
             errread, errwrite) = self._get_handles(stdin, stdout, stderr)
            # need to implement this for the next line... is stdout a tty?
            if c2pwrite <> None:
                    self.istty = os.isatty(c2pwrite)
            else:   self.istty = os.isatty(sys.stdout.fileno())
    
            self._execute_child(args, executable, preexec_fn, close_fds,
                                cwd, env, universal_newlines,
                                startupinfo, creationflags, shell,
                                p2cread, p2cwrite,
                                c2pread, c2pwrite,
                                errread, errwrite)
            if p2cwrite:
                self.stdin = os.fdopen(p2cwrite, 'wb', bufsize)
            if c2pread:
                if universal_newlines:
                    self.stdout = os.fdopen(c2pread, 'rU', bufsize)
                else:
                    self.stdout = os.fdopen(c2pread, 'rb', bufsize)
            if errread:
                if universal_newlines:
                    self.stderr = os.fdopen(errread, 'rU', bufsize)
                else:
                    self.stderr = os.fdopen(errread, 'rb', bufsize)
        else:
            self.istty = os.isatty(sys.stdout.fileno())
            returncode = self.run()  # don't want .run() to have to set rt. explicitly
            if returncode:  self.returncode = returncode
            else:           self.returncode = 0
            
        subprocess._active.append(self)
                
                
    def _execute_child(self, args, executable, preexec_fn, close_fds,
                       cwd, env, universal_newlines,
                       startupinfo, creationflags, shell,
                       p2cread, p2cwrite,
                       c2pread, c2pwrite,
                       errread, errwrite):
        """Execute program (POSIX version)"""

        if executable == None:
            executable = args[0]

        # For transferring possible exec failure from child to parent
        # The first char specifies the exception type: 0 means
        # OSError, 1 means some other error.
        errpipe_read, errpipe_write = os.pipe()
        self._set_cloexec_flag(errpipe_write)

        self.pid = os.fork()
        if self.pid == 0:  # Child
            try:
                # Close parent's pipe ends
                if p2cwrite:    os.close(p2cwrite)
                if c2pread:     os.close(c2pread)
                if errread:     os.close(errread)
                os.close(errpipe_read)

                # Dup fds for child
                if p2cread:     os.dup2(p2cread, 0)
                if c2pwrite:    os.dup2(c2pwrite, 1)
                if errwrite:    os.dup2(errwrite, 2)

                # Close pipe fds.  Make sure we doesn't close the same
                # fd more than once.
                if p2cread: os.close(p2cread)
                if c2pwrite and c2pwrite not in (p2cread,):  os.close(c2pwrite)
                if errwrite and errwrite not in (p2cread, c2pwrite):
                    os.close(errwrite)

                # Close all other fds, if asked for
                if close_fds:   self._close_fds(but=errpipe_write)

                if cwd != None: os.chdir(cwd)

                if preexec_fn:  apply(preexec_fn)

                # this is where we do it
                returncode = self.run()  # don't want .run() to have to set rt. explicitly
                if returncode:  self.returncode = returncode
                else:           self.returncode = 0
                #print '.run() returncode:', returncode

            except:
                exc_type, exc_value, tb = sys.exc_info()
                # Save the traceback and attach it to the exception object
                exc_lines = traceback.format_exception(exc_type,
                                                       exc_value,
                                                       tb)
                exc_value.child_traceback = ''.join(exc_lines)
                os.write(errpipe_write, pickle.dumps(exc_value))

            os._exit(self.returncode)
            
        # Parent
        os.close(errpipe_write)
        if p2cread and p2cwrite:    os.close(p2cread)
        if c2pwrite and c2pread:    os.close(c2pwrite)
        if errwrite and errread:    os.close(errwrite)

        # Wait for exec to fail or succeed; possibly raising exception
        data = os.read(errpipe_read, 1048576) # Exceptions limited to 1 MB
        os.close(errpipe_read)
        if data != "":
            os.waitpid(self.pid, 0)
            child_exception = pickle.loads(data)
            raise child_exception

    
    def run(self):  # override this with desired behavior
        pass

    def newline(self):
        print

    def parse_args(self, args):
        self.opts, self.args = self.parser.parse_args(self.args)
     
        
        
