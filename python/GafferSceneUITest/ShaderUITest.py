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

import IECore
import IECoreScene

import GafferUI
import GafferUITest
import GafferSceneTest
import GafferSceneUI

class ShaderUITest( GafferUITest.TestCase ) :

	def testNoduleOrdering( self ) :

		s = GafferSceneTest.TestShader()

		g = GafferUI.NodeGadget.create( s )
		n1 = g.nodule( s["parameters"]["i"] )
		n2 = g.nodule( s["parameters"]["c"] )
		g.bound()

		self.assertGreater(
			n1.transformedBound( None ).center().y,
			n2.transformedBound( None ).center().y
		)

	def testShaderPathNestedShaders( self ) :

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"output" : IECoreScene.Shader( "mySurface" ),
				"nested/texture" : IECoreScene.Shader( "myTexture" ),
				"projection" : IECoreScene.Shader( "myProjection" ),
			},
			connections = [
				( ( "projection", "out" ), ( "nested/texture", "uv" ) ),
				( ( "nested/texture", "out" ), ( "output", "color" ) ),
			],
			output = ( "output", "out" )
		)

		path = GafferSceneUI.ShaderUI._ShaderPath( [ network ], "/" )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/output", "/nested", "/projection" ] )

		path.setFromString( "/nested" )
		self.assertFalse( path.isLeaf() )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/nested/texture" ] )

		path.setFromString( "/nested/texture" )
		self.assertFalse( path.isLeaf() )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/nested/texture/uv" ] )

		path.setFromString( "/nested/texture/uv" )
		self.assertTrue( path.isLeaf() )
		self.assertEqual( path.property( "shader:inputs" ), { "projection" } )

		path.setFromString( "/output/color" )
		self.assertEqual( path.property( "shader:inputs" ), { "nested/texture" } )

if __name__ == "__main__":
	unittest.main()
