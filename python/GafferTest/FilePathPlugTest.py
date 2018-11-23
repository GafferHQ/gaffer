##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
import inspect
import unittest

import IECore

import Gaffer
import GafferTest

class FilePathPlugTest( GafferTest.StringPlugTest ) :

	def inOutNode( self, name="FilePathInOutNode", defaultValue="", substitutions = IECore.StringAlgo.Substitutions.AllSubstitutions ) :

		return GafferTest.FilePathInOutNode( name = name, defaultValue = defaultValue, substitutions = substitutions )

	def testPathExpansion( self ) :

		n = self.inOutNode()

		# nothing should be expanded when we're in a non-computation context
		n["in"].setValue( "testy/Testy.##.exr" )
		self.assertEqual( n["in"].getValue(), os.path.join( "testy", "Testy.##.exr" ) )

		n["in"].setValue( "${a}/$b/${a:b}" )
		self.assertEqual( n["in"].getValue(), os.path.join( "${a}", "$b", "${a:b}" ) )

		# but expansions should happen magically when the compute()
		# calls getValue().
		context = Gaffer.Context()

		context["env:dir"] = "a/path"
		n["in"].setValue( "a/${env:dir}/b" )
		with context :
			self.assertEqual( n["out"].getValue(), os.path.join( "a", "a", "path", "b" ) )

		# once again, nothing should be expanded when we're in a
		# non-computation context
		n["in"].setValue( "testy/Testy.##.exr" )
		self.assertEqual( n["in"].getValue(), os.path.join( "testy", "Testy.##.exr" ) )

	def testTildeExpansion( self ) :

		n = self.inOutNode()

		n["in"].setValue( "~" )
		self.assertEqual( n["out"].getValue(), os.path.expanduser( "~" ) )

		n["in"].setValue( "~/something.tif" )
		self.assertEqual( n["out"].getValue(), os.path.join( os.path.expanduser( "~" ), "something.tif" ) )

		# ~ shouldn't be expanded unless it's at the front - it would
		# be meaningless in other cases.
		n["in"].setValue( "in ~1900" )
		self.assertEqual( n["out"].getValue(), "in ~1900" )

	def testGenericConversion( self ) :

		n = self.inOutNode()

		n["in"].setValue( os.path.join( "C:", "path", "test.ext" ) )

		self.assertEqual( n["out"].getValue(), os.path.join( "C:", "path", "test.ext" ) )

	def testStringPlugCompatibility( self ):

		s1 = GafferTest.StringPlugTest.inOutNode( self )
		n = self.inOutNode()
		s2 = GafferTest.StringPlugTest.inOutNode( self )

		self.assertTrue( isinstance( s1["in"], Gaffer.StringPlug ) )
		self.assertTrue( isinstance( s1["out"], Gaffer.StringPlug ) )
		self.assertTrue( isinstance( n["in"], Gaffer.FilePathPlug ) )
		self.assertTrue( isinstance( n["out"], Gaffer.FilePathPlug ) )
		self.assertTrue( isinstance( s2["in"], Gaffer.StringPlug ) )
		self.assertTrue( isinstance( s2["out"], Gaffer.StringPlug ) )

		s1["in"].setValue( "test/string.ext" )
		n["in"].setInput( s1["out"] )
		s2["in"].setInput( n["out"] )

		self.assertEqual( s1["out"].getValue(), "test/string.ext" )
		self.assertEqual( n["out"].getValue(), os.path.join( "test", "string.ext" ) )
		if os.name == "nt" :
			# We lose a `\` every time we do a string subsitution with `EscapeSubstitutions`
			# enabled.
			self.assertEqual( s2["out"].getValue(), "teststring.ext" )
		else :
			self.assertEqual( s2["out"].getValue(), "test/string.ext" )


if __name__ == "__main__":
	unittest.main()
