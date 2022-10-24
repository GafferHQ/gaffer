##########################################################################
#
#  Copyright (c) 2020, John Haddon. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import pathlib
import unittest

import Gaffer
import GafferUI
import GafferUITest

class CodeWidgetTest( GafferUITest.TestCase ) :

	def testPythonCompleter( self ) :

		namespace = {
			"dictionary" : {
				"cat" : None,
				"dog" : "obi",
				"doggo" : "jackson",
				"subDictionary" : {
					"fish" : 0,
					"bird" : "wagtail",
				},
			},
			"luther" : 0,
			"ludo" : 1,
			"lewis" : "",
		}

		completer = GafferUI.CodeWidget.PythonCompleter( namespace )

		for partial, completions in {
			"dic" : [ "dict(", "dictionary" ],
			"dicti" : [ "dictionary" ],
			"dictionary.ke" : [ "dictionary.keys(" ],
			"dictionary['" : sorted( "dictionary['" + k + "']" for k in namespace["dictionary"].keys() ),
			'dictionary["' : sorted( 'dictionary["' + k + '"]' for k in namespace["dictionary"].keys() ),
			"dictionary['c" : [ "dictionary['cat']" ],
			"dictionary['ca" : [ "dictionary['cat']" ],
			"dictionary['dog']" : [],
			"dictionary['dog'].st" : [ "dictionary['dog'].startswith(", "dictionary['dog'].strip(" ],
			"dictionary['subDictionary'][" : sorted( "dictionary['subDictionary'][\"" + k + "\"]" for k in ( "fish", "bird" ) ),
			"dictionary['subDictionary']['bird'].star" : [ "dictionary['subDictionary']['bird'].startswith(" ],
			"ope" : [ "open(" ],
			"luth" : [ "luther" ],
			"someFunction( luth" : [ "someFunction( luther" ],
			"something.ope" : [],
			"someFunction( dicti" : [ "someFunction( dictionary" ],
			"someFunction( a, dicti" : [ "someFunction( a, dictionary" ],
			"someFunction( a,dicti" : [ "someFunction( a,dictionary" ],
			"someFunction(dicti" : [ "someFunction(dictionary" ],
			"func(dictionary['ca" : [ "func(dictionary['cat']" ],
			"dictionary" : [],
			"dictionary.__seti" : [ "dictionary.__setitem__(" ],
		}.items() :
			self.assertEqual(
				[ c.text for c in completer.completions( partial ) ],
				completions
			)

	def testPathCompletions( self ) :

		namespace = {
			"path" : pathlib.Path( "/")
		}

		completer = GafferUI.CodeWidget.PythonCompleter( namespace )
		completions = completer.completions( "path.absolut" )
		self.assertEqual( [ c.text for c in completions ], [ "path.absolute(" ] )

	def testDisabledGraphComponentAttributeCompletions( self ) :

		completer = GafferUI.CodeWidget.PythonCompleter(
			namespace = {
				"node" : Gaffer.Node()
			},
			includeGraphComponentAttributes = False
		)

		self.assertEqual( completer.completions( "node." ), [] )

if __name__ == "__main__":
	unittest.main()
