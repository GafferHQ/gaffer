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

import os
import unittest
import imath

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class OutputsTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()
		outputs = GafferScene.Outputs()
		outputs["in"].setInput( p["out"] )

		# check that the scene hierarchy is passed through

		self.assertEqual( outputs["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( outputs["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( outputs["out"].bound( "/" ), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( outputs["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )

		self.assertEqual( outputs["out"].object( "/plane" ), IECoreScene.MeshPrimitive.createPlane( imath.Box2f( imath.V2f( -0.5 ), imath.V2f( 0.5 ) ) ) )
		self.assertEqual( outputs["out"].transform( "/plane" ), imath.M44f() )
		self.assertEqual( outputs["out"].bound( "/plane" ), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( outputs["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )

		# check that we have some outputs

		output = outputs.addOutput( "beauty", IECoreScene.Output( "beauty.exr", "exr", "rgba" ) )
		output["parameters"].addChild( Gaffer.NameValuePlug( "test", IECore.FloatData( 10 ) ) )

		outputs.addOutput( "diffuse", IECoreScene.Output( "diffuse.exr", "exr", "color aov_diffuse" ) )

		g = outputs["out"]["globals"].getValue()
		self.assertEqual( len( g ), 2 )
		self.assertEqual( g["output:beauty"], IECoreScene.Output( "beauty.exr", "exr", "rgba", { "test" : 10.0 } ) )
		self.assertEqual( g["output:diffuse"], IECoreScene.Output( "diffuse.exr", "exr", "color aov_diffuse" ) )

		# check that we can turn 'em off as well
		output["active"].setValue( False )

		g = outputs["out"]["globals"].getValue()
		self.assertEqual( len( g ), 1 )
		self.assertEqual( g["output:diffuse"], IECoreScene.Output( "diffuse.exr", "exr", "color aov_diffuse" ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["outputsNode"] = GafferScene.Outputs()
		output = s["outputsNode"].addOutput( "beauty", IECoreScene.Output( "beauty.exr", "exr", "rgba" ) )
		output["parameters"].addChild( Gaffer.NameValuePlug( "test", IECore.FloatData( 10 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		g = s2["outputsNode"]["out"]["globals"].getValue()
		self.assertEqual( len( g ), 1 )
		self.assertEqual( g["output:beauty"], IECoreScene.Output( "beauty.exr", "exr", "rgba", { "test" : 10.0 } ) )
		self.assertEqual( len( s2["outputsNode"]["outputs"] ), 1 )
		self.assertTrue( "outputs1" not in s2["outputsNode"] )

	def testRegistry( self ) :

		preExistingOutputs = GafferScene.Outputs.registeredOutputs()

		GafferScene.Outputs.registerOutput( "test", IECoreScene.Output( "test.exr", "exr", "rgba" ) )
		GafferScene.Outputs.registerOutput( "test2", IECoreScene.Output( "test.exr", "exr", "rgba" ) )

		self.assertEqual( GafferScene.Outputs.registeredOutputs(), preExistingOutputs + ( "test", "test2" ) )

		o = GafferScene.Outputs()
		p = o.addOutput( "test" )
		self.assertEqual( p["name"].getValue(), "test" )
		self.assertEqual( p["fileName"].getValue(), "test.exr" )
		self.assertEqual( p["data"].getValue(), "rgba" )

		GafferScene.Outputs.deregisterOutput( "test" )
		self.assertEqual( GafferScene.Outputs.registeredOutputs(), preExistingOutputs + ( "test2", ) )

		o = GafferScene.Outputs()
		with self.assertRaisesRegex( RuntimeError, "Output not registered" ) :
			o.addOutput( "test" )

		GafferScene.Outputs.deregisterOutput( "test2" )
		self.assertEqual( GafferScene.Outputs.registeredOutputs(), preExistingOutputs )

	def testHashPassThrough( self ) :

		# the hash of the per-object part of the output should be
		# identical to the input, so that they share cache entries.

		p = GafferScene.Plane()
		outputs = GafferScene.Outputs()
		outputs["in"].setInput( p["out"] )

		self.assertSceneHashesEqual( p["out"], outputs["out"], checks = self.allSceneChecks - { "globals" } )

	def testParametersHaveUsefulNames( self ) :

		outputs = GafferScene.Outputs()
		outputs.addOutput( "test", IECoreScene.Output( "name", "type", "data", { "paramA" : 1, "paramB" : 2 } ) )

		self.assertEqual( set( outputs["outputs"][0]["parameters"].keys() ), set( [ "paramA", "paramB" ] ) )

	def testDirtyPropagation( self ) :

		outputs = GafferScene.Outputs()
		cs = GafferTest.CapturingSlot( outputs.plugDirtiedSignal() )

		p = outputs.addOutput( "test", IECoreScene.Output( "name", "type", "data", { "paramA" : 1, "paramB" : 2 } ) )
		self.assertTrue( outputs["out"]["globals"] in [ c[0] for c in cs ] )

		del cs[:]
		p["name"].setValue( "newName" )
		self.assertTrue( outputs["out"]["globals"] in [ c[0] for c in cs ] )

		del cs[:]
		outputs["outputs"].removeChild( p )
		self.assertTrue( outputs["out"]["globals"] in [ c[0] for c in cs ] )

	def testColonInParameterName( self ) :

		output = IECoreScene.Output( "name", "type", "data", { "test:paramA" : 1 } )

		outputs = GafferScene.Outputs()
		outputs.addOutput( "test", output )
		self.assertTrue( "test_paramA" in outputs["outputs"][0]["parameters"] )

		self.assertEqual( outputs["out"]["globals"].getValue()["output:test"], output )

if __name__ == "__main__":
	unittest.main()
