##########################################################################
#
#  Copyright (c) 2024, Alex Fuller. All rights reserved.
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

import imath

import GafferSceneTest
import GafferRenderMan

class RenderManDisplayFilterTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		displayFilter = GafferRenderMan.RenderManShader()
		displayFilter.loadShader( "PxrGradeDisplayFilter" )

		self.assertEqual( displayFilter["name"].getValue(), "PxrGradeDisplayFilter" )
		self.assertEqual( displayFilter["type"].getValue(), "ri:displayfilter" )

		displayFilter["parameters"]["multiply"].setValue( imath.Color3f( 1 ) )

		node = GafferRenderMan.RenderManDisplayFilter()
		node["displayFilter"].setInput( displayFilter["out"] )

		for mode in node.Mode.values.values() :

			# Since there is no upstream display filter, all modes
			# should have the same effect.
			node["mode"].setValue( mode )

			self.assertEqual(
				node["out"].globals()["option:ri:displayfilter"],
				displayFilter.attributes()["ri:displayfilter"]
			)

	def testRejectsNonDisplayFilterInputs( self ) :

		shader = GafferRenderMan.RenderManShader()
		shader.loadShader( "PxrConstant" )

		node = GafferRenderMan.RenderManDisplayFilter()
		self.assertFalse( node["displayFilter"].acceptsInput( shader["out"] ) )

	def testModes( self ) :

		def shaderName( scene ) :

			network = scene.globals()["option:ri:displayfilter"]
			return network.outputShader().name

		def order( scene ) :

			network = scene.globals()["option:ri:displayfilter"]
			shader = network.outputShader()

			if shader.name == "PxrDisplayFilterCombiner" :

				result = []
				for i in range( 0, 3 ) :
					shaderHandle = network.input( ( network.getOutput().shader, f"filter[{i}]" ) ).shader
					if shaderHandle :
						result.append( network.getShader( shaderHandle ).parameters["multiply"].value.r )

				return result

			else:

				return [ shader.parameters["multiply"].value.r ]

		displayFilter1 = GafferRenderMan.RenderManShader()
		displayFilter1.loadShader( "PxrGradeDisplayFilter" )
		displayFilter1["parameters"]["multiply"].setValue( imath.Color3f( 1 ) )

		displayFilter2 = GafferRenderMan.RenderManShader()
		displayFilter2.loadShader( "PxrGradeDisplayFilter" )
		displayFilter2["parameters"]["multiply"].setValue( imath.Color3f( 2 ) )

		displayFilter3 = GafferRenderMan.RenderManShader()
		displayFilter3.loadShader( "PxrGradeDisplayFilter" )
		displayFilter3["parameters"]["multiply"].setValue( imath.Color3f( 3 ) )

		node1 = GafferRenderMan.RenderManDisplayFilter()
		node1["displayFilter"].setInput( displayFilter1["out"] )
		# When there is only one filter, the output shader should be the filter itself
		self.assertEqual( shaderName( node1["out"] ), "PxrGradeDisplayFilter" )
		self.assertEqual( order( node1["out"] ), [ 1 ] )

		node2 = GafferRenderMan.RenderManDisplayFilter()
		node2["in"].setInput( node1["out"] )
		node2["displayFilter"].setInput( displayFilter2["out"] )
		self.assertEqual( shaderName( node2["out"] ), "PxrGradeDisplayFilter" )
		self.assertEqual( order( node2["out"] ), [ 2 ] )

		node2["mode"].setValue( GafferRenderMan.RenderManDisplayFilter.Mode.InsertLast )
		# But 2 or more will place a combine filter as the output
		self.assertEqual( shaderName( node2["out"] ), "PxrDisplayFilterCombiner" )
		self.assertEqual( order( node2["out"] ), [ 1, 2 ] )

		node2["mode"].setValue( GafferRenderMan.RenderManDisplayFilter.Mode.InsertFirst )
		self.assertEqual( shaderName( node2["out"] ), "PxrDisplayFilterCombiner" )
		self.assertEqual( order( node2["out"] ), [ 2, 1 ] )

		node3 = GafferRenderMan.RenderManDisplayFilter()
		node3["in"].setInput( node2["out"] )
		node3["displayFilter"].setInput( displayFilter3["out"] )
		self.assertEqual( shaderName( node3["out"] ), "PxrGradeDisplayFilter" )
		self.assertEqual( order( node3["out"] ), [ 3 ] )

		node3["mode"].setValue( GafferRenderMan.RenderManDisplayFilter.Mode.InsertLast )
		self.assertEqual( shaderName( node3["out"] ), "PxrDisplayFilterCombiner" )
		self.assertEqual( order( node3["out"] ), [ 2, 1, 3 ] )

		node3["mode"].setValue( GafferRenderMan.RenderManDisplayFilter.Mode.InsertFirst )
		self.assertEqual( shaderName( node3["out"] ), "PxrDisplayFilterCombiner" )
		self.assertEqual( order( node3["out"] ), [ 3, 2, 1 ] )

if __name__ == "__main__":
	unittest.main()
