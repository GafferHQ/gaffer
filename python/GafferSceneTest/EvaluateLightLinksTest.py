##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class EvaluateLightLinksTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = GafferScene.Sphere( "Sphere" )

		attributes = GafferScene.StandardAttributes()
		attributes["attributes"]["linkedLights"]["enabled"].setValue( True )
		attributes["in"].setInput( sphere["out"] )

		mainGroup = GafferScene.Group( "MainGroup" )
		mainGroup["in"].addChild( GafferScene.ScenePlug( "in1" ) )
		mainGroup["in"].addChild( GafferScene.ScenePlug( "in2" ) )

		light1 = GafferSceneTest.TestLight()
		light2 = GafferSceneTest.TestLight()

		lightGroup = GafferScene.Group( "LightGroup" )
		lightGroup["in"].addChild( GafferScene.ScenePlug( "in1" ) )
		lightGroup["in"].addChild( GafferScene.ScenePlug( "in2" ) )
		lightGroup["in"]["in1"].setInput( light1["out"] )
		lightGroup["in"]["in2"].setInput( light2["out"] )

		mainGroup["in"]["in1"].setInput( attributes["out"] )
		mainGroup["in"]["in2"].setInput( lightGroup["out"] )

		lightSet = GafferScene.Set( "lightSet" )
		lightSet["in"].setInput( mainGroup["out"] )
		lightSet["name"].setValue( 'lightSet' )
		lightSet["paths"].setValue( IECore.StringVectorData( [ '/group/group/light', '/group/group/light1' ] ) )

		evalNode = GafferScene.EvaluateLightLinks()
		evalNode["in"].setInput( lightSet["out"] )

		# Test a single light
		attributes["attributes"]["linkedLights"]["value"].setValue( "/group/group/light" )

		self.assertEqual(
			set( map( str, evalNode["out"].attributes( "/group/sphere" )[ "linkedLights" ] ) ),
			set( [ "/group/group/light" ] ) )

		# Test a simple list of lights
		attributes["attributes"]["linkedLights"]["value"].setValue( "/group/group/light /group/group/light1" )

		self.assertEqual(
			set( map( str, evalNode["out"].attributes( "/group/sphere" )[ "linkedLights" ] ) ),
			set( [ "/group/group/light", "/group/group/light1" ] ) )

		# Make sure only lights come through
		attributes["attributes"]["linkedLights"]["value"].setValue( "/group/group/light /group/group/light1 /group/sphere" )

		self.assertEqual(
			set( map( str, evalNode["out"].attributes( "/group/sphere" )[ "linkedLights" ] ) ),
			set( [ "/group/group/light", "/group/group/light1" ] ) )

		# Make sure changing sets updates the result of the expression evaluation
		attributes["attributes"]["linkedLights"]["value"].setValue( "lightSet" )

		self.assertEqual(
			set( map( str, evalNode["out"].attributes( "/group/sphere" )[ "linkedLights" ] ) ),
			set( [ "/group/group/light", "/group/group/light1" ] ) )

		lightSet["paths"].setValue( IECore.StringVectorData( [ '/group/group/light' ] ) )

		self.assertEqual(
			set( map( str, evalNode["out"].attributes( "/group/sphere" )[ "linkedLights" ] ) ),
			set( [ "/group/group/light" ] ) )

		# Make sure the defaultLights set is treated correctly when no light linking is set by the user
		attributes["attributes"]["linkedLights"]["enabled"].setValue( False )

		# No attributes are assigned if the 'defaultLights' set is equal to '__lights'
		self.assertEqual( evalNode["out"].setHash( "__lights" ), evalNode["out"].setHash( "defaultLights" ) )

		self.assertNotIn( "linkedLights", evalNode["out"].attributes( "/group" ) )
		self.assertNotIn( "linkedLights", evalNode["out"].attributes( "/group/sphere" ) )

		# If the two sets are not equal, the group at root level gets an
		# attribute assigned which is inherited by all children
		light1["defaultLight"].setValue( False )

		self.assertEqual( IECore.StringVectorData( [ "/group/group/light1" ] ), evalNode["out"].attributes( "/group" )["linkedLights"] )
		self.assertNotIn( "linkedLights", evalNode["out"].attributes( "/group/sphere" ) )

	def testHash( self ) :

		sphere = GafferScene.Sphere( "Sphere" )

		standardAttributes = GafferScene.StandardAttributes()
		standardAttributes["in"].setInput( sphere["out"] )

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( standardAttributes["out"] )
		customAttributes["attributes"].addChild( Gaffer.CompoundDataPlug.MemberPlug( "member" ) )
		customAttributes["attributes"]["member"].addChild( Gaffer.StringPlug( "name" ) )
		customAttributes["attributes"]["member"]["name"].setValue( "ai:visibility:shadow_group" )
		customAttributes["attributes"]["member"].addChild( Gaffer.StringPlug( "value" ) )
		customAttributes["attributes"]["member"].addChild( Gaffer.BoolPlug( "enabled" ) )

		sphereGroup = GafferScene.Group()
		sphereGroup["in"].addChild( GafferScene.ScenePlug( "in1" ) )
		sphereGroup["in"]["in1"].setInput( customAttributes["out"] )

		light1 = GafferSceneTest.TestLight()
		light2 = GafferSceneTest.TestLight()

		group = GafferScene.Group()
		group["in"].addChild( GafferScene.ScenePlug( "in1" ) )
		group["in"].addChild( GafferScene.ScenePlug( "in2" ) )
		group["in"].addChild( GafferScene.ScenePlug( "in3" ) )

		group["in"]["in1"].setInput( light1["out"] )
		group["in"]["in2"].setInput( light2["out"] )
		group["in"]["in3"].setInput( sphereGroup["out"] )

		lightSet = GafferScene.Set( "lightSet" )
		lightSet["in"].setInput( group["out"] )
		lightSet["mode"].setValue( 2 )  # Remove
		lightSet["name"].setValue( '__lights' )
		lightSet["paths"].setValue( IECore.StringVectorData( [ '/group/light1' ] ) )
		lightSet["enabled"].setValue( False )

		evalNode = GafferScene.EvaluateLightLinks()
		evalNode["in"].setInput( lightSet["out"] )

		# If the default light set and __lights are the same and no expression
		# has been assigned, the hashes need to match

		self.assertEqual(lightSet["out"].set( "__lights" ), lightSet["out"].set( "defaultLights" ) )

		self.assertEqual( lightSet["out"].attributesHash( "/group/group" ), evalNode["out"].attributesHash( "/group/group" ) )

		self.assertEqual( lightSet["out"].attributesHash( "/group/group/sphere" ), evalNode["out"].attributesHash( "/group/group/sphere" ) )

		# If a shadow linking expression was assigned to the sphere, the
		# attributeHash for the sphere needs to change

		customAttributes["attributes"]["member"]["enabled"].setValue( True )

		evalNodeHash = evalNode["out"].attributesHash( "/group/group/sphere" )  # expression being ""

		self.assertNotEqual( lightSet["out"].attributesHash( "/group/group/sphere" ), evalNodeHash )

		# Changing the expression changes the hash
		customAttributes["attributes"]["member"]["value"].setValue( "/group/light" )

		self.assertNotEqual( lightSet["out"].attributesHash( "/group/group/sphere" ), evalNode["out"].attributesHash( "/group/group/sphere" ) )

		self.assertNotEqual( evalNodeHash, evalNode["out"].attributesHash( "/group/group/sphere" ) )

		customAttributes["attributes"]["member"]["value"].setValue( "" )

		# Changing the __lights set does as well
		lightSet["enabled"].setValue( True )

		self.assertNotEqual( lightSet["out"].attributesHash( "/group/group/sphere" ), evalNode["out"].attributesHash( "/group/group/sphere" ) )

		self.assertNotEqual( evalNodeHash, evalNode["out"].attributesHash( "/group/group/sphere" ) )

		lightSet["enabled"].setValue( False )

		customAttributes["attributes"]["member"]["enabled"].setValue( False )

		# If a light linking expression was assigned to the sphere, the
		# attributeHashes for the sphere can't match

		standardAttributes["attributes"]["linkedLights"]["enabled"].setValue( True )

		evalNodeHash = evalNode["out"].attributesHash( "/group/group/sphere" )  # expression being ""

		self.assertNotEqual( lightSet["out"].attributesHash( "/group/group/sphere" ), evalNodeHash )

		# Changing the expression changes the hash
		standardAttributes["attributes"]["linkedLights"]["value"].setValue( "/group/light" )

		self.assertNotEqual( lightSet["out"].attributesHash( "/group/group/sphere" ), evalNode["out"].attributesHash( "/group/group/sphere" ) )

		self.assertNotEqual( evalNodeHash, evalNode["out"].attributesHash( "/group/group/sphere" ) )

		standardAttributes["attributes"]["linkedLights"]["value"].setValue( "" )

		# Changing the __lights set does as well
		lightSet["enabled"].setValue( True )

		self.assertNotEqual( lightSet["out"].attributesHash( "/group/group/sphere" ), evalNode["out"].attributesHash( "/group/group/sphere" ) )

		self.assertNotEqual( evalNodeHash, evalNode["out"].attributesHash( "/group/group/sphere" ) )

		lightSet["enabled"].setValue( False )

		standardAttributes["attributes"]["linkedLights"]["enabled"].setValue( False )

		# If we remove a light from the defaultLights set, the attributeHash
		# for the sphere's parent at root level needs to change, the sphere's
		# attributeHash needs to stay the same. No expressions are assigned in
		# this test.

		light1["defaultLight"].setValue( False )  # changes defaultLights set

		evalNodeHash = evalNode["out"].attributesHash( "/group" )
		self.assertNotEqual( lightSet["out"].attributesHash( "/group" ), evalNodeHash )

		self.assertEqual( lightSet["out"].attributesHash( "/group/group/sphere" ), evalNode["out"].attributesHash( "/group/group/sphere" ) )

		# Changing the __lights set changes the hash as well
		lightSet["enabled"].setValue( True )

		self.assertNotEqual( lightSet["out"].attributesHash( "/group" ), evalNode["out"].attributesHash( "/group" ) )

		self.assertNotEqual( evalNodeHash, evalNode["out"].attributesHash( "/group" ) )

		lightSet["enabled"].setValue( False )

		light1["defaultLight"].setValue( True )

	def testLightFilterAttribute( self ) :

		# There are not concrete LightFilter nodes in GafferScene. We'll use a
		# sphere as a proxy.
		lightFilter = GafferScene.Sphere( "LightFilter" )
		lightFilter["name"].setValue( "lightFilter" )

		attributes = GafferScene.StandardAttributes()
		attributes["attributes"]["filteredLights"]["enabled"].setValue( True )
		attributes["in"].setInput( lightFilter["out"] )

		mainGroup = GafferScene.Group( "MainGroup" )

		light1 = GafferSceneTest.TestLight()
		light2 = GafferSceneTest.TestLight()

		lightGroup = GafferScene.Group( "LightGroup" )
		lightGroup["in"][0].setInput( light1["out"] )
		lightGroup["in"][1].setInput( light2["out"] )

		mainGroup["in"][0].setInput( attributes["out"] )
		mainGroup["in"][1].setInput( lightGroup["out"] )

		evalNode = GafferScene.EvaluateLightLinks()
		evalNode["in"].setInput( mainGroup["out"] )

		self.assertEqual(
			set( evalNode["out"].attributes( '/group/lightFilter' )["filteredLights"] ),
			set( [] )
		)

		attributes["attributes"]["filteredLights"]["value"].setValue( "defaultLights" )

		self.assertEqual(
			set( evalNode["out"].attributes( '/group/lightFilter' )["filteredLights"] ),
			{ '/group/group/light', '/group/group/light1' }
		)
