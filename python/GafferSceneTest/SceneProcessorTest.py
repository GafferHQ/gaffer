##########################################################################
#
#  Copyright (c) 2015, Scene Engine Design Inc. All rights reserved.
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

import inspect
import unittest
import imath

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class SceneProcessorTest( GafferSceneTest.SceneTestCase ) :

	def testNumberOfInputs( self ) :

		n = GafferScene.SceneProcessor()
		self.assertTrue( isinstance( n["in"], GafferScene.ScenePlug ) )

		n = GafferScene.SceneProcessor( minInputs = 2, maxInputs = 2 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertTrue( isinstance( n["in"][0], GafferScene.ScenePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferScene.ScenePlug ) )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), 2 )

		n = GafferScene.SceneProcessor( minInputs = 2, maxInputs = 1000 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertTrue( isinstance( n["in"][0], GafferScene.ScenePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferScene.ScenePlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), 1000 )

		n = GafferScene.SceneProcessor( minInputs = 2 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertTrue( isinstance( n["in"][0], GafferScene.ScenePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferScene.ScenePlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), Gaffer.ArrayPlug().maxSize() )

	def testDeriveAndUseExternalFilters( self ) :

		class MatteAssignment( GafferScene.SceneProcessor ) :

			def __init__( self, name = "MatteAssignment" ) :

				GafferScene.SceneProcessor.__init__( self, name )

				self["__red"] = GafferScene.StandardAttributes()
				self["__red"]["in"].setInput( self["in"] )
				self["__red"]["attributes"].addChild( Gaffer.NameValuePlug( "render:matteColor", imath.Color3f( 1, 0, 0 ) ) )
				self["redFilter"] = self["__red"]["filter"].createCounterpart( "redFilter", Gaffer.Plug.Direction.In )
				self["__red"]["filter"].setInput( self["redFilter"] )

				self["__green"] = GafferScene.StandardAttributes()
				self["__green"]["in"].setInput( self["__red"]["out"] )
				self["__green"]["attributes"].addChild( Gaffer.NameValuePlug( "render:matteColor", imath.Color3f( 0, 1, 0 ) ) )
				self["greenFilter"] = self["__green"]["filter"].createCounterpart( "greenFilter", Gaffer.Plug.Direction.In )
				self["__green"]["filter"].setInput( self["greenFilter"] )

				self["out"].setInput( self["__green"]["out"] )

		IECore.registerRunTimeTyped( MatteAssignment )

		s = GafferScene.Sphere()

		g = GafferScene.Group()
		g["in"][0].setInput( s["out"] )
		g["in"][1].setInput( s["out"] )

		f1 = GafferScene.PathFilter()
		f1["paths"].setValue( IECore.StringVectorData( [ "/group/sphere" ] ) )

		f2 = GafferScene.PathFilter()
		f2["paths"].setValue( IECore.StringVectorData( [ "/group/sphere1" ] ) )

		a = MatteAssignment()
		a["in"].setInput( g["out"] )
		a["redFilter"].setInput( f1["out"] )
		a["greenFilter"].setInput( f2["out"] )

		self.assertEqual( a["out"].attributes( "/group" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/group/sphere" )["render:matteColor"].value, imath.Color3f( 1, 0, 0 ) )
		self.assertEqual( a["out"].attributes( "/group/sphere1" )["render:matteColor"].value, imath.Color3f( 0, 1, 0 ) )

	def testScriptedSubGraph( self ) :

		s = Gaffer.ScriptNode()

		s["plane"] = GafferScene.Plane()

		s["processor"] = GafferScene.SceneProcessor()
		s["processor"]["a"] = GafferScene.StandardAttributes()
		s["processor"]["a"]["in"].setInput( s["processor"]["in"] )
		s["processor"]["a"]["enabled"].setInput( s["processor"]["enabled"] )
		s["processor"]["a"]["attributes"]["visibility"]["enabled"].setValue( True )
		Gaffer.PlugAlgo.promoteWithName( s["processor"]["a"]["attributes"]["visibility"]["value"], name = "visibility" )
		s["processor"]["out"].setInput( s["processor"]["a"]["out"] )
		s["processor"]["in"].setInput( s["plane"]["out"] )

		self.assertEqual( s["processor"]["out"].attributes( "/plane" )["scene:visible"].value, True )
		s["processor"]["visibility"].setValue( False )
		self.assertEqual( s["processor"]["out"].attributes( "/plane" )["scene:visible"].value, False )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["processor"].keys(), s["processor"].keys() )
		self.assertEqual( s2["processor"]["out"].attributes( "/plane" )["scene:visible"].value, False )
		s2["processor"]["visibility"].setValue( True )
		self.assertEqual( s2["processor"]["out"].attributes( "/plane" )["scene:visible"].value, True )

	def testEnabledEvaluationUsesGlobalContext( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()
		script["processor"] = GafferScene.StandardAttributes()
		script["processor"]["in"].setInput( script["plane"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			path = context.get("scene:path", None )
			assert( path is None )
			parent["processor"]["enabled"] = True
			"""
		) )

		with Gaffer.ContextMonitor( script["expression"] ) as monitor :
			self.assertSceneValid( script["processor"]["out"] )

		self.assertEqual( monitor.combinedStatistics().numUniqueValues( "scene:path" ), 0 )

	def testEnabledPlugTypeConversion( self ) :

		plane = GafferScene.Plane()
		string = GafferTest.StringInOutNode()

		processor = GafferScene.StandardAttributes()
		processor["in"].setInput( plane["out"] )
		processor["attributes"]["doubleSided"]["enabled"].setValue( True )
		processor["attributes"]["doubleSided"]["value"].setValue( True )
		processor["enabled"].setInput( string["out"] )

		string["in"].setValue( "" )
		self.assertScenesEqual( processor["in"], processor["out"] )
		self.assertSceneHashesEqual( processor["in"], processor["out"] )

		string["in"].setValue( "x" )
		self.assertNotEqual( processor["in"].attributes( "/plane" ), processor["out"].attributes( "/plane" ) )
		self.assertNotEqual( processor["in"].attributesHash( "/plane" ), processor["out"].attributesHash( "/plane" ) )

if __name__ == "__main__":
	unittest.main()
