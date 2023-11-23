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
import GafferUITest
import GafferScene
import GafferSceneUI

class OptionInspectorTest( GafferUITest.TestCase ) :

	def testName( self ) :

		plane = GafferScene.Plane()

		inspector = GafferSceneUI.Private.OptionInspector( plane["out"], None, "option:foo" )
		self.assertEqual( inspector.name(), "option:foo" )

	@staticmethod
	def __inspect( scene, optionName, editScope = None ) :

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.OptionInspector( scene, editScopePlug, optionName )
		with Gaffer.Context() as context :
			return inspector.inspect()

	def __assertExpectedResult(
		self,
		result,
		source,
		sourceType,
		editable,
		nonEditableReason = "",
		edit = None,
		editWarning = ""
	) :

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

		options = GafferScene.StandardOptions()
		options["options"]["renderCamera"]["enabled"].setValue( True )
		options["options"]["renderCamera"]["value"].setValue( "/customCamera" )

		self.assertEqual(
			self.__inspect( options["out"], "render:camera" ).value().value,
			"/customCamera"
		)

	def testSourceAndEdits( self ) :

		s = Gaffer.ScriptNode()

		s["standardOptions"] = GafferScene.StandardOptions()
		s["standardOptions"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["standardOptions"]["options"]["renderCamera"]["value"].setValue( "/defaultCamera" )

		s["group"] = GafferScene.Group()
		s["editScope1"] = Gaffer.EditScope()
		s["editScope2"] = Gaffer.EditScope()

		s["group"]["in"][0].setInput( s["standardOptions"]["out"] )

		s["editScope1"].setup( s["group"]["out"] )
		s["editScope1"]["in"].setInput( s["group"]["out"] )

		s["editScope2"].setup( s["editScope1"]["out"] )
		s["editScope2"]["in"].setInput( s["editScope1"]["out"] )

		# Should be able to edit standardOptions directly.

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "render:camera" ),
			source = s["standardOptions"]["options"]["renderCamera"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["standardOptions"]["options"]["renderCamera"]
		)

		# Even if there is an edit scope in the way

		self.__assertExpectedResult(
			self.__inspect( s["editScope1"]["out"], "render:camera" ),
			source = s["standardOptions"]["options"]["renderCamera"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["standardOptions"]["options"]["renderCamera"]
		)

		# We shouldn't be able to edit it if we've been told to use an EditScope and it isn't in the history

		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "render:camera", s["editScope1"] ),
			source = s["standardOptions"]["options"]["renderCamera"],
			sourceType = SourceType.Other,
			editable = False,
			nonEditableReason = "The target EditScope (editScope1) is not in the scene history."
		)

		# If it is in the history though, and we're told to use it, then we will.

		inspection = self.__inspect( s["editScope2"]["out"], "render:camera", s["editScope2"] )
		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireOptionEdit(
				s["editScope2"], "render:camera", createIfNecessary = False
			)
		)

		self.__assertExpectedResult(
			inspection,
			source = s["standardOptions"]["options"]["renderCamera"],
			sourceType = SourceType.Upstream,
			editable = True
		)

		optionEditScope2Edit = inspection.acquireEdit()
		self.assertIsNotNone( optionEditScope2Edit )
		self.assertEqual(
			optionEditScope2Edit,
			GafferScene.EditScopeAlgo.acquireOptionEdit(
				s["editScope2"], "render:camera", createIfNecessary = False
			)
		)

		# If there's an edit downstream of the EditScope we're asked to use,
		# then we're allowed to be editable still

		inspection = self.__inspect( s["editScope2"]["out"], "render:camera", s["editScope1"] )
		self.assertTrue( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "" )
		self.assertEqual(
			inspection.acquireEdit(),
			GafferScene.EditScopeAlgo.acquireOptionEdit(
				s["editScope1"], "render:camera", createIfNecessary = False
			)
		)
		self.assertEqual( inspection.editWarning(), "" )

		# If there is a source node inside an edit scope, make sure we use that

		s["editScope1"]["standardOptions2"] = GafferScene.StandardOptions()
		s["editScope1"]["standardOptions2"]["options"]["resolutionMultiplier"]["enabled"].setValue( True )
		s["editScope1"]["standardOptions2"]["options"]["resolutionMultiplier"]["value"].setValue( 4.0 )
		s["editScope1"]["standardOptions2"]["in"].setInput( s["editScope1"]["BoxIn"]["out"] )
		s["editScope1"]["OptionEdits"]["in"].setInput( s["editScope1"]["standardOptions2"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "render:resolutionMultiplier", s["editScope1"] ),
			source = s["editScope1"]["standardOptions2"]["options"]["resolutionMultiplier"],
			sourceType = SourceType.EditScope,
			editable = True,
			edit = s["editScope1"]["standardOptions2"]["options"]["resolutionMultiplier"]
		)

		# If there is a OptionTweaks node in the scope's processor, make sure we use that

		cameraEdit = GafferScene.EditScopeAlgo.acquireOptionEdit(
			s["editScope1"], "render:camera", createIfNecessary = True
		)
		cameraEdit["enabled"].setValue( True )
		cameraEdit["value"].setValue( "/bar" )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "render:camera", s["editScope1"] ),
			source = cameraEdit,
			sourceType = SourceType.EditScope,
			editable = True,
			edit = cameraEdit
		)

		# If there is a StandardOptions node downstream of the scope's scene processor, make sure we use that

		s["editScope1"]["standardOptions3"] = GafferScene.StandardOptions()
		s["editScope1"]["standardOptions3"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["editScope1"]["standardOptions3"]["options"]["renderCamera"]["value"].setValue( "/baz" )
		s["editScope1"]["standardOptions3"]["in"].setInput( s["editScope1"]["OptionEdits"]["out"] )
		s["editScope1"]["BoxOut"]["in"].setInput( s["editScope1"]["standardOptions3"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "render:camera", s["editScope1"] ),
			source = s["editScope1"]["standardOptions3"]["options"]["renderCamera"],
			sourceType = SourceType.EditScope,
			editable = True,
			edit = s["editScope1"]["standardOptions3"]["options"]["renderCamera"]
		)

		# If there is a StandardOptions node outside of an edit scope, make sure we use that with no scope

		s["independentOptions"] = GafferScene.StandardOptions()
		s["independentOptions"]["options"]["renderCamera"]["enabled"].setValue( True )
		s["independentOptions"]["options"]["renderCamera"]["value"].setValue( "/camera" )
		s["independentOptions"]["in"].setInput( s["editScope2"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["independentOptions"]["out"], "render:camera", None ),
			source = s["independentOptions"]["options"]["renderCamera"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["independentOptions"]["options"]["renderCamera"]
		)

		# Check editWarnings and nonEditableReasons

		self.__assertExpectedResult(
			self.__inspect( s["independentOptions"]["out"], "render:camera", s["editScope2"] ),
			source = s["independentOptions"]["options"]["renderCamera"],
			sourceType = SourceType.Downstream,
			editable = True,
			edit = optionEditScope2Edit,
			editWarning = "Option has edits downstream in independentOptions."
		)

		s["editScope2"]["enabled"].setValue( False )

		self.__assertExpectedResult(
			self.__inspect( s["independentOptions"]["out"], "render:camera", s["editScope2"] ),
			source = s["independentOptions"]["options"]["renderCamera"],
			sourceType = SourceType.Downstream,
			editable = False,
			nonEditableReason = "The target EditScope (editScope2) is disabled."
		)

		s["editScope2"]["enabled"].setValue( True )
		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"], True )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "render:camera", s["editScope2"] ),
			source = s["editScope1"]["standardOptions3"]["options"]["renderCamera"],
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2 is locked."
		)

		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"], False )
		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"]["OptionEdits"]["edits"], True )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "render:camera", s["editScope2"] ),
			source = s["editScope1"]["standardOptions3"]["options"]["renderCamera"],
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2.OptionEdits.edits is locked."
		)

		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"]["OptionEdits"], True )
		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "render:camera", s["editScope2"] ),
			source = s["editScope1"]["standardOptions3"]["options"]["renderCamera"],
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2.OptionEdits is locked."
		)

	def testDisabledTweaks( self ) :

		options = GafferScene.StandardOptions()
		options["options"]["renderCamera"]["enabled"].setValue( True )
		options["options"]["renderCamera"]["value"].setValue( "/defaultCamera" )

		optionTweaks = GafferScene.OptionTweaks()
		optionTweaks["in"].setInput( options["out"] )
		cameraTweak = Gaffer.TweakPlug( "render:camera", "/bar" )
		optionTweaks["tweaks"].addChild( cameraTweak )

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( optionTweaks["out"], "render:camera" ),
			source = cameraTweak,
			sourceType = SourceType.Other,
			editable = True,
			edit = cameraTweak
		)

		cameraTweak["enabled"].setValue( False )

		self.__assertExpectedResult(
			self.__inspect( optionTweaks["out"], "render:camera" ),
			source = options["options"]["renderCamera"],
			sourceType = SourceType.Other,
			editable = True,
			edit = options["options"]["renderCamera"]
		)

	def testNonExistentOption( self ) :

		plane = GafferScene.Plane()
		self.assertIsNone( self.__inspect( plane["out"], "not:an:option" ) )

	def testDirtiedSignal( self ) :

		camera = GafferScene.Camera()

		options = GafferScene.StandardOptions()
		options["in"].setInput( camera["out"] )
		options["options"]["renderCamera"]["enabled"].setValue( True )
		options["options"]["renderCamera"]["value"].setValue( "/defaultCamera" )

		editScope1 = Gaffer.EditScope()
		editScope1.setup( options["out"] )
		editScope1["in"].setInput( options["out"] )

		editScope2 = Gaffer.EditScope()
		editScope2.setup( editScope1["out"] )
		editScope2["in"].setInput( editScope1["out"] )

		settings = Gaffer.Node()
		settings["editScope"] = Gaffer.Plug()

		inspector = GafferSceneUI.Private.OptionInspector(
			editScope2["out"], settings["editScope"], "render:camera"
		)

		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		# Changing the option should dirty the inspector
		options["options"]["renderCamera"]["value"].setValue( "/newCamera" )
		self.assertEqual( len( cs ), 1 )

		# Changing sets should not
		camera["sets"].setValue( "foo" )
		self.assertEqual( len( cs ), 1 )

		# Changing the EditScope should dirty the inspector
		settings["editScope"].setInput( editScope1["enabled"] )
		self.assertEqual( len( cs ), 2 )
		settings["editScope"].setInput( editScope2["enabled"] )
		self.assertEqual( len( cs ), 3 )
		settings["editScope"].setInput( None )
		self.assertEqual( len( cs ), 4 )

	def testReadOnlyMetadataSignalling( self ) :

		options = GafferScene.StandardOptions()
		options["options"]["renderCamera"]["enabled"].setValue( True )
		options["options"]["renderCamera"]["value"].setValue( "/defaultCamera" )

		editScope = Gaffer.EditScope()
		editScope.setup( options["out"] )
		editScope["in"].setInput( options["out"] )

		settings = Gaffer.Node()
		settings["editScope"] = Gaffer.Plug()

		inspector = GafferSceneUI.Private.OptionInspector(
			editScope["out"], settings["editScope"], "render:camera"
		)

		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		Gaffer.MetadataAlgo.setReadOnly( editScope, True )
		Gaffer.MetadataAlgo.setReadOnly( editScope, False )
		self.assertEqual( len( cs ), 0 )  # Changes not relevant because we're not using the EditScope

		settings["editScope"].setInput( editScope["enabled"] )
		self.assertEqual( len( cs ), 1 )
		Gaffer.MetadataAlgo.setReadOnly( editScope, True )
		self.assertEqual( len( cs ), 2 )  # Change affects the result of `inspect().editable()`

if __name__ == "__main__" :
	unittest.main()
