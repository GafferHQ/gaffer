##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
#      * Neither the name of  Image Engine Design Inc nor the names of
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

import GafferScene
import GafferSceneTest

class ResamplePrimitiveVariablesTest( GafferSceneTest.SceneTestCase ) :

	def makeQuad( self ) :

		verticesPerFace = IECore.IntVectorData( [4] )
		vertexIds = IECore.IntVectorData( [0, 1, 2, 3] )
		p = IECore.V3fVectorData( [IECore.V3f( 0, 0, 0 ), IECore.V3f( 1, 0, 0 ), IECore.V3f( 1, 1, 0 ), IECore.V3f( 0, 1, 0 )] )
		a = IECore.FloatVectorData( [0, 1, 2, 3] )
		b = IECore.FloatVectorData( [4, 5, 6, 7] )

		c = IECore.FloatData( 42 )

		mesh = IECore.MeshPrimitive( verticesPerFace, vertexIds, "linear", p )
		mesh["a"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.FaceVarying, a )
		mesh["b"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.FaceVarying, b )
		mesh["c"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Constant, c )

		self.assertTrue( mesh.arePrimitiveVariablesValid() )
		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( mesh )

		return objectToScene

	def testFaceVaryingToConstant( self ) :

		quadScene = self.makeQuad()

		resample = GafferScene.ResamplePrimitiveVariables()

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		resample["in"].setInput( quadScene["out"] )
		resample["filter"].setInput( pathFilter["out"] )
		resample["interpolation"].setValue( IECore.PrimitiveVariable.Interpolation.Constant ) # constant
		resample['names'].setValue( "a" )

		actualObject = resample["out"].object( "/object" )

		self.assertEqual( IECore.PrimitiveVariable.Interpolation.Constant, actualObject["a"].interpolation )
		self.assertEqual( actualObject["a"].data, IECore.FloatData( 1.5 ) )

	def testConstantToVertex( self ) :

		quadScene = self.makeQuad()

		resample = GafferScene.ResamplePrimitiveVariables()

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		resample["in"].setInput( quadScene["out"] )
		resample["filter"].setInput( pathFilter["out"] )
		resample["interpolation"].setValue( IECore.PrimitiveVariable.Interpolation.Vertex )
		resample['names'].setValue( "c" )

		actualObject = resample["out"].object( "/object" )

		self.assertEqual( IECore.PrimitiveVariable.Interpolation.Vertex, actualObject["c"].interpolation )
		self.assertEqual( actualObject["c"].data, IECore.FloatVectorData( [42, 42, 42, 42] ) )

	def testInvalidPrimitiveThrowsException(self):

		nurbsPrimitive = IECore.NURBSPrimitive()
		nurbsPrimitive["a"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Vertex,  IECore.FloatVectorData( [0, 1, 2, 3] ) )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( nurbsPrimitive )

		resample = GafferScene.ResamplePrimitiveVariables()

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		resample["in"].setInput( objectToScene["out"] )
		resample["filter"].setInput( pathFilter["out"] )
		resample["interpolation"].setValue( IECore.PrimitiveVariable.Interpolation.Invalid )  # invalid
		resample['names'].setValue( "a" )

		self.assertRaises( RuntimeError, lambda : resample["out"].object( "/object" ) )