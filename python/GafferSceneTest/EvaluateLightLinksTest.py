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

		print 'changing set contents'

		lightSet["paths"].setValue( IECore.StringVectorData( [ '/group/group/light' ] ) )

		print evalNode['out'].set(  'lightSet' )

		self.assertEqual(
			set( map( str, evalNode["out"].attributes( "/group/sphere" )[ "linkedLights" ] ) ),
			set( [ "/group/group/light" ] ) )
