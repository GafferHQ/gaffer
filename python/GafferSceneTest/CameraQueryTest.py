#########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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
import GafferScene
import GafferSceneTest

class CameraQueryTest( GafferSceneTest.SceneTestCase ):

	def testDefault( self ) :

		q = GafferScene.CameraQuery()

		self.assertEqual( len( q["queries"].children() ), 0 )
		self.assertEqual( len( q["out"].children() ), 0 )

	def testOutput( self ) :

		query = GafferScene.CameraQuery()

		n1 = query.addQuery( Gaffer.IntPlug() )
		n2 = query.addQuery( Gaffer.Color3fPlug() )
		n3 = query.addQuery( Gaffer.Box2iPlug() )
		badPlug = Gaffer.StringPlug( "missing" )

		self.assertEqual( query.outPlugFromQuery( n1 ), query["out"][0] )
		self.assertEqual( query.outPlugFromQuery( n2 ), query["out"][1] )
		self.assertEqual( query.outPlugFromQuery( n3 ), query["out"][2] )

		self.assertEqual( query.sourcePlugFromQuery( n1 ), query["out"][0]["source"] )
		self.assertEqual( query.sourcePlugFromQuery( n2 ), query["out"][1]["source"] )
		self.assertEqual( query.sourcePlugFromQuery( n3 ), query["out"][2]["source"] )

		self.assertEqual( query.valuePlugFromQuery( n1 ), query["out"][0]["value"] )
		self.assertEqual( query.valuePlugFromQuery( n2 ), query["out"][1]["value"] )
		self.assertEqual( query.valuePlugFromQuery( n3 ), query["out"][2]["value"] )

		self.assertEqual( query.queryPlug( query["out"][0]["value"] ), n1 )
		self.assertEqual( query.queryPlug( query["out"][1]["value"] ), n2 )
		self.assertEqual( query.queryPlug( query["out"][1]["value"]["r"] ), n2 )
		self.assertEqual( query.queryPlug( query["out"][2]["value"] ), n3 )
		self.assertEqual( query.queryPlug( query["out"][2]["value"]["min"] ), n3 )
		self.assertEqual( query.queryPlug( query["out"][2]["value"]["min"]["x"] ), n3 )
		self.assertRaises( IECore.Exception, query.queryPlug, badPlug )

	def testAddRemoveQuery( self ) :

		def checkChildrenCount( plug, count ) :
			self.assertEqual( len( plug["queries"].children() ), count )
			self.assertEqual( len( plug["out"].children() ), count )

		query = GafferScene.CameraQuery()

		checkChildrenCount( query, 0 )

		a = query.addQuery( Gaffer.IntPlug() )
		checkChildrenCount( query, 1 )
		self.assertEqual( query["queries"][0].getValue(), "" )
		self.assertEqual( query["out"][0]["source"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )

		b = query.addQuery( Gaffer.Color3fPlug(), "c" )
		checkChildrenCount( query, 2 )
		self.assertEqual( query["queries"].children(), ( a, b ) )
		self.assertEqual( query["queries"][1].getValue(), "c" )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.Color3fPlug.staticTypeId() )
		for i in range( 0, 2 ) :
			self.assertEqual( query["out"][i]["source"].typeId(), Gaffer.IntPlug.staticTypeId() )

		c = query.addQuery( Gaffer.Box2iPlug(), "b" )
		checkChildrenCount( query, 3 )
		self.assertEqual( query["queries"].children(), ( a, b, c ) )
		self.assertEqual( query["queries"][2].getValue(), "b" )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.Color3fPlug.staticTypeId() )
		self.assertEqual( query["out"][2]["value"].typeId(), Gaffer.Box2iPlug.staticTypeId() )
		for i in range( 0, 3 ) :
			self.assertEqual( query["out"][i]["source"].typeId(), Gaffer.IntPlug.staticTypeId() )

		query.removeQuery( b )
		checkChildrenCount( query, 2 )
		self.assertEqual( query["queries"].children(), ( a, c ) )
		self.assertEqual( query["out"][0]["value"].typeId(), Gaffer.IntPlug.staticTypeId() )
		self.assertEqual( query["out"][1]["value"].typeId(), Gaffer.Box2iPlug.staticTypeId() )
		for i in range( 0, 2 ) :
			self.assertEqual( query["out"][i]["source"].typeId(), Gaffer.IntPlug.staticTypeId() )

		query.removeQuery( c )
		checkChildrenCount( query, 1 )
		query.removeQuery( a )
		checkChildrenCount( query, 0 )

	def testSourceAndValue( self ) :

		camera = GafferScene.Camera()

		parameters = GafferScene.Parameters()
		parameters["in"].setInput( camera["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/camera" ] ) )
		parameters["filter"].setInput( filter["out"] )

		options = GafferScene.StandardOptions()
		options["in"].setInput( parameters["out"] )

		query = GafferScene.CameraQuery()
		query["scene"].setInput( options["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )

		q1 = query.addQuery( Gaffer.V2iPlug(), "resolution" )

		# Resolution not set on camera or in globals, so the query falls back to the default.
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Fallback )
		self.assertEqual( query["out"][0]["value"].getValue(), Gaffer.Metadata.value( "camera:parameter:resolution", "defaultValue" ) )

		# Resolution now set in globals.
		options["options"]["render:resolution"]["enabled"].setValue( True )
		options["options"]["render:resolution"]["value"].setValue( imath.V2i( 512, 256 ) )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Globals )
		self.assertEqual( query["out"][0]["value"].getValue(), imath.V2i( 512, 256 ) )

		# Resolution override on camera.
		camera["renderSettingOverrides"]["resolution"]["enabled"].setValue( True )
		camera["renderSettingOverrides"]["resolution"]["value"].setValue( imath.V2i( 128, 256 ) )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), imath.V2i( 128, 256 ) )

		q2 = query.addQuery( Gaffer.Color3fPlug(), "c1" )
		q3 = query.addQuery( Gaffer.FloatPlug(), "missing" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), imath.V2i( 128, 256 ) )
		# Queries of missing parameters without a registered default have a source of GafferScene.CameraQuery.Source.None_.
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][1]["value"].getValue(), imath.Color3f() )
		self.assertEqual( query["out"][2]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][2]["value"].getValue(), 0.0 )

		# Add parameters, one of which matches one of our queries.
		parameters["parameters"].addChild( Gaffer.NameValuePlug( "c1", IECore.Color3fData( imath.Color3f( 0.5 ) ) ) )
		parameters["parameters"].addChild( Gaffer.NameValuePlug( "c2", IECore.Color3fData( imath.Color3f( 0.75 ) ) ) )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), imath.V2i( 128, 256 ) )
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][1]["value"].getValue(), imath.Color3f( 0.5 ) )
		self.assertEqual( query["out"][2]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][2]["value"].getValue(), 0.0 )

		query.removeQuery( q2 )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), imath.V2i( 128, 256 ) )
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][1]["value"].getValue(), 0.0 )

		q4 = query.addQuery( Gaffer.Color3fPlug(), "c2" )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), imath.V2i( 128, 256 ) )
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][1]["value"].getValue(), 0.0 )
		self.assertEqual( query["out"][2]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][2]["value"].getValue(), imath.Color3f( 0.75 ) )

	def testFallbackValues( self ) :

		camera = GafferScene.Camera()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/camera" ] ) )

		tweaks = GafferScene.CameraTweaks()
		tweaks["in"].setInput( camera["out"] )
		tweaks["filter"].setInput( filter["out"] )

		query = GafferScene.CameraQuery()
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )
		query["scene"].setInput( tweaks["out"] )

		# Use a CameraTweaks to remove all parameters from the camera, exposing the defaults
		for name, plug in [
			( "projection", Gaffer.StringPlug() ),
			( "fStop", Gaffer.FloatPlug() ),
			( "aperture", Gaffer.V2fPlug() ),
			( "apertureOffset", Gaffer.V2fPlug() ),
			( "clippingPlanes", Gaffer.V2fPlug() ),
			( "focalLength", Gaffer.FloatPlug() ),
			( "focalLengthWorldScale", Gaffer.FloatPlug() ),
			( "focusDistance", Gaffer.FloatPlug() )
		] :
			tweaks["tweaks"].addChild( Gaffer.TweakPlug( plug, name ) )
			tweaks["tweaks"][name]["name"].setValue( name )
			tweaks["tweaks"][name]["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )

			query.addQuery( plug, name )

		# Test our queries, they should all report a GafferScene.CameraQuery.Source.Fallback source, with a value matching
		# our metadata and the camera default.
		for plug in query["out"].children() :
			parameter = query.queryPlug( plug ).getValue()
			c = query["scene"].object( "/camera" )
			with self.subTest( parameter = parameter ) :
				self.assertEqual( plug["source"].getValue(), GafferScene.CameraQuery.Source.Fallback )
				self.assertEqual( plug["value"].getValue(), Gaffer.Metadata.value( f"camera:parameter:{parameter}", "defaultValue" ) )
				self.assertEqual( plug["value"].getValue(), getattr( c, f"get{parameter[0].capitalize() + parameter[1:]}" )() )

		# Disable the CameraTweaks and ensure our queries are finding the camera parameters.
		tweaks["enabled"].setValue( False )
		for plug in query["out"].children() :
			parameter = query.queryPlug( plug ).getValue()
			c = query["scene"].object( "/camera" )
			with self.subTest( parameter = parameter ) :
				self.assertEqual( plug["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
				self.assertEqual( plug["value"].getValue(), getattr( c, f"get{parameter[0].capitalize() + parameter[1:]}" )() )

	def testShutterQuery( self ) :

		camera = GafferScene.Camera()

		options = GafferScene.StandardOptions()
		options["in"].setInput( camera["out"] )

		query = GafferScene.CameraQuery()
		query["scene"].setInput( options["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )

		q1 = query.addQuery( Gaffer.V2fPlug(), "shutter" )

		# Shutter not set so we return the default shutter for the camera
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Fallback )
		self.assertEqual( query["out"][0]["value"].getValue(), Gaffer.Metadata.value( "camera:parameter:shutter", "defaultValue" ) )

		# Shutter set in globals
		options["options"]["render:shutter"]["enabled"].setValue( True )
		options["options"]["render:shutter"]["value"].setValue( imath.V2f( -0.1, 0.2 ) )

		# Ensure this remains a relative shutter value, as this would ordinarily
		# be converted into an absolute shutter by SceneAlgo::applyCameraGlobals().
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Globals )
		self.assertEqual( query["out"][0]["value"].getValue(), imath.V2f( -0.1, 0.2 ) )

		# Shutter override on camera
		camera["renderSettingOverrides"]["shutter"]["enabled"].setValue( True )
		camera["renderSettingOverrides"]["shutter"]["value"].setValue( imath.V2f( -0.2, 0.4 ) )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), imath.V2f( -0.2, 0.4 ) )

	def testFStopQuery( self ) :

		camera = GafferScene.Camera()

		options = GafferScene.StandardOptions()
		options["in"].setInput( camera["out"] )

		tweaks = GafferScene.CameraTweaks()
		tweaks["in"].setInput( options["out"] )

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/camera" ] ) )
		tweaks["filter"].setInput( filter["out"] )

		query = GafferScene.CameraQuery()
		query["scene"].setInput( tweaks["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )

		q1 = query.addQuery( Gaffer.FloatPlug(), "fStop" )

		# fStop set from camera
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), camera["fStop"].getValue() )

		# Disable depthOfField in globals, ensure this doesn't affect the fStop query as this
		# would ordinarily be baked into a 0.0 fStop by SceneAlgo::applyCameraGlobals().
		options["options"]["render:depthOfField"]["enabled"].setValue( True )
		options["options"]["render:depthOfField"]["value"].setValue( False )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), camera["fStop"].getValue() )

		# Remove fStop parameter from camera, this should result in the query falling back
		# to the default value.
		tweaks["tweaks"].addChild( Gaffer.TweakPlug( "fStop", 5.6 ) )
		tweaks["tweaks"]["tweak"]["mode"].setValue( Gaffer.TweakPlug.Mode.Remove )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Fallback )
		self.assertEqual( query["out"][0]["value"].getValue(), Gaffer.Metadata.value( "camera:parameter:fStop", "defaultValue" ) )

	def testCameraMode( self ) :

		camera = GafferScene.Camera()
		camera["fStop"].setValue( 3.5 )

		camera2 = GafferScene.Camera()
		camera2["name"].setValue( "otherCamera" )
		camera2["fStop"].setValue( 7.0 )

		parent = GafferScene.Parent()
		parent["in"].setInput( camera["out"] )
		parent["parent"].setValue( "/" )
		parent["children"][0].setInput( camera2["out"] )

		standardOptions = GafferScene.StandardOptions()
		standardOptions["in"].setInput( parent["out"] )

		query = GafferScene.CameraQuery()
		query["scene"].setInput( standardOptions["out"] )
		q1 = query.addQuery( Gaffer.FloatPlug(), "fStop" )

		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), 0.0 )

		self.assertNotIn( "option:render:camera", query["scene"].globals() )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.RenderCamera )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), 0.0 )

		standardOptions["options"]["render:camera"]["enabled"].setValue( True )
		standardOptions["options"]["render:camera"]["value"].setValue( "" )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), 0.0 )

		standardOptions["options"]["render:camera"]["value"].setValue( "/camera" )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), 3.5 )

		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), 0.0 )

		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.RenderCamera )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), 3.5 )

		standardOptions["options"]["render:camera"]["value"].setValue( "/otherCamera" )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), 7.0 )

		standardOptions["options"]["render:camera"]["value"].setValue( "/notACamera" )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), 0.0 )

		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), 0.0 )

		query["location"].setValue( "/camera" )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), 3.5 )

		query["location"].setValue( "/otherCamera" )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), 7.0 )

		query["location"].setValue( "/notACamera" )
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), 0.0 )

	def testComputedValues( self ) :

		camera = GafferScene.Camera()

		options = GafferScene.StandardOptions()
		options["in"].setInput( camera["out"] )

		query = GafferScene.CameraQuery()
		query["scene"].setInput( options["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )

		q1 = query.addQuery( Gaffer.FloatPlug(), "fieldOfView" )
		q2 = query.addQuery( Gaffer.Box2fPlug(), "frustum" )
		q3 = query.addQuery( Gaffer.FloatPlug(), "apertureAspectRatio" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), camera["out"].object( "/camera" ).calculateFieldOfView()[0] )
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][1]["value"].getValue(), camera["out"].object( "/camera" ).frustum() )
		self.assertEqual( query["out"][2]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][2]["value"].getValue(), 1.0 )

		camera["fieldOfView"].setValue( 24 )

		self.assertEqual( query["out"][0]["value"].getValue(), camera["out"].object( "/camera" ).calculateFieldOfView()[0] )
		self.assertEqual( query["out"][1]["value"].getValue(), camera["out"].object( "/camera" ).frustum() )
		self.assertEqual( query["out"][2]["value"].getValue(), 1.0 )

		camera["apertureAspectRatio"].setValue( 2.0 )

		self.assertEqual( query["out"][0]["value"].getValue(), camera["out"].object( "/camera" ).calculateFieldOfView()[0] )
		self.assertEqual( query["out"][1]["value"].getValue(), camera["out"].object( "/camera" ).frustum() )
		self.assertEqual( query["out"][2]["value"].getValue(), 2.0 )

		# The frustum is dependent on the resolution, filmFit and pixelAspectRatio
		options["options"]["render:resolution"]["enabled"].setValue( True )
		options["options"]["render:resolution"]["value"].setValue( imath.V2i( 1024, 512 ) )
		options["options"]["render:filmFit"]["enabled"].setValue( True )
		options["options"]["render:filmFit"]["value"].setValue( 1 )
		options["options"]["render:pixelAspectRatio"]["enabled"].setValue( True )
		options["options"]["render:pixelAspectRatio"]["value"].setValue( 2.0 )

		self.assertNotEqual( query["out"][1]["value"].getValue(), camera["out"].object( "/camera" ).frustum() )
		cameraWithGlobals = camera["out"].object( "/camera" )
		GafferScene.SceneAlgo.applyCameraGlobals( cameraWithGlobals, query["scene"].globals(), query["scene"] )
		self.assertEqual( query["out"][1]["value"].getValue(), cameraWithGlobals.frustum() )

		query["location"].setValue( "/notACamera" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), query["out"][0]["value"].defaultValue() )
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][1]["value"].getValue(), query["out"][1]["value"].defaultValue() )
		self.assertEqual( query["out"][2]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][2]["value"].getValue(), query["out"][2]["value"].defaultValue() )

	def testChangeParameterValue( self ) :

		camera = GafferScene.Camera()

		query = GafferScene.CameraQuery()
		query["scene"].setInput( camera["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )

		q1 = query.addQuery( Gaffer.FloatPlug(), "fStop" )
		q2 = query.addQuery( Gaffer.V2fPlug(), "clippingPlanes" )
		q3 = query.addQuery( Gaffer.StringPlug(), "projection" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), camera["fStop"].getValue() )
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][1]["value"].getValue(), camera["clippingPlanes"].getValue() )
		self.assertEqual( query["out"][2]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][2]["value"].getValue(), camera["projection"].getValue() )

		camera["fStop"].setValue( 11.1 )
		camera["clippingPlanes"].setValue( imath.V2f( 11, 111 ) )
		camera["projection"].setValue( "orthographic" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), camera["fStop"].getValue() )
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][1]["value"].getValue(), camera["clippingPlanes"].getValue() )
		self.assertEqual( query["out"][2]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][2]["value"].getValue(), camera["projection"].getValue() )

	def testNonCameraObject( self ) :

		plane = GafferScene.Plane()

		query = GafferScene.CameraQuery()
		query["scene"].setInput( plane["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/plane" )

		query.addQuery( Gaffer.FloatPlug(), "focalLength" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), 0.0 )

	def testSerialisation( self ) :

		camera = GafferScene.Camera()

		camera["fStop"].setValue( 2.0 )
		camera["clippingPlanes"].setValue( imath.V2f( 3.0, 4.0 ) )
		camera["projection"].setValue( "orthographic" )

		query = GafferScene.CameraQuery()
		query["scene"].setInput( camera["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )

		q1 = query.addQuery( Gaffer.FloatPlug(), "fStop" )
		q2 = query.addQuery( Gaffer.V2fPlug(), "clippingPlanes" )
		q3 = query.addQuery( Gaffer.StringPlug(), "projection" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), 2.0 )
		self.assertEqual( query["out"][1]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][1]["value"].getValue(), imath.V2f( 3.0, 4.0 ) )
		self.assertEqual( query["out"][2]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][2]["value"].getValue(), "orthographic" )

		target = GafferScene.CustomOptions( "target" )
		target["options"].addChild( Gaffer.NameValuePlug( "f", IECore.FloatData( 3.0 ), "f", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		target["options"].addChild( Gaffer.NameValuePlug( "c", IECore.V2fData( imath.V2f( 5.0 ) ), "c", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		target["options"].addChild( Gaffer.NameValuePlug( "p", IECore.StringData( "unset" ), "p", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		target["options"].addChild( Gaffer.NameValuePlug( "s", IECore.IntData( 0 ), "s", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		target["options"]["f"]["value"].setInput( query["out"][0]["value"] )
		target["options"]["c"]["value"].setInput( query["out"][1]["value"] )
		target["options"]["p"]["value"].setInput( query["out"][2]["value"] )
		target["options"]["s"]["value"].setInput( query["out"][0]["source"] )

		scriptNode = Gaffer.ScriptNode()
		scriptNode.addChild( camera )
		scriptNode.addChild( query )
		scriptNode.addChild( target )

		self.assertTrue( scriptNode["CameraQuery"]["out"][0]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][0]["value"].getValue(), 2.0 )
		self.assertTrue( scriptNode["CameraQuery"]["out"][1]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][1]["value"].getValue(), imath.V2f( 3.0, 4.0 ) )
		self.assertTrue( scriptNode["CameraQuery"]["out"][2]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][2]["value"].getValue(), "orthographic" )
		self.assertEqual( scriptNode["target"]["options"]["f"]["value"].getInput(), query["out"][0]["value"] )
		self.assertEqual( scriptNode["target"]["options"]["c"]["value"].getInput(), query["out"][1]["value"] )
		self.assertEqual( scriptNode["target"]["options"]["p"]["value"].getInput(), query["out"][2]["value"] )
		self.assertEqual( scriptNode["target"]["options"]["s"]["value"].getInput(), query["out"][0]["source"] )

		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		self.assertTrue( scriptNode["CameraQuery"]["out"][0]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][0]["value"].getValue(), 2.0 )
		self.assertTrue( scriptNode["CameraQuery"]["out"][1]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][1]["value"].getValue(), imath.V2f( 3.0, 4.0 ) )
		self.assertTrue( scriptNode["CameraQuery"]["out"][2]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][2]["value"].getValue(), "orthographic" )
		self.assertEqual( str( scriptNode["target"]["options"]["f"]["value"].getInput() ), str( query["out"][0]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["c"]["value"].getInput() ), str( query["out"][1]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["p"]["value"].getInput() ), str( query["out"][2]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["s"]["value"].getInput() ), str( query["out"][0]["source"] ) )

		scriptNode["CameraQuery"].removeQuery( scriptNode["CameraQuery"]["queries"][0] )

		self.assertTrue( scriptNode["CameraQuery"]["out"][0]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][0]["value"].getValue(), imath.V2f( 3.0, 4.0 ) )
		self.assertTrue( scriptNode["CameraQuery"]["out"][1]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][1]["value"].getValue(), "orthographic" )
		self.assertIsNone( scriptNode["target"]["options"]["f"]["value"].getInput() )
		self.assertIsNone( scriptNode["target"]["options"]["s"]["value"].getInput() )
		self.assertEqual( str( scriptNode["target"]["options"]["c"]["value"].getInput() ), str( query["out"][1]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["p"]["value"].getInput() ), str( query["out"][2]["value"] ) )

		serialised = scriptNode.serialise()

		scriptNode = Gaffer.ScriptNode()
		scriptNode.execute( serialised )

		self.assertTrue( scriptNode["CameraQuery"]["out"][0]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][0]["value"].getValue(), imath.V2f( 3.0, 4.0 ) )
		self.assertTrue( scriptNode["CameraQuery"]["out"][1]["source"].getValue() )
		self.assertEqual( scriptNode["CameraQuery"]["out"][1]["value"].getValue(), "orthographic" )
		self.assertIsNone( scriptNode["target"]["options"]["f"]["value"].getInput() )
		self.assertIsNone( scriptNode["target"]["options"]["s"]["value"].getInput() )
		self.assertEqual( str( scriptNode["target"]["options"]["c"]["value"].getInput() ), str( query["out"][1]["value"] ) )
		self.assertEqual( str( scriptNode["target"]["options"]["p"]["value"].getInput() ), str( query["out"][2]["value"] ) )

	def testObjectPlugQuery( self ) :

		camera = GafferScene.Camera()

		query = GafferScene.CameraQuery()
		query["scene"].setInput( camera["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )

		camera["clippingPlanes"].setValue( imath.V2f( 1, 10 ) )

		query.addQuery( Gaffer.ObjectPlug( defaultValue = IECore.NullObject.defaultNullObject() ), "clippingPlanes" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), IECore.V2fData( imath.V2f( 1, 10 ) ) )

		camera["clippingPlanes"].setValue( imath.V2f( 2, 20 ) )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), IECore.V2fData( imath.V2f( 2, 20 ) ) )

		query["queries"][0].setValue( "invalid" )

		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.None_ )
		self.assertEqual( query["out"][0]["value"].getValue(), IECore.NullObject.defaultNullObject() )

	def testMismatchedTypes( self ) :

		camera = GafferScene.Camera()

		query = GafferScene.CameraQuery()
		query["scene"].setInput( camera["out"] )
		query["cameraMode"].setValue( GafferScene.CameraQuery.CameraMode.Location )
		query["location"].setValue( "/camera" )
		query.addQuery( Gaffer.StringPlug(), "focalLength" )

		# "focalLength" exists on the camera, so we return the correct source
		# even if the query is of a mismatched type.
		self.assertEqual( query["out"][0]["source"].getValue(), GafferScene.CameraQuery.Source.Camera )
		self.assertEqual( query["out"][0]["value"].getValue(), "" )

if __name__ == "__main__":
	unittest.main()
