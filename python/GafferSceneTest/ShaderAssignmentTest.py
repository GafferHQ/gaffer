##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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
import os
import subprocess
import unittest

import IECore
import IECoreScene

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest
import GafferDispatch

class ShaderAssignmentTest( GafferSceneTest.SceneTestCase ) :

	def testFilter( self ) :

		sphere = IECoreScene.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"ball1" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
					"ball2" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
				},
			} )
		)

		a = GafferScene.ShaderAssignment()
		a["in"].setInput( input["out"] )

		s = GafferSceneTest.TestShader()
		s["type"].setValue( "test:surface" )
		a["shader"].setInput( s["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/ball1" ] ) )
		a["filter"].setInput( f["out"] )

		self.assertEqual( a["out"].attributes( "/" ), IECore.CompoundObject() )
		self.assertNotEqual( a["out"].attributes( "/ball1" ), IECore.CompoundObject() )
		self.assertEqual( a["out"].attributes( "/ball2" ), IECore.CompoundObject() )

	def testFilterInputAcceptance( self ) :

		a = GafferScene.ShaderAssignment()

		f = GafferScene.PathFilter()
		self.assertTrue( a["filter"].acceptsInput( f["out"] ) )

		n = GafferTest.AddNode()
		self.assertFalse( a["filter"].acceptsInput( n["sum"] ) )

	def testAssignShaderFromOutsideBox( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["s"] = GafferSceneTest.TestShader()
		s["s"]["type"].setValue( "test:surface" )
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["p"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		s["o"] = GafferScene.Options()
		s["o"]["in"].setInput( s["a"]["out"] )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["p"], s["a"] ] ) )

		self.assertTrue( "test:surface" in s["o"]["out"].attributes( "/plane" ) )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

		self.assertTrue( s["Box"]["a"]["shader"].getInput().isSame( s["Box"]["shader"] ) )

	def testDisabled( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()
		s["s"] = GafferSceneTest.TestShader()
		s["s"]["type"].setValue( "test:surface" )
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["p"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		self.assertTrue( "test:surface" in s["a"]["out"].attributes( "/plane" ) )

		s["a"]["enabled"].setValue( False )

		self.assertTrue( "test:surface" not in s["a"]["out"].attributes( "/plane" ) )

	def testAssignDisabledShader( self ) :

		s = Gaffer.ScriptNode()

		s["p"] = GafferScene.Plane()

		s["s"] = GafferSceneTest.TestShader()
		s["s"]["name"].setValue( "test" )
		s["s"]["type"].setValue( "test:surface" )

		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["in"].setInput( s["p"]["out"] )
		s["a"]["shader"].setInput( s["s"]["out"] )

		self.assertTrue( "test:surface" in s["a"]["out"].attributes( "/plane" ) )
		self.assertEqual( s["a"]["out"].attributes( "/plane" )["test:surface"].outputShader().name, "test" )

		s["s2"] = GafferSceneTest.TestShader()
		s["s2"]["name"].setValue( "test2" )
		s["s2"]["type"].setValue( "test:surface" )

		s["a2"] = GafferScene.ShaderAssignment()
		s["a2"]["in"].setInput( s["a"]["out"] )
		s["a2"]["shader"].setInput( s["s2"]["out"] )

		self.assertTrue( "test:surface" in s["a"]["out"].attributes( "/plane" ) )
		self.assertEqual( s["a2"]["out"].attributes( "/plane" )["test:surface"].outputShader().name, "test2" )

		s["s2"]["enabled"].setValue( False )

		self.assertTrue( "test:surface" in s["a"]["out"].attributes( "/plane" ) )
		self.assertEqual( s["a2"]["out"].attributes( "/plane" )["test:surface"].outputShader().name, "test" )

	def testInputAcceptanceInsideBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = GafferSceneTest.TestShader()
		s["n"] = Gaffer.Node()
		s["n"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["a"] = GafferScene.ShaderAssignment()

		# the shader assignment shouldn't accept inputs from any old
		# node - it should be a shader node.

		self.assertTrue( s["a"]["shader"].acceptsInput( s["s"]["out"] ) )
		self.assertFalse( s["a"]["shader"].acceptsInput( s["n"]["out"] ) )

		# and that shouldn't change just because we happen to be inside a box

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["s"], s["n"], s["a"] ] ) )

		self.assertTrue( b["a"]["shader"].acceptsInput( b["s"]["out"] ) )
		self.assertFalse( b["a"]["shader"].acceptsInput( b["n"]["out"] ) )

	def testInputAcceptanceFromBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["a"] = GafferScene.ShaderAssignment()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["a"] = GafferScene.ShaderAssignment()
		s["b"]["n"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		# This emulates old plugs which were promoted when the "shader" plug on a ShaderAssignment
		# was just a plain Plug rather than a ShaderPlug.
		s["b"]["in"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["out"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, direction = Gaffer.Plug.Direction.Out )

		# Shader assignments should accept connections speculatively
		# from unconnected box inputs and outputs. We use `execute()` for
		# this because the backwards compatibility is provided only when
		# a script is loading.

		s.execute( """script["b"]["a"]["shader"].setInput( script["b"]["in"] )""" )
		s.execute( """script["a"]["shader"].setInput( script["b"]["out"] )""" )

		# but should reject connections to connected box inputs and outputs
		# if they're unsuitable.

		s["b"]["a"]["shader"].setInput( None )
		s["b"]["in"].setInput( s["n"]["out"] )
		self.assertFalse( s["b"]["a"]["shader"].acceptsInput( s["b"]["in"] ) )

		s["a"]["shader"].setInput( None )
		s["b"]["out"].setInput( s["b"]["n"]["out"] )
		self.assertFalse( s["a"]["shader"].acceptsInput( s["b"]["out"] ) )

		# and accept them again if they provide indirect access to a shader

		s["s"] = GafferSceneTest.TestShader()
		s["b"]["in"].setInput( s["s"]["out"] )
		self.assertTrue( s["b"]["a"]["shader"].acceptsInput( s["b"]["in"] ) )

		s["b"]["s"] = GafferSceneTest.TestShader()
		s["b"]["out"].setInput( s["b"]["s"]["out"] )
		self.assertTrue( s["a"]["shader"].acceptsInput( s["b"]["out"] ) )

	def testRejectInputsToBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		s["s"] = GafferSceneTest.TestShader()

		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferScene.ShaderAssignment()
		p = Gaffer.PlugAlgo.promote( s["b"]["a"]["shader"] )

		self.assertFalse( p.acceptsInput( s["n"]["out"] ) )
		self.assertTrue( p.acceptsInput( s["s"]["out"] ) )

	def testInputAcceptanceFromSwitches( self ) :

		script = Gaffer.ScriptNode()
		script["a"] = GafferScene.ShaderAssignment()
		script["s"] = Gaffer.Switch()
		script["s"].setup( Gaffer.Plug() )

		script.execute( """script["a"]["shader"].setInput( script["s"]["out"] )""" )
		self.assertTrue( script["a"]["shader"].getInput().isSame( script["s"]["out"] ) )

	def testAcceptsNoneInputs( self ) :

		a = GafferScene.ShaderAssignment()
		self.assertTrue( a["shader"].acceptsInput( None ) )

	def testInputAcceptanceFromDots( self ) :

		script = Gaffer.ScriptNode()

		script["a"] = GafferScene.ShaderAssignment()

		script["s"] = GafferSceneTest.TestShader()
		script["d"] = Gaffer.Dot()
		script["d"].setup( script["s"]["out"] )

		# Input only accepted during execution, for backwards compatibility
		# when loading old scripts.
		script.execute( """script["a"]["shader"].setInput( script["d"]["out"] )""" )
		self.assertTrue( script["a"]["shader"].getInput().isSame( script["d"]["out"] ) )

	def testFilterInputAcceptanceFromReferences( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferScene.ShaderAssignment()
		p = Gaffer.PlugAlgo.promote( s["b"]["a"]["filter"] )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( s["r"]["a"]["filter"].getInput().isSame( s["r"][p.getName()] ) )

		s["f"] = GafferScene.PathFilter()
		s["r"][p.getName()].setInput( s["f"]["out"] )

	def testFilterInputAcceptanceFromReferencesViaDot( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferScene.ShaderAssignment()
		s["b"]["d"] = Gaffer.Dot()
		s["b"]["d"].setup( s["b"]["a"]["filter"] )
		s["b"]["a"]["filter"].setInput( s["b"]["d"]["out"] )

		p = Gaffer.PlugAlgo.promote( s["b"]["d"]["in"] )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( s["r"]["a"]["filter"].source().isSame( s["r"][p.getName()] ) )

		s["f"] = GafferScene.PathFilter()
		s["r"][p.getName()].setInput( s["f"]["out"] )

	def testShaderInputAcceptanceFromReferences( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferScene.ShaderAssignment()
		p = Gaffer.PlugAlgo.promote( s["b"]["a"]["shader"] )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( s["r"]["a"]["shader"].getInput().node().isSame( s["r"] ) )

	def testEnabledDoesntAffectPassThroughs( self ) :

		s = GafferScene.ShaderAssignment()
		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s["enabled"].setValue( False )
		self.assertEqual( set( x[0] for x in cs ), set( ( s["enabled"], s["out"]["attributes"], s["out"] ) ) )

	def testInputAcceptanceFromBoxesViaBoxIO( self ) :

		s = Gaffer.ScriptNode()

		s["s"] = GafferSceneTest.TestShader()
		s["a"] = GafferScene.ShaderAssignment()
		s["a"]["shader"].setInput( s["s"]["out"] )

		Gaffer.Metadata.registerValue( s["s"]["out"], "nodule:type", "GafferUI::StandardNodule" )
		Gaffer.Metadata.registerValue( s["a"]["shader"], "nodule:type", "GafferUI::StandardNodule" )

		box = Gaffer.Box.create( s, Gaffer.StandardSet( { s["s"] } ) )
		Gaffer.BoxIO.insert( box )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["a"]["shader"].source().isSame( s2["Box"]["s"]["out"] ) )

	def testInsertBoxIO( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferScene.ShaderAssignment()
		s["n2"] = GafferScene.ShaderAssignment()
		s["n2"]["in"].setInput( s["n1"]["out"] )
		s["n3"] = GafferScene.ShaderAssignment()
		s["n3"]["in"].setInput( s["n2"]["out"] )

		box = Gaffer.Box.create( s, Gaffer.StandardSet( { s["n2"] } ) )
		Gaffer.BoxIO.insert( box )

		self.assertTrue( box["n2"]["in"].source().isSame( s["n1"]["out"] ) )
		self.assertTrue( s["n3"]["in"].source().isSame( box["n2"]["out"] ) )

	def testFilterOnlyAffectsAttributes( self ) :

		f = GafferScene.PathFilter()
		s = GafferScene.ShaderAssignment()
		s["filter"].setInput( f["out"] )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )
		f["enabled"].setValue( False )
		self.assertEqual( { x[0] for x in cs }, { s["filter"], s["out"]["attributes"], s["out"] } )

	def testPassThroughsDontDeclareDependency( self ) :

		s = GafferScene.ShaderAssignment()
		for inChild in s["in"] :
			outChild = s["out"].getChild( inChild.getName() )
			if outChild.getInput() is not None :
				self.assertNotIn( outChild, s.affects( inChild ) )
			else :
				self.assertEqual( outChild.getName(), "attributes" )
				self.assertIn( outChild, s.affects( inChild ) )

	def testAssignThroughContextVaryingSwitch( self ) :

		script = Gaffer.ScriptNode()

		script["shader1"] = GafferSceneTest.TestShader()
		script["shader1"]["type"].setValue( "test:surface" )
		script["shader1"]["name"].setValue( "shader1" )

		script["shader2"] = GafferSceneTest.TestShader()
		script["shader2"]["type"].setValue( "test:surface" )
		script["shader2"]["name"].setValue( "shader2" )

		script["switch"] = Gaffer.Switch()
		script["switch"].setup( script["shader1"]["out"] )
		script["switch"]["in"][0].setInput( script["shader1"]["out"] )
		script["switch"]["in"][1].setInput( script["shader2"]["out"] )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["switch"]["index"] = context.getFrame()' )

		script["plane"] = GafferScene.Plane()

		script["planeFilter"] = GafferScene.PathFilter()
		script["planeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		script["assignment"] = GafferScene.ShaderAssignment()
		script["assignment"]["in"].setInput( script["plane"]["out"] )
		script["assignment"]["filter"].setInput( script["planeFilter"]["out"] )
		script["assignment"]["shader"].setInput( script["switch"]["out"] )

		with Gaffer.Context() as context :

			context.setFrame( 0 )
			self.assertEqual(
				script["assignment"]["out"].attributes( "/plane" )["test:surface"].outputShader().name,
				"shader1"
			)

			context.setFrame( 1 )
			self.assertEqual(
				script["assignment"]["out"].attributes( "/plane" )["test:surface"].outputShader().name,
				"shader2"
			)

	def testContextCompatibility( self ) :

		script = Gaffer.ScriptNode()

		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "shader" )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["shader"]["parameters"]["i"] = len( context.get( "scene:path", [] ) )' )

		script["sphere"] = GafferScene.Sphere()

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/group", "/group/sphere" ] ) )

		script["assignment"] = GafferScene.ShaderAssignment()
		script["assignment"]["in"].setInput( script["group"]["out"] )
		script["assignment"]["filter"].setInput( script["filter"]["out"] )
		script["assignment"]["shader"].setInput( script["shader"]["out"] )

		script["writer"] = GafferScene.SceneWriter()
		script["writer"]["in"].setInput( script["assignment"]["out"] )
		script["writer"]["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.scc" ) )

		script["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.gfr" ) )
		script.save()

		def assertContextCompatibility( expected, envVar ) :

			env = os.environ.copy()
			if envVar is not None :
				env["GAFFERSCENE_SHADERASSIGNMENT_CONTEXTCOMPATIBILITY"] = envVar

			subprocess.check_call(
				[ "gaffer", "execute", script["fileName"].getValue(), "-nodes", "writer" ],
				env = env
			)

			scene = IECoreScene.SceneCache( script["writer"]["fileName"].getValue(), IECore.IndexedIO.OpenMode.Read )
			group = scene.child( "group" )
			sphere = group.child( "sphere" )

			if expected :
				self.assertEqual( group.readAttribute( "shader", 0 ).outputShader().parameters["i"].value, 1 )
				self.assertEqual( sphere.readAttribute( "shader", 0 ).outputShader().parameters["i"].value, 2 )
			else :
				self.assertEqual( group.readAttribute( "shader", 0 ).outputShader().parameters["i"].value, 0 )
				self.assertEqual( sphere.readAttribute( "shader", 0 ).outputShader().parameters["i"].value, 0 )

		assertContextCompatibility( False, envVar = None )
		assertContextCompatibility( False, envVar = "0" )
		assertContextCompatibility( False, envVar = "?" )
		assertContextCompatibility( True, envVar = "1" )

		Gaffer.NodeAlgo.applyUserDefaults( script["assignment"] )
		script.save()

		assertContextCompatibility( False, envVar = None )
		assertContextCompatibility( False, envVar = "0" )
		assertContextCompatibility( False, envVar = "?" )
		assertContextCompatibility( False, envVar = "1" )

	def testInputRejectsNonShaderSwitch( self ) :

		assignment = GafferScene.ShaderAssignment()

		add = GafferTest.AddNode()
		switch = Gaffer.Switch()
		switch.setup( add["sum"] )

		# We have to accept the input at this point, because all we know is
		# that it's from a switch that provides ints. Later on a shader might
		# be connected as an input.
		self.assertTrue( assignment["shader"].acceptsInput( switch["out"] ) )

		# But if the switch has a non-shader input, then we should
		# reject the connection.
		switch["in"][0].setInput( add["sum"] )
		self.assertFalse( assignment["shader"].acceptsInput( switch["out"] ) )

		# And this should hold true even if the switch has a context-varying
		# index.
		random = Gaffer.Random()
		random["contextEntry"].setValue( "frame" )
		switch["index"].setInput( random["outFloat"] )
		self.assertFalse( assignment["shader"].acceptsInput( switch["out"] ) )

		# Remove the switch input, and we should be able to connect.
		# But once connected, the switch should reject a non-shader input.
		switch["in"][0].setInput( None )
		assignment["shader"].setInput( switch["out"] )
		self.assertFalse( switch["in"][0].acceptsInput( add["sum"] ) )

	def testBogusSwitchConnections( self ) :

		assignment = GafferScene.ShaderAssignment()

		switch = Gaffer.Switch()
		switch.setup( assignment["shader"] )

		shader = GafferSceneTest.TestShader()
		self.assertFalse( switch["in"].acceptsInput( shader["out"] ) )

	def testOSLAssignmentPrefix( self ) :

		script = Gaffer.ScriptNode()

		script["shader"] = GafferSceneTest.TestShader()
		script["shader"]["type"].setValue( "osl:shader" )

		script["sphere"] = GafferScene.Sphere()

		script["assignment"] = GafferScene.ShaderAssignment()
		script["assignment"]["in"].setInput( script["sphere"]["out"] )
		script["assignment"]["shader"].setInput( script["shader"]["out"] )

		script["writer"] = GafferScene.SceneWriter()
		script["writer"]["in"].setInput( script["assignment"]["out"] )
		script["writer"]["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.scc" ) )

		script["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.gfr" ) )
		script.save()


		def assertAssignment( expected, envVar ) :

			env = os.environ.copy()
			if envVar is not None :
				env["GAFFERSCENE_SHADERASSIGNMENT_OSL_PREFIX"] = envVar
			elif env.get( "GAFFERSCENE_SHADERASSIGNMENT_OSL_PREFIX" ) :
				del env["GAFFERSCENE_SHADERASSIGNMENT_OSL_PREFIX"]

			o = subprocess.check_output(
				[ "gaffer", "execute", script["fileName"].getValue(), "-nodes", "writer" ],
				env = env
			)

			scene = IECoreScene.SceneCache( script["writer"]["fileName"].getValue(), IECore.IndexedIO.OpenMode.Read )
			sphere = scene.child( "sphere" )

			self.assertEqual( [ i for i in sphere.attributeNames() if ":surface" in i ], [ expected ] )

		assertAssignment( "osl:surface", envVar = None )
		assertAssignment( "foo:surface", envVar = "foo" )

		

if __name__ == "__main__":
	unittest.main()
