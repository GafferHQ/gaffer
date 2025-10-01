##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

import string

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest
import GafferScene
import GafferSceneUI
import GafferSceneTest

from GafferSceneUI import _GafferSceneUI

class SceneInspectorTest( GafferUITest.TestCase ) :

	def testInspectorPathContextProperties( self ) :

		options = GafferScene.StandardOptions()

		contextA = Gaffer.Context()
		contextB = Gaffer.Context()

		tree = _GafferSceneUI._SceneInspector.InspectorTree( options["out"], [ contextA, contextB ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree )

		self.assertIn( "inspector:contextA", path.propertyNames() )
		self.assertIn( "inspector:contextB", path.propertyNames() )
		self.assertTrue( path.contextProperty( "inspector:contextA" ).isSame( contextA ) )
		self.assertTrue( path.contextProperty( "inspector:contextB" ).isSame( contextB ) )

		tree.setContexts( [ contextB, contextA ] )
		self.assertTrue( path.contextProperty( "inspector:contextA" ).isSame( contextB ) )
		self.assertTrue( path.contextProperty( "inspector:contextB" ).isSame( contextA ) )

	def testInspectorPathOptions( self ) :

		options = GafferScene.StandardOptions()

		tree = _GafferSceneUI._SceneInspector.InspectorTree( options["out"], [ Gaffer.Context(), Gaffer.Context() ], None )
		optionsPath = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Globals/Options" )

		# Not valid yet, because there aren't any options in the scene.
		self.assertFalse( optionsPath.isValid() )

		options["options"]["render:camera"]["enabled"].setValue( True )
		self.assertTrue( optionsPath.isValid() )
		self.assertEqual( { str( p ) for p in optionsPath.children() }, { "/Globals/Options/Standard" } )

		optionsPath.setFromString( "/Globals/Options/Standard" )
		self.assertTrue( optionsPath.isValid() )
		self.assertEqual( { str( p ) for p in optionsPath.children() }, { "/Globals/Options/Standard/render:camera" } )

		optionsPath.setFromString( "/Globals/Options/Standard/render:camera" )
		self.assertTrue( optionsPath.isValid() )

		inspector = optionsPath.property( "inspector:inspector" )
		self.assertIsInstance( inspector, GafferSceneUI.Private.OptionInspector )
		self.assertEqual( inspector.name(), "render:camera" )

	def testInspectorPathChangedSignal( self ) :

		options = GafferScene.StandardOptions()
		options["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		context = Gaffer.Context()
		tree = _GafferSceneUI._SceneInspector.InspectorTree( options["out"], [ context, context ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree )

		cs = GafferTest.CapturingSlot( path.pathChangedSignal() )
		self.assertEqual( len( cs ), 0 )

		options["options"]["render:camera"]["enabled"].setValue( True )
		self.assertEqual( len( cs ), 1 )

		context2 = Gaffer.Context()
		context2["test"] = 10
		tree.setContexts( [ context2, context2 ] )
		self.assertEqual( len( cs ), 2 )

		options["user"]["p"].setValue( 10 )
		self.assertEqual( len( cs ), 2 ) # Not dirtied again, since user plug doesn't affect scene

	def testInspectorTreeSetContexts( self ) :

		plane = GafferScene.Plane()

		context1A = Gaffer.Context()
		context1B = Gaffer.Context()

		context2A = Gaffer.Context()
		context2A["foo"] = 1
		context2B = Gaffer.Context( context2A )

		tree = _GafferSceneUI._SceneInspector.InspectorTree( plane["out"], [ context1A, context1A ], None )
		dirtyings = GafferTest.CapturingSlot( tree.dirtiedSignal() )

		# Not dirtied, because they're the exact same contexts.
		tree.setContexts( [ context1A, context1A ] )
		self.assertEqual( len( dirtyings ), 0 )
		# Not dirtied, because they're contexts with the same values.
		tree.setContexts( [ context1B, context1B ] )
		tree.setContexts( [ context1A, context1B ] )
		tree.setContexts( [ context1B, context1A ] )
		self.assertEqual( len( dirtyings ), 0 )
		# Dirted, because they're contexts with different values.
		tree.setContexts( [ context2B, context1B ] )
		self.assertEqual( len( dirtyings ), 1 )
		tree.setContexts( [ context2A, context2B ] )
		self.assertEqual( len( dirtyings ), 2 )

	def testInspectorTreeRejectsNullContexts( self ) :

		plane = GafferScene.Plane()

		with self.assertRaisesRegex( RuntimeError, "Context must not be null" ) :
			tree = _GafferSceneUI._SceneInspector.InspectorTree( plane["out"], [ None, None ], None )

		tree = _GafferSceneUI._SceneInspector.InspectorTree( plane["out"], [ Gaffer.Context(), Gaffer.Context() ], None )
		with self.assertRaisesRegex( RuntimeError, "Context must not be null" ) :
			tree.setContexts( [ None, None ] )

	def testInspectorPathWithNonExistentLocation( self ) :

		plane = GafferScene.Plane()
		context = Gaffer.Context()
		context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/i/don't/exist" )

		tree = _GafferSceneUI._SceneInspector.InspectorTree( plane["out"], [ context, context ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Location" )

		self.assertEqual( path.children(), [] )

	def testAttributesAreSortedAlphabetically( self ) :

		plane = GafferScene.Plane()

		attributes = GafferScene.CustomAttributes()
		attributes["in"].setInput( plane["out"] )
		for s in string.ascii_lowercase :
			attributes["attributes"].addChild( Gaffer.NameValuePlug( s, s ) )

		context = Gaffer.Context()
		context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/plane" )

		tree = _GafferSceneUI._SceneInspector.InspectorTree( attributes["out"], [ context, context ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Location/Attributes/Other" )
		self.assertEqual(
			"".join( [ c[-1] for c in path.children() ] ),
			string.ascii_lowercase
		)

	def testInspectorPathWithoutScenePath( self ) :

		plane = GafferScene.Plane()
		context = Gaffer.Context()

		tree = _GafferSceneUI._SceneInspector.InspectorTree( plane["out"], [ context, context ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Location" )

		self.assertEqual( path.children(), [] )

	def testDiffColumnCellData( self ) :

		contextQuery = Gaffer.ContextQuery()
		contextQuery.addQuery( Gaffer.StringPlug(), "camera" )

		options = GafferScene.StandardOptions()
		options["options"]["render:camera"]["enabled"].setValue( True )
		options["options"]["render:camera"]["value"].setInput( contextQuery["out"][0]["value"] )

		context1 = Gaffer.Context()
		context1["camera"] = "camera1"

		tree = _GafferSceneUI._SceneInspector.InspectorTree( options["out"], [ context1, context1 ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Globals/Options/Standard/render:camera" )

		# A/B contexts are identical, so columns show identical values.

		aColumn = _GafferSceneUI._SceneInspector.InspectorDiffColumn( _GafferSceneUI._SceneInspector.InspectorDiffColumn.DiffContext.A )
		aCell = aColumn.cellData( path )
		self.assertEqual( aCell.value, "camera1" )
		self.assertIsNone( aCell.background )

		bColumn = _GafferSceneUI._SceneInspector.InspectorDiffColumn( _GafferSceneUI._SceneInspector.InspectorDiffColumn.DiffContext.B )
		bCell = bColumn.cellData( path )
		self.assertEqual( bCell.value, aCell.value )
		self.assertEqual( bCell.background, aCell.background )

		# Change contexts

		context2 = Gaffer.Context()
		context2["camera"] = "camera2"
		tree.setContexts( [ context1, context2 ] )

		# Columns now show different values, and have background colours to
		# highlight the difference.

		aCell = aColumn.cellData( path )
		self.assertEqual( aCell.value, "camera1" )
		self.assertIsNotNone( aCell.background )

		bCell = bColumn.cellData( path )
		self.assertEqual( bCell.value, "camera2" )
		self.assertIsNotNone( bCell.background )
		self.assertNotEqual( bCell.background, aCell.background )

	def testPathDirtying( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()
		script.setFocus( script["plane"] )

		sceneInspector = GafferSceneUI.SceneInspector( script )
		sceneInspector.setNodeSet( script.focusSet() )
		sceneInspector.settings()["compare"]["scene"]["value"].setInput( script["sphere"]["out"] )

		path = sceneInspector._SceneInspector__locationPathListing.getPath()
		pathChanges = GafferTest.CapturingSlot( path.pathChangedSignal() )

		# Changes to main input should always dirty the path.
		script["plane"]["transform"]["translate"]["x"].setValue( 1 )
		self.assertEqual( len( pathChanges ), 1 )

		# Changes to the comparison scene should only dirty the
		# path when comparison is enabled.

		del pathChanges[:]
		script["sphere"]["transform"]["translate"]["x"].setValue( 1 )
		self.assertEqual( len( pathChanges ), 0 )

		with Gaffer.DirtyPropagationScope() :
			sceneInspector.settings()["compare"]["scene"]["enabled"].setValue( True )
		self.assertEqual( len( pathChanges ), 1 )
		script["sphere"]["transform"]["translate"]["x"].setValue( 2 )
		self.assertEqual( len( pathChanges ), 2 )

	def testNoComputationOnUIThread( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()
		script.setFocus( script["plane"] )

		with Gaffer.ThreadMonitor() as monitor :

			with GafferUI.Window() as window :

				sceneInspector = GafferSceneUI.SceneInspector( script )
				sceneInspector.setNodeSet( script.focusSet() )
				sceneInspector.settings()["location"].setValue( "/plane" )

			window.setVisible( True )
			self.waitForIdle( 1000 )

		self.assertNotIn( monitor.thisThreadId(), monitor.combinedStatistics() )

	def testDiffColumnWithMixedScenePath( self ) :

		plane = GafferScene.Plane()
		scenePathContext = Gaffer.Context()
		scenePathContext["scene:path"] = GafferScene.ScenePlug.stringToPath( "/plane" )

		tree = _GafferSceneUI._SceneInspector.InspectorTree( plane["out"], [ Gaffer.Context(), scenePathContext ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Location/Bound/Local" )
		self.assertTrue( path.isValid() )

		aColumn = _GafferSceneUI._SceneInspector.InspectorDiffColumn( _GafferSceneUI._SceneInspector.InspectorDiffColumn.DiffContext.A )
		self.assertIsNone( aColumn.cellData( path ).value )

		bColumn = _GafferSceneUI._SceneInspector.InspectorDiffColumn( _GafferSceneUI._SceneInspector.InspectorDiffColumn.DiffContext.B )
		self.assertIsNotNone( bColumn.cellData( path ).value )

		tree.setContexts( list( reversed( tree.getContexts() ) ) )
		self.assertIsNotNone( aColumn.cellData( path ).value )
		self.assertIsNone( bColumn.cellData( path ).value )

	def testShaderInspections( self ) :

		textureA = GafferSceneTest.TestShader( "TextureA" )
		textureA.loadShader( "mix" )

		textureB = GafferSceneTest.TestShader( "TextureB" )
		textureB.loadShader( "mix" )

		mix = GafferSceneTest.TestShader( "Mix" )
		mix.loadShader( "mix" )
		mix["parameters"]["a"].setInput( textureA["out"]["c"] )
		mix["parameters"]["b"].setInput( textureB["out"]["c"] )

		surface = GafferSceneTest.TestShader( "Surface" )
		surface.loadShader( "simpleShader" )
		surface["parameters"]["c"].setInput( mix["out"]["c"] )
		surface["type"].setValue( "surface" )

		plane = GafferScene.Plane()
		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["in"].setInput( plane["out"] )
		shaderAssignment["shader"].setInput( surface["out"] )

		context = Gaffer.Context()
		context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/plane" )

		tree = _GafferSceneUI._SceneInspector.InspectorTree( shaderAssignment["out"], [ context, context ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Location/Attributes/Standard/surface" )

		# The value should contain the entire shader network. This can't be shown in a single
		# cell, but allows the diff column to show gross differences using the background
		# colour.

		with context :
			shaderNetwork = shaderAssignment["out"]["attributes"].getValue()["surface"]

		def inspectPath( path ) :

			inspector = path.property( "inspector:inspector" )
			context = path.contextProperty( "inspector:context" )
			with context :
				return inspector.inspect().value()

		self.assertEqual( inspectPath( path ), shaderNetwork )

		# We want the children ordered according to the network topology,
		# closest to the output first.
		childNames = [ c[-1] for c in path.children() ]
		self.assertEqual( childNames[:2], [ "Surface", "Mix" ] )
		self.assertEqual( set( childNames[2:] ), { "TextureA", "TextureB" } )
		self.assertEqual( set( childNames ), set( shaderNetwork.shaders().keys() ) )

		# And each child should have a value containing the shader, and then
		# children for the shader parameters, ordered alphabetically.

		for shaderPath in path.children() :
			self.assertEqual( inspectPath( shaderPath ), shaderNetwork.getShader( shaderPath[-1] ) )
			parameterPaths = shaderPath.children()
			parameterNames = [ c[-1] for c in parameterPaths ]
			self.assertEqual( set( parameterNames ), set( shaderNetwork.getShader( shaderPath[-1] ).parameters.keys() ) )
			self.assertEqual( parameterNames, sorted( parameterNames ) )
			for parameterPath in parameterPaths :
				shaderName = shaderPath[-1]
				parameterName = parameterPath[-1]
				parameterInput = shaderNetwork.input( ( shaderName, parameterName ) )
				inspectedValue = inspectPath( parameterPath )

				self.assertEqual( parameterInput, GafferSceneUI.Private.ParameterInspector.connectionSource( inspectedValue ) )
				if not parameterInput :
					self.assertEqual( inspectedValue, shaderNetwork.getShader( shaderName ).parameters[parameterName] )

	def testCustomInspectors( self ) :

		def customInspector( scene, editScope ) :

			return [
				GafferSceneUI.SceneInspector.Inspection(
					"Smallest Face",
					GafferSceneUI.Private.BasicInspector( scene["object"], editScope, lambda objectPlug : objectPlug.getValue().minVerticesPerFace() )
				),
				GafferSceneUI.SceneInspector.Inspection(
					"Largest Face",
					GafferSceneUI.Private.BasicInspector( scene["object"], editScope, lambda objectPlug : objectPlug.getValue().maxVerticesPerFace() )
				),
			]

		GafferSceneUI.SceneInspector.registerInspectors( "Location/Custom", customInspector )
		self.addCleanup( GafferSceneUI.SceneInspector.deregisterInspectors, "Location/Custom" )

		sphere = GafferScene.Sphere()
		context = Gaffer.Context()
		context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/sphere" )
		tree = _GafferSceneUI._SceneInspector.InspectorTree( sphere["out"], [ context, context ], None )

		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Location/Custom/Smallest Face" )
		self.assertTrue( path.isValid() )
		with context :
			self.assertEqual( path.property( "inspector:inspector" ).inspect().value(), IECore.IntData( 3 ) )

		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Location/Custom/Largest Face" )
		self.assertTrue( path.isValid() )
		with context :
			self.assertEqual( path.property( "inspector:inspector" ).inspect().value(), IECore.IntData( 4 ) )

		GafferSceneUI.SceneInspector.deregisterInspectors( "Location/Custom" )

		tree = _GafferSceneUI._SceneInspector.InspectorTree( sphere["out"], [ context, context ], None )
		path = _GafferSceneUI._SceneInspector.InspectorPath( tree, "/Location/Custom/Smallest Face" )
		self.assertFalse( path.isValid() )

if __name__ == "__main__":
	unittest.main()
