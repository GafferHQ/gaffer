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
		
		writer.execute( [ script.context() ] )
		
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
		
		script = Gaffer.ScriptNode()
		writer = GafferScene.SceneWriter()
		script["writer"] = writer
		writer["in"].setInput( reader["out"] )
		writer["fileName"].setValue( self.__testFile )
		writer.execute( [ script.context() ] )
		os.remove( "/tmp/fromPython.scc" )
		
		testCacheFile( self.__testFile )

	def tearDown( self ) :
		
		if os.path.exists( self.__testFile ) :
			os.remove( self.__testFile )

if __name__ == "__main__":
	unittest.main()
