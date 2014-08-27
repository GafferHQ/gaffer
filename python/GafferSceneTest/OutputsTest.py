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

import IECore

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
		self.assertEqual( outputs["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( outputs["out"].bound( "/" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( outputs["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )

		self.assertEqual( outputs["out"].object( "/plane" ), IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -0.5 ), IECore.V2f( 0.5 ) ) ) )
		self.assertEqual( outputs["out"].transform( "/plane" ), IECore.M44f() )
		self.assertEqual( outputs["out"].bound( "/plane" ), IECore.Box3f( IECore.V3f( -0.5, -0.5, 0 ), IECore.V3f( 0.5, 0.5, 0 ) ) )
		self.assertEqual( outputs["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )

		# check that we have some outputs

		output = outputs.addOutput( "beauty", IECore.Display( "beauty.exr", "exr", "rgba" ) )
		output["parameters"].addMember( "test", IECore.FloatData( 10 ) )

		outputs.addOutput( "diffuse", IECore.Display( "diffuse.exr", "exr", "color aov_diffuse" ) )

		g = outputs["out"]["globals"].getValue()
		self.assertEqual( len( g ), 2 )
		self.assertEqual( g["output:beauty"], IECore.Display( "beauty.exr", "exr", "rgba", { "test" : 10.0 } ) )
		self.assertEqual( g["output:diffuse"], IECore.Display( "diffuse.exr", "exr", "color aov_diffuse" ) )

		# check that we can turn 'em off as well
		output["active"].setValue( False )

		g = outputs["out"]["globals"].getValue()
		self.assertEqual( len( g ), 1 )
		self.assertEqual( g["output:diffuse"], IECore.Display( "diffuse.exr", "exr", "color aov_diffuse" ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["outputsNode"] = GafferScene.Outputs()
		output = s["outputsNode"].addOutput( "beauty", IECore.Display( "beauty.exr", "exr", "rgba" ) )
		output["parameters"].addMember( "test", IECore.FloatData( 10 ) )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		g = s2["outputsNode"]["out"]["globals"].getValue()
		self.assertEqual( len( g ), 1 )
		self.assertEqual( g["output:beauty"], IECore.Display( "beauty.exr", "exr", "rgba", { "test" : 10.0 } ) )
		self.assertEqual( len( s2["outputsNode"]["outputs"] ), 1 )
		self.assertTrue( "outputs1" not in s2["outputsNode"] )

	def testRegistry( self ) :

		GafferScene.Outputs.registerOutput( "test", IECore.Display( "test.exr", "exr", "rgba" ) )
		GafferScene.Outputs.registerOutput( "test2", IECore.Display( "test.exr", "exr", "rgba" ) )

		self.assertEqual( GafferScene.Outputs.registeredOutputs(), ( "test", "test2" ) )

	def testHashPassThrough( self ) :

		# the hash of the per-object part of the output should be
		# identical to the input, so that they share cache entries.

		p = GafferScene.Plane()
		outputs = GafferScene.Outputs()
		outputs["in"].setInput( p["out"] )

		self.assertSceneHashesEqual( p["out"], outputs["out"], childPlugNames = ( "transform", "bound", "attributes", "object", "childNames" ) )

	def testParametersHaveUsefulNames( self ) :

		outputs = GafferScene.Outputs()
		outputs.addOutput( "test", IECore.Display( "name", "type", "data", { "paramA" : 1, "paramB" : 2 } ) )

		self.assertEqual( set( outputs["outputs"][0]["parameters"].keys() ), set( [ "paramA", "paramB" ] ) )

	def testDirtyPropagation( self ) :

		outputs = GafferScene.Outputs( "outputs" )
		cs = GafferTest.CapturingSlot( outputs.plugDirtiedSignal() )

		outputs.addOutput( "test", IECore.Display( "name", "type", "data", { "paramA" : 1, "paramB" : 2 } ) )
		self.assertTrue( "outputs.out.globals" in set( e[0].fullName() for e in cs ) )

	def testBackwardsCompatibility( self ) :

		script = Gaffer.ScriptNode()
		script["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/displaysBeforePlugRename.gfr" )
		script.load()

		with script.context() :
			g = script["Displays"]["out"]["globals"].getValue()

		self.assertTrue( "output:Batch/Beauty" in g )
		self.assertTrue( "output:Interactive/Beauty" in g )
		self.assertEqual( g["output:Interactive/Beauty"].getName(), "beauty" )
		self.assertTrue( g["output:Batch/Beauty"].getName().endswith( "displaysBeforePlugRename/beauty/beauty.0001.exr" ) )

if __name__ == "__main__":
	unittest.main()
