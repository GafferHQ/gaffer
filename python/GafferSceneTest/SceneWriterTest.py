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
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneWriterTest( GafferSceneTest.SceneTestCase ) :

	def testWrite( self ) :

		s = GafferScene.Sphere()

		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )

		g["transform"]["translate"]["x"].setValue( 5 )
		g["transform"]["translate"]["z"].setValue( 2 )

		script = Gaffer.ScriptNode()

		writer = GafferScene.SceneWriter()
		script["writer"] = writer
		writer["in"].setInput( g["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() + "/test.scc" )

		writer.execute()

		sc = IECoreScene.SceneCache( self.temporaryDirectory() + "/test.scc", IECore.IndexedIO.OpenMode.Read )

		t = sc.child( "group" )

		self.assertEqual( t.readTransformAsMatrix( 0 ), imath.M44d().translate( imath.V3d( 5, 0, 2 ) ) )

	def testWriteAnimation( self ) :

		script = Gaffer.ScriptNode()
		script["sphere"] = GafferScene.Sphere()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["xExpression"] = Gaffer.Expression()
		script["xExpression"].setExpression( 'parent["group"]["transform"]["translate"]["x"] = context.getFrame()' )
		script["zExpression"] = Gaffer.Expression()
		script["zExpression"].setExpression( 'parent["group"]["transform"]["translate"]["z"] = context.getFrame() * 2' )
		script["writer"] = GafferScene.SceneWriter()
		script["writer"]["in"].setInput( script["group"]["out"] )
		script["writer"]["fileName"].setValue( self.temporaryDirectory() + "/test.scc" )

		with Gaffer.Context() :
			script["writer"].executeSequence( [ 1, 1.5, 2 ] )

		sc = IECoreScene.SceneCache( self.temporaryDirectory() + "/test.scc", IECore.IndexedIO.OpenMode.Read )
		t = sc.child( "group" )

		self.assertEqual( t.readTransformAsMatrix( 0 ), imath.M44d().translate( imath.V3d( 1, 0, 2 ) ) )
		self.assertEqual( t.readTransformAsMatrix( 1 / 24.0 ), imath.M44d().translate( imath.V3d( 1, 0, 2 ) ) )
		self.assertEqual( t.readTransformAsMatrix( 1.5 / 24.0 ), imath.M44d().translate( imath.V3d( 1.5, 0, 3 ) ) )
		self.assertEqual( t.readTransformAsMatrix( 2 / 24.0 ), imath.M44d().translate( imath.V3d( 2, 0, 4 ) ) )

	def testSceneCacheRoundtrip( self ) :

		scene = IECoreScene.SceneCache( self.temporaryDirectory() + "/fromPython.scc", IECore.IndexedIO.OpenMode.Write )
		sc = scene.createChild( "a" )
		sc.writeObject( IECoreScene.MeshPrimitive.createBox(imath.Box3f(imath.V3f(0),imath.V3f(1))), 0 )
		matrix = imath.M44d().translate( imath.V3d( 1, 0, 0 ) ).rotate( imath.V3d( 0, 0, IECore.degreesToRadians( -30 ) ) )
		sc.writeTransform( IECore.M44dData( matrix ), 0 )
		sc = sc.createChild( "b" )
		sc.writeObject( IECoreScene.MeshPrimitive.createBox(imath.Box3f(imath.V3f(0),imath.V3f(1))), 0 )
		sc.writeTransform( IECore.M44dData( matrix ), 0 )
		sc = sc.createChild( "c" )
		sc.writeObject( IECoreScene.MeshPrimitive.createBox(imath.Box3f(imath.V3f(0),imath.V3f(1))), 0 )
		sc.writeTransform( IECore.M44dData( matrix ), 0 )

		del scene, sc

		def testCacheFile( f ) :
			sc = IECoreScene.SceneCache( f, IECore.IndexedIO.OpenMode.Read )
			a = sc.child( "a" )
			self.assertTrue( a.hasObject() )
			self.assertIsInstance( a.readObject( 0 ), IECoreScene.MeshPrimitive )
			self.assertTrue( a.readTransformAsMatrix( 0 ).equalWithAbsError( matrix, 1e-6 ) )
			b = a.child( "b" )
			self.assertTrue( b.hasObject() )
			self.assertIsInstance( b.readObject( 0 ), IECoreScene.MeshPrimitive )
			self.assertTrue( b.readTransformAsMatrix( 0 ).equalWithAbsError( matrix, 1e-6 ) )
			c = b.child( "c" )
			self.assertTrue( c.hasObject() )
			self.assertIsInstance( c.readObject( 0 ), IECoreScene.MeshPrimitive )
			self.assertTrue( c.readTransformAsMatrix( 0 ).equalWithAbsError( matrix, 1e-6 ) )

		testCacheFile( self.temporaryDirectory() + "/fromPython.scc" )

		reader = GafferScene.SceneReader()
		reader["fileName"].setValue( self.temporaryDirectory() + "/fromPython.scc" )

		script = Gaffer.ScriptNode()
		writer = GafferScene.SceneWriter()
		script["writer"] = writer
		writer["in"].setInput( reader["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() + "/test.scc" )
		writer.execute()
		os.remove( self.temporaryDirectory() + "/fromPython.scc" )

		testCacheFile( self.temporaryDirectory() + "/test.scc" )


	def testCanWriteSets( self ):

		script = Gaffer.ScriptNode()

		s = GafferScene.Sphere()
		script.addChild( s )

		c = GafferScene.Cube()
		script.addChild( c )

		sphereGroup = GafferScene.Group()
		script.addChild( sphereGroup )
		sphereGroup["in"][0].setInput( s["out"] )
		sphereGroup["name"].setValue( 'sphereGroup' )


		sn = GafferScene.Set( "Set" )
		script.addChild( sn )
		sn["paths"].setValue( IECore.StringVectorData( [ '/sphereGroup' ] ) )
		sn["name"].setValue( 'foo' )
		sn["in"].setInput( sphereGroup["out"] )


		sn2 = GafferScene.Set( "Set" )
		script.addChild( sn2 )
		sn2["mode"].setValue( 1 ) # add to the existing set
		sn2["paths"].setValue( IECore.StringVectorData( [ '/sphereGroup/sphere' ] ) )
		sn2["name"].setValue( 'foo' )
		sn2["in"].setInput( sn["out"] )

		g = GafferScene.Group()
		script.addChild( g )
		g["name"].setValue( 'group' )

		g["in"][0].setInput( sn2["out"] )
		g["in"][1].setInput( c["out"] )

		writer = GafferScene.SceneWriter()
		script.addChild( writer )

		script["writer"] = writer
		writer["in"].setInput( g["out"] )
		writer["fileName"].setValue( self.temporaryDirectory() + "/setTest.scc" )

		writer.execute()

		sc = IECoreScene.SceneCache( self.temporaryDirectory() + "/setTest.scc", IECore.IndexedIO.OpenMode.Read )

		scGroup = sc.child("group")
		scSphereGroup = scGroup.child("sphereGroup")
		scSphere = scSphereGroup.child("sphere")

		self.assertEqual(  scGroup.readTags(), [] )

		self.assertEqual( scSphereGroup.readTags(), [ IECore.InternedString("foo") ] )

		self.assertEqual( set (scSphere.readTags() ), set([IECore.InternedString("foo"), IECore.InternedString("ObjectType:MeshPrimitive")]))

		scCube = scGroup.child("cube")
		self.assertEqual( scCube.readTags() , [ IECore.InternedString("ObjectType:MeshPrimitive") ] )


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
		writer["fileName"].setValue( self.temporaryDirectory() + "/test.scc" )
		self.assertEqual( writer.hash( c ), IECore.MurmurHash() )

		# now theres a file and a scene, we get some output
		plane = GafferScene.Plane()
		writer["in"].setInput( plane["out"] )
		self.assertNotEqual( writer.hash( c ), IECore.MurmurHash() )

		# output varies by time
		self.assertNotEqual( writer.hash( c ), writer.hash( c2 ) )

		# output varies by file name
		current = writer.hash( c )
		writer["fileName"].setValue( self.temporaryDirectory() + "/test2.scc" )
		self.assertNotEqual( writer.hash( c ), current )

		# output varies by new Context entries
		current = writer.hash( c )
		c["renderDirectory"] = self.temporaryDirectory() + "/sceneWriterTest"
		self.assertNotEqual( writer.hash( c ), current )

		# output varies by changed Context entries
		current = writer.hash( c )
		c["renderDirectory"] = self.temporaryDirectory() + "/sceneWriterTest2"
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

	def testAlembic( self ) :

		p = GafferScene.Plane()

		w = GafferScene.SceneWriter()
		w["in"].setInput( p["out"] )
		w["fileName"].setValue( self.temporaryDirectory() + "/test.abc" )
		w["task"].execute()

		r = GafferScene.SceneReader()
		r["fileName"].setInput( w["fileName"] )

		self.assertScenesEqual( p["out"], r["out"] )

if __name__ == "__main__":
	unittest.main()
