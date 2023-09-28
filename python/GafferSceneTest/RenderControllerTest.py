##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class RenderControllerTest( GafferSceneTest.SceneTestCase ) :

	def testConstructorAndAccessors( self ) :

		sphere = GafferScene.Sphere()
		context1 = Gaffer.Context()
		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)
		controller = GafferScene.RenderController( sphere["out"], context1, renderer )

		self.assertTrue( controller.renderer().isSame( renderer ) )
		self.assertTrue( controller.getScene().isSame( sphere["out"] ) )
		self.assertTrue( controller.getContext().isSame( context1 ) )

		cube = GafferScene.Cube()
		context2 = Gaffer.Context()

		controller.setScene( cube["out"] )
		controller.setContext( context2 )

		self.assertTrue( controller.getScene().isSame( cube["out"] ) )
		self.assertTrue( controller.getContext().isSame( context2 ) )

	def testBoundUpdate( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.update()
		self.assertEqual(
			renderer.command( "gl:queryBound", {} ),
			group["out"].bound( "/" )
		)

		sphere["transform"]["translate"]["x"].setValue( 1 )
		controller.update()
		self.assertEqual(
			renderer.command( "gl:queryBound", {} ),
			group["out"].bound( "/" )
		)

	def testUpdateMatchingPaths( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 3 )
		controller.update()

		def bound( path ) :

			renderer.option( "gl:selection", IECore.PathMatcherData( IECore.PathMatcher( [ path ] ) ) )
			return renderer.command( "gl:queryBound", { "selection" : True } )

		boundOrig = sphere["out"].bound( "/sphere" )
		self.assertEqual( bound( "/group/sphere" ), boundOrig )
		self.assertEqual( bound( "/group/sphere1" ), boundOrig )

		sphere["radius"].setValue( 2 )

		self.assertEqual( bound( "/group/sphere" ), boundOrig )
		self.assertEqual( bound( "/group/sphere1" ), boundOrig )

		controller.updateMatchingPaths( IECore.PathMatcher( [ "/group/sphere" ] ) )

		boundUpdated = sphere["out"].bound( "/sphere" )
		self.assertEqual( bound( "/group/sphere" ), boundUpdated )
		self.assertEqual( bound( "/group/sphere1" ), boundOrig )

		controller.update()

		self.assertEqual( bound( "/group/sphere" ), boundUpdated )
		self.assertEqual( bound( "/group/sphere1" ), boundUpdated )

	def testUpdateMatchingPathsAndInheritedTransforms( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )
		group["in"][1].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 3 )
		controller.update()

		def bound( path ) :

			renderer.option( "gl:selection", IECore.PathMatcherData( IECore.PathMatcher( [ path ] ) ) )
			return renderer.command( "gl:queryBound", { "selection" : True } )

		untranslatedBound = group["out"].bound( "/group/sphere" ) * group["out"].fullTransform( "/group/sphere" )
		self.assertEqual( bound( "/group/sphere" ), untranslatedBound )
		self.assertEqual( bound( "/group/sphere1" ), untranslatedBound )

		group["transform"]["translate"]["x"].setValue( 2 )
		translatedBound = group["out"].bound( "/group/sphere" ) * group["out"].fullTransform( "/group/sphere" )

		controller.updateMatchingPaths( IECore.PathMatcher( [ "/group/sphere" ] ) )

		self.assertEqual( bound( "/group/sphere" ), translatedBound )
		self.assertEqual( bound( "/group/sphere1" ), untranslatedBound )

		controller.update()

		self.assertEqual( bound( "/group/sphere" ), translatedBound )
		self.assertEqual( bound( "/group/sphere1" ), translatedBound )

	def testUpdateRemoveFromLightSet( self ) :

		sphere = GafferScene.Sphere()
		lightSet = GafferScene.Set()
		lightSet["in"].setInput( sphere["out"] )
		lightSet["name"].setValue( '__lights' )
		lightSet["paths"].setValue( IECore.StringVectorData( [ '/sphere' ] ) )

		renderer = GafferScene.Private.IECoreScenePreview.Renderer.create(
			"OpenGL",
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)
		controller = GafferScene.RenderController( sphere["out"], Gaffer.Context(), renderer )
		controller.update()
		self.assertEqual(
			renderer.command( "gl:queryBound", {} ),
			lightSet["out"].bound( "/" )
		)

		controller.setScene( lightSet["out"] )
		controller.update()
		self.assertEqual(
			renderer.command( "gl:queryBound", {} ),
			lightSet["out"].bound( "/" )
		)

		# While doing this exact same thing worked the first time, there was a bug where
		# rendering geo that had previously been rendered in the lights pass would fail.
		controller.setScene( sphere["out"] )
		controller.update()
		self.assertEqual(
			renderer.command( "gl:queryBound", {} ),
			lightSet["out"].bound( "/" )
		)

	def testLightLinks( self ) :

		sphere = GafferScene.Sphere()

		attributes = GafferScene.StandardAttributes()
		attributes["in"].setInput( sphere["out"] )
		attributes["attributes"]["linkedLights"]["enabled"].setValue( True )
		attributes["attributes"]["linkedLights"]["value"].setValue( "defaultLights" )
		attributes["attributes"]["doubleSided"]["enabled"].setValue( True )
		attributes["attributes"]["doubleSided"]["value"].setValue( False )

		lightA = GafferSceneTest.TestLight()
		lightA["name"].setValue( "lightA" )
		lightA["sets"].setValue( "A" )

		lightB = GafferSceneTest.TestLight()
		lightB["name"].setValue( "lightB" )
		lightB["sets"].setValue( "B" )

		group = GafferScene.Group()
		group["in"][0].setInput( attributes["out"] )
		group["in"][1].setInput( lightA["out"] )
		group["in"][2].setInput( lightB["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 10 )
		controller.update()

		capturedSphere = renderer.capturedObject( "/group/sphere" )
		capturedLightA = renderer.capturedObject( "/group/lightA" )
		capturedLightB = renderer.capturedObject( "/group/lightB" )

		# Since the linking expression is "defaultLights" and there are
		# no non-default lights, we don't expect to have light links.

		self.assertEqual( capturedSphere.capturedLinks( "lights" ), None )
		self.assertEqual( capturedSphere.numLinkEdits( "lights" ), 1 )

		# If we restrict to just one set of lights, then we expect an
		# edit to update the links.

		attributes["attributes"]["linkedLights"]["value"].setValue( "A" )
		controller.update()
		self.assertEqual( capturedSphere.capturedLinks( "lights" ), { capturedLightA } )
		self.assertEqual( capturedSphere.numLinkEdits( "lights" ), 2 )

		# Likewise if we restrict to the other set of lights.

		attributes["attributes"]["linkedLights"]["value"].setValue( "B" )
		controller.update()
		self.assertEqual( capturedSphere.capturedLinks( "lights" ), { capturedLightB } )
		self.assertEqual( capturedSphere.numLinkEdits( "lights" ), 3 )

		# If we change an attribute which has no bearing on light linking,
		# we don't want links to be emitted again. Attributes change frequently
		# and light linking can be expensive.

		attributes["attributes"]["doubleSided"]["value"].setValue( True )
		controller.update()
		self.assertEqual( capturedSphere.capturedLinks( "lights" ), { capturedLightB } )
		self.assertEqual( capturedSphere.numLinkEdits( "lights" ), 3 )

		del capturedSphere, capturedLightA, capturedLightB

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testLightLinkPerformance( self ) :

		numSpheres = 10000
		numLights = 1000

		# Make a bunch of spheres

		sphere = GafferScene.Sphere()

		spherePlane = GafferScene.Plane()
		spherePlane["name"].setValue( "spheres" )
		spherePlane["divisions"].setValue( imath.V2i( 1, numSpheres / 2 - 1 ) )

		sphereInstancer = GafferScene.Instancer()
		sphereInstancer["in"].setInput( spherePlane["out"] )
		sphereInstancer["prototypes"].setInput( sphere["out"] )
		sphereInstancer["parent"].setValue( "/spheres" )

		# Make a bunch of lights

		light = GafferSceneTest.TestLight()

		lightPlane = GafferScene.Plane()
		lightPlane["name"].setValue( "lights" )
		lightPlane["divisions"].setValue( imath.V2i( 1, numLights / 2 - 1 ) )

		lightInstancer = GafferScene.Instancer()
		lightInstancer["in"].setInput( lightPlane["out"] )
		lightInstancer["prototypes"].setInput( light["out"] )
		lightInstancer["parent"].setValue( "/lights" )

		# Make a single non-default light. This
		# will trigger linking of all the others.

		nonDefaultLight = GafferSceneTest.TestLight()
		nonDefaultLight["defaultLight"].setValue( False )

		# Group everything into one scene

		group = GafferScene.Group()
		group["in"][0].setInput( sphereInstancer["out"] )
		group["in"][1].setInput( lightInstancer["out"] )
		group["in"][2].setInput( nonDefaultLight["out"] )

		# See how quickly we can output those links

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 10 )

		with GafferTest.TestRunner.PerformanceScope() :
			controller.update()

		# Sanity check that we did output links as expected.

		links = renderer.capturedObject( "/group/spheres/instances/sphere/0" ).capturedLinks( "lights" )
		self.assertEqual( len( links ), numLights )

	def testHideLinkedLight( self ) :

		# One default light and one non-default light, which will
		# result in light links being emitted to the renderer.

		defaultLight = GafferSceneTest.TestLight()
		defaultLight["name"].setValue( "defaultLight" )
		defaultLightAttributes = GafferScene.StandardAttributes()
		defaultLightAttributes["in"].setInput( defaultLight["out"] )

		nonDefaultLight = GafferSceneTest.TestLight()
		nonDefaultLight["name"].setValue( "nonDefaultLight" )
		nonDefaultLight["defaultLight"].setValue( False )

		plane = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( defaultLightAttributes["out"] )
		group["in"][1].setInput( nonDefaultLight["out"] )
		group["in"][2].setInput( plane["out"] )

		# Output a scene. Only the default light should be linked.

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 10 )
		controller.update()

		capturedPlane = renderer.capturedObject( "/group/plane" )

		self.assertEqual( capturedPlane.capturedLinks( "lights" ), { renderer.capturedObject( "/group/defaultLight" ) } )

		# Hide the default light. It should be removed from the render,
		# and the plane should be linked to an empty light set.

		defaultLightAttributes["attributes"]["visibility"]["enabled"].setValue( True )
		defaultLightAttributes["attributes"]["visibility"]["value"].setValue( False )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/defaultLight" ) )
		self.assertEqual( capturedPlane.capturedLinks( "lights" ), set() )

	def testAttributeDirtyPropagation( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		options = GafferScene.StandardOptions()

		sphereSet = GafferScene.Set()
		sphereSet["name"].setValue( "render:spheres" )
		setFilter = GafferScene.PathFilter()
		setFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )
		sphereSet["filter"].setInput( setFilter["out"] )

		group["in"][0].setInput( sphere["out"] )
		options["in"].setInput( group["out"] )
		sphereSet["in"].setInput( options["out"] )

		globalAttr = GafferScene.CustomAttributes()
		globalAttrPlug = Gaffer.NameValuePlug( "user:globalAttr", IECore.IntData( 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		globalAttr["attributes"].addChild( globalAttrPlug )
		globalAttr["global"].setValue( True )

		groupAttr = GafferScene.CustomAttributes()
		groupAttrPlug = Gaffer.NameValuePlug( "localAttr1", IECore.IntData( 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		groupAttr["attributes"].addChild( groupAttrPlug )
		groupAttrFilter = GafferScene.PathFilter()
		groupAttr["filter"].setInput( groupAttrFilter["out"] )
		groupAttrFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		sphereAttr = GafferScene.CustomAttributes()
		sphereAttrPlug = Gaffer.NameValuePlug( "user:localAttr2", IECore.IntData( 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		sphereAttr["attributes"].addChild( sphereAttrPlug )
		sphereAttrFilter = GafferScene.PathFilter()
		sphereAttr["filter"].setInput( sphereAttrFilter["out"] )
		sphereAttrFilter["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		globalAttr["in"].setInput( sphereSet["out"] )
		groupAttr["in"].setInput( globalAttr["out"] )
		sphereAttr["in"].setInput( groupAttr["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( sphereAttr["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 10 )
		controller.update()

		capturedSphere = renderer.capturedObject( "/group/sphere" )

		self.assertEqual( capturedSphere.numAttributeEdits(), 1 )
		self.assertEqual(
			capturedSphere.capturedAttributes().attributes(),
			IECore.CompoundObject( {
				"user:globalAttr" : IECore.IntData( 0 ),
				"localAttr1" : IECore.IntData( 0 ),
				"user:localAttr2" : IECore.IntData( 0 ),
				"sets" : IECore.InternedStringVectorData( [ "spheres" ] )
			} )
		)

		sphereAttrPlug["value"].setValue( 1 )
		controller.update()

		self.assertEqual( capturedSphere.numAttributeEdits(), 2 )
		self.assertEqual(
			capturedSphere.capturedAttributes().attributes(),
			IECore.CompoundObject( {
				"user:globalAttr" : IECore.IntData( 0 ),
				"localAttr1" : IECore.IntData( 0 ),
				"user:localAttr2" : IECore.IntData( 1 ),
				"sets" : IECore.InternedStringVectorData( [ "spheres" ] )
			} )
		)

		groupAttrPlug["value"].setValue( 2 )
		controller.update()

		self.assertEqual( capturedSphere.numAttributeEdits(), 3 )
		self.assertEqual(
			capturedSphere.capturedAttributes().attributes(),
			IECore.CompoundObject( {
				"user:globalAttr" : IECore.IntData( 0 ),
				"localAttr1" : IECore.IntData( 2 ),
				"user:localAttr2" : IECore.IntData( 1 ),
				"sets" : IECore.InternedStringVectorData( [ "spheres" ] )
			} )
		)

		globalAttrPlug["value"].setValue( 3 )
		controller.update()

		self.assertEqual( capturedSphere.numAttributeEdits(), 4 )
		self.assertEqual(
			capturedSphere.capturedAttributes().attributes(),
			IECore.CompoundObject( {
				"user:globalAttr" : IECore.IntData( 3 ),
				"localAttr1" : IECore.IntData( 2 ),
				"user:localAttr2" : IECore.IntData( 1 ),
				"sets" : IECore.InternedStringVectorData( [ "spheres" ] )
			} )
		)

		sphereSet["enabled"].setValue( False )
		controller.update()

		self.assertEqual( capturedSphere.numAttributeEdits(), 5 )
		self.assertEqual(
			capturedSphere.capturedAttributes().attributes(),
			IECore.CompoundObject( {
				"user:globalAttr" : IECore.IntData( 3 ),
				"localAttr1" : IECore.IntData( 2 ),
				"user:localAttr2" : IECore.IntData( 1 ),
				"sets" : IECore.InternedStringVectorData( [ ] )
			} )
		)

		options["options"]["renderCamera"]["enabled"].setValue( True )
		controller.update()

		self.assertEqual( capturedSphere.numAttributeEdits(), 5 )

		options["options"]["renderCamera"]["value"].setValue( "/camera" )
		controller.update()

		self.assertEqual( capturedSphere.numAttributeEdits(), 5 )

		del capturedSphere

	def testNullObjects( self ) :

		camera = GafferScene.Camera()
		sphere = GafferScene.Sphere()
		light = GafferSceneTest.TestLight()

		lightAttr = GafferScene.StandardAttributes()
		lightAttr["in"].setInput( sphere["out"] )
		lightAttr["attributes"]["linkedLights"]["enabled"].setValue( True )
		lightAttr["attributes"]["linkedLights"]["value"].setValue( "defaultLights" )

		group = GafferScene.Group()
		group["in"][0].setInput( camera["out"] )
		group["in"][1].setInput( sphere["out"] )
		group["in"][2].setInput( light["out"] )

		allFilter = GafferScene.PathFilter()
		allFilter["paths"].setValue( IECore.StringVectorData( [ "..." ] ) )

		attr = GafferScene.CustomAttributes()
		unrenderableAttrPlug = Gaffer.NameValuePlug( "cr:unrenderable", IECore.BoolData( True ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		attr["attributes"].addChild( unrenderableAttrPlug )
		attr["filter"].setInput( allFilter["out"] )
		attr["in"].setInput( group["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( attr["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 10 )
		controller.update()

	def testBlur( self ) :

		sphere = GafferScene.Sphere()
		sphere["type"].setValue( sphere.Type.Primitive )
		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		sphereAttributes = GafferScene.StandardAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["filter"].setInput( sphereFilter["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( sphereAttributes["out"] )
		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		groupAttributes = GafferScene.StandardAttributes()
		groupAttributes["in"].setInput( group["out"] )
		groupAttributes["filter"].setInput( groupFilter["out"] )

		options = GafferScene.StandardOptions()
		options["in"].setInput( groupAttributes["out"] )

		# Animated source for testing
		frame = GafferTest.FrameNode()

		# Source that isn't animated, but has an animated hash
		dummyFrame = Gaffer.Node()
		dummyFrame["output"] = Gaffer.FloatPlug()
		dummyFrame["expression"] = Gaffer.Expression()
		dummyFrame["expression"].setExpression( 'parent["output"] = context.getFrame() * 0 + 3' )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( options["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )
		controller.update()

		def assertMotionSamples( expectedSamples, deform ) :

			capturedSphere = renderer.capturedObject( "/group/sphere" )
			self.assertIsNotNone( capturedSphere )

			if deform:
				samples = [ i.radius() for i in capturedSphere.capturedSamples() ]
				times = capturedSphere.capturedSampleTimes()
			else:
				samples = [ i.translation().x for i in capturedSphere.capturedTransforms() ]
				times = capturedSphere.capturedTransformTimes()

			self.assertEqual( len( samples ), len( expectedSamples ) )
			for (i,j) in zip( samples, expectedSamples ):
				self.assertAlmostEqual( i, j, places = 6 )

			if len( expectedSamples ) > 1 :
				self.assertEqual( len( times ), len( expectedSamples ) )
				for (i,j) in zip( times, expectedSamples ):
					self.assertAlmostEqual( i, j, places = 6 )
			else :
				self.assertEqual( times, [] )

		# INITIAL TRANSFORM TESTS

		assertMotionSamples( [ 0 ], False )
		sphere["transform"]["translate"]["x"].setValue( 2 )
		controller.update()
		assertMotionSamples( [ 2 ], False )

		# Hook up animated value, but blur not turned on yet
		sphere["transform"]["translate"]["x"].setInput( frame["output"] )
		controller.update()
		assertMotionSamples( [ 1 ], False )

		# Test blur.
		options['options']['transformBlur']["enabled"].setValue( True )
		options['options']['transformBlur']["value"].setValue( True )
		controller.update()
		assertMotionSamples( [ 0.75, 1.25 ], False )

		# Test blur on but no movement
		sphere["transform"]["translate"]["x"].setInput( None )
		controller.update()
		assertMotionSamples( [ 2 ], False )

		# We get a single sample out even if the transform hash is changing but the transform isn't
		sphere["transform"]["translate"]["x"].setInput( dummyFrame["output"] )
		controller.update()
		assertMotionSamples( [ 3 ], False )

		# INITIAL DEFORMATION TESTS
		# Test non-blurred updates.

		assertMotionSamples( [ 1 ], True )
		sphere["radius"].setValue( 2 )
		controller.update()
		assertMotionSamples( [ 2 ], True )

		# Hook up animated value, but blur not turned on yet
		sphere["radius"].setInput( frame["output"] )
		controller.update()
		assertMotionSamples( [ 1 ], True )

		# Test deformation blur.
		options['options']['deformationBlur']["enabled"].setValue( True )
		options['options']['deformationBlur']["value"].setValue( True )
		controller.update()
		assertMotionSamples( [ 0.75, 1.25 ], True )

		# Test deformation blur on but no deformation
		sphere["radius"].setInput( None )
		controller.update()
		assertMotionSamples( [ 2 ], True )


		# Test shutter
		sphere["transform"]["translate"]["x"].setInput( frame["output"] )
		sphere["radius"].setInput( frame["output"] )
		options['options']['shutter']["enabled"].setValue( True )
		options['options']['shutter']["value"].setValue( imath.V2f( -0.7, 0.4 ) )
		controller.update()
		assertMotionSamples( [ 0.3, 1.4 ], False )
		assertMotionSamples( [ 0.3, 1.4 ], True )

		# Test with camera shutter
		camera = GafferScene.Camera()
		group["in"][1].setInput( camera["out"] )
		controller.update()
		self.assertEqual( renderer.capturedObject( "/group/camera" ).capturedSamples()[0].getShutter(), imath.V2f( 0.3, 1.4 ) )

		options['options']['renderCamera']["enabled"].setValue( True )
		options['options']['renderCamera']["value"].setValue( "/group/camera" )
		controller.update()
		assertMotionSamples( [ 0.3, 1.4 ], False )
		assertMotionSamples( [ 0.3, 1.4 ], True )
		camera['renderSettingOverrides']['shutter']["enabled"].setValue( True )
		camera['renderSettingOverrides']['shutter']["value"].setValue( imath.V2f( -0.5, 0.5 ) )
		controller.update()
		assertMotionSamples( [ 0.5, 1.5 ], False )
		assertMotionSamples( [ 0.5, 1.5 ], True )
		self.assertEqual( renderer.capturedObject( "/group/camera" ).capturedSamples()[0].getShutter(), imath.V2f( 0.5, 1.5 ) )

		# Test attribute controls
		camera['renderSettingOverrides']['shutter']["enabled"].setValue( False )
		options['options']['shutter']["value"].setValue( imath.V2f( -0.4, 0.4 ) )
		controller.update()
		assertMotionSamples( [ 0.6, 1.4 ], False )
		assertMotionSamples( [ 0.6, 1.4 ], True )

		groupAttributes['attributes']['transformBlur']["enabled"].setValue( True )
		groupAttributes['attributes']['transformBlur']["value"].setValue( False )
		controller.update()
		assertMotionSamples( [ 1 ], False )
		sphereAttributes['attributes']['transformBlur']["enabled"].setValue( True )
		controller.update()
		assertMotionSamples( [ 0.6, 1.4 ], False )

		groupAttributes['attributes']['deformationBlur']["enabled"].setValue( True )
		groupAttributes['attributes']['deformationBlur']["value"].setValue( False )
		controller.update()
		assertMotionSamples( [ 1 ], True )
		sphereAttributes['attributes']['deformationBlur']["enabled"].setValue( True )
		controller.update()
		assertMotionSamples( [ 0.6, 1.4 ], True )

		groupAttributes['attributes']['transformBlurSegments']["enabled"].setValue( True )
		groupAttributes['attributes']['transformBlurSegments']["value"].setValue( 4 )
		groupAttributes['attributes']['deformationBlurSegments']["enabled"].setValue( True )
		groupAttributes['attributes']['deformationBlurSegments']["value"].setValue( 2 )
		controller.update()
		assertMotionSamples( [ 0.6, 0.8, 1.0, 1.2, 1.4 ], False )
		assertMotionSamples( [ 0.6, 1.0, 1.4 ], True )

		sphereAttributes['attributes']['transformBlurSegments']["enabled"].setValue( True )
		sphereAttributes['attributes']['transformBlurSegments']["value"].setValue( 2 )
		sphereAttributes['attributes']['deformationBlurSegments']["enabled"].setValue( True )
		sphereAttributes['attributes']['deformationBlurSegments']["value"].setValue( 4 )
		controller.update()
		assertMotionSamples( [ 0.6, 1.0, 1.4 ], False )
		assertMotionSamples( [ 0.6, 0.8, 1.0, 1.2, 1.4 ], True )

		groupAttributes['attributes']['transformBlur']["value"].setValue( True )
		groupAttributes['attributes']['deformationBlur']["value"].setValue( True )
		sphereAttributes['attributes']['transformBlur']["value"].setValue( False )
		sphereAttributes['attributes']['deformationBlur']["value"].setValue( False )
		controller.update()
		assertMotionSamples( [ 1.0 ], False )
		assertMotionSamples( [ 1.0 ], True )

		# Apply transformation to group instead of sphere, giving the same results
		sphere["transform"]["translate"]["x"].setInput( None )
		sphere["transform"]["translate"]["x"].setValue( 0 )
		group["transform"]["translate"]["x"].setInput( frame["output"] )

		groupAttributes['attributes']['transformBlur']["value"].setValue( True )
		sphereAttributes['attributes']['transformBlur']["value"].setValue( False )
		sphereAttributes['attributes']['transformBlurSegments']["enabled"].setValue( False )
		controller.update()
		assertMotionSamples( [ 0.6, 0.8, 1.0, 1.2, 1.4 ], False )

		# Override transform segments on sphere
		sphereAttributes['attributes']['transformBlur']["value"].setValue( True )
		sphereAttributes['attributes']['transformBlurSegments']["enabled"].setValue( True )
		sphereAttributes['attributes']['transformBlurSegments']["value"].setValue( 1 )
		controller.update()
		# Very counter-intuitively, this does nothing, because the sphere is not moving
		assertMotionSamples( [ 0.6, 0.8, 1.0, 1.2, 1.4 ], False )

		# But then if the sphere moves, the sample count does take affect
		sphere["transform"]["translate"]["y"].setInput( frame["output"] )
		controller.update()
		assertMotionSamples( [ 0.6, 1.4 ], False )

	def testCoordinateSystem( self ) :

		coordinateSystem = GafferScene.CoordinateSystem()
		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( coordinateSystem["out"], Gaffer.Context(), renderer )
		controller.update()

		capturedObject = renderer.capturedObject( "/coordinateSystem" )
		self.assertEqual( capturedObject.capturedSamples(), [ coordinateSystem["out"].object( "/coordinateSystem" ) ] )

	def testFailedAttributeEdit( self ) :

		sphere = GafferScene.Sphere()

		attributes = GafferScene.CustomAttributes()
		attributes["in"].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( attributes["out"], Gaffer.Context(), renderer )
		controller.update()
		self.assertEqual( renderer.capturedObject( "/sphere" ).numAttributeEdits(), 1 )

		# Successful edit should just update the object in place and
		# increment `numAttributeEdits()`.

		attributes["attributes"].addChild( Gaffer.NameValuePlug( "test", 10 ) )
		controller.update()
		self.assertEqual( renderer.capturedObject( "/sphere" ).numAttributeEdits(), 2 )
		self.assertEqual( renderer.capturedObject( "/sphere" ).capturedAttributes().attributes()["test"], IECore.IntData( 10 ) )

		# Failed edit should replace the object, so `numAttributeEdits()` should
		# be reset to 1.

		attributes["attributes"].addChild( Gaffer.NameValuePlug( "cr:uneditable", 10 ) )
		with IECore.CapturingMessageHandler() as mh :
			controller.update()

		self.assertEqual( renderer.capturedObject( "/sphere" ).numAttributeEdits(), 1 )
		self.assertEqual( renderer.capturedObject( "/sphere" ).capturedAttributes().attributes()["cr:uneditable"], IECore.IntData( 10 ) )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].message, "1 attribute edit required geometry to be regenerated" )

		# Adding `cr:unrenderable` should also cause an edit failure, because such
		# objects can't be rendered. But this time the object should be removed
		# and not replaced.

		attributes["attributes"].addChild( Gaffer.NameValuePlug( "cr:unrenderable", True ) )
		with IECore.CapturingMessageHandler() as mh :
			controller.update()

		self.assertIsNone( renderer.capturedObject( "/sphere" ) )

	def testIDs( self ) :

		cube = GafferScene.Cube()
		sphere = GafferScene.Sphere()
		plane = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( cube["out"] )
		group["in"][1].setInput( sphere["out"] )
		group["in"][2].setInput( plane["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )

		paths = [ "/group/cube", "/group/sphere", "/group/plane" ]
		for path in paths :
			self.assertEqual(
				controller.idForPath( path, createIfNecessary = False ), 0
			)

		controller.update()
		for path in paths :
			self.assertNotEqual(
				controller.idForPath( path, createIfNecessary = False ), 0
			)
			self.assertEqual(
				controller.pathForID( renderer.capturedObject( path ).id() ),
				path
			)
			self.assertEqual(
				controller.idForPath( path ),
				renderer.capturedObject( path ).id()
			)

		self.assertIsNone( controller.pathForID( 0 ) )
		self.assertIsNone( controller.pathForID( 4 ) )
		self.assertEqual( 0, controller.idForPath( "/no/object/here" ) )
		self.assertEqual( 0, controller.idForPath( "/no/object/here", createIfNecessary = False ) )
		self.assertNotEqual( 0, controller.idForPath( "/might/exist/later/and/want/id/now", createIfNecessary = True ) )

		self.assertEqual(
			controller.pathsForIDs( [
				renderer.capturedObject( p ).id() for p in paths
			] ),
			IECore.PathMatcher( paths )
		)

		self.assertEqual(
			set( controller.idsForPaths( IECore.PathMatcher( paths ) ) ),
			{ renderer.capturedObject( p ).id() for p in paths }
		)

	def testProgressCallback( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["group"]["in"][1].setInput( script["sphere"]["out"] )
		script["group"]["in"][2].setInput( script["sphere"]["out"] )

		script["allFilter"] = GafferScene.PathFilter()
		script["allFilter"]["paths"].setValue( IECore.StringVectorData( [ "/*", "/*/*" ] ) )

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["group"]["out"] )
		script["transform"]["filter"].setInput( script["allFilter"]["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( script["transform"]["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )

		statuses = []
		def callback( status ) :

			statuses.append( status )

		# First update should yield one call per location (including the root),
		# plus one for completion.
		controller.update( callback )
		Status = Gaffer.BackgroundTask.Status
		self.assertEqual( statuses, [ Status.Running ] * 5 + [ Status.Completed ] )

		# Next update should go straight to completion, because nothing has
		# changed.
		del statuses[:]
		controller.update( callback )
		self.assertEqual( statuses, [ Status.Completed ] )

		# Move everything and do a partial update. We expect updates only to the
		# path we requested, and it's ancestors (not including the root, because
		# its transform hasn't changed).
		del statuses[:]
		script["transform"]["transform"]["translate"]["x"].setValue( 1 )
		controller.updateMatchingPaths( IECore.PathMatcher( [ "/group/sphere" ] ), callback )
		self.assertEqual( statuses, [ Status.Running ] * 2 + [ Status.Completed ] )

		# Move everything again and do a background update with a priority path.
		# We expect updates to all locations (except the root, because its transform
		# hasn't changed).
		del statuses[:]
		script["transform"]["transform"]["translate"]["x"].setValue( 2 )
		task = controller.updateInBackground( callback, priorityPaths = IECore.PathMatcher( [ "/group/sphere" ] ) )
		task.wait()
		self.assertEqual( statuses, [ Status.Running ] * 4 + [ Status.Completed ] )

	def testLightMute( self ) :

		#   Light					light:mute	Muted Result
		#   --------------------------------------------------------
		# - lightMute				True				True
		# - light					undefined			undefined
		# - lightMute2				True				True
		# - lightMute3				True				True
		# --- lightMute3Child		False				False
		# - light2					undefined			undefined
		# --- light2ChildMute		True				True
		# --- light2Child			False				False
		# - groupMute				True				--
		# --- lightGroupMuteChild	undefined			True (inherited)

		lightMute = GafferSceneTest.TestLight()
		lightMute["name"].setValue( "lightMute" )
		light = GafferSceneTest.TestLight()
		light["name"].setValue( "light" )
		lightMute2 = GafferSceneTest.TestLight()
		lightMute2["name"].setValue( "lightMute2" )
		lightMute3 = GafferSceneTest.TestLight()
		lightMute3["name"].setValue( "lightMute3" )
		lightMute3Child = GafferSceneTest.TestLight()
		lightMute3Child["name"].setValue( "lightMute3Child" )
		light2 = GafferSceneTest.TestLight()
		light2["name"].setValue( "light2" )
		light2ChildMute = GafferSceneTest.TestLight()
		light2ChildMute["name"].setValue( "light2ChildMute" )
		light2Child = GafferSceneTest.TestLight()
		light2Child["name"].setValue( "light2Child" )
		lightGroupMuteChild = GafferSceneTest.TestLight()
		lightGroupMuteChild["name"].setValue( "lightGroupMuteChild" )

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["children"][0].setInput( lightMute["out"] )
		parent["children"][1].setInput( light["out"] )
		parent["children"][2].setInput( lightMute2["out"] )
		parent["children"][3].setInput( lightMute3["out"] )

		lightMute3Parent = GafferScene.Parent()
		lightMute3Parent["in"].setInput( parent["out"] )
		lightMute3Parent["parent"].setValue( "/lightMute3" )
		lightMute3Parent["children"][0].setInput( lightMute3Child["out"] )

		parent["children"][4].setInput( light2["out"] )

		light2Parent = GafferScene.Parent()
		light2Parent["in"].setInput( lightMute3Parent["out"] )
		light2Parent["parent"].setValue( "/light2" )
		light2Parent["children"][0].setInput( light2ChildMute["out"] )
		light2Parent["children"][1].setInput( light2Child["out"] )

		groupMute = GafferScene.Group()
		groupMute["name"].setValue( "groupMute" )
		groupMute["in"][0].setInput( lightGroupMuteChild["out"] )

		parent["children"][5].setInput( groupMute["out"] )

		unMuteFilter = GafferScene.PathFilter()
		unMuteFilter["paths"].setValue(
			IECore.StringVectorData( [ "/lightMute3/lightMute3Child", "/light2/light2Child" ] )
		)
		unMuteAttributes = GafferScene.CustomAttributes()
		unMuteAttributes["in"].setInput( light2Parent["out"] )
		unMuteAttributes["filter"].setInput( unMuteFilter["out"] )
		unMuteAttributes["attributes"].addChild( Gaffer.NameValuePlug( "light:mute", False ) )

		muteFilter = GafferScene.PathFilter()
		muteFilter["paths"].setValue(
			IECore.StringVectorData( [ "/lightMute", "/lightMute2", "/lightMute3", "/light2/light2ChildMute", "/groupMute" ] )
		)
		muteAttributes = GafferScene.CustomAttributes()
		muteAttributes["in"].setInput( unMuteAttributes["out"] )
		muteAttributes["filter"].setInput( muteFilter["out"] )
		muteAttributes["attributes"].addChild( Gaffer.NameValuePlug( "light:mute", True ) )

		# Make sure we got the hierarchy and attributes right
		self.assertEqual(
			parent["out"].childNames( "/" ),
			IECore.InternedStringVectorData( [ "lightMute", "light", "lightMute2", "lightMute3", "light2", "groupMute", ] )
		)
		self.assertEqual(
			muteAttributes["out"].childNames( "/lightMute3" ),
			IECore.InternedStringVectorData( [ "lightMute3Child", ] )
		)
		self.assertEqual(
			muteAttributes["out"].childNames( "/light2" ),
			IECore.InternedStringVectorData( [ "light2ChildMute", "light2Child", ] )
		)
		self.assertEqual(
			muteAttributes["out"].childNames( "/groupMute" ),
			IECore.InternedStringVectorData( [ "lightGroupMuteChild", ] )
		)
		self.assertTrue( muteAttributes["out"].attributes( "/lightMute" )["light:mute"].value )
		self.assertNotIn( "light:mute", muteAttributes["out"].attributes( "/light" ) )
		self.assertTrue( muteAttributes["out"].attributes( "/lightMute2" )["light:mute"].value )
		self.assertTrue( muteAttributes["out"].attributes( "/lightMute3" )["light:mute"].value )
		self.assertFalse( muteAttributes["out"].attributes( "/lightMute3/lightMute3Child" )["light:mute"].value )
		self.assertNotIn( "light:mute", muteAttributes["out"].attributes( "/light2" ) )
		self.assertTrue( muteAttributes["out"].attributes( "/light2/light2ChildMute" )["light:mute"].value )
		self.assertFalse( muteAttributes["out"].attributes( "/light2/light2Child" )["light:mute"].value )
		self.assertTrue( muteAttributes["out"].attributes( "/groupMute" )["light:mute"].value )
		self.assertNotIn( "light:mute", muteAttributes["out"].attributes( "/groupMute/lightGroupMuteChild" ) )
		self.assertTrue( muteAttributes["out"].fullAttributes( "/groupMute/lightGroupMuteChild" ) )

		# Output the lights to the renderer

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( muteAttributes["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )
		controller.update()

		self.assertTrue( renderer.capturedObject( "/lightMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertNotIn( "light:mute", renderer.capturedObject( "/light" ).capturedAttributes().attributes() )
		self.assertTrue( renderer.capturedObject( "/lightMute2" ).capturedAttributes().attributes()["light:mute"] .value)
		self.assertTrue( renderer.capturedObject( "/lightMute3" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/lightMute3/lightMute3Child" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertNotIn( "light:mute", renderer.capturedObject( "/light2" ).capturedAttributes().attributes() )
		self.assertTrue( renderer.capturedObject( "/light2/light2ChildMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/light2/light2Child" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/groupMute/lightGroupMuteChild" ).capturedAttributes().attributes()["light:mute"].value )

		# Changing the muted lights should update

		#   Light					light:mute	Muted Result
		#   --------------------------------------------------------
		# - lightMute				False				False
		# - light					False				False
		# - lightMute2				False				False
		# - lightMute3				False				False
		# --- lightMute3Child		True				True
		# - light2					False				False
		# --- light2ChildMute		False				False
		# --- light2Child			True				True
		# - groupMute				False				--
		# --- lightGroupMuteChild	undefined			False

		muteFilter["paths"].setValue(
			IECore.StringVectorData(
				[
					"/lightMute3/lightMute3Child",
					"/light2/light2Child"
				]
			)
		)
		unMuteFilter["paths"].setValue(
			IECore.StringVectorData(
				[
					"/lightMute",
					"/light",
					"/lightMute2",
					"/lightMute3",
					"/light2",
					"/light2/light2ChildMute",
					"/groupMute",
				]
			)
		)
		controller.update()

		self.assertFalse( renderer.capturedObject( "/lightMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/light" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/lightMute2" ).capturedAttributes().attributes()["light:mute"] .value)
		self.assertFalse( renderer.capturedObject( "/lightMute3" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute3/lightMute3Child" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/light2" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/light2/light2ChildMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/light2/light2Child" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/groupMute/lightGroupMuteChild" ).capturedAttributes().attributes()["light:mute"].value )



	def testLightSolo( self ) :

		#   Light                       light:mute      soloLights  Mute Result
		#   ---------------------------------------------------------------------------
		# - lightSolo                   undefined       in          False
		# - light                       undefined       out         True
		# - lightSolo2                  False           in          False
		# - lightMute                   True            out         True
		# --- lightMuteChild            undefined       out         True
		# --- lightMuteChildSolo        undefined       in          True
		# - lightMuteSolo               True            in          True
		# --- lightMuteSoloChild        undefined       out         True
		# --- lightMuteSoloChildSolo    undefined       in          True
		# - groupMute                   True            out         --
		# --- lightGroupMuteChildSolo   undefined       in          True

		lightSolo = GafferSceneTest.TestLight()
		lightSolo["name"].setValue( "lightSolo" )
		light = GafferSceneTest.TestLight()
		light["name"].setValue( "light" )
		lightSolo2 = GafferSceneTest.TestLight()
		lightSolo2["name"].setValue( "lightSolo2" )
		lightMute = GafferSceneTest.TestLight()
		lightMute["name"].setValue( "lightMute" )
		lightMuteChild = GafferSceneTest.TestLight()
		lightMuteChild["name"].setValue( "lightMuteChild" )
		lightMuteChildSolo = GafferSceneTest.TestLight()
		lightMuteChildSolo["name"].setValue( "lightMuteChildSolo" )
		lightMuteSolo = GafferSceneTest.TestLight()
		lightMuteSolo["name"].setValue( "lightMuteSolo" )
		lightMuteSoloChild = GafferSceneTest.TestLight()
		lightMuteSoloChild["name"].setValue( "lightMuteSoloChild" )
		lightMuteSoloChildSolo = GafferSceneTest.TestLight()
		lightMuteSoloChildSolo["name"].setValue( "lightMuteSoloChildSolo" )
		lightGroupMuteChildSolo = GafferSceneTest.TestLight()
		lightGroupMuteChildSolo["name"].setValue( "lightGroupMuteChildSolo" )

		parent = GafferScene.Parent()
		parent["parent"].setValue( "/" )
		parent["children"][0].setInput( lightSolo["out"] )
		parent["children"][1].setInput( light["out"] )
		parent["children"][2].setInput( lightSolo2["out"] )

		parent["children"][3].setInput( lightMute["out"] )

		lightMuteParent = GafferScene.Parent()
		lightMuteParent["in"].setInput( parent["out"] )
		lightMuteParent["parent"].setValue( "/lightMute" )
		lightMuteParent["children"][0].setInput( lightMuteChild["out"] )
		lightMuteParent["children"][1].setInput( lightMuteChildSolo["out"] )

		parent["children"][4].setInput( lightMuteSolo["out"] )

		lightMuteSoloParent = GafferScene.Parent()
		lightMuteSoloParent["in"].setInput( lightMuteParent["out"] )
		lightMuteSoloParent["parent"].setValue( "/lightMuteSolo" )
		lightMuteSoloParent["children"][0].setInput( lightMuteSoloChild["out"] )
		lightMuteSoloParent["children"][1].setInput( lightMuteSoloChildSolo["out"] )

		groupMute = GafferScene.Group()
		groupMute["name"].setValue( "groupMute" )
		groupMute["in"][0].setInput( lightGroupMuteChildSolo["out"] )

		parent["children"][5].setInput( groupMute["out"] )

		unMuteFilter = GafferScene.PathFilter()
		unMuteFilter["paths"].setValue(
			IECore.StringVectorData( [ "/lightSolo2" ] )
		)
		unMuteAttributes = GafferScene.CustomAttributes()
		unMuteAttributes["in"].setInput( lightMuteSoloParent["out"] )
		unMuteAttributes["filter"].setInput( unMuteFilter["out"] )
		unMuteAttributes["attributes"].addChild( Gaffer.NameValuePlug( "light:mute", False ) )

		muteFilter = GafferScene.PathFilter()
		muteFilter["paths"].setValue(
			IECore.StringVectorData( [ "/lightMute", "/lightMuteSolo", "/groupMute" ] )
		)
		muteAttributes = GafferScene.CustomAttributes()
		muteAttributes["in"].setInput( unMuteAttributes["out"] )
		muteAttributes["filter"].setInput( muteFilter["out"] )
		muteAttributes["attributes"].addChild( Gaffer.NameValuePlug( "light:mute", True ) )

		soloFilter = GafferScene.PathFilter()
		soloFilter["paths"].setValue(
			IECore.StringVectorData(
				[
					"/lightSolo",
					"/lightSolo2",
					"/lightMute/lightMuteChildSolo",
					"/lightMuteSolo",
					"/lightMuteSolo/lightMuteSoloChildSolo",
					"/groupMute/lightGroupMuteChildSolo",
				]
			)
		)

		soloSet = GafferScene.Set()
		soloSet["in"].setInput( muteAttributes["out"])
		soloSet["name"].setValue( "soloLights" )
		soloSet["filter"].setInput( soloFilter["out"] )

		# Make sure we got the hierarchy, attributes and set right
		self.assertEqual(
			parent["out"].childNames( "/" ),
			IECore.InternedStringVectorData( [ "lightSolo", "light", "lightSolo2", "lightMute", "lightMuteSolo", "groupMute", ] )
		)
		self.assertEqual(
			soloSet["out"].childNames( "/lightMute" ),
			IECore.InternedStringVectorData( [ "lightMuteChild", "lightMuteChildSolo", ] )
		)
		self.assertEqual(
			soloSet["out"].childNames( "/lightMuteSolo" ),
			IECore.InternedStringVectorData( [ "lightMuteSoloChild", "lightMuteSoloChildSolo", ] )
		)
		self.assertEqual(
			soloSet["out"].childNames( "/groupMute" ),
			IECore.InternedStringVectorData( [ "lightGroupMuteChildSolo", ] )
		)
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightSolo" ) )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/light" ) )
		self.assertFalse( soloSet["out"].attributes( "/lightSolo2" )["light:mute"].value )
		self.assertTrue( soloSet["out"].attributes( "/lightMute" )["light:mute"].value )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightMute/lightMuteChild" ) )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightMute/lightMuteChildSolo" ) )
		self.assertTrue( soloSet["out"].attributes( "/lightMuteSolo" )["light:mute"].value )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightMuteSolo/lightMuteSoloChild" ) )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/lightMuteSolo/lightMuteSoloChildSolo" ) )
		self.assertTrue( soloSet["out"].attributes( "/groupMute" )["light:mute"].value )
		self.assertNotIn( "light:mute", soloSet["out"].attributes( "/groupMute/lightGroupMuteChildSolo" ) )
		self.assertTrue( "light:mute", soloSet["out"].fullAttributes( "/groupMute/lightGroupMuteChildSolo" ) )

		self.assertEqual(
			sorted( soloSet["out"].set( "soloLights" ).value.paths() ),
			sorted(
				[
					"/lightSolo",
					"/lightSolo2",
					"/lightMute/lightMuteChildSolo",
					"/lightMuteSolo",
					"/lightMuteSolo/lightMuteSoloChildSolo",
					"/groupMute/lightGroupMuteChildSolo",
				]
			)
		)

		# Output the lights to the renderer

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( soloSet["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )
		controller.update()

		# Check that the output is correct

		self.assertFalse( renderer.capturedObject( "/lightSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/light" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/lightSolo2" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute/lightMuteChild" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute/lightMuteChildSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMuteSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMuteSolo/lightMuteSoloChild" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMuteSolo/lightMuteSoloChildSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/groupMute/lightGroupMuteChildSolo" ).capturedAttributes().attributes()["light:mute"].value )

		#   Light                       light:mute      soloLights  Mute Result
		#   ---------------------------------------------------------------------------
		# - lightSolo                   undefined       out         True
		# - light                       undefined       in          False
		# - lightSolo2                  False           out         True
		# - lightMute                   True            in          True
		# --- lightMuteChild            undefined       in          True
		# --- lightMuteChildSolo        undefined       out         True
		# - lightMuteSolo               True            out         True
		# --- lightMuteSoloChild        undefined       in          True
		# --- lightMuteSoloChildSolo    undefined       out         True
		# - groupMute                   True            in          --
		# --- lightGroupMuteChildSolo   undefined       out         True

		soloFilter["paths"].setValue(
			IECore.StringVectorData(
				[
					"/light",
					"/lightMute",
					"/lightMute/lightMuteChild",
					"/lightMuteSolo/lightMuteSoloChild",
					"/groupMute",
				]
			)
		)
		controller.update()

		self.assertTrue( renderer.capturedObject( "/lightSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertFalse( renderer.capturedObject( "/light" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightSolo2" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute/lightMuteChild" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMute/lightMuteChildSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMuteSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMuteSolo/lightMuteSoloChild" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/lightMuteSolo/lightMuteSoloChildSolo" ).capturedAttributes().attributes()["light:mute"].value )
		self.assertTrue( renderer.capturedObject( "/groupMute/lightGroupMuteChildSolo" ).capturedAttributes().attributes()["light:mute"].value )

	def testSoloLightsSetUpdate( self ) :

		plane = GafferScene.Plane()

		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )

		soloFilter = GafferScene.PathFilter()
		soloFilter["paths"].setValue( IECore.StringVectorData() )

		soloSet = GafferScene.Set()
		soloSet["in"].setInput( group["out"])
		soloSet["name"].setValue( "soloLights" )
		soloSet["filter"].setInput( soloFilter["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( soloSet["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )
		controller.update()

		# First time emitting the scene the attributes have been edited
		self.assertEqual( renderer.capturedObject( "/group/plane" ).numAttributeEdits(), 1 )

		# A scene update when the `soloLights` set was and is empty should not cause an update
		group["in"][1].setInput( plane["out"] )
		controller.update()

		self.assertEqual( renderer.capturedObject( "/group/plane" ).numAttributeEdits(), 1 )

		# Changing the `soloLights` set should cause an update
		soloFilter["paths"].setValue( IECore.StringVectorData( [ "/group/plane" ] ) )
		controller.update()

		self.assertEqual( renderer.capturedObject( "/group/plane" ).numAttributeEdits(), 2 )

		# Making it empty again should cause an update
		soloFilter["paths"].setValue( IECore.StringVectorData() )
		controller.update()

		self.assertEqual( renderer.capturedObject( "/group/plane" ).numAttributeEdits(), 3 )

		# Going back to `soloLights` having been empty and currently empty should result in no update
		group["in"][2].setInput( plane["out"] )
		controller.update()

		self.assertEqual( renderer.capturedObject( "/group/plane" ).numAttributeEdits(), 3 )

	def testExcludedLocationsHaveNoObject( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 10 )
		controller.update()

		self.assertIsNotNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		v = GafferScene.VisibleSet()
		v.exclusions.addPath( "/group/plane" )
		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		v.exclusions = IECore.PathMatcher( [ "/group" ] )
		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNone( renderer.capturedObject( "/group/sphere" ) )

		controller.setVisibleSet( GafferScene.VisibleSet() )
		controller.update()

		self.assertIsNotNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

	def testExcludedLocationBoundsVisibility( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 10 )
		controller.update()

		self.assertIsNotNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		v = GafferScene.VisibleSet()
		v.exclusions.addPath( "/group/plane" )
		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		v.expansions.addPath( "/group" )
		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/plane/__unexpandedChildren__" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		v.expansions.removePath( "/group" )
		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		v.exclusions = IECore.PathMatcher( [ "/group" ] )
		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNone( renderer.capturedObject( "/group/sphere" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/__unexpandedChildren__" ) )

		controller.setVisibleSet( GafferScene.VisibleSet() )
		controller.update()

		self.assertIsNotNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

	def testExcludedLocationPlaceholderMode( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.update()

		self.assertEqual( renderer.capturedObject( "/group/__unexpandedChildren__" ).capturedSamples()[0].getMode(), GafferScene.Private.IECoreScenePreview.Placeholder.Mode.Default )

		v = GafferScene.VisibleSet()
		v.exclusions.addPath( "/group" )
		controller.setVisibleSet( v )
		controller.update()

		self.assertEqual( renderer.capturedObject( "/group/__unexpandedChildren__" ).capturedSamples()[0].getMode(), GafferScene.Private.IECoreScenePreview.Placeholder.Mode.Excluded )

		controller.setVisibleSet( GafferScene.VisibleSet() )
		controller.update()

		self.assertEqual( renderer.capturedObject( "/group/__unexpandedChildren__" ).capturedSamples()[0].getMode(), GafferScene.Private.IECoreScenePreview.Placeholder.Mode.Default )

	def testIncludeLocation( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( plane["out"] )
		group["in"][1].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNone( renderer.capturedObject( "/group/sphere" ) )

		v = GafferScene.VisibleSet()
		v.inclusions.addPath( "/group/plane" )
		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNotNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNone( renderer.capturedObject( "/group/sphere" ) )

		v.inclusions = IECore.PathMatcher( [ "/group" ] )
		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNotNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		controller.setVisibleSet( GafferScene.VisibleSet() )
		controller.update()

		self.assertIsNone( renderer.capturedObject( "/group/plane" ) )
		self.assertIsNone( renderer.capturedObject( "/group/sphere" ) )

	def testDescendantVisibilityChangeDoesntUpdateObject( self ) :

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( group["out"], Gaffer.Context(), renderer )
		controller.update()

		v = GafferScene.VisibleSet()
		v.expansions = IECore.PathMatcher( [ "/group" ] )

		controller.setVisibleSet( v )
		controller.update()

		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )
		self.assertEqual( v.visibility( "/group/sphere" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, False ) )

		# Adding sphere to the VisibleSet `inclusions` will not change its drawMode but will change descendantVisibility
		v.inclusions = IECore.PathMatcher( [ "/group/sphere" ] )
		self.assertEqual( v.visibility( "/group/sphere" ), GafferScene.VisibleSet.Visibility( GafferScene.VisibleSet.Visibility.DrawMode.Visible, True ) )

		# As sphere's drawMode is unchanged, this update shouldn't result in any object hashes or computes
		Gaffer.ValuePlug.clearCache()
		Gaffer.ValuePlug.clearHashCache()
		with Gaffer.PerformanceMonitor() as monitor :
			controller.setVisibleSet( v )
			controller.update()

		self.assertEqual( monitor.plugStatistics( sphere["out"]["object"] ).hashCount, 0 )
		self.assertEqual( monitor.plugStatistics( sphere["out"]["object"] ).computeCount, 0 )

	def testIncludedPurposes( self ) :

		rootFilter = GafferScene.PathFilter()
		rootFilter["paths"].setValue( IECore.StringVectorData( [ "*" ] ) )

		sphere = GafferScene.Sphere()
		sphereAttributes = GafferScene.CustomAttributes()
		sphereAttributes["in"].setInput( sphere["out"] )
		sphereAttributes["filter"].setInput( rootFilter["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( sphereAttributes["out"] )
		groupAttributes = GafferScene.CustomAttributes()
		groupAttributes["in"].setInput( group["out"] )
		groupAttributes["filter"].setInput( rootFilter["out"] )

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( groupAttributes["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( standardOptions["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )
		controller.update()

		# Should be visible by default - we haven't used any purpose attributes or options.

		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		# Should still be visible when we add a purpose attribute, because we haven't
		# specified the `render:includedPurposes` option.

		sphereAttributes["attributes"].addChild( Gaffer.NameValuePlug( "usd:purpose", "proxy", defaultEnabled = True ) )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		# But should be hidden when we add `render:includedPurposes` to exclude it.

		standardOptions["options"]["includedPurposes"]["enabled"].setValue( True )
		self.assertEqual(
			standardOptions["options"]["includedPurposes"]["value"].getValue(),
			IECore.StringVectorData( [ "default", "render" ] ),
		)
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertIsNone( renderer.capturedObject( "/group/sphere" ) )

		# Should be shown again if we change purpose to one that is included.

		sphereAttributes["attributes"][0]["value"].setValue( "render" )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		# Shouldn't matter if parent has a purpose which is excluded, because local
		# purpose will override that.

		groupAttributes["attributes"].addChild( Gaffer.NameValuePlug( "usd:purpose", "proxy", defaultEnabled = True ) )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

		# Unless there is no local purpose, in which case we inherit the parent
		# purpose and will get hidden.

		sphereAttributes["attributes"][0]["enabled"].setValue( False )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertIsNone( renderer.capturedObject( "/group/sphere" ) )

		# Reverting to no `includedPurposes` option should revert to showing everything.

		standardOptions["options"]["includedPurposes"]["enabled"].setValue( False )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertIsNotNone( renderer.capturedObject( "/group/sphere" ) )

	def testCapsuleRenderOptions( self ) :

		rootFilter = GafferScene.PathFilter()
		rootFilter["paths"].setValue( IECore.StringVectorData( [ "*" ] ) )

		cube = GafferScene.Cube()

		encapsulate = GafferScene.Encapsulate()
		encapsulate["in"].setInput( cube["out"] )
		encapsulate["filter"].setInput( rootFilter["out"] )

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( encapsulate["out"] )
		standardOptions["options"]["includedPurposes"]["enabled"].setValue( True )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( standardOptions["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )

		def assertExpectedRenderOptions() :

			captured = renderer.capturedObject( "/cube" )
			self.assertIsNotNone( captured )
			self.assertEqual( len( captured.capturedSamples() ), 1 )
			self.assertIsInstance( captured.capturedSamples()[0], GafferScene.Capsule )
			self.assertEqual(
				captured.capturedSamples()[0].getRenderOptions(),
				GafferScene.Private.RendererAlgo.RenderOptions( standardOptions["out"] )
			)

		# Check that a capsule has the initial RenderOptions we expect.

		self.assertTrue( controller.updateRequired() )
		controller.update()
		assertExpectedRenderOptions()

		# Check that the capsule is updated when the RenderOptions change.

		standardOptions["options"]["includedPurposes"]["value"].setValue( IECore.StringVectorData( [ "default", "proxy" ] ) )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		assertExpectedRenderOptions()

		# Check that the capsule is not updated when the globals change
		# but the RenderOptions that the capsule uses aren't affected.

		capture = renderer.capturedObject( "/cube" )
		standardOptions["options"]["performanceMonitor"]["enabled"].setValue( True )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertTrue( renderer.capturedObject( "/cube" ).isSame( capture ) )

		# Change RenderOptions again, this time to the default, and check we
		# get another update.

		del capture
		standardOptions["options"]["includedPurposes"]["value"].setValue( IECore.StringVectorData( [ "default", "render", "proxy", "guide" ] ) )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		assertExpectedRenderOptions()

		# Remove `includedPurposes` option, so it's not in the globals. The
		# fallback is the same as the previous value, so we should get no
		# update.

		capture = renderer.capturedObject( "/cube" )
		standardOptions["options"]["includedPurposes"]["enabled"].setValue( False )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertTrue( renderer.capturedObject( "/cube" ).isSame( capture ) )

	def testNoUnnecessaryObjectUpdatesOnPurposeChange( self ) :

		cube = GafferScene.Cube()

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( cube["out"] )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		controller = GafferScene.RenderController( standardOptions["out"], Gaffer.Context(), renderer )
		controller.setMinimumExpansionDepth( 2 )

		# Check initial capture

		self.assertTrue( controller.updateRequired() )
		controller.update()
		capture = renderer.capturedObject( "/cube" )
		self.assertIsNotNone( capture )

		# Check that changing the purposes doesn't make an unnecessary edit for
		# the object. It was included before and it is still included, so we
		# want to reuse the old object.

		standardOptions["options"]["includedPurposes"]["enabled"].setValue( True )
		standardOptions["options"]["includedPurposes"]["value"].setValue( IECore.StringVectorData( [ "default", "proxy" ] ) )
		self.assertTrue( controller.updateRequired() )
		controller.update()
		self.assertTrue( capture.isSame( renderer.capturedObject( "/cube" ) ) )

if __name__ == "__main__":
	unittest.main()
