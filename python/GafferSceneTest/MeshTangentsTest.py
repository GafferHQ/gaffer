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
		s = IECore.FloatVectorData( [0, 1, 0] )
		t = IECore.FloatVectorData( [0, 0, 1] )

		mesh = IECore.MeshPrimitive( verticesPerFace, vertexIds, "linear", p )
		mesh["s"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.FaceVarying, s )
		mesh["t"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.FaceVarying, t )

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

		tangentPrimVar = object["dPds"]
		binormalPrimVar = object["dPdt"]

		self.assertEqual( len( tangentPrimVar.data ), 3 )
		self.assertEqual( len( binormalPrimVar.data ), 3 )

		for v in tangentPrimVar.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 1, 0, 0 ), 0.000001 ) )

		for v in binormalPrimVar.data :
			self.failUnless( v.equalWithAbsError( IECore.V3f( 0, 1, 0 ), 0.000001 ) )
