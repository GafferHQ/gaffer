##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import os
import unittest

import Gaffer
import GafferOSL
import GafferOSLTest

class OSLCodeTest( GafferOSLTest.OSLTestCase ) :

	def test( self ) :

		for shader in ( "types", "outputTypes" ) :

			oslFileName = os.path.join( os.path.dirname( __file__ ), "shaders", shader + ".osl" )

			n1 = GafferOSL.OSLShader()
			n1.loadShader( self.compileShader( oslFileName ) )

			with open( oslFileName ) as f :
				code = f.read()

			n2 = GafferOSL.OSLCode()
			n2.setCode( code )
			self.assertEqual( n2.getCode(), code )

			self.assertEqual( n1["parameters"].keys(), n2["parameters"].keys() )
			self.assertEqual( n1["out"].keys(), n2["out"].keys() )

			for p1 in n1["parameters"].children() + n1["out"].children() :
				p2 = n2.descendant( p1.relativeName( n1 ) )
				self.assertEqual( repr( p1 ), repr( p2 ) )
				self.assertEqual( p1.getValue(), p2.getValue() )

	def testParseError( self ) :

		n = GafferOSL.OSLCode()
		self.assertRaises( RuntimeError, n.setCode, "oops" )

	def testParseErrorDoesntDestroyExistingPlugs( self ) :

		with open( os.path.join( os.path.dirname( __file__ ), "shaders", "types.osl" ) ) as f :
			code = f.read()

		n = GafferOSL.OSLCode()
		n.setCode( code )

		existingParameterPlugs = dict( n["parameters"] )
		self.assertRaises( RuntimeError, n.setCode, "oops" )
		self.assertEqual( dict( n["parameters" ] ), existingParameterPlugs )

	def testEmpty( self ) :

		n = GafferOSL.OSLCode()
		n.setCode( "" )
		self.assertEqual( n.getCode(), "" )

		code = "surface test( float x = 0, string ss = \"t\" ){}"
		n.setCode( code )
		self.assertEqual( n.getCode(), code )

		n.setCode( "" )
		self.assertEqual( n.getCode(), "" )
		self.assertEqual( len( n["parameters"] ), 0 )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		code = "surface test( float x = 0, string ss = \"t\" ){}"

		s["n"] = GafferOSL.OSLCode()
		s["n"].setCode( code )
		self.assertTrue( "x" in s["n"]["parameters"] )
		self.assertTrue( "ss" in s["n"]["parameters"] )
		self.assertEqual( s["n"].getCode(), code )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertTrue( "x" in s2["n"]["parameters"] )
		self.assertTrue( "ss" in s2["n"]["parameters"] )
		self.assertEqual( s2["n"].getCode(), code )

	def testNoExtensionInName( self ) :

		n = GafferOSL.OSLCode()
		n.setCode( "surface test(){}" )

		self.assertEqual( os.path.splitext( n["name"].getValue() )[1], "" )

if __name__ == "__main__":
	unittest.main()
