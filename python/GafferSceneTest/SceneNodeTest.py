##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

import unittest
import threading

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneNodeTest( GafferTest.TestCase ) :

	def testRootConstraints( self ) :

		# we don't allow the root of the scene ("/") to carry objects, transforms,
		# or attributes. if we did, then there wouldn't be a sensible way of merging
		# them (particularly transforms) when a Group node has multiple inputs.
		# it's also pretty confusing to have stuff go on at the root level,
		# particularly as the root isn't well represented in the SceneHierarchy editor,
		# and applications like maya don't have stuff happening at the root
		# level either. we achieve this by having the SceneNode simply not
		# call the various processing functions for the root.

		node = GafferSceneTest.CompoundObjectSource()
		node["in"].setValue(
			IECore.CompoundObject( {
				"object" : IECore.SpherePrimitive()
			} )
		)

		self.assertEqual( node["out"].object( "/" ), IECore.NullObject() )

		node = GafferSceneTest.CompoundObjectSource()
		node["in"].setValue(
			IECore.CompoundObject( {
				"transform" : IECore.M44fData( IECore.M44f.createTranslated( IECore.V3f( 1 ) ) )
			} )
		)

		self.assertEqual( node["out"].transform( "/" ), IECore.M44f() )

		node = GafferSceneTest.CompoundObjectSource()
		node["in"].setValue(
			IECore.CompoundObject( {
				"attributes" : IECore.CompoundObject()
			} )
		)

		self.assertEqual( node["out"].attributes( "/" ), IECore.CompoundObject() )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferScene, namesToIgnore = set( ( "IECore::PathMatcherData", ) ) )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( GafferScene )

	def testRootAttributes( self ) :

		# create node inheriting from SceneNode:
		node = GafferScene.CustomAttributes()
		node["attributes"].addOptionalMember( "user:foobar", True, enabled = True )

		# scene nodes always have passthrough behaviour for attributes at the root, so this particular one should return an empty compound object:
		context = Gaffer.Context()
		context.set( "scene:path", IECore.InternedStringVectorData([]) )
		with context:
			self.assertEqual( node["out"]["attributes"].getValue(), IECore.CompoundObject() )

		# unless the caching system is misbehaving, it should return the attribute values we asked for at other locations:
		context.set( "scene:path", IECore.InternedStringVectorData(["yup"]) )
		with context:
			self.assertEqual( node["out"]["attributes"].getValue(), IECore.CompoundObject({'user:foobar':IECore.BoolData( 1 )}) )

	def testRootObject( self ):

		# okie dokie - create a sphere node and check it's generating a sphere in the correct place:
		sphere = GafferScene.Sphere()

		context = Gaffer.Context()
		context.set("scene:path", IECore.InternedStringVectorData(["sphere"]) )
		with context:
			self.assertEqual( sphere["out"]["object"].getValue().typeId(), IECore.MeshPrimitive.staticTypeId() )

		# right, now subtree it. If the cache is behaving itself, then there shouldn't be an object at the root of the
		# resulting scene, cuz that aint allowed.
		subTree = GafferScene.SubTree()
		subTree["in"].setInput( sphere["out"] )
		subTree["root"].setValue("sphere")
		context.set("scene:path", IECore.InternedStringVectorData([]) )
		with context:
			self.assertEqual( subTree["out"]["object"].getValue().typeId(), IECore.NullObject.staticTypeId() )

	def testRootTransform( self ):

		# okie dokie - create a sphere node and check it's generating a sphere in the correct place:
		sphere = GafferScene.Sphere()
		sphere["transform"]["translate"]["x"].setValue( 1.0 )
		sphere["transform"]["translate"]["y"].setValue( 2.0 )
		sphere["transform"]["translate"]["z"].setValue( 3.0 )

		context = Gaffer.Context()
		context.set("scene:path", IECore.InternedStringVectorData(["sphere"]) )
		with context:
			self.assertEqual( sphere["out"]["transform"].getValue(), IECore.M44f.createTranslated( IECore.V3f( 1,2,3 ) ) )

		# right, now subtree it. If the cache is behaving itself, then the transform at the root of the
		# resulting scene should be set to identity.
		subTree = GafferScene.SubTree()
		subTree["in"].setInput( sphere["out"] )
		subTree["root"].setValue("sphere")
		context.set("scene:path", IECore.InternedStringVectorData([]) )
		with context:
			self.assertEqual( subTree["out"]["transform"].getValue(), IECore.M44f() )

	def testCacheThreadSafety( self ) :

		p1 = GafferScene.Plane()
		p1["divisions"].setValue( IECore.V2i( 50 ) )

		p2 = GafferScene.Plane()
		p2["divisions"].setValue( IECore.V2i( 51 ) )

		g = GafferScene.Group()
		g["in"].setInput( p1["out"] )
		g["in1"].setInput( p2["out"] )

		# not enough for both objects - will cause cache thrashing
		Gaffer.ValuePlug.setCacheMemoryLimit( p1["out"].object( "/plane" ).memoryUsage() )

		exceptions = []
		def traverser() :

			try :
				GafferSceneTest.traverseScene( g["out"], Gaffer.Context() )
			except Exception, e :
				exceptions.append( e )

		threads = []
		for i in range( 0, 10 ) :
			thread = threading.Thread( target = traverser )
			threads.append( thread )
			thread.start()

		for thread in threads :
			thread.join()

		for e in exceptions :
			raise e

	def setUp( self ) :

		self.__previousCacheMemoryLimit = Gaffer.ValuePlug.getCacheMemoryLimit()

	def tearDown( self ) :

		Gaffer.ValuePlug.setCacheMemoryLimit( self.__previousCacheMemoryLimit )

if __name__ == "__main__":
	unittest.main()

