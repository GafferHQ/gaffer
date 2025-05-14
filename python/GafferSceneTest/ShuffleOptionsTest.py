##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class ShuffleOptionsTest( GafferSceneTest.SceneTestCase ) :

	def testShuffles( self ) :

		options = GafferScene.CustomOptions()
		for name in "abcd" :
			options["options"].addChild( Gaffer.NameValuePlug( name, name ) )

		shuffle = GafferScene.ShuffleOptions()
		shuffle["in"].setInput( options["out"] )
		self.assertScenesEqual( shuffle["out"], shuffle["in"] )

		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "a", "A", deleteSource = True ) )
		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "b", "c", replaceDestination = True ) )
		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "c", "C" ) )

		self.assertEqual(
			shuffle["out"].globals(),
			IECore.CompoundObject( {
				"option:A" : IECore.StringData( "a" ),
				"option:b" : IECore.StringData( "b" ),
				"option:c" : IECore.StringData( "b" ),
				"option:C" : IECore.StringData( "c" ),
				"option:d" : IECore.StringData( "d" ),
			} )
		)

		options["options"][0]["name"].setValue( "x" )
		self.assertEqual(
			shuffle["out"].globals(),
			IECore.CompoundObject( {
				"option:x" : IECore.StringData( "a" ),
				"option:b" : IECore.StringData( "b" ),
				"option:c" : IECore.StringData( "b" ),
				"option:C" : IECore.StringData( "c" ),
				"option:d" : IECore.StringData( "d" ),
			} )
		)

		shuffle["shuffles"][1]["enabled"].setValue( False )
		self.assertEqual(
			shuffle["out"].globals(),
			IECore.CompoundObject( {
				"option:x" : IECore.StringData( "a" ),
				"option:b" : IECore.StringData( "b" ),
				"option:c" : IECore.StringData( "c" ),
				"option:C" : IECore.StringData( "c" ),
				"option:d" : IECore.StringData( "d" ),
			} )
		)

	def testNonOptionsIgnored( self ) :

		shuffle = GafferScene.ShuffleOptions()
		shuffle["in"]["globals"].setValue(
			IECore.CompoundObject( {
				"a" : IECore.StringData( "a" ),
				"otherPrefix:a" : IECore.StringData( "b" ),
			} )
		)

		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "a", "b" ) )
		self.assertScenesEqual( shuffle["in"], shuffle["out"] )

if __name__ == "__main__":
	unittest.main()
