##########################################################################
#
#  Copyright (c) 2026, Image Engine Design Inc. All rights reserved.
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

# "Property" is a rather generic name, this would generally be a bad idea, but for
# these tests specifically, this was getting rather verbose
Property = GafferSceneUI.Private.PrimitiveVariableInspector.Property

class PrimitiveVariableInspectorTest( GafferUITest.TestCase ) :

	def testName( self ) :

		plane = GafferScene.Plane()

		inspector = GafferSceneUI.Private.PrimitiveVariableInspector( plane["out"], None, "P", Property.Data )
		self.assertEqual( inspector.name(), "P" )

	def testDirtiedSignal( self ) :

		sphere = GafferScene.Sphere()
		inspector = GafferSceneUI.Private.PrimitiveVariableInspector( sphere["out"], None, "P", Property.Data )
		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		sphere["radius"].setValue( 2 )
		self.assertEqual( len( cs ), 1 )

		sphere["transform"]["translate"]["x"].setValue( 1 )
		self.assertEqual( len( cs ), 1 )

	@staticmethod
	def __inspect( scene, path, primitiveVariable, parameter, editScope=None ) :

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.PrimitiveVariableInspector( scene, editScopePlug, primitiveVariable, parameter )
		with Gaffer.Context() as context :
			context["scene:path"] = IECore.InternedStringVectorData( path.split( "/" )[1:] )
			return inspector.inspect()

	def testInspectObject( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		inspection = self.__inspect( script["sphere"]["out"], "/sphere", "P", Property.Data )

		self.assertEqual( inspection.value(), script["sphere"]["out"].object( "/sphere" )["P"].data )
		self.assertEqual( inspection.source(), script["sphere"]["out"] )
		self.assertEqual( inspection.sourceType(), inspection.SourceType.Other )
		self.assertEqual( inspection.fallbackDescription(), "" )
		self.assertFalse( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "sphere.out is not editable." )
		self.assertRaises( RuntimeError, inspection.acquireEdit )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "sphere.out is not editable." )
		self.assertRaises( RuntimeError, inspection.disableEdit )
		self.assertFalse( inspection.canEdit( inspection.value() ) )
		self.assertRaises( RuntimeError, inspection.edit, inspection.value() )

	def testNonExistentLocation( self ) :

		plane = GafferScene.Plane()
		self.assertIsNone( self.__inspect( plane["out"], "/nothingHere", "P", Property.Data ) )

	def testNonExistentPrimitiveVariable( self ) :

		plane = GafferScene.Plane()
		self.assertIsNone( self.__inspect( plane["out"], "/plane", "badPrimVar", Property.Data ) )

	def testHistory( self ) :

		cube = GafferScene.Cube()

		cubeFilter = GafferScene.PathFilter()
		cubeFilter["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( cube["out"] )
		primitiveVariables["filter"].setInput( cubeFilter["out"] )
		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "test", 10 ) )

		meshTangents = GafferScene.MeshTangents()
		meshTangents["in"].setInput( primitiveVariables["out"] )
		meshTangents["filter"].setInput( cubeFilter["out"] )

		group = GafferScene.Group()
		group["in"][0].setInput( meshTangents["out"] )

		self.assertEqual( set( group["out"].object( "/group/cube" ).keys() ), { "N", "P", "test", "uTangent", "uv", "vTangent" } )

		self.ignoreMessage( IECore.Msg.Level.Warning, "HistoryPath", "Path evaluated on unexpected thread" )

		inspector = GafferSceneUI.Private.PrimitiveVariableInspector( group["out"], None, "P", Property.Data )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/group/cube" )
			historyPath = inspector.historyPath()

		children = historyPath.children()
		self.assertEqual(
			[ c.property( "history:node" ) for c in children ],
			[ cube, group ]
		)

		inspector = GafferSceneUI.Private.PrimitiveVariableInspector( group["out"], None, "test", Property.Data )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/group/cube" )
			historyPath = inspector.historyPath()

		children = historyPath.children()
		self.assertEqual(
			[ c.property( "history:node" ) for c in children ],
			[ cube, primitiveVariables, group ]
		)

		inspector = GafferSceneUI.Private.PrimitiveVariableInspector( group["out"], None, "uTangent", Property.Data )

		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/group/cube" )
			historyPath = inspector.historyPath()

		children = historyPath.children()
		self.assertEqual(
			[ c.property( "history:node" ) for c in children ],
			[ cube, meshTangents, group ]
		)

	def testSourceAndSourceType( self ) :

		script = Gaffer.ScriptNode()

		script["cube"] = GafferScene.Cube()

		script["cubeFilter"] = GafferScene.PathFilter()
		script["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		script["primitiveVariables1"] = GafferScene.PrimitiveVariables()
		script["primitiveVariables1"]["in"].setInput( script["cube"]["out"] )
		script["primitiveVariables1"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["primitiveVariables1"]["primitiveVariables"].addChild( Gaffer.NameValuePlug( "beforeEditScope", 10 ) )

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["primitiveVariables1"]["out"] )
		script["editScope"]["in"].setInput( script["primitiveVariables1"]["out"] )

		script["editScope"]["primitiveVariables"] = GafferScene.PrimitiveVariables()
		script["editScope"]["primitiveVariables"]["in"].setInput( script["editScope"]["in"] )
		script["editScope"]["primitiveVariables"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["editScope"]["primitiveVariables"]["primitiveVariables"].addChild( Gaffer.NameValuePlug( "insideEditScope", 10 ) )

		script["editScope"]["out"].setInput( script["editScope"]["primitiveVariables"]["out"] )

		script["primitiveVariables2"] = GafferScene.PrimitiveVariables()
		script["primitiveVariables2"]["in"].setInput( script["editScope"]["out"] )
		script["primitiveVariables2"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["primitiveVariables2"]["primitiveVariables"].addChild( Gaffer.NameValuePlug( "afterEditScope", 10 ) )

		def assertExpectedSource( scene, primitiveVariable, source, sourceType = None, editScope = None, editable = True ) :

			inspection = self.__inspect(
				scene, "/cube", primitiveVariable, Property.Data, editScope = editScope
			)

			if source is None :
				self.assertIsNone( inspection )
				return

			self.assertIsNotNone( inspection )
			self.assertEqual( inspection.source(), source )
			self.assertEqual( inspection.sourceType(), sourceType )
			if editable:
				self.assertEqual( inspection.acquireEdit(), source )
			else:
				with self.assertRaisesRegex( RuntimeError, "Not editable.*" ) :
					inspection.acquireEdit()
			self.assertEqual( inspection.editable(), editable )

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		assertExpectedSource( script["primitiveVariables2"]["out"], "afterEditScope", script["primitiveVariables2"]["primitiveVariables"][0], SourceType.Other )
		assertExpectedSource( script["primitiveVariables2"]["out"], "afterEditScope", script["primitiveVariables2"]["primitiveVariables"][0], SourceType.Downstream, editScope = script["editScope"], editable = False )
		assertExpectedSource( script["primitiveVariables2"]["out"], "insideEditScope", script["editScope"]["primitiveVariables"]["primitiveVariables"][0], SourceType.Other, editable = False )
		assertExpectedSource( script["primitiveVariables2"]["out"], "insideEditScope", script["editScope"]["primitiveVariables"]["primitiveVariables"][0], SourceType.EditScope, editScope = script["editScope"] )
		assertExpectedSource( script["primitiveVariables2"]["out"], "beforeEditScope", script["primitiveVariables1"]["primitiveVariables"][0], SourceType.Other )
		assertExpectedSource( script["primitiveVariables2"]["out"], "beforeEditScope", script["primitiveVariables1"]["primitiveVariables"][0], SourceType.Upstream, editScope = script["editScope"], editable = False )

		assertExpectedSource( script["editScope"]["out"], "afterEditScope", None )
		assertExpectedSource( script["editScope"]["out"], "afterEditScope", None, editScope = script["editScope"] )
		assertExpectedSource( script["editScope"]["out"], "insideEditScope", script["editScope"]["primitiveVariables"]["primitiveVariables"][0], SourceType.Other, editable = False )
		assertExpectedSource( script["editScope"]["out"], "insideEditScope", script["editScope"]["primitiveVariables"]["primitiveVariables"][0], SourceType.EditScope, editScope = script["editScope"] )
		assertExpectedSource( script["editScope"]["out"], "beforeEditScope", script["primitiveVariables1"]["primitiveVariables"][0], SourceType.Other )
		assertExpectedSource( script["editScope"]["out"], "beforeEditScope", script["primitiveVariables1"]["primitiveVariables"][0], SourceType.Upstream, editScope = script["editScope"], editable = False )

		assertExpectedSource( script["editScope"]["in"], "afterEditScope", None )
		assertExpectedSource( script["editScope"]["in"], "afterEditScope", None, editScope = script["editScope"] )
		assertExpectedSource( script["editScope"]["in"], "insideEditScope", None )
		assertExpectedSource( script["editScope"]["in"], "insideEditScope", None, editScope = script["editScope"] )
		assertExpectedSource( script["editScope"]["in"], "beforeEditScope", script["primitiveVariables1"]["primitiveVariables"][0], SourceType.Other )
		assertExpectedSource( script["editScope"]["in"], "beforeEditScope", script["primitiveVariables1"]["primitiveVariables"][0], SourceType.Upstream, editScope = script["editScope"], editable = False )



	def __setupBasicConstant( self, parent ):
		parent["plane"] = GafferScene.Plane()

		parent["filter"] = GafferScene.PathFilter()
		parent["filter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		parent["primitiveVariables"] = GafferScene.PrimitiveVariables()
		parent["primitiveVariables"]["in"].setInput( parent["plane"]["out"] )
		parent["primitiveVariables"]["filter"].setInput( parent["filter"]["out"] )
		parent["primitiveVariables"]["primitiveVariables"].addChild(
			Gaffer.NameValuePlug(
				"testConstant",
				IECore.Color3fData( imath.Color3f( 0, 1, 2 ) ),
				Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic,
				"testPlug"
			)
		)

	def testValue( self ) :

		s = Gaffer.ScriptNode()

		self.__setupBasicConstant( s )

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "P", Property.Interpolation ).value(),
			IECore.StringData( "Vertex" )
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "P", Property.Type ).value(),
			IECore.StringData( "V3fVectorData" )
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "P", Property.Interpretation ).value(),
			IECore.StringData( "Point" )
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "uv", Property.Interpretation ).value(),
			IECore.StringData( "UV" )
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "testConstant", Property.Interpretation ).value(),
			IECore.StringData( "None" )
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "P", Property.Data ).value(),
			IECore.V3fVectorData( [ imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, -0.5, 0 ), imath.V3f( -0.5, 0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ], IECore.GeometricData.Interpretation.Point )
		)

		self.assertIsNone( self.__inspect( s["primitiveVariables"]["out"], "/plane", "P", Property.Indices ) )

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "uv", Property.Indices ).value(),
			IECore.IntVectorData( [ 0, 1, 3, 2 ] )
		)

	def testValueNotFound( self ) :

		s = Gaffer.ScriptNode()

		self.__setupBasicConstant( s )

		# TODO - this is inconsistent

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "badPrimVar", Property.Interpolation ).value(),
			IECore.StringData( "Invalid" )
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "badPrimVar", Property.Type ),
			None
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "badPrimVar", Property.Interpretation ),
			None
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "badPrimVar", Property.Data ),
			None
		)

		self.assertEqual(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "badPrimVar", Property.Indices ),
			None
		)

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
		self.assertEqual( result.fallbackDescription(), "" )

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

	def testDisabledTweaks( self ) :


		s = Gaffer.ScriptNode()

		self.__setupBasicConstant( s )

		s["plane"] = GafferScene.Plane()

		s["planeFilter"] = GafferScene.PathFilter()
		s["planeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		s["primitiveVariableTweaks1"] = GafferScene.PrimitiveVariableTweaks()
		s["primitiveVariableTweaks1"]["in"].setInput( s["plane"]["out"] )
		s["primitiveVariableTweaks1"]["filter"].setInput( s["planeFilter"]["out"] )
		scaleTweak1 = Gaffer.TweakPlug( "P", IECore.V3fData( imath.V3f( 2.0 ) ) )
		s["primitiveVariableTweaks1"]["tweaks"].addChild( scaleTweak1 )

		s["primitiveVariableTweaks2"] = GafferScene.PrimitiveVariableTweaks()
		s["primitiveVariableTweaks2"]["in"].setInput( s["primitiveVariableTweaks1"]["out"] )
		s["primitiveVariableTweaks2"]["filter"].setInput( s["planeFilter"]["out"] )
		scaleTweak2 = Gaffer.TweakPlug( "P", IECore.V3fData( imath.V3f( 3.0 ) ) )
		s["primitiveVariableTweaks2"]["tweaks"].addChild( scaleTweak2 )

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType

		self.__assertExpectedResult(
			self.__inspect( s["primitiveVariableTweaks2"]["out"], "/plane", "P", Property.Data ),
			source = scaleTweak2,
			sourceType = SourceType.Other,
			editable = True,
			edit = scaleTweak2
		)

		scaleTweak2["enabled"].setValue( False )

		self.__assertExpectedResult(
			self.__inspect( s["primitiveVariableTweaks2"]["out"], "/plane", "P", Property.Data ),
			source = scaleTweak1,
			sourceType = SourceType.Other,
			editable = True,
			edit = scaleTweak1
		)

	def testExternalSourceType( self ) :

		s = Gaffer.ScriptNode()

		self.__setupBasicConstant( s )

		externalPrimitiveVariableTweaks = GafferScene.PrimitiveVariableTweaks()
		externalPrimitiveVariableTweaks["in"].setInput( s["primitiveVariables"]["out"] )
		externalPrimitiveVariableTweaks["filter"].setInput( s["filter"]["out"] )
		tweak2 = Gaffer.TweakPlug( "testConstant", imath.Color3f( 4.0 ) )
		externalPrimitiveVariableTweaks["tweaks"].addChild( tweak2 )

		self.__assertExpectedResult(
			self.__inspect( s["primitiveVariables"]["out"], "/plane", "testConstant", Property.Data ),
			source = s["primitiveVariables"]["primitiveVariables"][0],
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.Other,
			editable = True,
			edit = None,
			editWarning = 'Edits to "testConstant" may affect other locations in the scene.'
		)

		self.__assertExpectedResult(
			self.__inspect( externalPrimitiveVariableTweaks["out"], "/plane", "testConstant", Property.Data ),
			source = tweak2,
			sourceType = GafferSceneUI.Private.Inspector.Result.SourceType.External,
			editable = False,
			edit = None,
			editWarning = "",
			nonEditableReason = "{} is external to the script.".format( externalPrimitiveVariableTweaks.fullName() )
		)

if __name__ == "__main__" :
	unittest.main()
