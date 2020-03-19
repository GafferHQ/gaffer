##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

import unittest

import IECore
import IECoreScene

import GafferTest
import GafferArnoldUI.Private.VisualiserAlgo as VisualiserAlgo

class VisualiserAlgoTest( GafferTest.TestCase ) :

	def testConformToOSLNetworkFull( self ) :

		# Tests reserved word suffxing, bool to int conversions and output renaming

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"blackbodyHandle" : IECoreScene.Shader( "blackbody", "ai:shader", { "normalize" : True } ),
				"imageHandle" :     IECoreScene.Shader( "image",     "ai:shader", { "filename" :"/a/map", "sflip" : True } ),
				"multiplyHandle" :  IECoreScene.Shader( "multiply",  "ai:shader" ),
			},
			connections = [
				( ( "blackbodyHandle", "" ), ( "multiplyHandle", "input1" ) ),
				( ( "imageHandle",     "" ), ( "multiplyHandle", "input2" ) ),
			],
			output = "multiplyHandle"
		)

		convertedNetwork = VisualiserAlgo.conformToOSLNetwork( network.getOutput(), network )

		self.assertEqual( convertedNetwork.shaders(), {
			"blackbodyHandle" : IECoreScene.Shader( "__viewer/__arnold_blackbody", "osl:shader", { "normalize_" : 1 } ),
			"imageHandle" :     IECoreScene.Shader( "__viewer/__arnold_image",     "osl:shader", { "filename" : "/a/map", "sflip" : 1 } ),
			"multiplyHandle" :  IECoreScene.Shader( "__viewer/__arnold_multiply",  "osl:shader" )
		} )

		self.assertEqual( convertedNetwork.inputConnections( "multiplyHandle" ), [
			( ( "blackbodyHandle", "out" ), ( "multiplyHandle", "input1" ) ),
			( ( "imageHandle",     "out" ), ( "multiplyHandle", "input2" ) )
		] )

		self.assertEqual( convertedNetwork.getOutput(), ( "multiplyHandle", "out" ) )

	def testConformToOSLNetworkImageFallback( self ) :

		# Tests fallback on image

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"image1Handle" :      IECoreScene.Shader( "image", "ai:shader", { "filename" : "1" } ),
				"image2Handle" :      IECoreScene.Shader( "image", "ai:shader", { "filename" : "2" } ),
				"unsupportedHandle" : IECoreScene.Shader( "__never_supported__", "ai:shader" )
			},
			connections = [
				( ( "image1Handle", "" ), ( "unsupportedHandle", "input1" ) ),
				( ( "image2Handle", "" ), ( "unsupportedHandle", "input2" ) ),
			],
			output = "unsupportedHandle"
		)

		with IECore.CapturingMessageHandler() as mh :
			convertedNetwork = VisualiserAlgo.conformToOSLNetwork( network.getOutput(), network )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertTrue( "__never_supported__" in mh.messages[0].message )
		self.assertTrue( "image2Handle" in mh.messages[0].message )

		self.assertEqual( convertedNetwork.shaders(), {
			"image" : IECoreScene.Shader( "__viewer/__arnold_image", "osl:shader", { "filename" : "2" } )
		} )
		self.assertEqual( convertedNetwork.getOutput(), ( "image", "out" ) )

	def testConformToOSLNetworkFailure( self ) :

		# Test null network

		network = IECoreScene.ShaderNetwork(
			shaders = {
				"unsupportedHandle" :  IECoreScene.Shader( "__never_supported__", "ai:shader" ),
				"unsupported2Handle" : IECoreScene.Shader( "__never_supported__", "ai:shader" )
			},
			connections = [
				( ( "unsupported2Handle", "" ), ( "unsupportedHandle", "input" ) )
			],
			output = "unsupportedHandle"
		)

		with IECore.CapturingMessageHandler() as mh :
			convertedNetwork = VisualiserAlgo.conformToOSLNetwork( network.getOutput(), network )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Error )
		self.assertTrue( "__never_supported__" in mh.messages[0].message )
		self.assertIsNone( convertedNetwork )

if __name__ == "__main__":
	unittest.main()
