##########################################################################
#
#  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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
import pathlib

import IECore
import IECoreScene

import Gaffer
import GafferTest

import GafferScene
import GafferScene.Private.IECoreScenePreview.MeshAlgo as MeshAlgo
import GafferSceneTest

class MeshTessellateTest( GafferSceneTest.SceneTestCase ) :

	# Compare the results from the node computation to manually calling MeshAlgo.tessellateMesh.
	def assertNodeCorrect( self, node, path ):
		source = node["in"].object( path )
		self.assertTrue( source.verticesPerFace.size() > 0 )

		if (
			not node["tessellatePolygons"].getValue() and
			source.interpolation == "linear" and
			node["scheme"].getValue() == ""
		):
			reference = source
		else:
			reference = MeshAlgo.tessellateMesh(
				source, node["divisions"].getValue(),
				calculateNormals = node["calculateNormals"].getValue(),
				scheme = node["scheme"].getValue(),
				interpolateBoundary = node["interpolateBoundary"].getValue(),
				faceVaryingLinearInterpolation = node["faceVaryingLinearInterpolation"].getValue(),
				triangleSubdivisionRule = node["triangleSubdivisionRule"].getValue(),
			)

		self.assertEqual( node["out"].object( path ), reference )

	# MeshTessellate is a pretty thin wrapper - the main way it could go wrong is if the
	# hash function missed something, and it didn't update when a parameter value changed.
	#
	# We just try setting each parameter, and make sure the result matches MesheAlgo.tessellateMesh
	def test( self ) :

		testReader = GafferScene.SceneReader()
		testReader["fileName"].setValue( pathlib.Path( __file__ ).parent / "usdFiles" / "generalTestMesh.usd" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/*' ] ) )

		tessellate = GafferScene.MeshTessellate()
		tessellate["in"].setInput( testReader["out"] )
		tessellate["filter"].setInput( filter["out"] )

		self.assertNodeCorrect( tessellate, "object" )

		tessellate["divisions"].setValue( 2 )
		self.assertNodeCorrect( tessellate, "object" )

		tessellate["calculateNormals"].setValue( True )
		self.assertNodeCorrect( tessellate, "object" )


		# For the parameters shared with MeshType, we should get the same result if we use a MeshType to set
		# the parameter, vs setting it on the MeshTessellate node
		meshType = GafferScene.MeshType()
		meshType["in"].setInput( tessellate["in"] )
		meshType["filter"].setInput( filter["out"] )
		meshType["meshType"].setInput( tessellate["scheme"] )
		meshType["interpolateBoundary"].setInput( tessellate["interpolateBoundary"] )
		meshType["faceVaryingLinearInterpolation"].setInput( tessellate["faceVaryingLinearInterpolation"] )
		meshType["triangleSubdivisionRule"].setInput( tessellate["triangleSubdivisionRule"] )

		defaultTessellate = GafferScene.MeshTessellate()
		defaultTessellate["in"].setInput( meshType["out"] )
		defaultTessellate["filter"].setInput( filter["out"] )
		defaultTessellate["divisions"].setValue( 2 )
		defaultTessellate["calculateNormals"].setValue( True )


		tessellate["scheme"].setValue( "bilinear" )
		self.assertNodeCorrect( tessellate, "object" )
		self.assertEqual( tessellate["out"].object("/object"), defaultTessellate["out"].object("/object") )

		tessellate["scheme"].setValue( "" )
		sphere = GafferScene.Sphere()

		tessellate["in"].setInput( sphere["out"] )
		self.assertNodeCorrect( tessellate, "sphere" )
		self.assertEqual( tessellate["out"].object("/sphere"), defaultTessellate["out"].object("/sphere") )

		tessellate["tessellatePolygons"].setValue( True )
		defaultTessellate["tessellatePolygons"].setValue( True )
		self.assertNodeCorrect( tessellate, "sphere" )
		self.assertEqual( tessellate["out"].object("/sphere"), defaultTessellate["out"].object("/sphere") )

		tessellate["tessellatePolygons"].setValue( False )
		defaultTessellate["tessellatePolygons"].setValue( False )
		tessellate["scheme"].setValue( "catmullClark" )
		self.assertNodeCorrect( tessellate, "sphere" )
		self.assertEqual( tessellate["out"].object("/sphere"), defaultTessellate["out"].object("/sphere") )

		tessellate["in"].setInput( testReader["out"] )

		for ib in [
			IECoreScene.MeshPrimitive.interpolateBoundaryNone,
			IECoreScene.MeshPrimitive.interpolateBoundaryEdgeOnly,
			IECoreScene.MeshPrimitive.interpolateBoundaryEdgeAndCorner
		]:
			tessellate["interpolateBoundary"].setValue( ib )
			self.assertNodeCorrect( tessellate, "object" )
			self.assertEqual( tessellate["out"].object("/object"), defaultTessellate["out"].object("/object") )

		for fvli in [
			IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationNone,
			IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersOnly,
			IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersPlus1,
			IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationCornersPlus2,
			IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationBoundaries,
			IECoreScene.MeshPrimitive.faceVaryingLinearInterpolationAll
		]:
			tessellate["faceVaryingLinearInterpolation"].setValue( fvli )
			self.assertNodeCorrect( tessellate, "object" )
			self.assertEqual( tessellate["out"].object("/object"), defaultTessellate["out"].object("/object") )

		for tsr in [
			IECoreScene.MeshPrimitive.triangleSubdivisionRuleCatmullClark,
			IECoreScene.MeshPrimitive.triangleSubdivisionRuleSmooth,
		]:
			tessellate["triangleSubdivisionRule"].setValue( tsr )
			self.assertNodeCorrect( tessellate, "object" )
			self.assertEqual( tessellate["out"].object("/object"), defaultTessellate["out"].object("/object") )


if __name__ == "__main__":
	unittest.main()
