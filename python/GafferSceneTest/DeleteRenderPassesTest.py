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

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class DeleteRenderPassesTest( GafferSceneTest.SceneTestCase ) :

	def testDirtyPropagation( self ) :

		plane = GafferScene.Plane()

		passes = GafferScene.RenderPasses()
		passes["in"].setInput( plane["out"] )
		passes["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		deletePasses = GafferScene.DeleteRenderPasses()
		deletePasses["in"].setInput( passes["out"] )

		cs = GafferTest.CapturingSlot( deletePasses.plugDirtiedSignal() )

		self.assertEqual( deletePasses["mode"].getValue(), GafferScene.DeleteRenderPasses.Mode.Delete )
		deletePasses["mode"].setValue( GafferScene.DeleteRenderPasses.Mode.Keep )

		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )

		self.assertEqual( len(dirtiedPlugs), 3 )
		self.assertTrue( "mode" in dirtiedPlugs )
		self.assertTrue( "out" in dirtiedPlugs )
		self.assertTrue( "out.globals" in dirtiedPlugs )

		cs = GafferTest.CapturingSlot( deletePasses.plugDirtiedSignal() )

		deletePasses["names"].setValue( "tom" )

		dirtiedPlugs = set( [ x[0].relativeName( x[0].node() ) for x in cs ] )
		self.assertEqual( len(dirtiedPlugs), 3 )
		self.assertTrue( "names" in dirtiedPlugs )
		self.assertTrue( "out" in dirtiedPlugs )
		self.assertTrue( "out.globals" in dirtiedPlugs )

	def testDeletePasses( self ) :

		passes = GafferScene.RenderPasses()
		passes["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		deletePasses = GafferScene.DeleteRenderPasses()
		deletePasses["in"].setInput( passes["out"] )

		deletePasses["mode"].setValue( GafferScene.DeleteRenderPasses.Mode.Delete ) # Remove selected passes
		deletePasses["names"].setValue( "dick harry" )

		self.assertEqual( deletePasses["out"]["globals"].getValue()["option:renderPass:names"], IECore.StringVectorData( [ "tom" ] ) )

		deletePasses["names"].setValue( "t* d*" )

		self.assertEqual( deletePasses["out"]["globals"].getValue()["option:renderPass:names"], IECore.StringVectorData( [ "harry" ] ) )

	def testKeepPasses( self ) :

		passes = GafferScene.RenderPasses()
		passes["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		deletePasses = GafferScene.DeleteRenderPasses()
		deletePasses["in"].setInput( passes["out"] )

		deletePasses["mode"].setValue( GafferScene.DeleteRenderPasses.Mode.Keep ) # Keep selected passes
		deletePasses["names"].setValue( "dick harry" )

		self.assertEqual( deletePasses["out"]["globals"].getValue()["option:renderPass:names"], IECore.StringVectorData( [ "dick", "harry" ] ) )

		deletePasses["names"].setValue( "t* d*" )

		self.assertEqual( deletePasses["out"]["globals"].getValue()["option:renderPass:names"], IECore.StringVectorData( [ "tom", "dick" ] ) )

	def testHashChanged( self ) :

		passes = GafferScene.RenderPasses()
		passes["names"].setValue( IECore.StringVectorData( [ "tom", "dick", "harry" ] ) )

		deletePasses = GafferScene.DeleteRenderPasses()
		deletePasses["in"].setInput( passes["out"] )

		deletePasses["mode"].setValue( GafferScene.DeleteRenderPasses.Mode.Keep )
		deletePasses["names"].setValue( " ".join( deletePasses["in"]["globals"].getValue()["option:renderPass:names"] ) )
		h = deletePasses["out"]["globals"].hash()

		deletePasses["names"].setValue( "tom" )
		h2 = deletePasses["out"]["globals"].hash()
		self.assertNotEqual( h, h2 )

	def testModePlug( self ) :

		deletePasses = GafferScene.DeleteRenderPasses()
		self.assertEqual( deletePasses["mode"].defaultValue(), deletePasses.Mode.Delete )
		self.assertEqual( deletePasses["mode"].getValue(), deletePasses.Mode.Delete )

		deletePasses["mode"].setValue( deletePasses.Mode.Keep )
		self.assertEqual( deletePasses["mode"].getValue(), deletePasses.Mode.Keep )

		self.assertEqual( deletePasses["mode"].minValue(), deletePasses.Mode.Delete )
		self.assertEqual( deletePasses["mode"].maxValue(), deletePasses.Mode.Keep )

	def testPassThrough( self ) :

		plane = GafferScene.Plane()

		deletePasses = GafferScene.DeleteRenderPasses()
		deletePasses["in"].setInput( plane["out"] )

		self.assertScenesEqual( plane["out"], deletePasses["out"] )
		self.assertSceneHashesEqual( plane["out"], deletePasses["out"], checks = self.allSceneChecks - { "globals" } )

if __name__ == "__main__":
	unittest.main()
