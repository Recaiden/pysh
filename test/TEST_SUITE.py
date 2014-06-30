#!/bin/env python
''' Unit tests for ps_main
    by Mike Miller 2004-2005
    released under the GNU public license, (GPL) version 2
'''
import sys
sys.path.append('../lib')

from ps_main import *
import unittest
import string



class ExpansionChecks(unittest.TestCase):

    def testExpBraces(self):
        '''brace expansion'''
        result = ps_interpreter.interpret('echo sp{1,2,3}a'.split(), {})
        self.assertEqual(result, ['echo', 'sp1a', 'sp2a', 'sp3a'])
        
    def testExpTilde(self):
        '''tilde expansion'''
        result = ps_interpreter.interpret('echo ~root'.split(), {})
        self.assertEqual(result, ['echo', '/root'])
        
    def testExpEnvironment(self):
        '''simple env variable expansion'''
        import os;  os.environ['DUDE'] = 'Holmes'
        result = ps_interpreter.interpret('echo %{DUDE}'.split(), {})
        self.assertEqual(result, ['echo', 'Holmes'])

    def testExpVariable(self):
        '''simple variable expansion'''
        po.namespace['a'] = 5
        result = ps_interpreter.interpret('echo %(a) %a'.split(), po.namespace)
        self.assertEqual(result, ['echo', '5', '5'])

    def testExpVariableComplex(self):
        '''complex variable expansion'''
        po.namespace['a'] = 5
        result = ps_interpreter.interpret('echo PHOTO.%%%(a).jpg'.split(), po.namespace)
        self.assertEqual(result, ['echo', 'PHOTO.%5.jpg'])
        
    def testExpVariableComplex2(self):
        '''complex variable - too many numbers'''
        #po.namespace['a'] = 5
        result = ps_interpreter.interpret('echo spicctrl%032-b%032256'.split(), {})
        self.assertEqual(result, ['echo', 'spicctrl -b 256'])
        
    def testExpGlob(self):
        '''Globby expansion'''
        po.namespace['a'] = 5
        result = ps_interpreter.interpret('echo glob/*.psl'.split(), {})
        self.assertEqual(result, ['echo', 'glob/sample.psl', 'glob/varexptest.psl'])
        




        
        
if __name__ == "__main__":

    unittest.main()
