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

if __name__ == "__main__":
	unittest.main()
