##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

class SceneWriterTest( GafferSceneTest.SceneTestCase ) :

	__testFile = "/tmp/test.scc"

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

	def testWriteAnimation( self ) :

		script = Gaffer.ScriptNode()
		script["sphere"] = GafferScene.Sphere()
		script["group"] = GafferScene.Group()
		script["group"]["in"].setInput( script["sphere"]["out"] )
		script["xExpression"] = Gaffer.Expression()
		script["xExpression"]["expression"].setValue( 'parent["group"]["transform"]["translate"]["x"] = context.getFrame()' )
		script["zExpression"] = Gaffer.Expression()
		script["zExpression"]["expression"].setValue( 'parent["group"]["transform"]["translate"]["z"] = context.getFrame() * 2' )
		script["writer"] = GafferScene.SceneWriter()
		script["writer"]["in"].setInput( script["group"]["out"] )
		script["writer"]["fileName"].setValue( self.__testFile )

		with Gaffer.Context() :
			script["writer"].executeSequence( [ 1, 1.5, 2 ] )

		sc = IECore.SceneCache( self.__testFile, IECore.IndexedIO.OpenMode.Read )
		t = sc.child( "group" )

		self.assertEqual( t.readTransformAsMatrix( 0 ), IECore.M44d.createTranslated( IECore.V3d( 1, 0, 2 ) ) )
		self.assertEqual( t.readTransformAsMatrix( 1 / 24.0 ), IECore.M44d.createTranslated( IECore.V3d( 1, 0, 2 ) ) )
		self.assertEqual( t.readTransformAsMatrix( 1.5 / 24.0 ), IECore.M44d.createTranslated( IECore.V3d( 1.5, 0, 3 ) ) )
		self.assertEqual( t.readTransformAsMatrix( 2 / 24.0 ), IECore.M44d.createTranslated( IECore.V3d( 2, 0, 4 ) ) )

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

		script = Gaffer.ScriptNode()
		writer = GafferScene.SceneWriter()
		script["writer"] = writer
		writer["in"].setInput( reader["out"] )
		writer["fileName"].setValue( self.__testFile )
		writer.execute()
		os.remove( "/tmp/fromPython.scc" )

		testCacheFile( self.__testFile )

	def testHash( self ) :

		c = Gaffer.Context()
		c.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		writer = GafferScene.SceneWriter()

		# empty file produces no effect
		self.assertEqual( writer["fileName"].getValue(), "" )
		self.assertEqual( writer.hash( c ), IECore.MurmurHash() )

		# no input scene produces no effect
		writer["fileName"].setValue( "/tmp/test.scc" )
		self.assertEqual( writer.hash( c ), IECore.MurmurHash() )

		# now theres a file and a scene, we get some output
		plane = GafferScene.Plane()
		writer["in"].setInput( plane["out"] )
		self.assertNotEqual( writer.hash( c ), IECore.MurmurHash() )

		# output varies by time
		self.assertNotEqual( writer.hash( c ), writer.hash( c2 ) )

		# output varies by file name
		current = writer.hash( c )
		writer["fileName"].setValue( "/tmp/test2.scc" )
		self.assertNotEqual( writer.hash( c ), current )

		# output varies by new Context entries
		current = writer.hash( c )
		c["renderDirectory"] = "/tmp/sceneWriterTest"
		self.assertNotEqual( writer.hash( c ), current )

		# output varies by changed Context entries
		current = writer.hash( c )
		c["renderDirectory"] = "/tmp/sceneWriterTest2"
		self.assertNotEqual( writer.hash( c ), current )

		# output doesn't vary by ui Context entries
		current = writer.hash( c )
		c["ui:something"] = "alterTheUI"
		self.assertEqual( writer.hash( c ), current )

		# also varies by input node
		current = writer.hash( c )
		cube = GafferScene.Cube()
		writer["in"].setInput( cube["out"] )
		self.assertNotEqual( writer.hash( c ), current )

	def testPassThrough( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["w"] = GafferScene.SceneWriter()
		s["w"]["in"].setInput( s["p"]["out"] )

		self.assertScenesEqual( s["p"]["out"], s["w"]["out"] )

	def testPassThroughSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["w"] = GafferScene.SceneWriter()

		ss = s.serialise()
		self.assertFalse( "out" in ss )

	def tearDown( self ) :

		if os.path.exists( self.__testFile ) :
			os.remove( self.__testFile )

if __name__ == "__main__":
	unittest.main()
