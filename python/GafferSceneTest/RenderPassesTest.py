##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class RenderPassesTest( GafferSceneTest.SceneTestCase ) :

	testNames = IECore.StringVectorData( [
		"gafferBot_beauty",
		"environment_shadow",
		"cow",
	] )

	def test( self ) :

		plane = GafferScene.Plane()
		passes = GafferScene.RenderPasses()
		passes["in"].setInput( plane["out"] )

		# check that the scene hierarchy is passed through
		self.assertScenesEqual( passes["out"], plane["out"] )

		# check that we can make passes
		passes["names"].setValue( self.testNames )

		g = passes["out"]["globals"].getValue()
		self.assertEqual( len( g ), 1 )
		self.assertEqual( g["option:renderPass:names"], self.testNames )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["passesNode"] = GafferScene.RenderPasses()
		s["passesNode"]["names"].setValue( self.testNames )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		g = s2["passesNode"]["out"]["globals"].getValue()
		self.assertEqual( len( g ), 1 )
		self.assertEqual( g["option:renderPass:names"], self.testNames )

	def testHashPassThrough( self ) :

		# The hash of everything except the globals should be
		# identical to the input, so that they share cache entries.

		plane = GafferScene.Plane()
		passes = GafferScene.RenderPasses()
		passes["in"].setInput( plane["out"] )
		passes["names"].setValue( self.testNames )

		self.assertSceneHashesEqual( plane["out"], passes["out"], checks = self.allSceneChecks - { "globals" } )

	def testDisabled( self ) :

		plane = GafferScene.Plane()
		passes = GafferScene.RenderPasses()
		passes["in"].setInput( plane["out"] )
		passes["names"].setValue( self.testNames )

		self.assertSceneHashesEqual( plane["out"], passes["out"], checks = self.allSceneChecks - { "globals" } )
		self.assertNotEqual( passes["out"]["globals"].hash(), plane["out"]["globals"].hash() )

		passes["enabled"].setValue( False )

		self.assertSceneHashesEqual( plane["out"], passes["out"] )
		self.assertScenesEqual( plane["out"], passes["out"] )

	def testDirtyPropagation( self ) :

		plane = GafferScene.Plane()
		passes = GafferScene.RenderPasses()
		passes["in"].setInput( plane["out"] )

		cs = GafferTest.CapturingSlot( passes.plugDirtiedSignal() )

		plane["dimensions"]["x"].setValue( 100.1 )

		dirtiedPlugs = { x[0] for x in cs if not x[0].getName().startswith( "__" ) }
		self.assertEqual(
			dirtiedPlugs,
			{
				passes["in"]["bound"],
				passes["in"]["childBounds"],
				passes["in"]["object"],
				passes["in"],
				passes["out"]["bound"],
				passes["out"]["childBounds"],
				passes["out"]["object"],
				passes["out"],
			}
		)

	def testDirtyPropagationOnPassAdditionAndRemoval( self ) :

		passes = GafferScene.RenderPasses()
		cs = GafferTest.CapturingSlot( passes.plugDirtiedSignal() )

		passes["names"].setValue( self.testNames )
		self.assertTrue( passes["out"]["globals"] in [ c[0] for c in cs ] )

		del cs[:]
		passes["names"].setValue( IECore.StringVectorData() )
		self.assertTrue( passes["out"]["globals"] in [ c[0] for c in cs ] )

	def testSetsPassThrough( self ) :

		plane = GafferScene.Plane()
		plane["sets"].setValue( "a b" )

		passes = GafferScene.RenderPasses()
		passes["in"].setInput( plane["out"] )

		self.assertEqual( plane["out"]["setNames"].hash(), passes["out"]["setNames"].hash() )
		self.assertTrue( plane["out"]["setNames"].getValue( _copy = False ).isSame( passes["out"]["setNames"].getValue( _copy = False ) ) )

		self.assertEqual( plane["out"].setHash( "a" ), passes["out"].setHash( "b" ) )
		self.assertTrue( plane["out"].set( "a", _copy = False ).isSame( passes["out"].set( "b", _copy = False ) ) )

	def testAppendPasses( self ) :

		passes = GafferScene.RenderPasses()
		passes["names"].setValue( IECore.StringVectorData( [ "a", "b", "c" ] ) )

		self.assertEqual( passes["out"]["globals"].getValue()["option:renderPass:names"], IECore.StringVectorData( [ "a", "b", "c" ] ) )

		passes2 = GafferScene.RenderPasses()
		passes2["names"].setValue( IECore.StringVectorData( [ "d", "e", "f" ] ) )

		self.assertEqual( passes2["out"]["globals"].getValue()["option:renderPass:names"], IECore.StringVectorData( [ "d", "e", "f" ] ) )

		passes2["in"].setInput( passes["out"] )

		self.assertEqual( passes2["out"]["globals"].getValue()["option:renderPass:names"], IECore.StringVectorData( [ "a", "b", "c", "d", "e", "f" ] ) )

		passes3 = GafferScene.RenderPasses()
		passes3["in"].setInput( passes2["out"] )
		passes3["names"].setValue( IECore.StringVectorData( [ "a", "d", "g" ] ) )

		self.assertEqual( passes3["out"]["globals"].getValue()["option:renderPass:names"], IECore.StringVectorData( [ "b", "c", "e", "f", "a", "d", "g" ] ) )

if __name__ == "__main__":
	unittest.main()
