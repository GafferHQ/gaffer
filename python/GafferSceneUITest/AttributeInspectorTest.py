##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

class AttributeInspectorTest( GafferUITest.TestCase ) :

	def testName( self ) :

		light = GafferSceneTest.TestLight()

		inspector = GafferSceneUI.Private.AttributeInspector( light["out"], None, "gl:visualiser:scale" )
		self.assertEqual( inspector.name(), "gl:visualiser:scale" )

	@staticmethod
	def __inspect( scene, path, attribute, editScope=None ) :

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.AttributeInspector( scene, editScopePlug, attribute )
		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( path.split( "/" )[1:] )
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

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		light["visualiserAttributes"]["scale"]["value"].setValue( 2.0 )

		self.assertEqual(
			self.__inspect( light["out"], "/light", "gl:visualiser:scale" ).value(),
			IECore.FloatData( 2.0 )
		)

	def testFallbackValue( self ) :

		light = GafferSceneTest.TestLight()
		group = GafferScene.Group()
		group["in"][0].setInput( light["out"] )

		# With no "gl:visualiser:scale" attribute at /group/light, the inspection returns
		# the registered default value with `sourceType` identifying it as a fallback.

		inspection = self.__inspect( group["out"], "/group/light", "gl:visualiser:scale" )
		self.assertEqual( inspection.value().value, Gaffer.Metadata.value( "attribute:gl:visualiser:scale", "defaultValue" ) )
		self.assertEqual( inspection.sourceType(), GafferSceneUI.Private.Inspector.Result.SourceType.Fallback )
		self.assertEqual( inspection.fallbackDescription(), "Default value" )

		globalGlAttributes = GafferScene.OpenGLAttributes()
		globalGlAttributes["in"].setInput( group["out"] )
		globalGlAttributes["global"].setValue( True )
		globalGlAttributes["attributes"]["visualiserScale"]["enabled"].setValue( True )
		globalGlAttributes["attributes"]["visualiserScale"]["value"].setValue( 4.0 )

		# With no "gl:visualiser:scale" attribute at /group/light, the inspection returns
		# the inherited global attribute value with `sourceType` identifying it as a fallback.

		inspection = self.__inspect( globalGlAttributes["out"], "/group/light", "gl:visualiser:scale" )
		self.assertEqual( inspection.value(), IECore.FloatData( 4.0 ) )
		self.assertEqual( inspection.sourceType(), GafferSceneUI.Private.Inspector.Result.SourceType.Fallback )
		self.assertEqual( inspection.fallbackDescription(), "Global attribute" )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		glAttributes = GafferScene.OpenGLAttributes()
		glAttributes["in"].setInput( globalGlAttributes["out"] )
		glAttributes["filter"].setInput( groupFilter["out"] )
		glAttributes["attributes"]["visualiserScale"]["enabled"].setValue( True )
		glAttributes["attributes"]["visualiserScale"]["value"].setValue( 2.0 )

		# With no "gl:visualiser:scale" attribute at /group/light, the inspection returns
		# the inherited attribute value from /group with `sourceType` identifying it as a fallback.

		inspection = self.__inspect( glAttributes["out"], "/group/light", "gl:visualiser:scale" )
		self.assertEqual( inspection.value(), IECore.FloatData( 2.0 ) )
		self.assertEqual( inspection.sourceType(), GafferSceneUI.Private.Inspector.Result.SourceType.Fallback )
		self.assertEqual( inspection.fallbackDescription(), "Inherited from /group" )

		# With a "gl:visualiser:scale" attribute created at the inspected location, it is
		# returned instead of the inherited fallback.

		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		light["visualiserAttributes"]["scale"]["value"].setValue( 4.0 )

		inspection = self.__inspect( glAttributes["out"], "/group/light", "gl:visualiser:scale" )
		self.assertEqual( inspection.value(), IECore.FloatData( 4.0 ) )
		self.assertEqual( inspection.sourceType(), GafferSceneUI.Private.Inspector.Result.SourceType.Other )

	def testSourceAndEdits( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()
		s["light"]["visualiserAttributes"]["scale"]["enabled"].setValue( True )

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
			self.__inspect( s["group"]["out"], "/group/light", "gl:visualiser:scale", None ),
			source = s["light"]["visualiserAttributes"]["scale"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["light"]["visualiserAttributes"]["scale"]
		)

		# Even if there is an edit scope in the way

		self.__assertExpectedResult(
			self.__inspect( s["editScope1"]["out"], "/group/light", "gl:visualiser:scale", None),
			source = s["light"]["visualiserAttributes"]["scale"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["light"]["visualiserAttributes"]["scale"]
		)

		# We shouldn't be able to edit it if we've been told to use and EditScope and it isn't in the history

		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "/group/light", "gl:visualiser:scale", s["editScope1"] ),
			source = s["light"]["visualiserAttributes"]["scale"],
			sourceType = SourceType.Other,
			editable=False,
			nonEditableReason = "The target edit scope editScope1 is not in the scene history."
		)

		# If it is in the history though, and we're told to use it, then we will.

		inspection = self.__inspect( s["editScope2"]["out"], "/group/light", "gl:visualiser:scale", s["editScope2"] )

		self.assertIsNone(
			GafferScene.EditScopeAlgo.acquireAttributeEdit(
				s["editScope2"], "/group/light", "gl:visualiser:scale", createIfNecessary = False
			)
		)

		self.__assertExpectedResult(
			inspection,
			source=s["light"]["visualiserAttributes"]["scale"],
			sourceType=SourceType.Upstream,
			editable = True
		)

		lightEditScope2Edit = inspection.acquireEdit()
		self.assertIsNotNone( lightEditScope2Edit )
		self.assertEqual(
			lightEditScope2Edit,
			GafferScene.EditScopeAlgo.acquireAttributeEdit(
				s["editScope2"], "/group/light", "gl:visualiser:scale", createIfNecessary = False
			)
		)

		# If there's an edit downstream of the EditScope we're asked to use,
		# then we're allowed to be editable still

		inspection = self.__inspect( s["editScope2"]["out"], "/group/light", "gl:visualiser:scale", s["editScope1"] )
		self.assertTrue( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "" )
		lightEditScope1Edit = inspection.acquireEdit()
		self.assertIsNotNone( lightEditScope1Edit )
		self.assertEqual(
			lightEditScope1Edit,
			GafferScene.EditScopeAlgo.acquireAttributeEdit(
				s["editScope1"], "/group/light", "gl:visualiser:scale", createIfNecessary = False
			)
		)
		self.assertEqual( inspection.editWarning(), "" )

		# If there is a source node inside an edit scope, make sure we use that

		s["editScope1"]["light2"] = GafferSceneTest.TestLight()
		s["editScope1"]["light2"]["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		s["editScope1"]["light2"]["visualiserAttributes"]["scale"]["value"].setValue( 0.5 )
		s["editScope1"]["light2"]["name"].setValue( "light2" )
		s["editScope1"]["parentLight2"] = GafferScene.Parent()
		s["editScope1"]["parentLight2"]["parent"].setValue( "/" )
		s["editScope1"]["parentLight2"]["children"][0].setInput( s["editScope1"]["light2"]["out"] )
		s["editScope1"]["parentLight2"]["in"].setInput( s["editScope1"]["BoxIn"]["out"] )
		s["editScope1"]["AttributeEdits"]["in"].setInput( s["editScope1"]["parentLight2"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/light2", "gl:visualiser:scale", s["editScope1"] ),
			source = s["editScope1"]["light2"]["visualiserAttributes"]["scale"],
			sourceType = SourceType.EditScope,
			editable = True,
			edit = s["editScope1"]["light2"]["visualiserAttributes"]["scale"]
		)

		# If there is a tweak in the scope's processor, make sure we use that

		light2Edit = GafferScene.EditScopeAlgo.acquireAttributeEdit(
			s["editScope1"], "/light2", "gl:visualiser:scale", createIfNecessary = True
		)
		light2Edit["enabled"].setValue( True )
		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/light2", "gl:visualiser:scale", s["editScope1"] ),
			source = light2Edit,
			sourceType = SourceType.EditScope,
			editable = True,
			edit = light2Edit
		)

		# If there is a manual tweak downstream of the scope's scene processor, make sure we use that

		s["editScope1"]["tweakLight2"] = GafferScene.AttributeTweaks()
		s["editScope1"]["tweakLight2"]["in"].setInput( s["editScope1"]["AttributeEdits"]["out"] )
		s["editScope1"]["tweakLight2Filter"] = GafferScene.PathFilter()
		s["editScope1"]["tweakLight2Filter"]["paths"].setValue( IECore.StringVectorData( [ "/light2" ] ) )
		s["editScope1"]["tweakLight2"]["filter"].setInput( s["editScope1"]["tweakLight2Filter"]["out"] )
		s["editScope1"]["BoxOut"]["in"].setInput( s["editScope1"]["tweakLight2"]["out"] )

		editScopeAttributeTweak = Gaffer.TweakPlug( "gl:visualiser:scale", 4.0 )
		s["editScope1"]["tweakLight2"]["tweaks"].addChild( editScopeAttributeTweak )

		self.__assertExpectedResult(
			self.__inspect( s["editScope2"]["out"], "/light2", "gl:visualiser:scale", s["editScope1"] ),
			source = editScopeAttributeTweak,
			sourceType = SourceType.EditScope,
			editable = True,
			edit = editScopeAttributeTweak
		)

		# If there is a manual tweak outside of an edit scope, make sure we use that with no scope
		s["independentAttributeTweak"] = GafferScene.AttributeTweaks()
		s["independentAttributeTweak"]["in"].setInput( s["editScope2"]["out"] )

		s["independentAttributeTweakFilter"] = GafferScene.PathFilter()
		s["independentAttributeTweakFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/light" ] ) )
		s["independentAttributeTweak"]["filter"].setInput( s["independentAttributeTweakFilter"]["out"] )

		independentAttributeTweakPlug = Gaffer.TweakPlug( "gl:visualiser:scale", 8.0 )
		independentAttributeTweakPlug["enabled"].setValue( True )
		s["independentAttributeTweak"]["tweaks"].addChild( independentAttributeTweakPlug )

		self.__assertExpectedResult(
			self.__inspect( s["independentAttributeTweak"]["out"], "/group/light", "gl:visualiser:scale", None ),
			source = independentAttributeTweakPlug,
			sourceType = SourceType.Other,
			editable = True,
			edit = independentAttributeTweakPlug
		)

		# Check we show the last input plug if the source plug is an output

		scaleCurve = Gaffer.Animation.acquire( s["light"]["visualiserAttributes"]["scale"]["value"] )
		scaleCurve.addKey( Gaffer.Animation.Key( time = 1, value = 2 ) )

		self.__assertExpectedResult(
			self.__inspect( s["group"]["out"], "/group/light", "gl:visualiser:scale", None ),
			source = s["light"]["visualiserAttributes"]["scale"],
			sourceType = SourceType.Other,
			editable = True,
			edit = s["light"]["visualiserAttributes"]["scale"]
		)

		# Check editWarnings and nonEditableReasons

		self.__assertExpectedResult(
			self.__inspect( s["independentAttributeTweak"]["out"], "/group/light", "gl:visualiser:scale", s["editScope2"] ),
			source = independentAttributeTweakPlug,
			sourceType = SourceType.Downstream,
			editable = True,
			edit = lightEditScope2Edit,
			editWarning = "Attribute has edits downstream in independentAttributeTweak."
		)

		s["editScope2"]["enabled"].setValue( False )

		self.__assertExpectedResult(
			self.__inspect( s["independentAttributeTweak"]["out"], "/group/light", "gl:visualiser:scale", s["editScope2"] ),
			source = independentAttributeTweakPlug,
			sourceType = SourceType.Downstream,
			editable = False,
			nonEditableReason = "The target edit scope editScope2 is disabled."
		)

		s["editScope2"]["enabled"].setValue( True )
		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"], True )

		self.__assertExpectedResult(
			self.__inspect( s["independentAttributeTweak"]["out"], "/light2", "gl:visualiser:scale", s["editScope2"] ),
			source = editScopeAttributeTweak,
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2 is locked."
		)

		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"], False )
		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"]["AttributeEdits"]["edits"], True )

		self.__assertExpectedResult(
			self.__inspect( s["independentAttributeTweak"]["out"], "/light2", "gl:visualiser:scale", s["editScope2"] ),
			source = editScopeAttributeTweak,
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2.AttributeEdits.edits is locked."
		)

		Gaffer.MetadataAlgo.setReadOnly( s["editScope2"]["AttributeEdits"], True )

		self.__assertExpectedResult(
			self.__inspect( s["independentAttributeTweak"]["out"], "/light2", "gl:visualiser:scale", s["editScope2"] ),
			source = editScopeAttributeTweak,
			sourceType = SourceType.Upstream,
			editable = False,
			nonEditableReason = "editScope2.AttributeEdits is locked."
		)

	def testAttributesWarning( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( sphere["out"] )
		customAttributes["filter"].setInput( sphereFilter["out"] )
		customAttributes["attributes"].addChild(
			Gaffer.NameValuePlug(
				"test:attr",
				IECore.FloatData( 1.0 ),
				Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
				"testPlug"
			)
		)

		self.__assertExpectedResult(
			self.__inspect( customAttributes["out"], "/sphere", "test:attr", None ),
			source = customAttributes["attributes"]["testPlug"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = customAttributes["attributes"]["testPlug"],
			editWarning = "Edits to \"test:attr\" may affect other locations in the scene."
		)

	def testEditScopeNotInHistory( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		attributeTweaks = GafferScene.AttributeTweaks()
		attributeTweaks["in"].setInput( light["out"] )
		attributeTweaks["filter"].setInput( lightFilter["out"] )
		attributeTweaks["tweaks"].addChild( Gaffer.TweakPlug( "gl:visualiser:scale", 2.0 ) )

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( light["out"], "/light", "gl:visualiser:scale", editScope ),
			source = light["visualiserAttributes"]["scale"],
			sourceType = SourceType.Other,
			editable = False,
			nonEditableReason = "The target edit scope EditScope is not in the scene history."
		)

		self.__assertExpectedResult(
			self.__inspect( attributeTweaks["out"], "/light", "gl:visualiser:scale" ),
			source = attributeTweaks["tweaks"][0],
			sourceType = SourceType.Other,
			editable = True,
			edit = attributeTweaks["tweaks"][0]
		)

		self.__assertExpectedResult(
			self.__inspect( attributeTweaks["out"], "/light", "gl:visualiser:scale", editScope ),
			source = attributeTweaks["tweaks"][0],
			sourceType = SourceType.Other,
			editable = False,
			nonEditableReason = "The target edit scope EditScope is not in the scene history."
		)

	def testDisabledTweaks( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		attributeTweaks = GafferScene.AttributeTweaks()
		attributeTweaks["in"].setInput( light["out"] )
		attributeTweaks["filter"].setInput( lightFilter["out"] )
		scaleTweak = Gaffer.TweakPlug( "gl:visualiser:scale", 2.0 )
		attributeTweaks["tweaks"].addChild( scaleTweak )

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( attributeTweaks["out"], "/light", "gl:visualiser:scale" ),
			source = scaleTweak,
			sourceType = SourceType.Other,
			editable = True,
			edit = scaleTweak
		)

		scaleTweak["enabled"].setValue( False )

		self.__assertExpectedResult(
			self.__inspect( attributeTweaks["out"], "/light", "gl:visualiser:scale" ),
			source = light["visualiserAttributes"]["scale"],
			sourceType = SourceType.Other,
			editable = True,
			edit = light["visualiserAttributes"]["scale"]
		)

	def testEditScopeNesting( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		editScope1 = Gaffer.EditScope( "EditScope1" )
		editScope1.setup( light["out"] )
		editScope1["in"].setInput( light["out"] )

		i = self.__inspect( editScope1["out"], "/light", "gl:visualiser:scale", editScope1 )
		scope1Edit = i.acquireEdit()
		scope1Edit["enabled"].setValue( True )
		self.assertEqual( scope1Edit.ancestor( Gaffer.EditScope ), editScope1 )

		editScope2 = Gaffer.EditScope()
		editScope2.setup( light["out"] )
		editScope1.addChild( editScope2 )
		editScope2["in"].setInput( scope1Edit.ancestor( GafferScene.SceneProcessor )["out"] )
		editScope1["BoxOut"]["in"].setInput( editScope2["out"] )

		i = self.__inspect( editScope1["out"], "/light", "gl:visualiser:scale", editScope2 )
		scope2Edit = i.acquireEdit()
		scope2Edit["enabled"].setValue( True )
		self.assertEqual( scope2Edit.ancestor( Gaffer.EditScope ), editScope2 )

		# Check we still fin the edit in scope 1

		i = self.__inspect( editScope1["out"], "/light", "gl:visualiser:scale", editScope1 )
		self.assertEqual( i.acquireEdit()[0].ancestor( Gaffer.EditScope ), editScope1 )

	def testDownstreamSourceType( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )

		lightFilter = GafferScene.PathFilter()
		lightFilter["paths"].setValue( IECore.StringVectorData( [ "/light" ] ) )

		attributeTweaks = GafferScene.AttributeTweaks()
		attributeTweaks["in"].setInput( editScope["out"] )
		attributeTweaks["filter"].setInput( lightFilter["out"] )
		scaleTweak = Gaffer.TweakPlug( "gl:visualiser:scale", 2.0 )
		attributeTweaks["tweaks"].addChild( scaleTweak )

		self.__assertExpectedResult(
			self.__inspect( attributeTweaks["out"], "/light", "gl:visualiser:scale", editScope ),
			source = scaleTweak,
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Downstream,
			editable = True,
			edit = None,
			editWarning = "Attribute has edits downstream in AttributeTweaks."
		)

	def testLightInsideBox( self ) :

		box = Gaffer.Box()
		box["light"] = GafferSceneTest.TestLight()
		box["light"]["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		Gaffer.PlugAlgo.promote( box["light"]["out"] )

		self.__assertExpectedResult(
			self.__inspect( box["out"], "/light", "gl:visualiser:scale" ),
			source = box["light"]["visualiserAttributes"]["scale"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = box["light"]["visualiserAttributes"]["scale"]
		)

	def testDirtiedSignal( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		editScope1 = Gaffer.EditScope()
		editScope1.setup( light["out"] )
		editScope1["in"].setInput( light["out"] )

		editScope2 = Gaffer.EditScope()
		editScope2.setup( editScope1["out"] )
		editScope2["in"].setInput( editScope1["out"] )

		settings = Gaffer.Node()
		settings["editScope"] = Gaffer.Plug()

		inspector = GafferSceneUI.Private.AttributeInspector(
			editScope2["out"], settings["editScope"], "gl:visualiser:scale"
		)

		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		# Tweaking an attribute should dirty the inspector
		light["visualiserAttributes"]["scale"]["value"].setValue( 2.0 )
		self.assertEqual( len( cs ) , 1 )

		# But tweaking the transform should not.
		light["transform"]["translate"]["x"].setValue( 10 )
		self.assertEqual( len( cs ), 1 )

		# Changing EditScope should also dirty the inspector
		settings["editScope"].setInput( editScope1["enabled"] )
		self.assertEqual( len( cs ), 2 )
		settings["editScope"].setInput( editScope2["enabled"] )
		self.assertEqual( len( cs ), 3 )
		settings["editScope"].setInput( None )
		self.assertEqual( len( cs ), 4 )

	def testNonExistentLocation( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )
		self.assertIsNone( self.__inspect( light["out"], "/nothingHere", "gl:visualiser:scale" ) )

	def testNonExistentAttribute( self ) :

		light = GafferSceneTest.TestLight()
		self.assertIsNone( self.__inspect( light["out"], "/light", "bad:attribute" ) )

	def testReadOnlyMetadataSignalling( self ) :

		light = GafferSceneTest.TestLight()
		light["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )

		settings = Gaffer.Node()
		settings["editScope"] = Gaffer.Plug()

		inspector = GafferSceneUI.Private.AttributeInspector(
			editScope["out"], settings["editScope"], "gl:visualiser:scale"
		)

		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		Gaffer.MetadataAlgo.setReadOnly( editScope, True )
		Gaffer.MetadataAlgo.setReadOnly( editScope, False )
		self.assertEqual( len( cs ), 0 ) # Changes not relevant because we're not using the EditScope.

		settings["editScope"].setInput( editScope["enabled"] )
		self.assertEqual( len( cs ), 1 )
		Gaffer.MetadataAlgo.setReadOnly( editScope, True )
		self.assertEqual( len( cs ), 2 ) # Change affects the result of `inspect().editable()`

	def testCameraAttribute( self ) :

		camera = GafferScene.Camera()
		camera["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		self.__assertExpectedResult(
			self.__inspect( camera["out"], "/camera", "gl:visualiser:scale", None ),
			source = camera["visualiserAttributes"]["scale"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = camera["visualiserAttributes"]["scale"]
		)

	def testAttributes( self ) :

		sphere = GafferScene.Sphere()

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		customAttributes = GafferScene.CustomAttributes()
		customAttributes["in"].setInput( sphere["out"] )
		customAttributes["filter"].setInput( sphereFilter["out"] )
		customAttributes["attributes"].addChild(
			Gaffer.NameValuePlug(
				"test:attr",
				IECore.FloatData( 1.0 ),
				Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
				"testPlug"
			)
		)

		self.__assertExpectedResult(
			self.__inspect( customAttributes["out"], "/sphere", "test:attr", None ),
			source = customAttributes["attributes"]["testPlug"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = customAttributes["attributes"]["testPlug"],
			editWarning = "Edits to \"test:attr\" may affect other locations in the scene."
		)

	def testDisabledAttribute( self ) :

		light = GafferSceneTest.TestLight()

		group = GafferScene.Group()
		group["in"][0].setInput( light["out"] )

		# The value of the attribute isn't editable in this case, but the `enabled`
		# plug is, so it is considered editable.
		self.__assertExpectedResult(
			self.__inspect( light["out"], "/light", "gl:visualiser:scale", None ),
			source = light["visualiserAttributes"]["scale"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Fallback,
			editable = True,
			edit = light["visualiserAttributes"]["scale"]
		)

		# Values should be inherited from predecessors in the history.
		self.__assertExpectedResult(
			self.__inspect( group["out"], "/group/light", "gl:visualiser:scale", None ),
			source = light["visualiserAttributes"]["scale"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Fallback,
			editable = True,
			edit = light["visualiserAttributes"]["scale"]
		)

	def testRegisteredAttribute( self ) :

		light = GafferSceneTest.TestLight()

		editScope = Gaffer.EditScope()
		editScope.setup( light["out"] )
		editScope["in"].setInput( light["out"] )

		self.__assertExpectedResult(
			self.__inspect( editScope["out"], "/light", "gl:visualiser:scale", None ),
			source = light["visualiserAttributes"]["scale"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Fallback,
			editable = True,
			edit = light["visualiserAttributes"]["scale"]
		)

		inspection = self.__inspect( editScope["out"], "/light", "gl:visualiser:scale", editScope )
		edit = inspection.acquireEdit()
		self.assertEqual(
			edit,
			GafferScene.EditScopeAlgo.acquireAttributeEdit(
				editScope, "/light", "gl:visualiser:scale", createIfNecessary = False
			)
		)

		edit["enabled"].setValue( True )

		# With the tweak in place in `editScope`, force the history to be checked again
		# to make sure we get the right source back.

		self.__assertExpectedResult(
			self.__inspect( editScope["out"], "/light", "gl:visualiser:scale", editScope ),
			source = edit,
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.EditScope,
			editable = True,
			edit = edit
		)

	def testDontEditParentOfInspectedLocation( self ) :

		light = GafferSceneTest.TestLight()

		childGroup = GafferScene.Group()
		childGroup["in"][0].setInput( light["out"] )
		childGroup["name"].setValue( "child" )

		parentGroup = GafferScene.Group()
		parentGroup["in"][0].setInput( childGroup["out"] )
		parentGroup["name"].setValue( "parent" )

		editScope = Gaffer.EditScope()
		editScope.setup( parentGroup["out"] )
		editScope["in"].setInput( parentGroup["out"] )

		inspection = self.__inspect( editScope["out"], "/parent/child", "gl:visualiser:scale", editScope )
		edit = inspection.acquireEdit()
		row = edit.ancestor( Gaffer.Spreadsheet.RowPlug )

		self.assertEqual( row["name"].getValue(), "/parent/child" )

		edit["enabled"].setValue( False )

		inspection = self.__inspect( editScope["out"], "/parent/child", "gl:visualiser:scale", editScope )
		edit = inspection.acquireEdit()
		row = edit.ancestor( Gaffer.Spreadsheet.RowPlug )

		self.assertEqual( row["name"].getValue(), "/parent/child" )

	def testLightFilter( self ) :

		lightFilter = GafferSceneTest.TestLightFilter()

		editScope = Gaffer.EditScope()
		editScope.setup( lightFilter["out"] )
		editScope["in"].setInput( lightFilter["out"] )

		self.__assertExpectedResult(
			self.__inspect( editScope["out"], "/lightFilter", "filteredLights" ),
			source = lightFilter["filteredLights"],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Fallback,
			editable = True,
			edit = lightFilter["filteredLights"]
		)

		self.assertIsNone( self.__inspect( editScope["out"], "/lightFilter", "bogusAttribute" ) )

		inspection = self.__inspect( editScope["out"], "/lightFilter", "filteredLights", editScope )
		edit = inspection.acquireEdit()
		edit["enabled"].setValue( True )

		self.__assertExpectedResult(
			self.__inspect( editScope["out"], "/lightFilter", "filteredLights", editScope ),
			source = edit,
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.EditScope,
			editable = True,
			edit = edit
		)

	def testAcquireEditCreateIfNecessary( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()
		s["light"]["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		s["group"] = GafferScene.Group()
		s["editScope"] = Gaffer.EditScope()

		s["group"]["in"][0].setInput( s["light"]["out"] )

		s["editScope"].setup( s["group"]["out"] )
		s["editScope"]["in"].setInput( s["group"]["out"] )

		inspection = self.__inspect( s["group"]["out"], "/group/light", "gl:visualiser:scale", None )
		self.assertEqual( inspection.acquireEdit( createIfNecessary = False ), s["light"]["visualiserAttributes"]["scale"] )

		inspection = self.__inspect( s["editScope"]["out"], "/group/light", "gl:visualiser:scale", s["editScope"] )
		self.assertIsNone( inspection.acquireEdit( createIfNecessary = False ) )

		edit = inspection.acquireEdit( createIfNecessary = True )
		self.assertIsNotNone( edit )
		self.assertEqual( inspection.acquireEdit( createIfNecessary = False ), edit )

	def testDisableEdit( self ) :

		s = Gaffer.ScriptNode()

		s["light"] = GafferSceneTest.TestLight()
		s["light"]["visualiserAttributes"]["scale"]["enabled"].setValue( True )

		s["group"] = GafferScene.Group()
		s["editScope1"] = Gaffer.EditScope()
		s["editScope2"] = Gaffer.EditScope()

		s["group"]["in"][0].setInput( s["light"]["out"] )

		s["editScope1"].setup( s["group"]["out"] )
		s["editScope1"]["in"].setInput( s["group"]["out"] )

		s["editScope2"].setup( s["editScope1"]["out"] )
		s["editScope2"]["in"].setInput( s["editScope1"]["out"] )

		Gaffer.MetadataAlgo.setReadOnly( s["light"]["visualiserAttributes"]["scale"]["enabled"], True )
		inspection = self.__inspect( s["group"]["out"], "/group/light", "gl:visualiser:scale", None )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "light.visualiserAttributes.scale.enabled is locked." )
		self.assertRaisesRegex( IECore.Exception, "Cannot disable edit : light.visualiserAttributes.scale.enabled is locked.", inspection.disableEdit )

		Gaffer.MetadataAlgo.setReadOnly( s["light"]["visualiserAttributes"]["scale"]["enabled"], False )
		Gaffer.MetadataAlgo.setReadOnly( s["light"]["visualiserAttributes"]["scale"], True )
		inspection = self.__inspect( s["group"]["out"], "/group/light", "gl:visualiser:scale", None )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "light.visualiserAttributes.scale is locked." )
		self.assertRaisesRegex( IECore.Exception, "Cannot disable edit : light.visualiserAttributes.scale is locked.", inspection.disableEdit )

		Gaffer.MetadataAlgo.setReadOnly( s["light"]["visualiserAttributes"]["scale"], False )
		inspection = self.__inspect( s["group"]["out"], "/group/light", "gl:visualiser:scale", None )
		self.assertTrue( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "" )
		inspection.disableEdit()
		self.assertFalse( s["light"]["visualiserAttributes"]["scale"]["enabled"].getValue() )

		lightEdit = GafferScene.EditScopeAlgo.acquireAttributeEdit(
			s["editScope1"], "/group/light", "gl:visualiser:scale", createIfNecessary = True
		)
		lightEdit["enabled"].setValue( True )
		lightEdit["value"].setValue( 2.0 )

		inspection = self.__inspect( s["editScope1"]["out"], "/group/light", "gl:visualiser:scale", s["editScope2"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "The target edit scope editScope2 is not in the scene history." )

		inspection = self.__inspect( s["editScope2"]["out"], "/group/light", "gl:visualiser:scale", s["editScope2"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "Edit is not in the current edit scope. Change scope to editScope1 to disable." )
		self.assertRaisesRegex( IECore.Exception, "Cannot disable edit : Edit is not in the current edit scope. Change scope to editScope1 to disable.", inspection.disableEdit )

		Gaffer.MetadataAlgo.setReadOnly( s["editScope1"], True )
		inspection = self.__inspect( s["editScope1"]["out"], "/group/light", "gl:visualiser:scale", s["editScope1"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "editScope1 is locked." )
		self.assertRaisesRegex( IECore.Exception, "Cannot disable edit : editScope1 is locked.", inspection.disableEdit )

		Gaffer.MetadataAlgo.setReadOnly( s["editScope1"], False )
		inspection = self.__inspect( s["editScope1"]["out"], "/group/light", "gl:visualiser:scale", s["editScope1"] )
		self.assertTrue( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "" )
		inspection.disableEdit()
		self.assertFalse( lightEdit["enabled"].getValue() )

		inspection = self.__inspect( s["editScope1"]["out"], "/group/light", "gl:visualiser:scale", s["editScope1"] )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "Edit is not in the current edit scope. Change scope to None to disable." )

		inspection = self.__inspect( s["editScope1"]["out"], "/group/light", "gl:visualiser:scale", None )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "light.visualiserAttributes.scale.enabled is not enabled." )

if __name__ == "__main__" :
	unittest.main()
