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

import inspect

import GafferUI
import GafferOSLTest
import GafferOSLUI

class HighlighterTest( GafferOSLTest.OSLTestCase ) :

	def __highlights( self, text ) :

		highlighter = GafferOSLUI._CodeWidget._Highlighter()
		result = []

		previousType = None
		for line in text.split( "\n" ) :
			highlights = highlighter.highlights( line, previousType )
			result.extend( highlights )
			if highlights and highlights[-1].end is None :
				previousType = highlights[-1].type
			else :
				previousType = None

		return result

	def test( self ) :

		Type =  GafferUI.CodeWidget.Highlighter.Type
		Highlight = GafferUI.CodeWidget.Highlighter.Highlight

		for code, highlights in {

			'"apple"' :
			[
				Highlight( 0, 7, Type.DoubleQuotedString ),
			],

			"0xabc1" :
			[
				Highlight( 0, 6, Type.Number ),
			],

			"100" :
			[
				Highlight( 0, 3, Type.Number ),
			],

			"100." :
			[
				Highlight( 0, 4, Type.Number ),
			],

			"0.1" :
			[
				Highlight( 0, 3, Type.Number ),
			],

			".1" :
			[
				Highlight( 0, 2, Type.Number ),
			],

			"1e6" :
			[
				Highlight( 0, 3, Type.Number ),
			],

			"catch bool  enum extern" :
			[
				Highlight( 0, 5, Type.ReservedWord ),
				Highlight( 6, 10, Type.ReservedWord ),
				Highlight( 12, 16, Type.ReservedWord ),
				Highlight( 17, 23, Type.ReservedWord ),
			],

			'"catch 0.1 string int"' :
			[
				Highlight( 0, 22, Type.DoubleQuotedString ),
			],

			"// simple comment" :
			[
				Highlight( 0, 17, Type.Comment ),
			],

			"// int 10.1" :
			[
				Highlight( 0, 11, Type.Comment ),
			],

			"/* comment */ 10.1" :
			[
				Highlight( 0, 13, Type.Comment ),
				Highlight( 14, 18, Type.Number ),
			],

			"""
			/* multi
			* line
			* comment
			*/
			""" :
			[
				Highlight( 0, None, Type.Comment ),
				Highlight( 0, None, Type.Comment ),
				Highlight( 0, None, Type.Comment ),
				Highlight( 0, 2, Type.Comment ),
			],

			"""
			/* multi
			* line
			* comment
			* 3.4
			*/ int, string
			""" :
			[
				Highlight( 0, None, Type.Comment ),
				Highlight( 0, None, Type.Comment ),
				Highlight( 0, None, Type.Comment ),
				Highlight( 0, None, Type.Comment ),
				Highlight( 0, 2, Type.Comment ),
				Highlight( 3, 6, Type.Keyword ),
				Highlight( 8, 14, Type.Keyword ),
			],

			"a += b" :
			[
				Highlight( 2, 4, Type.Operator ),
			],

			"a << b" :
			[
				Highlight( 2, 4, Type.Operator ),
			],

			"#ifdef 100" :
			[
				Highlight( 0, 6, Type.Preprocessor ),
				Highlight( 7, 10, Type.Number ),
			],

			"OSL_VERSION_MAJOR" :
			[
				Highlight( 0, 17, Type.Preprocessor ),
			],

			"color" :
			[
				Highlight( 0, 5, Type.Keyword ),
			],

			"output1" : [],

		}.items() :

			self.assertEqual(
				self.__highlights( inspect.cleandoc( code ) ),
				highlights,
				msg = "Code is `{}`".format( code )
			)

if __name__ == "__main__":
	unittest.main()
