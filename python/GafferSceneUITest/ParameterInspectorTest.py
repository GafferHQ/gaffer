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

		if isinstance( parameter, str ) :
			parameter = ( "", parameter )

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.ParameterInspector(
			scene, editScopePlug, attribute, parameter
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
		editScopeShaderTweak = Gaffer.TweakPlug( "intensity", imath.Color3f( 1, 0, 0 ) )
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
		independentLightTweakPlug = Gaffer.TweakPlug( "intensity", imath.Color3f( 1, 1, 0 ) )
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
		shader["parameters"]["optionalString"]["enabled"].setValue( True )

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

		self.__assertExpectedResult(
			self.__inspect( shaderAssignment["out"], "/plane", "optionalString", None, attribute="test:surface" ),
			source = shader["parameters"]["optionalString"], sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True, editWarning = "Edits to TestShader may affect other locations in the scene."
		)

	def testEditScopeNotInHistory( self ) :

		light = GafferSceneTest.TestLight()

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		shaderTweaks = GafferScene.ShaderTweaks()
		shaderTweaks["in"].setInput( light["out"] )
		shaderTweaks["filter"].setInput( lightFilter["out"] )
		shaderTweaks["tweaks"].addChild( Gaffer.TweakPlug( "exposure", 3 ) )

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

	def testAcquireEditCreateIfNecessary( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()
		s["group"] = GafferScene.Group()
		s["editScope"] = Gaffer.EditScope()

		s["group"]["in"][0].setInput( s["light"]["out"] )

		s["editScope"].setup( s["group"]["out"] )
		s["editScope"]["in"].setInput( s["group"]["out"] )

		inspection = self.__inspect( s["group"]["out"], "/group/light", "exposure", None )
		self.assertEqual( inspection.acquireEdit( createIfNecessary = False ), s["light"]["parameters"]["exposure"] )

		inspection = self.__inspect( s["editScope"]["out"], "/group/light", "exposure", s["editScope"] )
		self.assertIsNone( inspection.acquireEdit( createIfNecessary = False ) )

		edit = inspection.acquireEdit( createIfNecessary = True )
		self.assertIsNotNone( edit )
		self.assertEqual( inspection.acquireEdit( createIfNecessary = False ), edit )

	def testDisableEdit( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()

		s["lightFilter"] = GafferScene.PathFilter()
		s["lightFilter"]["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		s["shaderTweaks"] = GafferScene.ShaderTweaks()
		s["shaderTweaks"]["in"].setInput( s["light"]["out"] )
		s["shaderTweaks"]["filter"].setInput( s["lightFilter"]["out"] )
		exposureTweak = Gaffer.TweakPlug( "exposure", 10 )
		s["shaderTweaks"]["tweaks"].addChild( exposureTweak )

		s["editScope"] = Gaffer.EditScope()
		s["editScope"].setup( s["shaderTweaks"]["out"] )
		s["editScope"]["in"].setInput( s["shaderTweaks"]["out"] )

		s["editScope2"] = Gaffer.EditScope()
		s["editScope2"].setup( s["editScope"]["out"] )
		s["editScope2"]["in"].setInput( s["editScope"]["out"] )

		Gaffer.MetadataAlgo.setReadOnly( exposureTweak["enabled"], True )
		inspection = self.__inspect( s["shaderTweaks"]["out"], "/light", "exposure", None )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "shaderTweaks.tweaks.tweak.enabled is locked." )
		self.assertRaisesRegex( IECore.Exception, "Cannot disable edit : shaderTweaks.tweaks.tweak.enabled is locked.", inspection.disableEdit )

		Gaffer.MetadataAlgo.setReadOnly( exposureTweak["enabled"], False )
		Gaffer.MetadataAlgo.setReadOnly( exposureTweak, True )
		inspection = self.__inspect( s["shaderTweaks"]["out"], "/light", "exposure", None )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "shaderTweaks.tweaks.tweak is locked." )
		self.assertRaisesRegex( IECore.Exception, "Cannot disable edit : shaderTweaks.tweaks.tweak is locked.", inspection.disableEdit )

		Gaffer.MetadataAlgo.setReadOnly( exposureTweak, False )
		inspection = self.__inspect( s["shaderTweaks"]["out"], "/light", "exposure", None )
		self.assertTrue( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "" )
		inspection.disableEdit()
		self.assertFalse( exposureTweak["enabled"].getValue() )

		lightEdit = GafferScene.EditScopeAlgo.acquireParameterEdit(
			s["editScope"], "/light", "light", ( "", "exposure" ), createIfNecessary = True
		)
		lightEdit["enabled"].setValue( True )
		lightEdit["value"].setValue( 2.0 )

		inspection = self.__inspect( s["editScope"]["out"], "/light", "exposure", s["editScope2"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "The target EditScope (editScope2) is not in the scene history." )

		inspection = self.__inspect( s["editScope2"]["out"], "/light", "exposure", s["editScope2"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "Edit is not in the current edit scope. Change scope to editScope to disable." )
		self.assertRaisesRegex( IECore.Exception, "Cannot disable edit : Edit is not in the current edit scope. Change scope to editScope to disable.", inspection.disableEdit )

		Gaffer.MetadataAlgo.setReadOnly( s["editScope"], True )
		inspection = self.__inspect( s["editScope"]["out"], "/light", "exposure", s["editScope"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "editScope is locked." )
		self.assertRaisesRegex( IECore.Exception, "Cannot disable edit : editScope is locked.", inspection.disableEdit )

		Gaffer.MetadataAlgo.setReadOnly( s["editScope"], False )
		inspection = self.__inspect( s["editScope"]["out"], "/light", "exposure", s["editScope"] )
		self.assertTrue( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "" )
		inspection.disableEdit()
		self.assertFalse( lightEdit["enabled"].getValue() )

		inspection = self.__inspect( s["editScope"]["out"], "/light", "exposure", s["editScope"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "Edit is not in the current edit scope. Change scope to None to disable." )

		inspection = self.__inspect( s["editScope"]["out"], "/light", "exposure", None )
		self.assertEqual( inspection.source(), s["light"]["parameters"]["exposure"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "Disabling edits not supported for this plug." )

	def testDisabledTweaks( self ) :

		light = GafferSceneTest.TestLight()

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		shaderTweaks = GafferScene.ShaderTweaks()
		shaderTweaks["in"].setInput( light["out"] )
		shaderTweaks["filter"].setInput( lightFilter["out"] )
		exposureTweak = Gaffer.TweakPlug( "exposure", 10 )
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
		exposureTweak = Gaffer.TweakPlug( "exposure", 10 )
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

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )

		self.assertIsNone( self.__inspect( light["out"], "/light", "exposure", attribute = "nothingHere" ) )
		self.assertIsNone( self.__inspect( editScope["out"], "/light", "exposure", editScope, attribute = "nothingHere" ) )

	def testNonExistentParameter( self ) :

		light = GafferSceneTest.TestLight()

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )

		self.assertIsNone( self.__inspect( light["out"], "/light", "nothingHere" ) )
		self.assertIsNone( self.__inspect( editScope["out"], "/light", "nothingHere", editScope ) )

	def testWrongAttributeType( self ) :

		light = GafferSceneTest.TestLight()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		attr = GafferScene.CustomAttributes()
		attr["attributes"].addChild(
			Gaffer.NameValuePlug( "test", 10, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		)
		attr["in"].setInput( light["out"] )
		attr["filter"].setInput( filter["out"] )

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( attr["out"] )

		self.assertIn( "test", editScope["out"].attributes( "/light" ) )

		self.assertIsNone( self.__inspect( editScope["out"], "/light", "nothingHere", None, attribute = "test" ) )
		self.assertIsNone( self.__inspect( editScope["out"], "/light", "nothingHere", editScope, attribute = "test" ) )

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

	def testUnsupportedSourceNode( self ) :

		s = Gaffer.ScriptNode()

		s["sceneReader"] = GafferScene.SceneReader()
		s["sceneReader"]["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/usdFiles/sphereLight.usda" )

		s["editScope"] = Gaffer.EditScope()
		s["editScope"].setup( s["sceneReader"]["out"] )
		s["editScope"]["in"].setInput( s["sceneReader"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["sceneReader"]["out"], "/SpotLight23", "intensity", None ),
			source = None,
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = False,
			nonEditableReason = "No editable source found in history."
		)

		inspection = self.__inspect( s["editScope"]["out"], "/SpotLight23", "intensity", s["editScope"] )
		edit = inspection.acquireEdit()

		self.assertIsNotNone( edit )

		self.__assertExpectedResult(
			inspection,
			source = None,
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = edit
		)

	def testReadOnlyPlug( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( s["light"]["out"], "/light", "intensity", None ),
			source = s["light"]["parameters"]["intensity"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["light"]["parameters"]["intensity"]
		)

		Gaffer.MetadataAlgo.setReadOnly( s["light"]["parameters"]["intensity"], True )

		self.__assertExpectedResult(
			self.__inspect( s["light"]["out"], "/light", "intensity", None ),
			source = s["light"]["parameters"]["intensity"],
			sourceType = SourceType.Other,
			editable = False,
			nonEditableReason = "light.parameters.intensity is locked."
		)

	def testAnimatedPlugEditability( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		curve = Gaffer.Animation.acquire( s["light"]["parameters"]["exposure"] )
		key = Gaffer.Animation.Key( time = 10, value = 10 )
		curve.addKey( key )

		self.assertTrue( Gaffer.Animation.isAnimated( s["light"]["parameters"]["exposure"] ) )

		with Gaffer.Context() as context :
			context.setFrame( 10 )

			self.__assertExpectedResult(
				self.__inspect( s["light"]["out"], "/light", "exposure", None ),
				source = s["light"]["parameters"]["exposure"],
				sourceType = SourceType.Other,
				editable = True,
				edit = s["light"]["parameters"]["exposure"]
			)

		Gaffer.MetadataAlgo.setReadOnly( curve, True )

		with Gaffer.Context() as context :
			context.setFrame( 10 )

			self.__assertExpectedResult(
				self.__inspect( s["light"]["out"], "/light", "exposure", None ),
				source = s["light"]["parameters"]["exposure"],
				sourceType = SourceType.Other,
				editable = False,
				nonEditableReason = "Animation.curves.curve0 is locked."
			)

	def testPlugWithInput( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()

		s["scope"] = Gaffer.EditScope()
		s["scope"].setup( s["light"]["out"] )
		s["scope"]["in"].setInput( s["light"]["out"] )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression(
			"parent[\"light\"][\"parameters\"][\"exposure\"] = 10.0",
			"python"
		)

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.assertEqual( s["light"]["parameters"]["exposure"].getValue(), 10 )

		self.__assertExpectedResult(
			self.__inspect( s["scope"]["out"], "/light", "exposure", None ),
			source = s["light"]["parameters"]["exposure"],
			sourceType = SourceType.Other,
			editable = False,
			nonEditableReason = "light.parameters.exposure has a non-settable input."
		)

		inspection = self.__inspect( s["scope"]["out"], "/light", "exposure", s["scope"] )

		self.assertTrue( inspection.editable() )

		edit = inspection.acquireEdit()
		edit["enabled"].setValue( True )
		edit["value"].setValue( 5 )

		self.__assertExpectedResult(
			self.__inspect( s["scope"]["out"], "/light", "exposure", s["scope"] ),
			source = edit,
			sourceType = SourceType.EditScope,
			editable = True,
			edit = s["scope"]["LightEdits"]["edits"]["row1"]["cells"]["exposure"]["value"]
		)

		s["expression2"] = Gaffer.Expression()
		s["expression2"].setExpression(
			"parent[\"scope\"][\"LightEdits\"][\"edits\"][\"row1\"][\"cells\"][\"exposure\"][\"value\"][\"value\"] = 20",
			"python"
		)

		self.__assertExpectedResult(
			self.__inspect( s["scope"]["out"], "/light", "exposure", s["scope"] ),
			source = edit,
			sourceType = SourceType.EditScope,
			editable = False,
			nonEditableReason = "scope.LightEdits.edits.row1.cells.exposure.value.value has a non-settable input."
		)

	def testDefaultSpreadsheetRow( self ) :

		s = Gaffer.ScriptNode()

		s["spreadsheet"] = Gaffer.Spreadsheet()
		s["spreadsheet"]["rows"].addColumn( Gaffer.FloatPlug( "exposure" ) )
		s["spreadsheet"]["rows"]["default"]["cells"]["exposure"]["value"].setValue( 5 )

		s["light"] = GafferSceneTest.TestLight()
		s["light"]["parameters"]["exposure"].setInput( s["spreadsheet"]["out"]["exposure"] )

		self.assertEqual( s["light"]["parameters"]["exposure"].getValue(), 5 )

		self.__assertExpectedResult(
			self.__inspect( s["light"]["out"], "/light", "exposure", None ),
			source = s["spreadsheet"]["rows"]["default"]["cells"]["exposure"]["value"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = False,
			nonEditableReason = "spreadsheet.rows.default.cells.exposure.value is a spreadsheet default row."
		)

	def testLightOptionalValuePlug( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()

		s["light"]["parameters"].addChild( Gaffer.OptionalValuePlug( "testFloat", Gaffer.FloatPlug(), False ) )

		s["editScope"] = Gaffer.EditScope()
		s["editScope"].setup( s["light"]["out"] )
		s["editScope"]["in"].setInput( s["light"]["out"] )

		self.assertIsNone( self.__inspect( s["editScope"]["out"], "/light", "testFloat" ) )
		self.assertIsNone( self.__inspect( s["editScope"]["out"], "/light", "testFloat", s["editScope"] ) )

		s["light"]["parameters"]["testFloat"]["enabled"].setValue( True )

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( s["editScope"]["out"], "/light", "testFloat" ),
			source = s["light"]["parameters"]["testFloat"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["light"]["parameters"]["testFloat"]
		)

		inspection = self.__inspect( s["editScope"]["out"], "/light", "testFloat", s["editScope"] )
		self.assertIsNotNone( inspection )
		edit = inspection.acquireEdit()
		edit["enabled"].setValue( True )
		edit["value"].setValue( 5.0 )

		self.__assertExpectedResult(
			self.__inspect( s["editScope"]["out"], "/light", "testFloat", s["editScope"] ),
			source = edit,
			sourceType = SourceType.EditScope,
			editable = True,
			edit = edit
		)

	def testNetworkTweak( self ) :

		s = Gaffer.ScriptNode()

		s["add"] = GafferScene.Shader()
		s["add"]["parameters"]["a"] = Gaffer.Color3fPlug()
		s["add"]["out"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )

		s["light"] = GafferSceneTest.TestLight()
		s["light"]["parameters"]["intensity"].setInput( s["add"]["out"] )

		s["filter"] = GafferScene.PathFilter()
		s["filter"]["paths"].setValue( IECore.StringVectorData( ["/light"] ) )

		s["tweaks"] = GafferScene.ShaderTweaks()
		s["tweaks"]["in"].setInput( s["light"]["out"] )

		s["tweaks"]["filter"].setInput( s["filter"]["out"] )
		addATweak = Gaffer.TweakPlug( "add.a", imath.Color3f( 0.0, 0.5, 1.0 ) )
		s["tweaks"]["tweaks"].addChild( addATweak )

		self.__assertExpectedResult(
			self.__inspect( s["tweaks"]["out"], "/light", ( "add", "a" ) ),
			source = addATweak,
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = addATweak
		)

	def testShaderNetwork( self ) :

		s = Gaffer.ScriptNode()

		s["add"] = GafferScene.Shader()
		s["add"]["parameters"]["a"] = Gaffer.Color3fPlug()
		s["add"]["out"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )

		s["add1"] = GafferScene.Shader()
		s["add1"]["parameters"]["a"] = Gaffer.Color3fPlug()
		s["add1"]["parameters"]["a"].setInput( s["add"]["out"] )
		s["add1"]["parameters"]["b"] = Gaffer.Color3fPlug()
		s["add1"]["out"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )

		s["multiOut"] = GafferScene.Shader()
		s["multiOut"]["parameters"]["a"] = Gaffer.Color3fPlug()
		s["multiOut"]["parameters"]["b"] = Gaffer.Color3fPlug()
		s["multiOut"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["multiOut"]["out"]["a"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )
		s["multiOut"]["out"]["b"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )

		s["box"] = Gaffer.Box()

		s["box"]["add"] = GafferScene.Shader()
		s["box"]["add"]["parameters"]["a"] = Gaffer.Color3fPlug()
		s["box"]["add"]["out"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )

		s["box"]["outColor"] = Gaffer.BoxOut()
		s["box"]["outColor"].setup( s["box"]["add"]["out"] )
		s["box"]["outColor"]["in"].setInput( s["box"]["add"]["out"] )

		s["srf"] = GafferScene.Shader()
		s["srf"]["type"].setValue( "test:surface" )

		s["srf"]["parameters"]["a"] = Gaffer.Color3fPlug()
		s["srf"]["parameters"]["a"].setInput( s["add1"]["out"] )

		s["srf"]["parameters"]["b"] = Gaffer.Color3fPlug()
		s["srf"]["parameters"]["b"].setInput( s["multiOut"]["out"]["a"] )
		s["srf"]["parameters"]["c"] = Gaffer.Color3fPlug()
		s["srf"]["parameters"]["c"].setInput( s["multiOut"]["out"]["b"] )

		s["srf"]["parameters"]["d"] = Gaffer.Color3fPlug()
		s["srf"]["parameters"]["d"].setInput( s["box"]["out"] )

		s["srf"]["parameters"]["e"] = Gaffer.Color3fPlug()

		s["srf"]["out"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out )

		s["cube"] = GafferScene.Cube()

		s["assign"] = GafferScene.ShaderAssignment()
		s["assign"]["in"].setInput( s["cube"]["out"] )
		s["assign"]["shader"].setInput( s["srf"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["assign"]["out"], "/cube", ( "add", "a" ), attribute = "test:surface" ),
			source = s["add"]["parameters"]["a"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = s["add"]["parameters"]["a"],
			editWarning = "Edits to add may affect other locations in the scene."
		)

		self.__assertExpectedResult(
			self.__inspect( s["assign"]["out"], "/cube", ( "add1", "b" ), attribute = "test:surface" ),
			source = s["add1"]["parameters"]["b"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = s["add1"]["parameters"]["b"],
			editWarning = "Edits to add1 may affect other locations in the scene."
		)

		self.__assertExpectedResult(
			self.__inspect( s["assign"]["out"], "/cube", ( "multiOut", "a" ), attribute = "test:surface" ),
			source = s["multiOut"]["parameters"]["a"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = s["multiOut"]["parameters"]["a"],
			editWarning = "Edits to multiOut may affect other locations in the scene."
		)

		self.__assertExpectedResult(
			self.__inspect( s["assign"]["out"], "/cube", ( "add2", "a" ), attribute = "test:surface" ),
			source = s["box"]["add"]["parameters"]["a"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = s["box"]["add"]["parameters"]["a"],
			editWarning = "Edits to box.add may affect other locations in the scene."
		)


if __name__ == "__main__":
	unittest.main()
