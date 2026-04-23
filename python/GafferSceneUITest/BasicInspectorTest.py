##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import functools
import unittest

import IECore

import Gaffer
import GafferTest
import GafferUITest
import GafferScene
import GafferSceneUI

class BasicInspectorTest( GafferUITest.TestCase ) :

	def testName( self ) :

		sphere = GafferScene.SceneNode()

		inspector = GafferSceneUI.Private.BasicInspector( sphere["out"]["object"], None, lambda plug : None, name = "MyName" )
		self.assertEqual( inspector.name(), "MyName" )

	def testPlugMustBeChildOfScene( self ) :

		sphere = GafferScene.Sphere()
		add = GafferTest.AddNode()

		for plug in ( sphere["out"], add["sum"] ) :
			with self.assertRaisesRegex( Exception, 'Plug "{}" is not a child of a ScenePlug'.format( plug.fullName() ) ) :
				GafferSceneUI.Private.BasicInspector( plug, None, lambda plug : None )

	def testDirtiedSignal( self ) :

		sphere = GafferScene.Sphere()
		inspector = GafferSceneUI.Private.BasicInspector( sphere["out"]["object"], None, lambda plug : None, name = "MyName" )
		cs = GafferTest.CapturingSlot( inspector.dirtiedSignal() )

		sphere["radius"].setValue( 2 )
		self.assertEqual( len( cs ), 1 )

		sphere["transform"]["translate"]["x"].setValue( 1 )
		self.assertEqual( len( cs ), 1 )

	@staticmethod
	def __inspect( plug, valueFunction, path = None, editScope = None ) :

		editScopePlug = Gaffer.Plug()
		editScopePlug.setInput( editScope["enabled"] if editScope is not None else None )
		inspector = GafferSceneUI.Private.BasicInspector(
			plug, editScopePlug, valueFunction
		)
		with Gaffer.Context() as context :
			if path is not None :
				context["scene:path"] = GafferScene.ScenePlug.stringToPath( path )
			return inspector.inspect()

	def testInspectObject( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		inspection = self.__inspect( script["sphere"]["out"]["object"], lambda objectPlug : objectPlug.getValue(), path = "/sphere" )

		self.assertEqual( inspection.value(), script["sphere"]["out"].object( "/sphere" ) )
		self.assertEqual( inspection.source(), script["sphere"]["out"]["object"] )
		self.assertEqual( inspection.sourceType(), inspection.SourceType.Other )
		self.assertEqual( inspection.fallbackDescription(), "" )
		self.assertFalse( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "sphere.out.object is not editable." )
		self.assertRaises( RuntimeError, inspection.acquireEdit )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "sphere.out.object is not editable." )
		self.assertRaises( RuntimeError, inspection.disableEdit )
		self.assertFalse( inspection.canEdit( inspection.value() ) )
		self.assertRaises( RuntimeError, inspection.edit, inspection.value() )

	def testInspectNonExistentObject( self ) :

		sphere = GafferScene.Sphere()
		inspection = self.__inspect( sphere["out"]["object"], lambda objectPlug : objectPlug["ifThisLambdaIsCalledItWillError"].getValue(), path = "/iDoNotExist" )
		self.assertIsNone( inspection )

	def testInspectGlobals( self ) :

		script = Gaffer.ScriptNode()

		script["options"] = GafferScene.CustomOptions()
		script["options"]["options"].addChild( Gaffer.NameValuePlug( "test", 10 ) )
		inspection = self.__inspect( script["options"]["out"]["globals"], lambda globalsPlug : globalsPlug.getValue() )

		self.assertEqual( inspection.value(), script["options"]["out"].globals() )
		self.assertEqual( inspection.source(), script["options"]["out"]["globals"] )
		self.assertEqual( inspection.sourceType(), inspection.SourceType.Other )
		self.assertEqual( inspection.fallbackDescription(), "" )
		self.assertFalse( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "options.out.globals is not editable." )
		self.assertRaises( RuntimeError, inspection.acquireEdit )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "options.out.globals is not editable." )
		self.assertRaises( RuntimeError, inspection.disableEdit )
		self.assertFalse( inspection.canEdit( inspection.value() ) )
		self.assertRaises( RuntimeError, inspection.edit, inspection.value() )

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

		inspector = GafferSceneUI.Private.BasicInspector( group["out"]["object"], None, lambda objectPlug : objectPlug.getValue() )
		with Gaffer.Context() as context :
			context["scene:path"] = GafferScene.ScenePlug.stringToPath( "/group/cube" )
			historyPath = inspector.historyPath()

		self.ignoreMessage( IECore.Msg.Level.Warning, "HistoryPath", "Path evaluated on unexpected thread" )

		children = historyPath.children()
		self.assertEqual(
			[ c.property( "history:node" ) for c in children ],
			[ cube, primitiveVariables, meshTangents, group ]
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

		def primitiveVariableData( objectPlug, primitiveVariable ) :

			o = objectPlug.getValue()
			if primitiveVariable in o :
				return o[primitiveVariable].data

			return None

		def assertExpectedSource( scene, primitiveVariable, source, sourceType = None, editScope = None ) :

			inspection = self.__inspect(
				scene["object"], functools.partial( primitiveVariableData, primitiveVariable = primitiveVariable ),
				path = "/cube", editScope = editScope
			)

			if source is None :
				self.assertIsNone( inspection )
				return

			self.assertIsNotNone( inspection )
			self.assertEqual( inspection.source(), source )
			self.assertEqual( inspection.sourceType(), sourceType )
			self.assertFalse( inspection.editable() )
			with self.assertRaisesRegex( RuntimeError, "Not editable.*" ) :
				inspection.acquireEdit()

		SourceType = GafferSceneUI.Private.Inspector.Result.SourceType
		assertExpectedSource( script["primitiveVariables2"]["out"], "afterEditScope", script["primitiveVariables2"]["out"]["object"], SourceType.Other )
		assertExpectedSource( script["primitiveVariables2"]["out"], "afterEditScope", script["primitiveVariables2"]["out"]["object"], SourceType.Downstream, editScope = script["editScope"] )
		assertExpectedSource( script["primitiveVariables2"]["out"], "insideEditScope", script["editScope"]["primitiveVariables"]["out"]["object"], SourceType.Other )
		assertExpectedSource( script["primitiveVariables2"]["out"], "insideEditScope", script["editScope"]["primitiveVariables"]["out"]["object"], SourceType.EditScope, editScope = script["editScope"] )
		assertExpectedSource( script["primitiveVariables2"]["out"], "beforeEditScope", script["primitiveVariables1"]["out"]["object"], SourceType.Other )
		assertExpectedSource( script["primitiveVariables2"]["out"], "beforeEditScope", script["primitiveVariables1"]["out"]["object"], SourceType.Upstream, editScope = script["editScope"] )

		assertExpectedSource( script["editScope"]["out"], "afterEditScope", None )
		assertExpectedSource( script["editScope"]["out"], "afterEditScope", None, editScope = script["editScope"] )
		assertExpectedSource( script["editScope"]["out"], "insideEditScope", script["editScope"]["primitiveVariables"]["out"]["object"], SourceType.Other )
		assertExpectedSource( script["editScope"]["out"], "insideEditScope", script["editScope"]["primitiveVariables"]["out"]["object"], SourceType.EditScope, editScope = script["editScope"] )
		assertExpectedSource( script["editScope"]["out"], "beforeEditScope", script["primitiveVariables1"]["out"]["object"], SourceType.Other )
		assertExpectedSource( script["editScope"]["out"], "beforeEditScope", script["primitiveVariables1"]["out"]["object"], SourceType.Upstream, editScope = script["editScope"] )

		assertExpectedSource( script["editScope"]["in"], "afterEditScope", None )
		assertExpectedSource( script["editScope"]["in"], "afterEditScope", None, editScope = script["editScope"] )
		assertExpectedSource( script["editScope"]["in"], "insideEditScope", None )
		assertExpectedSource( script["editScope"]["in"], "insideEditScope", None, editScope = script["editScope"] )
		assertExpectedSource( script["editScope"]["in"], "beforeEditScope", script["primitiveVariables1"]["out"]["object"], SourceType.Other )
		assertExpectedSource( script["editScope"]["in"], "beforeEditScope", script["primitiveVariables1"]["out"]["object"], SourceType.Upstream, editScope = script["editScope"] )

if __name__ == "__main__":
	unittest.main()
