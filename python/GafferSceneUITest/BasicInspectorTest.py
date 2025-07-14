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

		sphere = GafferScene.Sphere()
		inspection = self.__inspect( sphere["out"]["object"], lambda objectPlug : objectPlug.getValue(), path = "/sphere" )

		self.assertEqual( inspection.value(), sphere["out"].object( "/sphere" ) )
		self.assertIsNone( inspection.source() )
		self.assertEqual( inspection.sourceType(), inspection.SourceType.Other )
		self.assertEqual( inspection.fallbackDescription(), "" )
		self.assertFalse( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "No editable source found in history." )
		self.assertRaises( RuntimeError, inspection.acquireEdit )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "No editable source found in history." )
		self.assertRaises( RuntimeError, inspection.disableEdit )
		self.assertFalse( inspection.canEdit( inspection.value() ) )
		self.assertRaises( RuntimeError, inspection.edit, inspection.value() )

	def testInspectNonExistentObject( self ) :

		sphere = GafferScene.Sphere()
		inspection = self.__inspect( sphere["out"]["object"], lambda objectPlug : objectPlug["ifThisLambdaIsCalledItWillError"].getValue(), path = "/iDoNotExist" )
		self.assertIsNone( inspection )

	def testInspectGlobals( self ) :

		options = GafferScene.CustomOptions()
		options["options"].addChild( Gaffer.NameValuePlug( "test", 10 ) )
		inspection = self.__inspect( options["out"]["globals"], lambda globalsPlug : globalsPlug.getValue() )

		self.assertEqual( inspection.value(), options["out"].globals() )
		self.assertIsNone( inspection.source() )
		self.assertEqual( inspection.sourceType(), inspection.SourceType.Other )
		self.assertEqual( inspection.fallbackDescription(), "" )
		self.assertFalse( inspection.editable() )
		self.assertEqual( inspection.nonEditableReason(), "No editable source found in history." )
		self.assertRaises( RuntimeError, inspection.acquireEdit )
		self.assertFalse( inspection.canDisableEdit() )
		self.assertEqual( inspection.nonDisableableReason(), "No editable source found in history." )
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

if __name__ == "__main__":
	unittest.main()
