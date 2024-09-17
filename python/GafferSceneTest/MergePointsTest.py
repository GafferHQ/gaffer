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
import inspect
import pathlib
import random

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest
import GafferTest

class MergePointsTest( GafferSceneTest.SceneTestCase ) :

	def testBasic( self ) :
		# The base class MergeObjects functionality is tested thoroughly in MergeMeshesTest.py, and
		# the points specific functionality is tested in IECoreScenePreviewTest/PrimitiveAlgoTest.py,
		# so we only need basic tests here to make sure everything is getting passed through correctly.

		plane1 = GafferScene.Plane()

		plane2 = GafferScene.Plane()
		plane2["dimensions"].setValue( imath.V2f( 2 ) )
		plane2["transform"]["translate"].setValue( imath.V3f( 0, 0, 3 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( plane1["out"] )
		group["in"][1].setInput( plane2["out"] )

		chooseFilter = GafferScene.PathFilter()
		chooseFilter["paths"].setValue( IECore.StringVectorData( [ "/group/plane", "/group/plane1" ] ) )

		meshToPoints = GafferScene.MeshToPoints()
		meshToPoints["in"].setInput( group["out"] )
		meshToPoints["filter"].setInput( chooseFilter["out"] )

		mergePoints = GafferScene.MergePoints()
		mergePoints["in"].setInput( meshToPoints["out"] )
		mergePoints["filter"].setInput( chooseFilter["out"] )

		result = mergePoints["out"].object( "mergedPoints" )

		ref = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( *i ) for i in [
			( -0.5, -0.5, 0 ), ( 0.5, -0.5, 0 ), ( -0.5, 0.5, 0 ), ( 0.5, 0.5, 0 ),
			( -1, -1, 3 ), ( 1, -1, 3 ), ( -1, 1, 3 ), ( 1, 1, 3 )
		] ] ) )
		ref["N"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex, IECore.V3fVectorData( [ imath.V3f( 0, 0, 1 ) ] * 8, IECore.GeometricData.Interpretation.Normal )
		)
		ref["type"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant, IECore.StringData( "particle" )
		)

		self.assertEqual( result, ref )

if __name__ == "__main__":
	unittest.main()
