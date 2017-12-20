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

import imath

import IECore
import IECoreScene

import GafferScene
import GafferSceneTest

class ResamplePrimitiveVariablesTest( GafferSceneTest.SceneTestCase ) :

	def makeQuad( self ) :

		verticesPerFace = IECore.IntVectorData( [4] )
		vertexIds = IECore.IntVectorData( [0, 1, 2, 3] )
		p = IECore.V3fVectorData( [imath.V3f( 0, 0, 0 ), imath.V3f( 1, 0, 0 ), imath.V3f( 1, 1, 0 ), imath.V3f( 0, 1, 0 )] )
		a = IECore.FloatVectorData( [0, 1, 2, 3] )
		b = IECore.FloatVectorData( [4, 5, 6, 7] )

		c = IECore.FloatData( 42 )

		mesh = IECoreScene.MeshPrimitive( verticesPerFace, vertexIds, "linear", p )
		mesh["a"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, a )
		mesh["b"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.FaceVarying, b )
		mesh["c"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, c )

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
		resample["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant ) # constant
		resample['names'].setValue( "a" )

		actualObject = resample["out"].object( "/object" )

		self.assertEqual( IECoreScene.PrimitiveVariable.Interpolation.Constant, actualObject["a"].interpolation )
		self.assertEqual( actualObject["a"].data, IECore.FloatData( 1.5 ) )

	def testNoFilterIsNOP( self ) :

		quadScene = self.makeQuad()

		resample = GafferScene.ResamplePrimitiveVariables()

		resample["in"].setInput( quadScene["out"] )
		resample["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Constant ) # constant
		resample['names'].setValue( "a" )

		actualObject = resample["out"].object( "/object" )

		self.assertEqual( actualObject["a"].interpolation, IECoreScene.PrimitiveVariable.Interpolation.FaceVarying )
		self.assertEqual( actualObject["a"].data, IECore.FloatVectorData( [0, 1, 2, 3] ) )

	def testConstantToVertex( self ) :

		quadScene = self.makeQuad()

		resample = GafferScene.ResamplePrimitiveVariables()

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		resample["in"].setInput( quadScene["out"] )
		resample["filter"].setInput( pathFilter["out"] )
		resample["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Vertex )
		resample['names'].setValue( "c" )

		actualObject = resample["out"].object( "/object" )

		self.assertEqual( IECoreScene.PrimitiveVariable.Interpolation.Vertex, actualObject["c"].interpolation )
		self.assertEqual( actualObject["c"].data, IECore.FloatVectorData( [42, 42, 42, 42] ) )

	def testInvalidPrimitiveThrowsException(self):

		nurbsPrimitive = IECoreScene.NURBSPrimitive()
		nurbsPrimitive["a"] = IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Vertex,  IECore.FloatVectorData( [0, 1, 2, 3] ) )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( nurbsPrimitive )

		resample = GafferScene.ResamplePrimitiveVariables()

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		resample["in"].setInput( objectToScene["out"] )
		resample["filter"].setInput( pathFilter["out"] )
		resample["interpolation"].setValue( IECoreScene.PrimitiveVariable.Interpolation.Invalid )  # invalid
		resample['names'].setValue( "a" )

		self.assertRaises( RuntimeError, lambda : resample["out"].object( "/object" ) )
