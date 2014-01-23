##########################################################################
#  
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
import unittest
import threading

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneReadWriteTest( GafferSceneTest.SceneTestCase ) :
	
	__testFile = "/tmp/test.scc"
	
	def testFileRefreshProblem( self ) :
		
		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )
		
		t = sc.createChild( "1" )
		t.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )
		
		s = t.createChild( "2" )
		s.writeObject( IECore.SpherePrimitive( 10 ), 0.0 )
		
		del sc, t, s
		
		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )
		
		scene = reader["out"]
		self.assertEqual( scene.childNames( "/" ), IECore.InternedStringVectorData( [ "1" ] ) )
		
		del scene
		
		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )
		
		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )
		
		s = t.createChild( "shape" )
		s.writeObject( IECore.SpherePrimitive( 10 ), 0.0 )
		
		del sc, t, s
		
		# we have to remember to set the refresh counts to different values in different tests, otherwise
		# it thinks it's reading an old file...
		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )
		
		scene = reader["out"]
		self.assertEqual( scene.childNames( "/" ), IECore.InternedStringVectorData( [ "transform" ] ) )
	
	def testRead( self ) :
		
		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )
		
		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )
		
		s = t.createChild( "shape" )
		s.writeObject( IECore.SpherePrimitive( 10 ), 0.0 )
		
		del sc, t, s
		
		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		
		# we have to remember to set the refresh counts to different values in different tests, otherwise
		# it thinks it's reading an old file...
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )
		
		scene = reader["out"]
		self.assertSceneValid( scene )
		
		self.assertEqual( scene.transform( "transform" ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) )
		self.assertEqual( scene.object( "transform/shape" ), IECore.SpherePrimitive( 10 ) )
	
	def testWrite( self ) :
		
		s = GafferTest.SphereNode()
		
		o = GafferScene.ObjectToScene()
		
		o["__inputSource"].setInput( s["out"] )
		
		g = GafferScene.Group()
		g["in"].setInput( o["out"] )
		
		g["transform"]["translate"]["x"].setValue( 5 )
		g["transform"]["translate"]["z"].setValue( 2 )
		
		script = Gaffer.ScriptNode()
		
		writer = GafferScene.SceneWriter()
		script["writer"] = writer
		writer["in"].setInput( g["out"] )
		writer["fileName"].setValue( self.__testFile )
		
		writer.execute()
		
		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Read )
		
		t = sc.child( "group" )
		
		self.assertEqual( t.readTransformAsMatrix( 0 ), IECore.M44d.createTranslated( IECore.V3d( 5, 0, 2 ) ) )
		
	def testSceneCacheRoundtrip( self ) :
		
		scene = IECore.SceneCache( "/tmp/fromPython.scc", IECore.IndexedIO.OpenMode.Write )
		sc = scene.createChild( "a" )
		sc.writeObject( IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1))), 0 )
		matrix = IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ).rotate( IECore.V3d( 0, 0, IECore.degreesToRadians( -30 ) ) )
		sc.writeTransform( IECore.M44dData( matrix ), 0 )
		sc = sc.createChild( "b" )
		sc.writeObject( IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1))), 0 )
		sc.writeTransform( IECore.M44dData( matrix ), 0 )
		sc = sc.createChild( "c" )
		sc.writeObject( IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1))), 0 )
		sc.writeTransform( IECore.M44dData( matrix ), 0 )
		
		del scene, sc
		
		def testCacheFile( f ) :
			sc = IECore.SceneCache( f, IECore.IndexedIO.OpenMode.Read )
			a = sc.child( "a" )
			self.failUnless( a.hasObject() )
			self.failUnless( isinstance( a.readObject( 0 ), IECore.MeshPrimitive ) )
			self.failUnless( a.readTransformAsMatrix( 0 ).equalWithAbsError( matrix, 1e-6 ) )
			b = a.child( "b" )
			self.failUnless( b.hasObject() )
			self.failUnless( isinstance( b.readObject( 0 ), IECore.MeshPrimitive ) )
			self.failUnless( b.readTransformAsMatrix( 0 ).equalWithAbsError( matrix, 1e-6 ) )
			c = b.child( "c" )
			self.failUnless( c.hasObject() )
			self.failUnless( isinstance( c.readObject( 0 ), IECore.MeshPrimitive ) )
			self.failUnless( c.readTransformAsMatrix( 0 ).equalWithAbsError( matrix, 1e-6 ) )
		
		testCacheFile( "/tmp/fromPython.scc" )
		
		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( "/tmp/fromPython.scc" )
		self.assertSceneValid( reader["out"] )
		
		script = Gaffer.ScriptNode()
		writer = GafferScene.SceneWriter()
		script["writer"] = writer
		writer["in"].setInput( reader["out"] )
		writer["fileName"].setValue( self.__testFile )
		writer.execute()
		os.remove( "/tmp/fromPython.scc" )
		
		testCacheFile( self.__testFile )
	
	def writeAnimatedSCC( self ) :
		
		scene = IECore.SceneCache( SceneReadWriteTest.__testFile, IECore.IndexedIO.OpenMode.Write )
		
		time = 0
		sc1 = scene.createChild( str( 1 ) )
		mesh = IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1)))
		mesh["Cd"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ IECore.V3f( 1, 0, 0 ) ] * 6 ) )
		sc1.writeObject( mesh, time )
		sc1.writeTransform( IECore.M44dData(), time )
		
		sc2 = sc1.createChild( str( 2 ) )
		mesh = IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1)))
		mesh["Cd"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ IECore.V3f( 0, 1, 0 ) ] * 6 ) )
		sc2.writeObject( mesh, time )
		sc2.writeTransform( IECore.M44dData(), time )
		
		sc3 = sc2.createChild( str( 3 ) )
		mesh = IECore.MeshPrimitive.createBox(IECore.Box3f(IECore.V3f(0),IECore.V3f(1)))
		mesh["Cd"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ IECore.V3f( 0, 0, 1 ) ] * 6 ) )
		sc3.writeObject( mesh, time )
		sc3.writeTransform( IECore.M44dData(), time )
		
		for frame in [ 0.5, 1, 1.5, 2, 5, 10 ] :
			
			matrix = IECore.M44d.createTranslated( IECore.V3d( 1, frame, 0 ) )
			sc1.writeTransform( IECore.M44dData( matrix ), float( frame ) / 24 )
			
			mesh["Cd"] = IECore.PrimitiveVariable( IECore.PrimitiveVariable.Interpolation.Uniform, IECore.V3fVectorData( [ IECore.V3f( frame, 1, 0 ) ] * 6 ) )
			sc2.writeObject( mesh, float( frame ) / 24 )
			matrix = IECore.M44d.createTranslated( IECore.V3d( 2, frame, 0 ) )
			sc2.writeTransform( IECore.M44dData( matrix ), float( frame ) / 24 )
			
			matrix = IECore.M44d.createTranslated( IECore.V3d( 3, frame, 0 ) )
			sc3.writeTransform( IECore.M44dData( matrix ), float( frame ) / 24 )
		
	def testAnimatedScene( self ) :
		
		self.writeAnimatedSCC()
		
		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( SceneReadWriteTest.__testFile )
		reader["refreshCount"].setValue( self.uniqueInt( SceneReadWriteTest.__testFile ) )
		
		scene = reader["out"]
		
		context = Gaffer.Context()
		context.setFrame( 0 )
		
		with context:
			self.assertEqual( scene.transform( "/1" ), IECore.M44f() )
			self.assertEqual( scene.transform( "/1/2" ), IECore.M44f() )
			self.assertEqual( scene.transform( "/1/2/3" ), IECore.M44f() )
		
		for time in [ 0.5, 1, 1.5, 2, 5, 10 ] :
			
			context.setFrame( time )
			
			with context:
				self.assertEqual( scene.transform( "/1" ), IECore.M44f.createTranslated( IECore.V3f( 1, time, 0 ) ) )
				self.assertEqual( scene.transform( "/1/2" ), IECore.M44f.createTranslated( IECore.V3f( 2, time, 0 ) ) )
				self.assertEqual( scene.transform( "/1/2/3" ), IECore.M44f.createTranslated( IECore.V3f( 3, time, 0 ) ) )
				
				mesh = scene.object( "/1/2" )
				self.assertEqual( mesh["Cd"].data, IECore.V3fVectorData( [ IECore.V3f( time, 1, 0 ) ] * 6 ) )
	
	def testEnabled( self ) :
		
		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Write )
		
		t = sc.createChild( "transform" )
		t.writeTransform( IECore.M44dData( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) ), 0.0 )
		
		s = t.createChild( "shape" )
		s.writeObject( IECore.SpherePrimitive( 10 ), 0.0 )
		
		del sc, t, s
		
		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.__testFile )
		
		# we have to remember to set the refresh counts to different values in different tests, otherwise
		# it thinks it's reading an old file...
		reader["refreshCount"].setValue( self.uniqueInt( self.__testFile ) )
		
		self.assertSceneValid( reader["out"] )
		self.assertEqual( reader["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "transform" ] ) )
		
		reader["enabled"].setValue( False )
		self.assertSceneValid( reader["out"] )
		self.assertTrue( reader["out"].bound( "/" ).isEmpty() )
		self.assertEqual( reader["out"].childNames( "/" ), IECore.InternedStringVectorData() )
	
	def testEmptyFileName( self ) :
	
		s = GafferScene.SceneReader()
		
		self.assertSceneValid( s["out"] )
		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData() )
		self.assertEqual( s["out"].bound( "/" ), IECore.Box3f() )
		self.assertEqual( s["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( s["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertEqual( s["out"].object( "/" ), IECore.NullObject() )

	def tearDown( self ) :
		
		if os.path.exists( self.__testFile ) :
			os.remove( self.__testFile )

if __name__ == "__main__":
	unittest.main()
