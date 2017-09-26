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

import os
import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class MeshTangentsTest( GafferSceneTest.SceneTestCase ) :

	def makeTriangleScene( self ) :

		verticesPerFace = IECore.IntVectorData( [3] )
		vertexIds = IECore.IntVectorData( [0, 1, 2] )
		p = IECore.V3fVectorData( [IECore.V3f( 0, 0, 0 ), IECore.V3f( 1, 0, 0 ), IECore.V3f( 0, 1, 0 )] )
		prefData = IECore.V3fVectorData( [IECore.V3f( 0, 0, 0 ), IECore.V3f( 0, -1, 0 ), IECore.V3f( 1, 0, 0 )] )

		mesh = IECore.MeshPrimitive( verticesPerFace, vertexIds, "linear", p )

		mesh["uv"] = IECore.PrimitiveVariable(
			IECore.PrimitiveVariable.Interpolation.FaceVarying,
			IECore.V2fVectorData(
				[ IECore.V2f( 0, 0 ), IECore.V2f( 1, 0 ), IECore.V2f( 0, 1 ) ],
				IECore.GeometricData.Interpretation.UV
			)
		)

		mesh["foo"] = IECore.PrimitiveVariable(
			IECore.PrimitiveVariable.Interpolation.FaceVarying,
			IECore.V2fVectorData(
				[ IECore.V2f( 0, 0 ), IECore.V2f( 0, 1 ), IECore.V2f( 1, 0 ) ],
				IECore.GeometricData.Interpretation.UV
			)
		)

		mesh["Pref"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Vertex, prefData )

		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setValue( mesh )

		return objectToScene

	def test( self ) :

		meshTangents = GafferScene.MeshTangents()

		triangleScene = self.makeTriangleScene()
		meshTangents["in"].setInput( triangleScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		meshTangents["filter"].setInput( pathFilter["out"] )

		object = meshTangents['out'].object( "/object" )

		uTangent = object["uTangent"]
		vTangent = object["vTangent"]

		self.assertEqual( len( uTangent.data ), 3 )
		self.assertEqual( len( vTangent.data ), 3 )

		for v in uTangent.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 1, 0, 0 ), 0.000001 ) )

		for v in vTangent.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 0, 1, 0 ), 0.000001 ) )

	def testCanRenameOutputTangents( self ) :

		meshTangents = GafferScene.MeshTangents()

		triangleScene = self.makeTriangleScene()
		meshTangents["in"].setInput( triangleScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		meshTangents["filter"].setInput( pathFilter["out"] )
		meshTangents["uTangent"].setValue( "foo" )
		meshTangents["vTangent"].setValue( "bar" )

		object = meshTangents['out'].object( "/object" )

		uTangent = object["foo"]
		vTangent = object["bar"]

		self.assertEqual( len( uTangent.data ), 3 )
		self.assertEqual( len( vTangent.data ), 3 )

		for v in uTangent.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 1, 0, 0 ), 0.000001 ) )

		for v in vTangent.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 0, 1, 0 ), 0.000001 ) )

	def testCanUseSecondUVSet( self ) :

		meshTangents = GafferScene.MeshTangents()

		meshTangents["uvSet"].setValue( "foo" )

		triangleScene = self.makeTriangleScene()
		meshTangents["in"].setInput( triangleScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		meshTangents["filter"].setInput( pathFilter["out"] )

		object = meshTangents['out'].object( "/object" )

		uTangent = object["uTangent"]
		vTangent = object["vTangent"]

		self.assertEqual( len( uTangent.data ), 3 )
		self.assertEqual( len( vTangent.data ), 3 )

		for v in uTangent.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 0, 1, 0 ), 0.000001 ) )

		# really I'd expect the naive answer to the vTangent to be IECore.V3f( 1, 0, 0 )
		# but the code forces the triple of n, uT, vT to flip the direction of vT if we don't have a correctly handed set of basis vectors
		for v in vTangent.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( -1, 0, 0 ), 0.000001 ) )

	def testCanUsePref( self ) :

		meshTangents = GafferScene.MeshTangents()

		meshTangents["position"].setValue( "Pref" )

		triangleScene = self.makeTriangleScene()
		meshTangents["in"].setInput( triangleScene["out"] )

		pathFilter = GafferScene.PathFilter( "PathFilter" )
		pathFilter["paths"].setValue( IECore.StringVectorData( ['/object'] ) )

		meshTangents["filter"].setInput( pathFilter["out"] )

		object = meshTangents['out'].object( "/object" )

		uTangent = object["uTangent"]
		vTangent = object["vTangent"]

		self.assertEqual( len( uTangent.data ), 3 )
		self.assertEqual( len( vTangent.data ), 3 )

		for v in uTangent.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 0, -1, 0 ), 0.000001 ) )

		for v in vTangent.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 1, 0, 0 ), 0.000001 ) )
