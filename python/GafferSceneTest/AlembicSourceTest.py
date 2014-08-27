##########################################################################
#
#  Copyright (c) 2012-2014, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import shutil
import unittest

import IECore
import IECoreAlembic

import Gaffer
import GafferScene
import GafferSceneTest

class AlembicSourceTest( GafferSceneTest.SceneTestCase ) :

	def testCube( self ) :

		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/cube.abc" )

		self.assertSceneValid( a["out"] )

		self.assertEqual( a["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( a["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( a["out"].bound( "/" ), IECore.Box3f( IECore.V3f( -2 ), IECore.V3f( 2 ) ) )
		self.assertEqual( a["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1"] ) )

		self.assertEqual( a["out"].object( "/group1" ), IECore.NullObject() )
		self.assertEqual( a["out"].transform( "/group1" ), IECore.M44f.createScaled( IECore.V3f( 2 ) ) * IECore.M44f.createTranslated( IECore.V3f( 2, 0, 0 ) ) )
		self.assertEqual( a["out"].bound( "/group1" ), IECore.Box3f( IECore.V3f( -2, -1, -1 ), IECore.V3f( 0, 1, 1 ) ) )
		self.assertEqual( a["out"].attributes( "/group1" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].childNames( "/group1" ), IECore.InternedStringVectorData( [ "pCube1"] ) )

		self.assertEqual( a["out"].object( "/group1/pCube1" ), IECore.NullObject() )
		self.assertEqual( a["out"].transform( "/group1/pCube1" ), IECore.M44f.createTranslated( IECore.V3f( -1, 0, 0 ) ) )
		self.assertEqual( a["out"].bound( "/group1/pCube1" ), IECore.Box3f( IECore.V3f( -1 ), IECore.V3f( 1 ) ) )
		self.assertEqual( a["out"].attributes( "/group1/pCube1" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].childNames( "/group1/pCube1" ), IECore.InternedStringVectorData( [ "pCubeShape1"] ) )

		self.assertTrue( isinstance( a["out"].object( "/group1/pCube1/pCubeShape1" ), IECore.MeshPrimitive ) )
		self.assertEqual( a["out"].transform( "/group1/pCube1/pCubeShape1" ), IECore.M44f() )
		self.assertEqual( a["out"].bound( "/group1/pCube1/pCubeShape1" ), IECore.Box3f( IECore.V3f( -1 ), IECore.V3f( 1 ) ) )
		self.assertEqual( a["out"].attributes( "/group1/pCube1/pCubeShape1" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].childNames( "/group1/pCube1/pCubeShape1" ), IECore.InternedStringVectorData( [] ) )

	def testAnimation( self ) :

		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc" )

		self.assertSceneValid( a["out"] )

		b = IECoreAlembic.AlembicInput( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc" )
		c = b.child( "pCube1" ).child( "pCubeShape1" )
		numSamples = b.numSamples()
		startTime = b.timeAtSample( 0 )
		endTime = b.timeAtSample( numSamples - 1 )

		for i in range( 0, numSamples * 2 ) :
			time = startTime + ( endTime - startTime ) * float( i ) / ( numSamples * 2 - 1 )
			c = Gaffer.Context()
			c.setFrame( time * 24 )
			with c :
				self.assertBoxesAlmostEqual( a["out"].bound( "/" ), b.boundAtTime( time ), 6 )
				self.assertBoxesAlmostEqual( a["out"].bound( "/pCube1/pCubeShape1" ), b.boundAtTime( time ), 6 )

	def testFullTransform( self ) :

		a = GafferScene.AlembicSource()
		a["fileName"].setValue( os.path.dirname( __file__ ) + "/alembicFiles/cube.abc" )

		self.assertEqual( a["out"].fullTransform( "/" ), IECore.M44f() )
		self.assertEqual( a["out"].fullTransform( "/group1" ), IECore.M44f.createScaled( IECore.V3f( 2 ) ) * IECore.M44f.createTranslated( IECore.V3f( 2, 0, 0 ) ) )
		self.assertEqual( a["out"].fullTransform( "/group1/pCube1" ), IECore.M44f.createTranslated( IECore.V3f( -1, 0, 0 ) )  * a["out"].fullTransform( "/group1" ) )
		self.assertEqual( a["out"].fullTransform( "/group1/pCube1/pCubeShape1" ), a["out"].fullTransform( "/group1/pCube1" ) )

	__refreshTestFileName = "/tmp/refreshTest.abc"

	def testRefresh( self ) :

		shutil.copyfile( os.path.dirname( __file__ ) + "/alembicFiles/cube.abc", self.__refreshTestFileName )

		a = GafferScene.AlembicSource()
		a["fileName"].setValue( self.__refreshTestFileName )

		self.assertSceneValid( a["out"] )
		self.assertEqual( a["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1" ] ) )

		shutil.copyfile( os.path.dirname( __file__ ) + "/alembicFiles/animatedCube.abc", self.__refreshTestFileName )

		self.assertSceneValid( a["out"] )
		self.assertEqual( a["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "group1" ] ) )

		a["refreshCount"].setValue( a["refreshCount"].getValue() + 1 )

		self.assertSceneValid( a["out"] )
		self.assertEqual( a["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "front", "pCube1", "persp", "side", "top" ] ) )

	def testEmptyFileName( self ) :

		a = GafferScene.AlembicSource()
		a["fileName"].setValue( "" )

		self.assertSceneValid( a["out"] )
		self.assertTrue( a["out"].bound( "/" ).isEmpty() )

	def testInvalidFileName( self ) :

		a = GafferScene.AlembicSource()
		a["fileName"].setValue( "nonexistent.abc" )

		self.assertRaises( RuntimeError, a["out"].childNames, "/" )

	def tearDown( self ) :

		for f in [
			self.__refreshTestFileName,
		] :
			if os.path.exists( f ) :
				os.remove( f )

if __name__ == "__main__":
	unittest.main()
