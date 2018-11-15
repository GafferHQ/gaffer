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

import unittest

import IECore

import GafferScene
import GafferSceneTest

class RendererAlgoTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = GafferScene.Sphere()

		defaultAdaptors = GafferScene.createAdaptors()
		defaultAdaptors["in"].setInput( sphere["out"] )

		def a() :

			r = GafferScene.StandardAttributes()
			r["attributes"]["doubleSided"]["enabled"].setValue( True )
			r["attributes"]["doubleSided"]["value"].setValue( False )

			return r

		GafferScene.registerAdaptor( "Test", a )

		testAdaptors = GafferScene.createAdaptors()
		testAdaptors["in"].setInput( sphere["out"] )

		self.assertFalse( "doubleSided" in sphere["out"].attributes( "/sphere" ) )
		self.assertTrue( "doubleSided" in testAdaptors["out"].attributes( "/sphere" ) )
		self.assertEqual( testAdaptors["out"].attributes( "/sphere" )["doubleSided"].value, False )

		GafferScene.deregisterAdaptor( "Test" )

		defaultAdaptors2 = GafferScene.createAdaptors()
		defaultAdaptors2["in"].setInput( sphere["out"] )

		self.assertScenesEqual( defaultAdaptors["out"], defaultAdaptors2["out"] )
		self.assertSceneHashesEqual( defaultAdaptors["out"], defaultAdaptors2["out"] )

	def tearDown( self ) :

		GafferSceneTest.SceneTestCase.tearDown( self )
		GafferScene.deregisterAdaptor( "Test" )

if __name__ == "__main__":
	unittest.main()
