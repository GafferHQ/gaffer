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
			node["scheme"].getValue() == MeshAlgo.SubdivisionScheme.FromMesh
		):
			reference = source
		else:
			reference = MeshAlgo.tessellateMesh(
				source, node["divisions"].getValue(),
				calculateNormals = node["calculateNormals"].getValue(),
				scheme = MeshAlgo.SubdivisionScheme( node["scheme"].getValue() )
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

		tessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.Bilinear )
		self.assertNodeCorrect( tessellate, "object" )

		tessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.FromMesh )
		sphere = GafferScene.Sphere()

		tessellate["in"].setInput( sphere["out"] )
		self.assertNodeCorrect( tessellate, "sphere" )

		tessellate["tessellatePolygons"].setValue( True )
		self.assertNodeCorrect( tessellate, "sphere" )

		tessellate["tessellatePolygons"].setValue( False )
		tessellate["scheme"].setValue( MeshAlgo.SubdivisionScheme.CatmullClark )
		self.assertNodeCorrect( tessellate, "sphere" )

if __name__ == "__main__":
	unittest.main()
