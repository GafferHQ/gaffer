##########################################################################
#
#  Copyright (c) 2023, Image Engine Design Inc. All rights reserved.
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

import imath
import unittest
import pathlib

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferVDB
import GafferVDBTest

class VolumeScatterTest( GafferVDBTest.VDBTestCase ) :

	def test( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( pathlib.Path( __file__ ).parent / "data" / "smoke.vdb" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/vdb" ] ) )

		vs = GafferVDB.VolumeScatter()
		vs["in"].setInput( reader["out"] )
		vs["filter"].setInput( filter["out"] )

		self.assertEqual( vs["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "vdb" ] ) )
		self.assertEqual( vs["out"].childNames( "/vdb" ), IECore.InternedStringVectorData( [ "scatter" ] ) )
		self.assertEqual( vs["out"].childNames( "/vdb/scatter" ), IECore.InternedStringVectorData() )

		vs["name"].setValue( "test" )

		self.assertEqual( vs["out"].childNames( "/vdb" ), IECore.InternedStringVectorData( [ "test" ] ) )

		vs["destination"].setValue( "/" )

		self.assertEqual( vs["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "vdb", "test" ] ) )
		self.assertEqual( vs["out"].childNames( "/vdb" ), IECore.InternedStringVectorData( ) )


		bound = vs['out'].bound( "/test" )
		self.assertTrue( bound.min().equalWithAbsError( imath.V3f( -34.31, -12.88, -26.69 ), 0.01 ) )
		self.assertTrue( bound.max().equalWithAbsError( imath.V3f( 19.55, 93.83, 27.64 ), 0.01 ) )

		points = vs['out'].object( "/test" )

		numP = len( points["P"].data )
		self.assertEqual( numP, 18449 )

		# Characterize the set of points generated in a way that we know approximately matches this smoke vdb.
		# These values are derived from the current distribution - if the distribution changes in the future,
		# the tolerances will need to loosen, but we should still see approximately these values, which come
		# from the shape of the fog ( the tolerances are pretty loose, due to some areas of very low density
		# where a change in distribution can have a big impact on the bounding box )
		self.assertTrue( points.bound().min().equalWithAbsError( imath.V3f(-31.85, -11.02, -25.19 ), 1.0 ) )
		self.assertTrue( points.bound().max().equalWithAbsError( imath.V3f(17.34, 91.58, 25.57 ), 1.0 ) )

		# The center should be fairly close to the true centre, relative to the size of the bound
		center = sum( points["P"].data ) / numP
		self.assertLess( ( ( center - imath.V3f(-4.50, 17.88, -0.593) ) / points.bound().size() ).length(), 0.003 )

		diffs = [ ( i - center ) for i in points["P"].data ]
		variance = sum( [ ( i - center ) * ( i - center ) for i in points["P"].data ] ) / numP
		stdDev = imath.V3f( *[ i ** 0.5 for i in variance ] )
		self.assertTrue( stdDev.equalWithRelError( imath.V3f( 7.92, 20.75, 6.94 ), 0.02 ) )

		vs["density"].setValue( 2 )

		self.assertEqual( len( vs['out'].object( "/test" )["P"].data ), 36788 )

		self.assertEqual( vs['out'].object( "/test" )["type"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, "gl:point" ) )

		vs["pointType"].setValue( "sphere" )

		self.assertEqual( vs['out'].object( "/test" )["type"], IECoreScene.PrimitiveVariable( IECoreScene.PrimitiveVariable.Interpolation.Constant, "sphere" ) )

	def testFail( self ) :

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( pathlib.Path( __file__ ).parent / "data" / "sphere.vdb" )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/vdb" ] ) )

		vs = GafferVDB.VolumeScatter()
		vs["in"].setInput( reader["out"] )
		vs["filter"].setInput( filter["out"] )

		# The grid name doesn't match, so we silently return an empty object
		self.assertEqual( vs['out'].object( "/vdb/scatter" ), IECore.NullObject() )

		vs["grid"].setValue( "ls_sphere" )

		with self.assertRaisesRegex( RuntimeError, "VolumeScatter does not yet support level sets" ) :
			vs['out'].object( "/vdb/scatter" )

if __name__ == "__main__":
	unittest.main()
