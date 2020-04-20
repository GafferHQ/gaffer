##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import imath
import os
import six
import sys

import IECore
import IECoreScene

import Gaffer
import GafferOSL
import GafferOSLTest

class ShadingEngineAlgoTest( GafferOSLTest.OSLTestCase ) :

	def testShadeTexture( self ) :

		uvShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/uv.osl" )
		constant = self.compileShader( os.path.dirname( __file__ ) + "/shaders/constant.osl" )
		addShader = self.compileShader( os.path.dirname( __file__ ) + "/shaders/add.osl" )

		n = IECoreScene.ShaderNetwork(
			shaders = {
				"uvs" : IECoreScene.Shader( uvShader, "osl:shader" ),
				"add" : IECoreScene.Shader( addShader, "osl:shader", { "b" : 1.0 } ),
				"constant" : IECoreScene.Shader( constant, "osl:surface" ),
			},
			connections = [
				( ( "uvs", "out" ), ( "add", "a" ) ),
				( ( "add", "out" ), ( "constant", "Cs" ) )
			],
			output = "constant"
		)

		resolution = imath.V2i( 2, 4 )
		window = imath.Box2i( imath.V2i( 0 ), imath.V2i( 1, 3 ) )
		u =  ( 0.25, 0.75, 0.25, 0.75, 0.25, 0.75, 0.25, 0.75 )
		v =  ( 0.125, 0.125, 0.375, 0.375, 0.625, 0.625, 0.875, 0.875 )
		b = [ 0.0 ] * 8
		uu = [ x + 1.0 for x in u ]
		vv = [ x + 1.0 for x in v ]
		bb = [ 1.0 ] * 8

		# Test None passed as ptr

		with six.assertRaisesRegex( self, Exception, "Python argument types .*" ) :
			GafferOSL.ShadingEngineAlgo.shadeUVTexture( None, resolution )

		# Test network output

		imageData = GafferOSL.ShadingEngineAlgo.shadeUVTexture( n, resolution )
		self.assertEqual( sorted( imageData.keys() ), sorted( ( "dataWindow", "displayWindow", "channels" ) ))

		self.assertEqual( imageData["dataWindow"], IECore.Box2iData( window ) )
		self.assertEqual( imageData["displayWindow"], IECore.Box2iData( window ) )

		c = imageData["channels"]
		self.assertEqual( sorted( c.keys() ), sorted( ( "R", "G", "B" ) ) )
		self.assertEqual( c["R"], IECore.FloatVectorData( uu ) )
		self.assertEqual( c["G"], IECore.FloatVectorData( vv ) )
		self.assertEqual( c["B"], IECore.FloatVectorData( bb ) )

		# Test invalid resolutions

		with self.assertRaises( Exception ) :
			GafferOSL.ShadingEngineAlgo.imageShadingPoints( imath.V2i( 0, 0 ) )

		with self.assertRaises( Exception ) :
			GafferOSL.ShadingEngineAlgo.imageShadingPoints( imath.V2i( -1, 0 ) )

		with self.assertRaises( Exception ) :
			GafferOSL.ShadingEngineAlgo.imageShadingPoints( imath.V2i( 0, -1 ) )

		# Test alternate output

		imageData = GafferOSL.ShadingEngineAlgo.shadeUVTexture( n, resolution, ( "uvs", "out" ) )

		c = imageData["channels"]
		self.assertEqual( sorted( c.keys() ), sorted( ( "R", "G", "B" ) ) )
		self.assertEqual( c["R"], IECore.FloatVectorData( u ) )
		self.assertEqual( c["G"], IECore.FloatVectorData( v ) )
		self.assertEqual( c["B"], IECore.FloatVectorData( b ) )

		# Test network without surface as output

		n = IECoreScene.ShaderNetwork(
			shaders = {
				"uvs" : IECoreScene.Shader( uvShader, "osl:shader" ),
			},
			output = ( "uvs", "out" )
		)

		imageData = GafferOSL.ShadingEngineAlgo.shadeUVTexture( n, resolution )

		self.assertEqual( imageData["dataWindow"], IECore.Box2iData( window ) )
		self.assertEqual( imageData["displayWindow"], IECore.Box2iData( window ) )

		c = imageData["channels"]
		self.assertEqual( sorted( c.keys() ), sorted( ( "R", "G", "B" ) ) )
		self.assertEqual( c["R"], IECore.FloatVectorData( u ) )
		self.assertEqual( c["G"], IECore.FloatVectorData( v ) )
		self.assertEqual( c["B"], IECore.FloatVectorData( b ) )

if __name__ == "__main__":
	unittest.main()
