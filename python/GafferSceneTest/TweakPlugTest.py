##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class TweakPlugTest( GafferSceneTest.SceneTestCase ) :

	def testConstructor( self ) :

		p = GafferScene.TweakPlug( "test", 10.0, GafferScene.TweakPlug.Mode.Multiply, enabled = False )

		self.assertEqual( p["name"].defaultValue(), "" )
		self.assertEqual( p["name"].getValue(), "test" )

		self.assertIsInstance( p["value"], Gaffer.FloatPlug )
		self.assertEqual( p["value"].defaultValue(), 10 )
		self.assertEqual( p["value"].getValue(), 10 )

		self.assertEqual( p["mode"].defaultValue(), p.Mode.Replace )
		self.assertEqual( p["mode"].getValue(), p.Mode.Multiply )

		self.assertEqual( p["enabled"].defaultValue(), True )
		self.assertEqual( p["enabled"].getValue(), False )

	def testWrongDataType( self ) :

		p = GafferScene.TweakPlug( "test", imath.Color3f( 1 ) )
		p["mode"].setValue( p.Mode.Multiply )
		self.assertIsInstance( p["value"], Gaffer.Color3fPlug )

		d = IECore.CompoundData( { "test" : 1 } )

		with self.assertRaisesRegexp( RuntimeError, "Cannot apply tweak to \"test\" : Value of type \"IntData\" does not match parameter of type \"Color3fData\"" ) :
			p.applyTweak( d )

if __name__ == "__main__":
	unittest.main()
