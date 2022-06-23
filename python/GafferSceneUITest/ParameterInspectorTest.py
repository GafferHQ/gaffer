##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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
import GafferTest
import GafferUITest
import GafferScene
import GafferSceneTest
import GafferSceneUI

class ParameterInspectorTest( GafferUITest.TestCase ) :

	def testName( self ) :

		sphere = GafferScene.SceneNode()

		inspector = GafferSceneUI.Private.ParameterInspector( sphere["out"], None, "light", ( "", "penumbra_angle" ) )
		self.assertEqual( inspector.name(), "penumbra_angle" )

		inspector = GafferSceneUI.Private.ParameterInspector( sphere["out"], None, "light", ( "", "penumbraAngle" ) )
		self.assertEqual( inspector.name(), "penumbraAngle" )

	@staticmethod
	def __inspect( scene, path, parameter, editScope=None, attribute="light" ) :

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.ParameterInspector(
			scene, editScopePlug, attribute, ( "", parameter )
		)
		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( path.split( "/" )[1:] )
			return inspector.inspect()

	def __assertExpectedResult( self, result, source, sourceType, editable, nonEditableReason = "", edit = None, editWarning = "" ) :

		self.assertEqual( result.source(), source )
		self.assertEqual( result.sourceType(), sourceType )
		self.assertEqual( result.editable(), editable )

		if editable :

			self.assertEqual( nonEditableReason, "" )
			self.assertEqual( result.nonEditableReason(), "" )

			acquiredEdit = result.acquireEdit()
			self.assertIsNotNone( acquiredEdit )
			if result.editScope() :
				self.assertTrue( result.editScope().isAncestorOf( acquiredEdit ) )

			if edit is not None :
				self.assertEqual(
					acquiredEdit.fullName() if acquiredEdit is not None else "",
					edit.fullName() if edit is not None else ""
				)

			self.assertEqual( result.editWarning(), editWarning )

		else :

			self.assertIsNone( edit )
			self.assertEqual( editWarning, "" )
			self.assertEqual( result.editWarning(), "" )
			self.assertNotEqual( nonEditableReason, "" )
			self.assertEqual( result.nonEditableReason(), nonEditableReason )
			self.assertRaises( RuntimeError, result.acquireEdit )

	def testValue( self ) :

		light = GafferSceneTest.TestLight()
		light["parameters"]["exposure"].setValue( 0.25 )

		self.assertEqual(
			self.__inspect( light["out"], "/light", "exposure" ).value(),
			IECore.FloatData( 0.25 )
		)

	def testSourceAndEdits( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()
		s["group"] = GafferScene.Group()
		s["editScope1"] = Gaffer.EditScope()
		s["editScope2"] = Gaffer.EditScope()

		s["group"]["in"][0].setInput( s["light"]["out"] )

		s["editScope1"].setup( s["group"]["out"] )
		s["editScope1"]["in"].setInput( s["group"]["out"] )

		s["editScope2"].setup( s["editScope1"]["out"] )
		s["editScope2"]["in"].setInput( s["editScope1"]["out"] )

		# Should be able to edit light directly.

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "/group/light", "intensity", None ),
			source = s["light"]["parameters"]["intensity"], sourceType = SourceType.Other,
			editable = True, edit = s["light"]["parameters"]["intensity"]
		)

		# Even if there is an edit scope in the way

		self.__assertExpectedResult(
			self.__inspect( s["editScope1"]["out"], "/group/light", "intensity", None ),
			source = s["light"]["parameters"]["intensity"], sourceType = SourceType.Other,
			editable = True, edit = s["light"]["parameters"]["intensity"]
		)

		# We shouldn't be able to edit if we've been told to use an EditScope and it isn't in the history.

		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "/group/light", "intensity", s["editScope1"] ),
			source = s["light"]["parameters"]["intensity"], sourceType = SourceType.Other,
			editable = False, nonEditableReason = "The target EditScope (editScope1) is not in the scene history."
		)

		# If it is in the history though, and we're told to use it, then we will.

		inspection = self.__inspect( s["editScope2"]["out"], "/group/light", "intensity", s["editScope2"] )

		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireParameterEdit(
				s["editScope2"], "/group/light", "light", ( "", "intensity" ), createIfNecessary = False
			)
		)

		self.__assertExpectedResult(
			inspection,
			source = s["light"]["parameters"]["intensity"], sourceType = SourceType.Upstream,
			editable = True
		)

		lightEditScope2Edit = inspection.acquireEdit()
		self.assertIsNotNone( lightEditScope2Edit )
		self.assertEqual(
			lightEditScope2Edit,
			GafferScene.EditScopeAlgo.acquireParameterEdit(
				s["editScope2"], "/group/light", "light", ( "", "intensity" ), createIfNecessary = False
			)
		)

		# If there's an edit downstream of the EditScope we're asked to use,
		# then we're allowed to be editable still

		inspection = self.__inspect( s["editScope2"]["out"], "/group/light", "intensity", s["editScope1"] )
		self.assertTrue( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "" )
		lightEditScope1Edit = inspection.acquireEdit()
		self.assertIsNotNone( lightEditScope1Edit )
		self.assertEqual(
			lightEditScope1Edit,
			GafferScene.EditScopeAlgo.acquireParameterEdit(
				s["editScope1"], "/group/light", "light", ( "", "intensity" ), createIfNecessary = False
			)
		)
		self.assertEqual( inspection.editWarning(), "" )

		# If there is a source node inside an edit scope, make sure we use that

		s["editScope1"]["light2"] = GafferSceneTest.TestLight()
		s["editScope1"]["light2"]["name"].setValue( "light2" )
		s["editScope1"]["parentLight2"] = GafferScene.Parent()
		s["editScope1"]["parentLight2"]["parent"].setValue( "/" )
		s["editScope1"]["parentLight2"]["children"][0].setInput( s["editScope1"]["light2"]["out"] )
		s["editScope1"]["parentLight2"]["in"].setInput( s["editScope1"]["BoxIn"]["out"] )
		s["editScope1"]["LightEdits"]["in"].setInput( s["editScope1"]["parentLight2"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/light2", "intensity", s["editScope1"] ),
			source = s["editScope1"]["light2"]["parameters"]["intensity"], sourceType = SourceType.EditScope,
			editable = True, edit = s["editScope1"]["light2"]["parameters"]["intensity"]
		)

		# If there is a tweak in the scope's processor make sure we use that

		light2Edit = GafferScene.EditScopeAlgo.acquireParameterEdit(
			s["editScope1"], "/light2", "light", ( "", "intensity" ), createIfNecessary = True
		)
		light2Edit["enabled"].setValue( True )
		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/light2", "intensity", s["editScope1"] ),
			source = light2Edit, sourceType = SourceType.EditScope,
			editable = True, edit = light2Edit
		)

		# If there is a manual tweak downstream of the scope's scene processor, make sure we use that

		s["editScope1"]["tweakLight2"] = GafferScene.ShaderTweaks()
		s["editScope1"]["tweakLight2"]["in"].setInput( s["editScope1"]["LightEdits"]["out"] )
		s["editScope1"]["tweakLight2Filter"] = GafferScene.PathFilter()
		s["editScope1"]["tweakLight2Filter"]["paths"].setValue( IECore.StringVectorData( [ "/light2" ] ) )
		s["editScope1"]["tweakLight2"]["filter"].setInput( s["editScope1"]["tweakLight2Filter"]["out"] )
		s["editScope1"]["BoxOut"]["in"].setInput( s["editScope1"]["tweakLight2"]["out"] )

		s["editScope1"]["tweakLight2"]["shader"].setValue( "light" )
		editScopeShaderTweak = GafferScene.TweakPlug( "intensity", imath.Color3f( 1, 0, 0 ) )
		s["editScope1"]["tweakLight2"]["tweaks"].addChild( editScopeShaderTweak )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/light2", "intensity", s["editScope1"] ),
			source = editScopeShaderTweak, sourceType = SourceType.EditScope,
			editable = True, edit = editScopeShaderTweak
		)

		# If there is a manual tweak outside of an edit scope make sure we use that with no scope

		s["independentLightTweak"] = GafferScene.ShaderTweaks()
		s["independentLightTweak"]["in"].setInput( s["editScope2"]["out"] )

		s["independentLightTweakFilter"] = GafferScene.PathFilter()
		s["independentLightTweakFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/light" ] ) )
		s["independentLightTweak"]["filter"].setInput( s["independentLightTweakFilter"]["out"] )

		s["independentLightTweak"]["shader"].setValue( "light" )
		independentLightTweakPlug = GafferScene.TweakPlug( "intensity", imath.Color3f( 1, 1, 0 ) )
		s["independentLightTweak"]["tweaks"].addChild( independentLightTweakPlug )

		self.__assertExpectedResult(
			self.__inspect( s["independentLightTweak"]["out"], "/group/light", "intensity", None ),
			source = independentLightTweakPlug, sourceType = SourceType.Other,
			editable = True, edit = independentLightTweakPlug
		)

		# Check we show the last input plug if the source plug is an output

		exposureCurve = Gaffer.Animation.acquire( s["light"]["parameters"]["exposure"] )
		exposureCurve.addKey( Gaffer.Animation.Key( time = 1, value = 2 ) )

		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "/group/light", "exposure", None ),
			source = s["light"]["parameters"]["exposure"], sourceType = SourceType.Other,
			editable = True, edit = s["light"]["parameters"]["exposure"]
		)

		inspection = self.__inspect( s["editScope1"]["out"], "/group/light", "exposure", s["editScope1"] )
		exposureTweak = inspection.acquireEdit()
		exposureTweak["enabled"].setValue( True )
		exposureTweakCurve = Gaffer.Animation.acquire( exposureTweak["value"] )
		exposureTweakCurve.addKey( Gaffer.Animation.Key( time = 2, value = 4 ) )

		self.__assertExpectedResult(
			self.__inspect( s["editScope1"]["out"], "/group/light", "exposure", s["editScope1"] ),
			source = exposureTweak, sourceType = SourceType.EditScope,
			editable = True, edit = exposureTweak
		)

		# Check editWarnings and nonEditableReasons

		self.__assertExpectedResult(
			self.__inspect( s["independentLightTweak"]["out"], "/group/light", "intensity", s["editScope2"] ),
			source = independentLightTweakPlug, sourceType = SourceType.Downstream,
			editable = True, edit = lightEditScope2Edit, editWarning = "Parameter has edits downstream in independentLightTweak."
		)

		s["editScope2"]["enabled"].setValue( False )

		self.__assertExpectedResult(
			self.__inspect( s["independentLightTweak"]["out"], "/group/light", "intensity", s["editScope2"] ),
			source = independentLightTweakPlug, sourceType = SourceType.Downstream,
			editable = False, nonEditableReason = "The target EditScope (editScope2) is disabled."
		)

		s["editScope2"]["enabled"].setValue( True )
		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"], True )

		self.__assertExpectedResult(
			self.__inspect( s["independentLightTweak"]["out"], "/light2", "intensity", s["editScope2"] ),
			source = editScopeShaderTweak, sourceType = SourceType.Upstream,
			editable = False, nonEditableReason = "editScope2 is locked."
		)

		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"], False )
		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"]["LightEdits"]["edits"], True )

		self.__assertExpectedResult(
			self.__inspect( s["independentLightTweak"]["out"], "/light2", "intensity", s["editScope2"] ),
			source = editScopeShaderTweak, sourceType = SourceType.Upstream,
			editable = False, nonEditableReason = "editScope2.LightEdits.edits is locked."
		)

		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"]["LightEdits"], True )

		self.__assertExpectedResult(
			self.__inspect( s["independentLightTweak"]["out"], "/light2", "intensity", s["editScope2"] ),
			source = editScopeShaderTweak, sourceType = SourceType.Upstream,
			editable = False, nonEditableReason = "editScope2.LightEdits is locked."
		)

	def testShaderAssignmentWarning( self ) :

		shader = GafferSceneTest.TestShader()
		shader["type"].setValue( "test:surface" )

		plane = GafferScene.Plane()

		planeFilter = GafferScene.PathFilter()
		planeFilter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		shaderAssignment = GafferScene.ShaderAssignment()
		shaderAssignment["shader"].setInput( shader["out"] )
		shaderAssignment["filter"].setInput( planeFilter["out"] )

		self.__assertExpectedResult(
			self.__inspect( shaderAssignment["out"], "/plane", "c", None, attribute="test:surface" ),
			source = shader["parameters"]["c"], sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True, editWarning = "Edits to TestShader may affect other locations in the scene."
		)

	def testEditScopeNotInHistory( self ) :

		light = GafferSceneTest.TestLight()

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		shaderTweaks = GafferScene.ShaderTweaks()
		shaderTweaks["in"].setInput( light["out"] )
		shaderTweaks["filter"].setInput( lightFilter["out"] )
		shaderTweaks["tweaks"].addChild( GafferScene.TweakPlug( "exposure", 3 ) )

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( light["out"], "/light", "exposure", editScope ),
			source = light["parameters"]["exposure"], sourceType = SourceType.Other,
			editable = False, nonEditableReason = "The target EditScope (EditScope) is not in the scene history."
		)

		self.__assertExpectedResult(
			self.__inspect( shaderTweaks["out"], "/light", "exposure" ),
			source = shaderTweaks["tweaks"][0], sourceType = SourceType.Other,
			editable = True, edit = shaderTweaks["tweaks"][0],
		)

		self.__assertExpectedResult(
			self.__inspect( shaderTweaks["out"], "/light", "exposure", editScope ),
			source = shaderTweaks["tweaks"][0], sourceType = SourceType.Other,
			editable = False, nonEditableReason = "The target EditScope (EditScope) is not in the scene history."
		)

	def testDisabledTweaks( self ) :

		light = GafferSceneTest.TestLight()

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		shaderTweaks = GafferScene.ShaderTweaks()
		shaderTweaks["in"].setInput( light["out"] )
		shaderTweaks["filter"].setInput( lightFilter["out"] )
		exposureTweak = GafferScene.TweakPlug( "exposure", 10 )
		shaderTweaks["tweaks"].addChild( exposureTweak )

		self.__assertExpectedResult(
			self.__inspect( shaderTweaks["out"], "/light", "exposure" ),
			source = exposureTweak, sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True, edit = exposureTweak
		)

		exposureTweak["enabled"].setValue( False )

		self.__assertExpectedResult(
			self.__inspect( shaderTweaks["out"], "/light", "exposure" ),
			source = light["parameters"]["exposure"], sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True, edit = light["parameters"]["exposure"]
		)

	def testInspectorShaderDiscovery( self ) :

		s = Gaffer.ScriptNode()

		s["sphere"] = GafferScene.Sphere()

		s["shader"] = GafferSceneTest.TestShader()
		s["shader"]["type"].setValue( "test:surface" )

		s["shaderAssignment"] = GafferScene.ShaderAssignment()
		s["shaderAssignment"]["shader"].setInput( s["shader"]["out"] )
		s["shaderAssignment"]["in"].setInput( s["sphere"]["out"] )

		i = self.__inspect( s["shaderAssignment"]["out"], "/sphere", "c", attribute="test:surface" )
		self.assertTrue( i.editable() )
		self.assertEqual( i.acquireEdit(), s["shader"]["parameters"]["c"] )

		s["switch"]= Gaffer.Switch()
		s["switch"].setup( s["shaderAssignment"]["shader"] )
		s["switch"]["in"][0].setInput( s["shader"]["out"] )
		s["shaderAssignment"]["shader"].setInput( s["switch"]["out"] )

		i = self.__inspect( s["shaderAssignment"]["out"], "/sphere", "c", attribute="test:surface" )
		self.assertTrue( i.editable() )
		self.assertEqual( i.acquireEdit(), s["shader"]["parameters"]["c"] )

		s["expr"] = Gaffer.Expression()
		s["expr"].setExpression( 'parent["switch"]["index"] = 0', "python" )

		i = self.__inspect( s["shaderAssignment"]["out"], "/sphere", "c", attribute="test:surface" )
		self.assertTrue( i.editable() )
		self.assertEqual( i.acquireEdit(), s["shader"]["parameters"]["c"] )

	def testEditScopeNesting( self ) :

		light = GafferSceneTest.TestLight()
		editScope1 = Gaffer.EditScope( "EditScope1" )

		editScope1.setup( light["out"] )
		editScope1["in"].setInput( light["out"] )

		i = self.__inspect( editScope1["out"], "/light", "intensity", editScope1 )
		scope1Edit = i.acquireEdit()
		scope1Edit["enabled"].setValue( True )
		self.assertEqual( scope1Edit.ancestor( Gaffer.EditScope ), editScope1 )

		editScope2 = Gaffer.EditScope( "EditScope2" )
		editScope2.setup( light["out"] )
		editScope1.addChild( editScope2 )
		editScope2["in"].setInput( scope1Edit.ancestor( GafferScene.SceneProcessor )["out"] )
		editScope1["BoxOut"]["in"].setInput( editScope2["out"] )

		i = self.__inspect( editScope1["out"], "/light", "intensity", editScope2 )
		scope2Edit = i.acquireEdit()
		scope2Edit["enabled"].setValue( True )
		self.assertEqual( scope2Edit.ancestor( Gaffer.EditScope ), editScope2 )

		# Check we still find the edit in scope 1

		i = self.__inspect( editScope1["out"], "/light", "intensity", editScope1 )
		self.assertEqual( i.acquireEdit()[0].ancestor( Gaffer.EditScope ), editScope1 )

	def testDownstreamSourceType( self ) :

		light = GafferSceneTest.TestLight()

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		shaderTweaks = GafferScene.ShaderTweaks()
		shaderTweaks["in"].setInput( editScope["out"] )
		shaderTweaks["filter"].setInput( lightFilter["out"] )
		exposureTweak = GafferScene.TweakPlug( "exposure", 10 )
		shaderTweaks["tweaks"].addChild( exposureTweak )

		self.__assertExpectedResult(
			self.__inspect( shaderTweaks["out"], "/light", "exposure", editScope ),
			source = exposureTweak, sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Downstream,
			editable = True, edit = None,
			editWarning = "Parameter has edits downstream in ShaderTweaks."
		)

	def testLightInsideBox( self ) :

		box = Gaffer.Box()
		box["light"] = GafferSceneTest.TestLight()
		Gaffer.PlugAlgo.promote( box["light"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( box["out"], "/light", "exposure" ),
			source = box["light"]["parameters"]["exposure"], sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True, edit = box["light"]["parameters"]["exposure"],
		)

	def testDirtiedSignal( self ) :

		light = GafferSceneTest.TestLight()

		editScope1 = Gaffer.EditScope()
		editScope1.setup( light["out"] )
		editScope1["in"].setInput( light["out"] )

		editScope2 = Gaffer.EditScope()
		editScope2.setup( editScope1["out"] )
		editScope2["in"].setInput( editScope1["out"] )

		settings = Gaffer.Node()
		settings["editScope"] = Gaffer.Plug()

		inspector = GafferSceneUI.Private.ParameterInspector(
			editScope2["out"], settings["editScope"], "light", ( "", "exposure" )
		)

		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		# Tweaking a parameter should dirty the inspector.
		light["parameters"]["exposure"].setValue( 10 )
		self.assertEqual( len( cs ), 1 )

		# But tweaking the transform should not.
		light["transform"]["translate"]["x"].setValue( 10 )
		self.assertEqual( len( cs ), 1 )

		# Changing EditScope should also dirty the inspector.
		settings["editScope"].setInput( editScope1["enabled"] )
		self.assertEqual( len( cs ), 2 )
		settings["editScope"].setInput( editScope2["enabled"] )
		self.assertEqual( len( cs ), 3 )
		settings["editScope"].setInput( None )
		self.assertEqual( len( cs ), 4 )

	def testNonExistentLocation( self ) :

		light = GafferSceneTest.TestLight()
		self.assertIsNone( self.__inspect( light["out"], "/nothingHere", "exposure" ) )

		group = GafferScene.Group()
		group["in"][0].setInput( light["out"] )

		self.assertIsNone( self.__inspect( group["out"], "/group/nothingHere", "exposure" ) )

	def testNonExistentAttribute( self ) :

		light = GafferSceneTest.TestLight()
		self.assertIsNone( self.__inspect( light["out"], "/light", "exposure", attribute = "nothingHere" ) )

	def testNonExistentParameter( self ) :

		light = GafferSceneTest.TestLight()
		self.assertIsNone( self.__inspect( light["out"], "/light", "nothingHere" ) )

	def testReadOnlyMetadataSignalling( self ) :

		light = GafferSceneTest.TestLight()

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )

		settings = Gaffer.Node()
		settings["editScope"] = Gaffer.Plug()

		inspector = GafferSceneUI.Private.ParameterInspector(
			editScope["out"], settings["editScope"], "light", ( "", "exposure" )
		)

		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		Gaffer.MetadataAlgo.setReadOnly( editScope, True )
		Gaffer.MetadataAlgo.setReadOnly( editScope, False )
		self.assertEqual( len( cs ), 0 ) # Changes not relevant because we're not using the EditScope.

		settings["editScope"].setInput( editScope["enabled"] )
		self.assertEqual( len( cs ), 1 )
		Gaffer.MetadataAlgo.setReadOnly( editScope, True )
		self.assertEqual( len( cs ), 2 ) # Change affects the result of `inspect().editable()`

if __name__ == "__main__":
	unittest.main()
