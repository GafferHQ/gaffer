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

class MergeCurvesTest( GafferSceneTest.SceneTestCase ) :

	def testBasic( self ) :
		# The base class MergeObjects functionality is tested thoroughly in MergeMeshesTest.py, and
		# the points specific functionality is tested in IECoreScenePreviewTest/PrimitiveAlgoTest.py,
		# so we only need basic tests here to make sure everything is getting passed through correctly.

		curveVerts1 = [ imath.V3f( i ) for i in [ (0,0,0),(0,1,0),(1,1,0),(1,0,0) ] ]
		curves1 = GafferScene.ObjectToScene()
		curves1["object"].setValue( IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4 ] ), IECore.CubicBasisf.linear(), False, IECore.V3fVectorData( curveVerts1 )
		) )

		curveVerts2 = [ imath.V3f( i, 2, 0 ) for i in range( 7 ) ]
		curves2 = GafferScene.ObjectToScene()
		curves2["object"].setValue( IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 7 ] ), IECore.CubicBasisf.linear(), False, IECore.V3fVectorData( curveVerts2 )
		) )
		curves2["transform"]["translate"].setValue( imath.V3f( 0, 0, 3 ) )

		group = GafferScene.Group()
		group["in"][0].setInput( curves1["out"] )
		group["in"][1].setInput( curves2["out"] )

		chooseFilter = GafferScene.PathFilter()
		chooseFilter["paths"].setValue( IECore.StringVectorData( [ "/group/object", "/group/object1" ] ) )

		mergeCurves = GafferScene.MergeCurves()
		mergeCurves["in"].setInput( group["out"] )
		mergeCurves["filter"].setInput( chooseFilter["out"] )

		result = mergeCurves["out"].object( "mergedCurves" )

		ref = IECoreScene.CurvesPrimitive(
			IECore.IntVectorData( [ 4, 7 ] ), IECore.CubicBasisf.linear(), False,
			IECore.V3fVectorData( curveVerts1 + [ i + imath.V3f( 0, 0, 3 ) for i in curveVerts2 ] )
		)

		self.assertEqual( result, ref )

if __name__ == "__main__":
	unittest.main()
