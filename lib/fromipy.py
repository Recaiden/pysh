__license__ = '''
    IPython copyright and licensing notes
    =====================================
    
    Unless indicated otherwise, files in this project are covered by a BSD-type
    license, included below.
    
    Individual authors are the holders of the copyright for their code and are
    listed in each file.
    
    Some files (DPyGetOpt.py, for example) may be licensed under different
    conditions. Ultimately each file indicates clearly the conditions under which
    its author/authors have decided to publish the code.
    
    
    IPython license
    ---------------
    
    IPython is released under a BSD-type license.
    
    Copyright (c) 2001, 2002, 2003, 2004 Fernando Perez <fperez@colorado.edu>.
    
    Copyright (c) 2001 Janko Hauser <jhauser@zscout.de> and Nathaniel Gray
    <n8gray@caltech.edu>.
    
    All rights reserved.
    
    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:
    
      a. Redistributions of source code must retain the above copyright notice,
         this list of conditions and the following disclaimer.
    
      b. Redistributions in binary form must reproduce the above copyright
         notice, this list of conditions and the following disclaimer in the
         documentation and/or other materials provided with the distribution.
    
      c. Neither the name of the copyright holders nor the names of any
         contributors to this software may be used to endorse or promote products
         derived from this software without specific prior written permission.
    
    
    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
    ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE FOR
    ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
    LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
    OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
    DAMAGE.
'''

import os, sys

#----------------------------------------------------------------------------
class HomeDirError(Exception):
    pass

def get_home_dir():
    """Return the closest possible equivalent to a 'home' directory.

    We first try $HOME.  Absent that, on NT it's $HOMEDRIVE\$HOMEPATH.

    Currently only Posix and NT are implemented, a HomeDirError exception is
    raised for all other OSes. """ #'

    try:
        return os.environ['HOME']
    except KeyError:
        if os.name == 'posix':
            raise HomeDirError,'undefined $HOME, IPython can not proceed.'
        elif sys.platform == 'win32':  #os.name == 'nt':  # For some strange reason, win9x returns 'nt' for os.name.
            try:
                return os.path.join(os.environ['HOMEDRIVE'],os.environ['HOMEPATH'])
            except:
                try:
                    # Use the registry to get the 'My Documents' folder.
                    import _winreg as wreg
                    key = wreg.OpenKey(wreg.HKEY_CURRENT_USER,
                                       "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
                    homedir = wreg.QueryValueEx(key,'Personal')[0]
                    key.Close()
                    return homedir
                except:
                    return 'C:\\'
        elif os.name == 'dos':
            # Desperate, may do absurd things in classic MacOS. May work under DOS.
            return 'C:\\'
        else:
            raise HomeDirError,'support for your operating system not implemented.'




