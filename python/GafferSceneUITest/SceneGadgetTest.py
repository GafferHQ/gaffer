##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import time
import unittest

import imath

import IECore
import IECoreScene
import IECoreGL

import Gaffer
import GafferTest
import GafferUI
import GafferUITest
import GafferScene
import GafferSceneUI

class SceneGadgetTest( GafferUITest.TestCase ) :

	renderer = "OpenGL"

	def testBound( self ) :

		s = Gaffer.ScriptNode()
		s["p"] = GafferScene.Plane()
		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["p"]["out"] )
		s["g"]["transform"]["translate"]["x"].setValue( 2 )

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setScene( s["g"]["out"] )

		self.waitForRender( sg )
		self.assertEqual( sg.bound(), s["g"]["out"].bound( "/" ) )

		s["g"]["transform"]["translate"]["y"].setValue( 4 )
		self.waitForRender( sg )
		self.assertEqual( sg.bound(), s["g"]["out"].bound( "/" ) )

		s["g"]["transform"]["translate"].setValue( imath.V3f( 0 ) )
		s["s"] = GafferScene.Sphere()
		s["g"]["in"][1].setInput( s["s"]["out"] )
		s["p"]["transform"]["translate"]["z"].setValue( 10 )
		self.waitForRender( sg )
		self.assertEqual( sg.bound(), s["g"]["out"].bound( "/" ) )
		# Nothing selected, so selected bound is empty
		self.assertEqual( sg.bound( True ), imath.Box3f() )

		v = GafferScene.VisibleSet()
		v.expansions = IECore.PathMatcher( [ "/group" ] )
		sg.setVisibleSet( v )
		sg.setSelection( IECore.PathMatcher( ["/group/plane"] ) )
		self.waitForRender( sg )

		self.assertEqual( sg.bound(), s["g"]["out"].bound( "/" ) )
		# Only plane is selected
		self.assertEqual( sg.bound( True ), s["p"]["out"].bound( "/" ) )
		# Omitting plane takes just sphere
		self.assertEqual( sg.bound( False, IECore.PathMatcher( ["/group/plane"]) ), s["s"]["out"].bound( "/" ) )
		# Omitting only selected object while using selected=True leaves empty bound
		self.assertEqual( sg.bound( True, IECore.PathMatcher( ["/group/plane"]) ), imath.Box3f() )

	def assertObjectAt( self, gadget, ndcPosition, path ) :

		viewportGadget = gadget.ancestor( GafferUI.ViewportGadget )

		rasterPosition = ndcPosition * imath.V2f( viewportGadget.getViewport() )
		gadgetLine = viewportGadget.rasterToGadgetSpace( rasterPosition, gadget )

		self.assertEqual( gadget.objectAt( gadgetLine ), path )

	def assertObjectsAt( self, gadget, ndcBox, paths ) :

		viewportGadget = gadget.ancestor( GafferUI.ViewportGadget )

		rasterMin = ndcBox.min() * imath.V2f( viewportGadget.getViewport() )
		rasterMax = ndcBox.max() * imath.V2f( viewportGadget.getViewport() )

		gadgetMin = viewportGadget.rasterToGadgetSpace( rasterMin, gadget ).p0
		gadgetMax = viewportGadget.rasterToGadgetSpace( rasterMax, gadget ).p1

		objectsAt = IECore.PathMatcher()
		gadget.objectsAt( gadgetMin, gadgetMax, objectsAt )

		objects = set( objectsAt.paths() )
		expectedObjects = set( IECore.PathMatcher( paths ).paths() )
		self.assertEqual( objects, expectedObjects )

	def waitForRender( self, gadget ) :

		gadget.waitForCompletion()
		if self.renderer != "OpenGL" :
			# `waitForCompletion()` only covers scene translation
			# to the renderer. Provide a grace period for pixels
			# to get into the buffers.
			timeout = time.time() + 1
			while time.time() < timeout :
				self.waitForIdle()

	def testObjectVisibility( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()
		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )
		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setMinimumExpansionDepth( 1 )
		sg.setScene( s["a"]["out"] )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )

		w.setVisible( True )
		self.waitForIdle( 1000 )

		sg.waitForCompletion()
		gw.getViewportGadget().frame( sg.bound() )
		self.waitForRender( sg )

		self.assertObjectAt( sg, imath.V2f( 0.5 ), IECore.InternedStringVectorData( [ "group", "sphere" ] ) )

		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a"]["attributes"]["visibility"]["value"].setValue( False )

		self.waitForRender( sg )
		self.assertObjectAt( sg, imath.V2f( 0.5 ), None )

		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a"]["attributes"]["visibility"]["value"].setValue( True )

		self.waitForRender( sg )
		self.assertObjectAt( sg, imath.V2f( 0.5 ), IECore.InternedStringVectorData( [ "group", "sphere" ] ) )

	@unittest.skipIf( GafferTest.inCI(), "Unknown problem running in cloud" )
	def testExpansion( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()
		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["s"]["out"] )
		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["g"]["out"] )

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setScene( s["a"]["out"] )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )

		w.setVisible( True )
		self.waitForIdle( 10000 )

		sg.waitForCompletion()
		gw.getViewportGadget().frame( sg.bound() )
		self.waitForRender( sg )

		self.assertObjectAt( sg, imath.V2f( 0.5 ), None )
		self.assertObjectsAt( sg, imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ), [ "/group" ] )

		v = GafferScene.VisibleSet()
		v.expansions = IECore.PathMatcher( [ "/group" ] )
		sg.setVisibleSet( v )
		self.waitForRender( sg )

		self.assertObjectAt( sg, imath.V2f( 0.5 ), IECore.InternedStringVectorData( [ "group", "sphere" ] ) )
		self.assertObjectsAt( sg, imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ), [ "/group/sphere" ] )

		v.expansions = IECore.PathMatcher( [] )
		v.inclusions = IECore.PathMatcher( [ "/group" ] )
		sg.setVisibleSet( v )
		self.waitForRender( sg )

		self.assertObjectAt( sg, imath.V2f( 0.5 ), IECore.InternedStringVectorData( [ "group", "sphere" ] ) )
		self.assertObjectsAt( sg, imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ), [ "/group/sphere" ] )

		v.exclusions = IECore.PathMatcher( [ "/group" ] )
		sg.setVisibleSet( v )
		self.waitForRender( sg )

		self.assertObjectAt( sg, imath.V2f( 0.5 ), None )
		self.assertObjectsAt( sg, imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ), [ "/group" ] )

		sg.setVisibleSet( GafferScene.VisibleSet() )
		self.waitForRender( sg )

		self.assertObjectAt( sg, imath.V2f( 0.5 ), None )
		self.assertObjectsAt( sg, imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ), [ "/group" ] )

	def testExpressions( self ) :

		s = Gaffer.ScriptNode()
		s["p"] = GafferScene.Plane()
		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["p"]["out"] )
		s["g"]["in"][1].setInput( s["p"]["out"] )
		s["g"]["in"][2].setInput( s["p"]["out"] )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['p']['dimensions']['x'] = 1 + context.getFrame() * 0.1" )

		g = GafferSceneUI.SceneGadget()
		g.setRenderer( self.renderer )
		g.setScene( s["g"]["out"] )
		g.bound()

	def testGLResourceDestruction( self ) :

		s = Gaffer.ScriptNode()
		s["p"] = GafferScene.Plane()
		s["g"] = GafferScene.Group()
		s["g"]["in"][0].setInput( s["p"]["out"] )
		s["g"]["in"][1].setInput( s["p"]["out"] )
		s["g"]["in"][2].setInput( s["p"]["out"] )
		s["g"]["in"][3].setInput( s["p"]["out"] )

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setScene( s["g"]["out"] )
		sg.setMinimumExpansionDepth( 2 )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )
		w.setVisible( True )

		# Reduce the GL cache size so that not everything will fit, and we'll
		# need to dispose of some objects. We can't dispose of objects on any
		# old thread, just the main GL thread, so it's important that we test
		# that we're doing that appropriately.
		IECoreGL.CachedConverter.defaultCachedConverter().setMaxMemory( 100 )

		for i in range( 1, 1000 ) :
			s["p"]["dimensions"]["x"].setValue( i )
			self.waitForIdle( 10 )

	def testExceptionsDuringCompute( self ) :

		# Make this scene
		#
		# - bigSphere
		#	- littleSphere (with exception in attributes expression)

		s = Gaffer.ScriptNode()

		s["s1"] = GafferScene.Sphere()
		s["s1"]["name"].setValue( "bigSphere" )

		s["s2"] = GafferScene.Sphere()
		s["s2"]["name"].setValue( "littleSphere" )
		s["s2"]["radius"].setValue( 0.1 )

		s["p"] = GafferScene.Parent()
		s["p"]["in"].setInput( s["s1"]["out"] )
		s["p"]["children"][0].setInput( s["s2"]["out"] )
		s["p"]["parent"].setValue( "/bigSphere" )

		s["a"] = GafferScene.StandardAttributes()
		s["a"]["in"].setInput( s["p"]["out"] )
		s["a"]["attributes"]["doubleSided"]["enabled"].setValue( True )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["a"]["attributes"]["doubleSided"]["value"] = context["nonexistent"]' )

		s["f"] = GafferScene.PathFilter()
		s["f"]["paths"].setValue( IECore.StringVectorData( [ "/bigSphere/littleSphere" ] ) )

		s["a"]["filter"].setInput( s["f"]["out"] )

		# Try to view it

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setScene( s["a"]["out"] )
		sg.setMinimumExpansionDepth( 4 )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )
			gw.getViewportGadget().setPlanarMovement( False )
			gw.getViewportGadget().setCamera(
				IECoreScene.Camera( parameters = { "projection" : "perspective", } )
			)

		originalMessageHandler = IECore.MessageHandler.getDefaultHandler()
		mh = IECore.CapturingMessageHandler()
		IECore.MessageHandler.setDefaultHandler(
			IECore.LevelFilteredMessageHandler( mh, IECore.LevelFilteredMessageHandler.defaultLevel() )
		)

		try :

			w.setVisible( True )
			self.waitForIdle( 1000 )
			sg.waitForCompletion()

			# Check we were told about the problem

			self.assertEqual( len( mh.messages ), 1 )
			self.assertEqual( mh.messages[0].level, mh.Level.Error )
			self.assertTrue( "nonexistent" in mh.messages[0].message )

			# And that there isn't some half-assed partial scene
			# being displayed.

			self.assertTrue( sg.bound().isEmpty() )
			gw.getViewportGadget().frame( imath.Box3f( imath.V3f( -1 ), imath.V3f( 1 ) ) )
			self.assertObjectAt( sg, imath.V2f( 0.5 ), None )

			# And that redraws don't cause more fruitless attempts
			# to compute the scene.

			gw.getViewportGadget().frame( imath.Box3f( imath.V3f( -1.1 ), imath.V3f( 1.1 ) ) )
			self.waitForIdle( 1000 )

			self.assertEqual( len( mh.messages ), 1 )
			self.assertObjectAt( sg, imath.V2f( 0.5 ), None )
			self.assertTrue( sg.bound().isEmpty() )

			# Fix the problem with the scene, and check that we can see something now

			s["f"]["enabled"].setValue( False )
			self.waitForRender( sg )

			self.assertEqual( len( mh.messages ), 1 )
			self.assertFalse( sg.bound().isEmpty() )
			self.assertObjectAt( sg, imath.V2f( 0.5 ), IECore.InternedStringVectorData( [ "bigSphere" ] ) )

		finally :

			IECore.MessageHandler.setDefaultHandler( originalMessageHandler )

	def testObjectsAtBox( self ) :

		plane = GafferScene.Plane()

		sphere = GafferScene.Sphere()
		sphere["radius"].setValue( 0.25 )

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["prototypes"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/plane" )

		subTree = GafferScene.SubTree()
		subTree["in"].setInput( instancer["out"] )
		subTree["root"].setValue( "/plane" )

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setScene( subTree["out"] )
		sg.setMinimumExpansionDepth( 100 )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )
		w.setVisible( True )
		self.waitForIdle( 10000 )

		gw.getViewportGadget().frame( sg.bound() )
		self.waitForRender( sg )

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ),
			[ "/instances/sphere/{}".format( i ) for i in range( 0, 4 ) ]
		)

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 0 ), imath.V2f( 0.5 ) ),
			[ "/instances/sphere/2" ]
		)

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 0.5, 0 ), imath.V2f( 1, 0.5 ) ),
			[ "/instances/sphere/3" ]
		)

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 0, 0.5 ), imath.V2f( 0.5, 1 ) ),
			[ "/instances/sphere/0" ]
		)

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 0.5 ), imath.V2f( 1 ) ),
			[ "/instances/sphere/1" ]
		)

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 10 ), imath.V2f( 20 ) ),
			[]
		)

	def testObjectAtLine( self ) :

		cubes = []
		names = ( "left", "center", "right" )
		for i in range( 3 ) :
			cube = GafferScene.Cube()
			cube["transform"]["translate"].setValue( imath.V3f( ( i - 1 ) * 2.0, 0.0, -2.5 ) )
			cube["name"].setValue( names[i] )
			cubes.append( cube )

		group = GafferScene.Group()
		for i, cube in enumerate( cubes ) :
			group["in"][i].setInput( cube["out"] )

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setScene( group["out"] )
		sg.setMinimumExpansionDepth( 100 )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )
		w.setVisible( True )
		self.waitForIdle( 10000 )

		vp = gw.getViewportGadget()

		# This is the single most important line in this test. If you don't set
		# this to false, you get an orthographic camera, even if you set a
		# perspective projection.
		vp.setPlanarMovement( False )

		c = IECoreScene.Camera()
		c.setProjection( "perspective" )
		c.setFocalLength( 35 )
		c.setAperture( imath.V2f( 36, 24 ) )
		vp.setCamera( c )

		cameraTransform = imath.M44f()
		cameraTransform.translate( imath.V3f( 0, 0, 2 ) )
		vp.setCameraTransform( cameraTransform )

		self.waitForRender( sg )

		# We assume in this case, that gadget space is world space

		leftCubeDir = IECore.LineSegment3f( imath.V3f( 0, 0, 2 ), imath.V3f( -2, 0, -2 ) )
		pathA = sg.objectAt( leftCubeDir )
		pathB, hitPoint = sg.objectAndIntersectionAt( leftCubeDir )
		self.assertIsNotNone( pathA )
		self.assertEqual( pathA, IECore.InternedStringVectorData( [ "group", "left" ] ) )
		self.assertEqual( pathA,  pathB )
		self.assertAlmostEqual( hitPoint.x, -2, delta = 0.01 )
		self.assertAlmostEqual( hitPoint.y, 0, delta = 0.01 )
		self.assertAlmostEqual( hitPoint.z, -2, delta = 0.01 )

		centerCubeDir = IECore.LineSegment3f( imath.V3f( 0, 0, 1 ), imath.V3f( 0, 0, -1 ) )
		pathA = sg.objectAt( centerCubeDir )
		pathB, hitPoint = sg.objectAndIntersectionAt( centerCubeDir )
		self.assertIsNotNone( pathA )
		self.assertEqual( pathA, IECore.InternedStringVectorData( [ "group", "center" ] ) )
		self.assertEqual( pathA,  pathB )
		self.assertAlmostEqual( hitPoint.x, 0, delta = 0.01 )
		self.assertAlmostEqual( hitPoint.y, 0, delta = 0.01  )
		self.assertAlmostEqual( hitPoint.z, -2, delta = 0.01 )

		rightCubeDir = IECore.LineSegment3f( imath.V3f( 0, 0, 2 ), imath.V3f( 2, 0, -2 ) )
		pathA = sg.objectAt( rightCubeDir )
		pathB, hitPoint = sg.objectAndIntersectionAt( rightCubeDir )
		self.assertIsNotNone( pathA )
		self.assertEqual( pathA, IECore.InternedStringVectorData( [ "group", "right" ] ) )
		self.assertEqual( pathA,  pathB )
		self.assertAlmostEqual( hitPoint.x, 2, delta = 0.01 )
		self.assertAlmostEqual( hitPoint.y, 0, delta = 0.01 )
		self.assertAlmostEqual( hitPoint.z, -2, delta = 0.01 )

		missDir = IECore.LineSegment3f( imath.V3f( 0, 0, 2 ), imath.V3f( 0, 10, -2 ) )
		pathA = sg.objectAt( missDir )
		pathB, hitPoint = sg.objectAndIntersectionAt( missDir )
		self.assertIsNone( pathA )
		self.assertIsNone( pathB )

	def testSetAndGetScene( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		self.assertEqual( sg.getScene(), None )

		sg.setScene( plane["out"] )
		self.assertEqual( sg.getScene(), plane["out"] )

		sg.setScene( sphere["out"] )
		self.assertEqual( sg.getScene(), sphere["out"] )

	def testBoundOfUnexpandedEmptyChildren( self ) :

		group1 = GafferScene.Group()
		group2 = GafferScene.Group()
		group2["in"][0].setInput( group1["out"] )

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setScene( group2["out"] )

		self.waitForRender( sg )
		self.assertEqual( sg.bound(), imath.Box3f() )

	def testSelectionMaskAccessors( self ) :

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		self.assertEqual( sg.getSelectionMask(), None )

		m = IECore.StringVectorData( [ "MeshPrimitive" ] )
		sg.setSelectionMask( m )
		self.assertEqual( sg.getSelectionMask(), m )

		m.append( "Camera" )
		self.assertNotEqual( sg.getSelectionMask(), m )
		sg.setSelectionMask( m )
		self.assertEqual( sg.getSelectionMask(), m )

		sg.setSelectionMask( None )
		self.assertEqual( sg.getSelectionMask(), None )

	def testSelectionMask( self ) :

		plane = GafferScene.Plane()
		plane["dimensions"].setValue( imath.V2f( 10 ) )
		plane["transform"]["translate"]["z"].setValue( 4 )

		camera = GafferScene.Camera()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( camera["out"] )

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setScene( group["out"] )
		sg.setMinimumExpansionDepth( 100 )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )
		w.setVisible( True )
		self.waitForIdle( 10000 )

		sg.waitForCompletion()
		gw.getViewportGadget().frame( sg.bound(), imath.V3f( 0, 0, -1 ) )
		self.waitForRender( sg )

		self.assertObjectAt(
			sg,
			imath.V2f( 0.6 ),
			IECore.InternedStringVectorData( [ "group", "plane" ] )
		)

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ),
			[ "/group/plane", "/group/camera" ]
		)

		sg.setSelectionMask( IECore.StringVectorData( [ "MeshPrimitive" ] ) )

		self.assertObjectAt(
			sg,
			imath.V2f( 0.6 ),
			IECore.InternedStringVectorData( [ "group", "plane" ] )
		)

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ),
			[ "/group/plane" ]
		)

		sg.setSelectionMask( IECore.StringVectorData( [ "Camera" ] ) )

		self.assertObjectAt(
			sg,
			imath.V2f( 0.6 ),
			None
		)

		self.assertObjectsAt(
			sg,
			imath.Box2f( imath.V2f( 0 ), imath.V2f( 1 ) ),
			[ "/group/camera" ]
		)

	def testResizeWindow( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		sg = GafferSceneUI.SceneGadget()
		sg.setRenderer( self.renderer )
		sg.setMinimumExpansionDepth( 999 )
		sg.setScene( s["s"]["out"] )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )

		w.setVisible( True )
		self.waitForIdle( 1000 )

		sg.waitForCompletion()
		gw.getViewportGadget().frame( sg.bound() )
		self.waitForRender( sg )

		for i in range( 0, 20 ) :
			gw._qtWidget().setFixedWidth( 200 + ( i % 2 ) * 200 )
			self.waitForIdle( 100 )

	def testSetRenderer( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferScene.Sphere()

		sg = GafferSceneUI.SceneGadget()
		sg.setMinimumExpansionDepth( 1 )
		sg.setScene( s["s"]["out"] )

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget( sg )

		w.setVisible( True )
		self.waitForIdle( 1000 )

		for i in range( 0, 5 ) :
			sg.setRenderer( self.renderer )
			self.waitForRender( sg )
			sg.setRenderer( "OpenGL" )
			self.waitForRender( sg )

	def setUp( self ) :

		GafferUITest.TestCase.setUp( self )

		self.__cachedConverterMaxMemory = IECoreGL.CachedConverter.defaultCachedConverter().getMaxMemory()

	def tearDown( self ) :

		GafferUITest.TestCase.tearDown( self )

		IECoreGL.CachedConverter.defaultCachedConverter().setMaxMemory( self.__cachedConverterMaxMemory )

if __name__ == "__main__":
	unittest.main()
