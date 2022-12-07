##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import pathlib
import imath

import IECore
import IECoreScene

import Gaffer
import GafferSceneTest
import GafferArnold

class ArnoldVDBTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		v = GafferArnold.ArnoldVDB()

		# Just an empty procedural at this point.
		self.assertEqual( v["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "volume" ] ) )
		self.assertSceneValid( v["out"] )
		self.assertEqual( v["out"].bound( "/volume" ), imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) )
		self.assertTrue( isinstance( v["out"].object( "/volume" ), IECoreScene.ExternalProcedural ) )

		# If we enter a valid vdb filename, then we should get something
		# with the right bounds, and the right parameters in the procedural.
		v["fileName"].setValue( pathlib.Path( __file__ ).parent / "volumes" / "sphere.vdb" )
		self.assertEqual( v["out"].bound( "/volume" ), imath.Box3f( imath.V3f( -1.1, 1.1, -1.1 ), imath.V3f( 1.1, 2.9, 1.1 ) ) )

		procedural = v["out"].object( "/volume" )
		self.assertTrue( isinstance( procedural, IECoreScene.ExternalProcedural ) )
		self.assertEqual( procedural.getBound(), v["out"].bound( "/volume" ) )
		self.assertEqual( procedural.getFileName(), "volume" )
		self.assertEqual( procedural.parameters()["filename" ].value, v["fileName"].getValue() )
		self.assertEqual( procedural.parameters()["grids" ], IECore.StringVectorData( [ v["grids"].getValue() ] ) )

		# Invalid grid names should create errors.
		v["grids"].setValue( "notAGrid" )
		with self.assertRaisesRegex( Gaffer.ProcessException, "has no grid named \"notAGrid\"" ) as caught :
			v["out"].bound( "/volume" )

		# As should invalid file names.
		v["grids"].setValue( "density" )
		v["fileName"].setValue( "notAFile.vdb" )
		with self.assertRaisesRegex( Gaffer.ProcessException, "No such file or directory" ) :
			v["out"].bound( "/volume" )

	def testStepSize( self ) :

		v = GafferArnold.ArnoldVDB()
		v["fileName"].setValue( pathlib.Path( __file__ ).parent / "volumes" / "sphere.vdb" )

		self.assertEqual( v["stepSize"].getValue(), 0 )
		self.assertEqual( v["stepScale"].getValue(), 1 )

		# Step size should be calculated for us.
		self.assertAlmostEqual( v["out"].object( "/volume" ).parameters()["step_size"].value, 0.2 )
		# But we can scale it if we want.
		v["stepScale"].setValue( 4 )
		self.assertAlmostEqual( v["out"].object( "/volume" ).parameters()["step_size"].value, 0.8 )
		# Or override it entirely.
		v["stepSize"].setValue( 0.01 )
		self.assertAlmostEqual( v["out"].object( "/volume" ).parameters()["step_size"].value, 0.04 )

if __name__ == "__main__":
	unittest.main()
