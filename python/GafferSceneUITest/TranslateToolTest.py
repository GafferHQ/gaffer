##########################################################################
#
#  Copyright (c) 2016, John Haddon. All rights reserved.
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
import math
import os

import imath

import IECore

import Gaffer
import GafferTest
import GafferUITest
import GafferScene
import GafferSceneUI

class TranslateToolTest( GafferUITest.TestCase ) :

	def testSelection( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )

		script["transformFilter"] = GafferScene.PathFilter()

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["group"]["out"] )
		script["transform"]["filter"].setInput( script["transformFilter"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["transform"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		self.assertEqual( len( tool.selection() ), 0 )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].path(), "/group/plane" )
		self.assertEqual( tool.selection()[0].context(), view.getContext() )
		self.assertTrue( tool.selection()[0].upstreamScene().isSame( script["plane"]["out"] ) )
		self.assertEqual( tool.selection()[0].upstreamPath(), "/plane" )
		self.assertTrue( tool.selection()[0].transformPlug().isSame( script["plane"]["transform"] ) )
		self.assertEqual( tool.selection()[0].transformSpace(), imath.M44f() )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group" ] ) )
		self.assertEqual( tool.selection()[0].path(), "/group" )
		self.assertEqual( tool.selection()[0].context(), view.getContext() )
		self.assertTrue( tool.selection()[0].upstreamScene().isSame( script["group"]["out"] ) )
		self.assertEqual( tool.selection()[0].upstreamPath(), "/group" )
		self.assertTrue( tool.selection()[0].transformPlug().isSame( script["group"]["transform"] ) )
		self.assertEqual( tool.selection()[0].transformSpace(), imath.M44f() )

		script["transformFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		self.assertTrue( tool.selection()[0].transformPlug().isSame( script["transform"]["transform"] ) )

		script["transformFilter"]["enabled"].setValue( False )
		self.assertTrue( tool.selection()[0].transformPlug().isSame( script["group"]["transform"] ) )

		script["transformFilter"]["enabled"].setValue( True )
		self.assertEqual( tool.selection()[0].path(), "/group" )
		self.assertEqual( tool.selection()[0].context(), view.getContext() )
		self.assertTrue( tool.selection()[0].upstreamScene().isSame( script["transform"]["out"] ) )
		self.assertEqual( tool.selection()[0].upstreamPath(), "/group" )
		self.assertTrue( tool.selection()[0].transformPlug().isSame( script["transform"]["transform"] ) )
		self.assertEqual( tool.selection()[0].transformSpace(), imath.M44f() )

		script["transform"]["enabled"].setValue( False )
		self.assertTrue( tool.selection()[0].transformPlug().isSame( script["group"]["transform"] ) )

	def testTranslate( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["plane"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertEqual(
			script["plane"]["out"].fullTransform( "/plane" ).translation(),
			imath.V3f( 1, 0, 0 ),
		)

	def testInteractionWithRotation( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["plane"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )
		tool["orientation"].setValue( tool.Orientation.Local )

		with Gaffer.UndoScope( script ) :
			tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				script["plane"]["out"].fullTransform( "/plane" ).translation(),
				0.0000001
			)
		)
		script.undo()

		script["plane"]["transform"]["rotate"]["y"].setValue( 90 )

		with Gaffer.UndoScope( script ) :
			tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				script["plane"]["out"].fullTransform( "/plane" ).translation(),
				0.0000001
			)
		)
		script.undo()

	def testInteractionWithGroupRotation( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )
		script["group"]["transform"]["rotate"]["y"].setValue( 90 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				script["group"]["out"].fullTransform( "/group/plane" ).translation(),
				0.0000001
			)
		)

	def testInteractionWithGroupTranslation( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )
		script["group"]["transform"]["translate"].setValue( imath.V3f( 1, 2, 3 ) )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		tool.translate( imath.V3f( -1, 0, 0 ) )

		self.assertEqual(
			script["group"]["out"].fullTransform( "/group/plane" ).translation(),
			imath.V3f( 0, 2, 3 ),
		)

	def testOrientation( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["transform"]["rotate"]["y"].setValue( 90 )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )
		script["group"]["transform"]["rotate"]["y"].setValue( 90 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		# Local

		tool["orientation"].setValue( tool.Orientation.Local )

		with Gaffer.UndoScope( script ) :
			tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( -1, 0, 0 ).equalWithAbsError(
				script["group"]["out"].fullTransform( "/group/plane" ).translation(),
				0.000001
			)
		)
		script.undo()

		# Parent

		tool["orientation"].setValue( tool.Orientation.Parent )

		with Gaffer.UndoScope( script ) :
			tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				script["group"]["out"].fullTransform( "/group/plane" ).translation(),
				0.0000001
			)
		)
		script.undo()

		# World

		tool["orientation"].setValue( tool.Orientation.World )

		with Gaffer.UndoScope( script ) :
			tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				script["group"]["out"].fullTransform( "/group/plane" ).translation(),
				0.0000001
			)
		)

	def testScale( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["transform"]["scale"].setValue( imath.V3f( 10 ) )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["plane"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		with Gaffer.UndoScope( script ) :
			tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				script["plane"]["out"].fullTransform( "/plane" ).translation(),
				0.0000001
			)
		)

		script.undo()

		tool["orientation"].setValue( tool.Orientation.Local )

		with Gaffer.UndoScope( script ) :
			tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 1, 0, 0 ).equalWithAbsError(
				script["plane"]["out"].fullTransform( "/plane" ).translation(),
				0.0000001
			)
		)

	def testGroup( self ) :

		script = Gaffer.ScriptNode()

		script["group"] = GafferScene.Group()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertEqual(
			script["group"]["out"].fullTransform( "/group" ).translation(),
			imath.V3f( 1, 0, 0 ),
		)

	def testTransform( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["transform"]["rotate"]["y"].setValue( 90 )

		script["transformFilter"] = GafferScene.PathFilter()
		script["transformFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["plane"]["out"] )
		script["transform"]["filter"].setInput( script["transformFilter"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["transform"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )
		tool["orientation"].setValue( tool.Orientation.Local )

		tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				script["transform"]["out"].fullTransform( "/plane" ).translation(),
				0.0000001
			)
		)

	def testTransformWithRotation( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["transformFilter"] = GafferScene.PathFilter()
		script["transformFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["plane"]["out"] )
		script["transform"]["filter"].setInput( script["transformFilter"]["out"] )
		script["transform"]["transform"]["rotate"]["y"].setValue( 90 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["transform"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )
		tool["orientation"].setValue( tool.Orientation.Local )

		tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				script["transform"]["out"].fullTransform( "/plane" ).translation(),
				0.0000001
			)
		)

	def testHandlesTransform( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["transform"]["rotate"]["y"].setValue( 90 )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["plane"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		tool["orientation"].setValue( tool.Orientation.Local )
		self.assertTrue(
			tool.handlesTransform().equalWithAbsError(
				imath.M44f().rotate( imath.V3f( 0, math.pi / 2, 0 ) ),
				0.000001
			)
		)

		tool["orientation"].setValue( tool.Orientation.Parent )
		self.assertEqual(
			tool.handlesTransform(), imath.M44f()
		)

		tool["orientation"].setValue( tool.Orientation.World )
		self.assertEqual(
			tool.handlesTransform(), imath.M44f()
		)

	def testContext( self ) :

		script = Gaffer.ScriptNode()
		script["variables"].addChild( Gaffer.NameValuePlug( "enabled", True ) )
		script["variables"].addChild( Gaffer.NameValuePlug( "x", 1.0 ) )

		script["plane"] = GafferScene.Plane()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			parent["plane"]["transform"]["translate"]["x"] = context["x"]
			parent["plane"]["enabled"] = context["enabled"]
			"""
		) )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["plane"]["out"] )
		view.setContext( script.context() )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		self.assertEqual( tool.selection()[0].path(), "/plane" )
		self.assertEqual( tool.selection()[0].transformSpace(), imath.M44f() )

	def testPivotExpression( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( inspect.cleandoc(
			"""
			parent["plane"]["transform"]["pivot"]["x"] = context["x"]
			"""
		) )

		script["variables"] = Gaffer.ContextVariables()
		script["variables"].setup( GafferScene.ScenePlug() )
		script["variables"]["in"].setInput( script["plane"]["out"] )
		script["variables"]["variables"].addChild( Gaffer.NameValuePlug( "x", 1.0 ) )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["variables"]["out"] )
		view.setContext( script.context() )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		self.assertEqual( tool.selection()[0].path(), "/plane" )
		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

	def testMultipleSelection( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["transform"]["rotate"]["y"].setValue( 90 )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )
		script["group"]["in"][1].setInput( script["sphere"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane", "/group/sphere" ] ) )

		selection = tool.selection()
		self.assertEqual( len( selection ), 2 )
		self.assertEqual( { s.transformPlug() for s in selection }, { script["plane"]["transform"], script["sphere"]["transform"] } )

		tool["orientation"].setValue( tool.Orientation.Local )
		tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertEqual( script["plane"]["transform"]["translate"].getValue(), imath.V3f( 1, 0, 0 ) )
		self.assertTrue(
			imath.V3f( 0, 0, -1 ).equalWithAbsError(
				script["sphere"]["transform"]["translate"].getValue(), 0.000001
			)
		)

	def testMultipleSelectionDoesntPickSamePlugTwice( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )
		script["group"]["in"][1].setInput( script["plane"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane", "/group/plane1" ] ) )

		# Even though there are two selected paths, there should only be
		# one thing in the tool's selection, because both paths are generated
		# by the same upstream node.

		selection = tool.selection()
		self.assertEqual( len( selection ), 1 )
		self.assertEqual( selection[0].transformPlug(), script["plane"]["transform"] )

	def testHandlesFollowLastSelected( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["transform"]["translate"].setValue( imath.V3f( 1 ) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )
		script["group"]["in"][1].setInput( script["sphere"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/group/plane" )
		self.assertEqual( tool.handlesTransform(), imath.M44f() )

		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/group/sphere" )
		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( script["sphere"]["transform"]["translate"].getValue() ) )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )
		self.assertEqual( tool.handlesTransform(), imath.M44f() )

	def testPromotedPlugs( self ) :

		script = Gaffer.ScriptNode()

		script["box"] = Gaffer.Box()
		script["box"]["sphere"] = GafferScene.Sphere()
		Gaffer.PlugAlgo.promote( script["box"]["sphere"]["transform"] )
		Gaffer.PlugAlgo.promote( script["box"]["sphere"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["box"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/sphere" )

		self.assertEqual( tool.selection()[0].transformPlug(), script["box"]["transform"] )

	def testSelectionChangedSignal( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["plane"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		cs = GafferTest.CapturingSlot( tool.selectionChangedSignal() )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )
		self.assertTrue( len( cs ) )
		self.assertEqual( cs[0][0], tool )

	def testEditAncestorIfSelectionNotTransformable( self ) :

		script = Gaffer.ScriptNode()
		script["sceneReader"] = GafferScene.SceneReader()
		script["sceneReader"]["fileName"].setValue( "${GAFFER_ROOT}/python/GafferSceneTest/alembicFiles/groupedPlane.abc" )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["sceneReader"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )
		selection = tool.selection()
		self.assertEqual( len( selection ), 1 )
		self.assertEqual( selection[0].transformPlug(), script["sceneReader"]["transform"] )
		self.assertEqual( selection[0].path(), "/group" )

	def testSelectionRefersToFirstPublicPlug( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView()

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )
		self.assertEqual( tool.selection(), [] )

		view["in"].setInput( script["plane"]["out"] )
		self.assertEqual( tool.selection(), [] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].scene(), script["plane"]["out"] )

		box = Gaffer.Box.create( script, Gaffer.StandardSet( [ script["plane"] ] ) )
		Gaffer.PlugAlgo.promote( box["plane"]["out"] )
		view["in"].setInput( box["out"] )
		self.assertEqual( tool.selection()[0].scene(), box["out"] )

	def testSelectionRefersToCorrectPlug( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["cube"] = GafferScene.Cube()
		script["freeze"] = GafferScene.FreezeTransform()
		script["freezeFilter"] = GafferScene.PathFilter()
		script["freezeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		script["freeze"]["in"].setInput( script["sphere"]["out"] )
		script["freeze"]["filter"].setInput( script["freezeFilter"]["out"] )
		script["instancer"] = GafferScene.Instancer()
		script["instancerFilter"] = GafferScene.PathFilter()
		script["instancerFilter"]["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )
		script["instancer"]["in"].setInput( script["freeze"]["out"] )
		script["instancer"]["prototypes"].setInput( script["cube"]["out"] )
		script["instancer"]["filter"].setInput( script["instancerFilter"]["out"] )
		script["subTree"] = GafferScene.SubTree()
		script["subTree"]["root"].setValue( "/sphere/instances" )
		script["subTree"]["in"].setInput( script["instancer"]["out"] )
		script["plane"] = GafferScene.Plane()
		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["subTree"]["out"] )
		script["group"]["in"][1].setInput( script["plane"]["out"] )

		view = GafferSceneUI.SceneView()

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )
		self.assertEqual( tool.selection(), [] )

		view["in"].setInput( script["group"]["out"] )
		self.assertEqual( tool.selection(), [] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].transformPlug(), script["plane"]["transform"] )

	def testLastSelectedObjectWithSharedTransformPlug( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["group"]["in"][1].setInput( script["sphere"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["group"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/sphere" ] ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].transformPlug(), script["sphere"]["transform"] )
		self.assertEqual( tool.selection()[0].path(), "/group/sphere" )

		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/group/sphere1" )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].transformPlug(), script["sphere"]["transform"] )
		self.assertEqual( tool.selection()[0].path(), "/group/sphere1" )

		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/group/sphere" )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].transformPlug(), script["sphere"]["transform"] )
		self.assertEqual( tool.selection()[0].path(), "/group/sphere" )

		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

	def testSelectionSorting( self ) :

		# This test exposes a bug we had when sorting the selection internal
		# to the TransformTool, triggering a heap-buffer-overflow report in
		# ASAN builds.

		# Craft a scene containing 26 spheres underneath a group.

		script = Gaffer.ScriptNode()
		script["sphere"] = GafferScene.Sphere()
		script["group"] = GafferScene.Group()

		selection = IECore.PathMatcher()
		for i in range( 0, 26 ) :
			script["group"]["in"][i].setInput( script["sphere"]["out"] )
			selection.addPath( "/group/sphere" + ( str( i ) if i else "" ) )

		# Write it out to disk and read it back in again. This gives us the
		# same scene, but now the individual spheres aren't transformable on
		# their own - the only editable transform is now the root.

		script["writer"] = GafferScene.SceneWriter()
		script["writer"]["in"].setInput( script["group"]["out"] )
		script["writer"]["fileName"].setValue( os.path.join( self.temporaryDirectory(), "test.abc" ) )
		script["writer"]["task"].execute()

		script["reader"] = GafferScene.SceneReader()
		script["reader"]["fileName"].setInput( script["writer"]["fileName"] )

		# Set up a TransformTool and tell it to transform each of the spheres.

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["reader"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), selection )

		# The tool should instead choose to transform the root location.

		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].transformPlug(), script["reader"]["transform"] )

	def testSetFilter( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["sets"].setValue( "A" )

		script["setFilter"] = GafferScene.SetFilter()
		script["setFilter"]["set"].setValue( "A" )

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["sphere"]["out"] )
		script["transform"]["filter"].setInput( script["setFilter"]["out"] )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["transform"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere" ] ) )
		self.assertEqual( tool.selection()[0].transformPlug(), script["transform"]["transform"] )

	def testSpreadsheetAndCollect( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["spreadsheet"] = Gaffer.Spreadsheet()
		script["spreadsheet"]["rows"].addColumn( script["sphere"]["transform"] )
		script["sphere"]["transform"].setInput( script["spreadsheet"]["out"]["transform"] )
		script["spreadsheet"]["rows"].addRow()["name"].setValue( "sphere1" )
		script["spreadsheet"]["rows"].addRow()["name"].setValue( "sphere2" )
		script["spreadsheet"]["selector"].setValue( "${collect:rootName}" )

		script["collect"] = GafferScene.CollectScenes()
		script["collect"]["in"].setInput( script["sphere"]["out"] )
		script["collect"]["rootNames"].setInput( script["spreadsheet"]["activeRowNames"] )

		self.assertEqual( script["collect"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere1", "sphere2" ] ) )

		view = GafferSceneUI.SceneView()
		view["in"].setInput( script["collect"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere1" ] ) )
		self.assertEqual( tool.selection()[0].transformPlug(), script["spreadsheet"]["rows"][1]["cells"]["transform"]["value"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere2" ] ) )
		self.assertEqual( tool.selection()[0].transformPlug(), script["spreadsheet"]["rows"][2]["cells"]["transform"]["value"] )

		# Check that we can work with promoted plugs too

		box = Gaffer.Box.create( script, Gaffer.StandardSet( [ script["collect"], script["sphere"], script["spreadsheet"] ] ) )
		promotedRowsPlug = Gaffer.PlugAlgo.promote( box["spreadsheet"]["rows"] )

		self.assertEqual( tool.selection()[0].transformPlug(), promotedRowsPlug[2]["cells"]["transform"]["value"] )

if __name__ == "__main__":
	unittest.main()
