#!/bin/env python
from pyparsing import *
import string

if len(sys.argv) > 1:
    cmdstring = string.join(sys.argv[1:])
else:
    cmdstring = '''alias dude=holmes; echo \"one two\" 'three ' && ver # nuthin more
    alias dir = ls -l; echo "one two" 'three ' && ver -h >>/dev/null
'''


# define grammar
ParserElement.setDefaultWhitespaceChars(' \t')
keywords    = ('alias', 'echo', 'setenv', 'ver')  # to be expanded later
keyword     = oneOf( string.join(keywords) )
argument    = Word(alphanums + '_-=/')
redirector  = oneOf('>e> >e>> < << > >> >3> >3>>')
path        = Word(printables)
redirection = redirector + path

#quoted_arg  = ( Suppress("'") + CharsNotIn("'") + Suppress("'") |
#                Suppress('"') + CharsNotIn('"') + Suppress('"') )
quoted_arg = quotedString.setParseAction( removeQuotes ) 

contmode    = oneOf( '; | || & &&' ).setResultsName('contmode')
escapes = Literal('\\') + Word(printables,exact=1)


statement = Group(
    keyword +
    ZeroOrMore(escapes) +
    ZeroOrMore(quoted_arg) +
    ZeroOrMore(argument) +
    ZeroOrMore( Group(redirection) ) +
    Optional(contmode, default=';')
    )
# ZeroOrMore(escapes) +
compound_statement = OneOrMore(statement) + LineEnd().suppress()
compound_statement.ignore(pythonStyleComment)

multi_line_stm = OneOrMore(compound_statement)

# parse
if '\n' in cmdstring:   print multi_line_stm.parseString(cmdstring)
else:                   print compound_statement.parseString(cmdstring)
