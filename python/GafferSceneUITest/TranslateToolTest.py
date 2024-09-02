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
import IECoreScene

import Gaffer
import GafferTest
import GafferUI
import GafferUITest
import GafferScene
import GafferSceneUI

class TranslateToolTest( GafferUITest.TestCase ) :

	def tearDown( self ) :

		IECoreScene.SharedSceneInterfaces.clear()

		GafferUITest.TestCase.tearDown( self )

	def testSelection( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )

		script["transformFilter"] = GafferScene.PathFilter()

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["group"]["out"] )
		script["transform"]["filter"].setInput( script["transformFilter"]["out"] )

		view = GafferSceneUI.SceneView( script )
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
		self.assertTrue( tool.selection()[0].editTarget().isSame( script["plane"]["transform"] ) )
		self.assertEqual( tool.selection()[0].transformSpace(), imath.M44f() )
		self.assertEqual( tool.selection()[0].warning(), "" )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group" ] ) )
		self.assertEqual( tool.selection()[0].path(), "/group" )
		self.assertEqual( tool.selection()[0].context(), view.getContext() )
		self.assertTrue( tool.selection()[0].upstreamScene().isSame( script["group"]["out"] ) )
		self.assertEqual( tool.selection()[0].upstreamPath(), "/group" )
		self.assertTrue( tool.selection()[0].editTarget().isSame( script["group"]["transform"] ) )
		self.assertEqual( tool.selection()[0].transformSpace(), imath.M44f() )
		self.assertEqual( tool.selection()[0].warning(), "" )

		script["transformFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )
		self.assertTrue( tool.selection()[0].editTarget().isSame( script["transform"]["transform"] ) )
		self.assertEqual( tool.selection()[0].warning(), "" )

		script["transformFilter"]["enabled"].setValue( False )
		self.assertTrue( tool.selection()[0].editTarget().isSame( script["group"]["transform"] ) )
		self.assertEqual( tool.selection()[0].warning(), "" )

		script["transformFilter"]["enabled"].setValue( True )
		self.assertEqual( tool.selection()[0].path(), "/group" )
		self.assertEqual( tool.selection()[0].context(), view.getContext() )
		self.assertTrue( tool.selection()[0].upstreamScene().isSame( script["transform"]["out"] ) )
		self.assertEqual( tool.selection()[0].upstreamPath(), "/group" )
		self.assertTrue( tool.selection()[0].editTarget().isSame( script["transform"]["transform"] ) )
		self.assertEqual( tool.selection()[0].transformSpace(), imath.M44f() )
		self.assertEqual( tool.selection()[0].warning(), "" )

		script["transform"]["enabled"].setValue( False )
		self.assertTrue( tool.selection()[0].editTarget().isSame( script["group"]["transform"] ) )
		self.assertEqual( tool.selection()[0].warning(), "" )

	def testTranslate( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

	def testNegativeScale( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["plane"]["transform"]["scale"]["x"].setValue( -10 )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["plane"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/plane" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )
		tool["orientation"].setValue( tool.Orientation.Local )

		# We want the direction of the handles to reflect the
		# flipped scale, but not its magnitude.

		self.assertTrue(
			tool.handlesTransform().equalWithAbsError(
				imath.M44f().scale( imath.V3f( -1, 1, 1 ) ),
				0.000001
			)
		)

		# And the handles need to move the object in the right
		# direction still.

		tool.translate( imath.V3f( 1, 2, 3 ) )

		self.assertTrue(
			script["plane"]["transform"]["translate"].getValue().equalWithAbsError(
				imath.V3f(-1, 2, 3),
				0.000001
			)
		)

	def testGroup( self ) :

		script = Gaffer.ScriptNode()

		script["group"] = GafferScene.Group()

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["group"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane", "/group/sphere" ] ) )

		self.assertTrue( tool.selectionEditable() )
		selection = tool.selection()
		self.assertEqual( len( selection ), 2 )
		self.assertEqual( { s.editTarget() for s in selection }, { script["plane"]["transform"], script["sphere"]["transform"] } )

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

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["group"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane", "/group/plane1" ] ) )

		# Even though there are two selected paths, there should only be
		# one thing in the tool's selection, because both paths are generated
		# by the same upstream node.

		selection = tool.selection()
		self.assertEqual( len( selection ), 1 )
		self.assertTrue( tool.selectionEditable() )
		self.assertEqual( selection[0].editTarget(), script["plane"]["transform"] )

	def testHandlesFollowLastSelected( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()
		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["transform"]["translate"].setValue( imath.V3f( 1 ) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["plane"]["out"] )
		script["group"]["in"][1].setInput( script["sphere"]["out"] )

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["box"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/sphere" )

		self.assertEqual( tool.selection()[0].editTarget(), script["box"]["transform"] )

	def testSelectionChangedSignal( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView( script )
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

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["sceneReader"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )
		selection = tool.selection()
		self.assertEqual( len( selection ), 1 )
		self.assertEqual( selection[0].editTarget(), script["sceneReader"]["transform"] )
		self.assertEqual( selection[0].path(), "/group" )
		self.assertEqual( selection[0].warning(), "Editing parent location \"/group\"" )

	def testSelectionRefersToFirstPublicPlug( self ) :

		script = Gaffer.ScriptNode()
		script["plane"] = GafferScene.Plane()

		view = GafferSceneUI.SceneView( script )

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

		view = GafferSceneUI.SceneView( script )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )
		self.assertEqual( tool.selection(), [] )

		view["in"].setInput( script["group"]["out"] )
		self.assertEqual( tool.selection(), [] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/plane" ] ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].editTarget(), script["plane"]["transform"] )

	def testLastSelectedObjectWithSharedTransformPlug( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["sphere"]["out"] )
		script["group"]["in"][1].setInput( script["sphere"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["group"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/sphere" ] ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selectionEditable() )
		self.assertEqual( tool.selection()[0].editTarget(), script["sphere"]["transform"] )
		self.assertEqual( tool.selection()[0].path(), "/group/sphere" )

		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/group/sphere1" )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selectionEditable() )
		self.assertEqual( tool.selection()[0].editTarget(), script["sphere"]["transform"] )
		self.assertEqual( tool.selection()[0].path(), "/group/sphere1" )

		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/group/sphere" )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selectionEditable() )
		self.assertEqual( tool.selection()[0].editTarget(), script["sphere"]["transform"] )
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
		script["writer"]["fileName"].setValue( self.temporaryDirectory() / "test.abc" )
		script["writer"]["task"].execute()

		script["reader"] = GafferScene.SceneReader()
		script["reader"]["fileName"].setInput( script["writer"]["fileName"] )

		# Set up a TransformTool and tell it to transform each of the spheres.

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["reader"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), selection )

		# The tool should instead choose to transform the root location.

		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].editTarget(), script["reader"]["transform"] )

	def testSetFilter( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["sets"].setValue( "A" )

		script["setFilter"] = GafferScene.SetFilter()
		script["setFilter"]["set"].setValue( "A" )

		script["transform"] = GafferScene.Transform()
		script["transform"]["in"].setInput( script["sphere"]["out"] )
		script["transform"]["filter"].setInput( script["setFilter"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["transform"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere" ] ) )
		self.assertEqual( tool.selection()[0].editTarget(), script["transform"]["transform"] )

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
		script["collect"]["rootNames"].setInput( script["spreadsheet"]["enabledRowNames"] )

		self.assertEqual( script["collect"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "sphere1", "sphere2" ] ) )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["collect"]["out"] )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere1" ] ) )
		self.assertEqual( tool.selection()[0].editTarget(), script["spreadsheet"]["rows"][1]["cells"]["transform"]["value"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere2" ] ) )
		self.assertEqual( tool.selection()[0].editTarget(), script["spreadsheet"]["rows"][2]["cells"]["transform"]["value"] )

		# Check that we can work with promoted plugs too

		box = Gaffer.Box.create( script, Gaffer.StandardSet( [ script["collect"], script["sphere"], script["spreadsheet"] ] ) )
		promotedRowsPlug = Gaffer.PlugAlgo.promote( box["spreadsheet"]["rows"] )

		self.assertEqual( tool.selection()[0].editTarget(), promotedRowsPlug[2]["cells"]["transform"]["value"] )

	def testEditScopes( self ) :

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["transform"]["translate"].setValue( imath.V3f( 1, 0, 0 ) )

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["sphere"]["out"] )
		script["editScope"]["in"].setInput( script["sphere"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["editScope"]["out"] )
		view["editScope"].setInput( script["editScope"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selection()[0].editable() )
		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/sphere" ) )
		self.assertEqual( script["editScope"]["out"].transform( "/sphere" ), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

		tool.translate( imath.V3f( 0, 1, 0 ) )
		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 1, 0 ) ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selection()[0].editable() )
		self.assertTrue( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/sphere" ) )
		self.assertEqual( script["editScope"]["out"].transform( "/sphere" ), imath.M44f().translate( imath.V3f( 1, 1, 0 ) ) )

	def testParentAndChildInSameEditScope( self ) :

		script = Gaffer.ScriptNode()

		script["cube"] = GafferScene.Cube()
		script["cube"]["transform"]["translate"].setValue( imath.V3f( 0, 1, 0 ) )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["cube"]["out"] )

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["group"]["out"] )
		script["editScope"]["in"].setInput( script["group"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["editScope"]["out"] )
		view["editScope"].setInput( script["editScope"]["out"] )

		groupTransformEdit = GafferScene.EditScopeAlgo.acquireTransformEdit( script["editScope"], "/group" )
		groupTransformEdit.rotate["y"].setValue( 90 )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/group/cube" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		self.assertTrue(
			tool.handlesTransform().equalWithAbsError(
				groupTransformEdit.matrix() * imath.M44f().translate( imath.V3f( 0, 1, 0 ) ),
				0.00001
			)
		)

		tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			script["editScope"]["out"].fullTransform( "/group/cube" ).equalWithAbsError(
				imath.M44f().translate( imath.V3f( 1, 1, 0 ) ) * groupTransformEdit.matrix(),
				0.00001
			)
		)

		tool.translate( imath.V3f( 1, 0, 0 ) )

		self.assertTrue(
			script["editScope"]["out"].fullTransform( "/group/cube" ).equalWithAbsError(
				imath.M44f().translate( imath.V3f( 2, 1, 0 ) ) * groupTransformEdit.matrix(),
				0.00001
			)
		)

	def testAnimationHotkey( self ) :

		script = Gaffer.ScriptNode()
		script["cube"] = GafferScene.Cube()

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["cube"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		for plug in Gaffer.FloatPlug.RecursiveRange( script["cube"]["transform"] ) :
			self.assertFalse( Gaffer.Animation.isAnimated( plug ) )

		view.viewportGadget().keyPressSignal()( view.viewportGadget(), GafferUI.KeyEvent( "S" ) )

		for plug in Gaffer.FloatPlug.RecursiveRange( script["cube"]["transform"] ) :
			self.assertTrue( Gaffer.Animation.isAnimated( plug ) )

	def testAnimationHotkeyWithEditScopes( self ) :

		script = Gaffer.ScriptNode()
		script["cube"] = GafferScene.Cube()

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["cube"]["out"] )
		script["editScope"]["in"].setInput( script["cube"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["editScope"]["out"] )
		view["editScope"].setInput( script["editScope"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		for plug in Gaffer.FloatPlug.RecursiveRange( script["cube"]["transform"] ) :
			self.assertFalse( Gaffer.Animation.isAnimated( plug ) )
		self.assertFalse( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/cube" ) )

		view.viewportGadget().keyPressSignal()( view.viewportGadget(), GafferUI.KeyEvent( "S" ) )

		for plug in Gaffer.FloatPlug.RecursiveRange( script["cube"]["transform"] ) :
			self.assertFalse( Gaffer.Animation.isAnimated( plug ) )
		self.assertTrue( GafferScene.EditScopeAlgo.hasTransformEdit( script["editScope"], "/cube" ) )
		edit = GafferScene.EditScopeAlgo.acquireTransformEdit( script["editScope"], "/cube" )
		for vectorPlug in ( edit.translate, edit.rotate, edit.scale, edit.pivot ) :
			for plug in vectorPlug :
				self.assertTrue( Gaffer.Animation.isAnimated( plug ) )

		tool.translate( imath.V3f( 1, 0, 0 ) )
		self.assertEqual(
			script["editScope"]["out"].transform( "/cube" ),
			imath.M44f().translate( imath.V3f( 1, 0, 0 ) )
		)

	def testTransformInEditScopeButEditScopeOff( self ) :

		# Create an EditScope with an edit in it

		script = Gaffer.ScriptNode()

		script["sphere"] = GafferScene.Sphere()

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["sphere"]["out"] )
		script["editScope"]["in"].setInput( script["sphere"]["out"] )

		transformEdit = GafferScene.EditScopeAlgo.acquireTransformEdit( script["editScope"], "/sphere" )
		transformEdit.translate.setValue( imath.V3f( 1, 0, 0 ) )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["editScope"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/sphere" ] ) )

		# We want the TranslateTool to pick up and use that edit
		# even if we haven't told it to use that EditScope.

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )
		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selectionEditable() )
		self.assertTrue( tool.selection()[0].editable() )
		self.assertEqual( tool.selection()[0].acquireTransformEdit( createIfNecessary = False ), transformEdit )
		self.assertEqual(
			tool.selection()[0].editTarget(),
			transformEdit.translate.ancestor( Gaffer.Spreadsheet.RowPlug )
		)

		tool.translate( imath.V3f( 0, 1, 0 ) )
		self.assertEqual( tool.handlesTransform(), imath.M44f().translate( imath.V3f( 1, 1, 0 ) ) )
		self.assertEqual( transformEdit.translate.getValue(), imath.V3f( 1, 1, 0 ) )

	def testNonEditableSelections( self ) :

		script = Gaffer.ScriptNode()
		script["sphere"] = GafferScene.Sphere()

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["sphere"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube", "/plane" ] ) )

		# We want the tool selection to tell us when something is wrong.

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )
		self.assertEqual( len( tool.selection() ), 2 )
		self.assertFalse( tool.selectionEditable() )
		self.assertEqual(
			{ s.path() for s in tool.selection() },
			{ "/cube", "/plane" },
		)
		self.assertEqual(
			{ s.warning() for s in tool.selection() },
			{ "Location does not exist" }
		)

	def testInteractionWithAimConstraints( self ) :

		script = Gaffer.ScriptNode()

		# Cube at ( 0, 10, 0 ), aimed at a sphere at the origin.

		script["sphere"] = GafferScene.Sphere()

		script["cube"] = GafferScene.Cube()
		script["cube"]["transform"]["translate"]["y"].setValue( 10 )

		script["parent"] = GafferScene.Parent()
		script["parent"]["parent"].setValue( "/" )
		script["parent"]["in"].setInput( script["sphere"]["out"] )
		script["parent"]["children"][0].setInput( script["cube"]["out"] )

		script["cubeFilter"] = GafferScene.PathFilter()
		script["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		script["aim"] = GafferScene.AimConstraint()
		script["aim"]["in"].setInput( script["parent"]["out"] )
		script["aim"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["aim"]["target"].setValue( "/sphere" )

		# Translate in Z (parent space) and check that we moved to
		# where we expected.

		self.assertEqual(
			script["aim"]["out"].transform( "/cube" ).translation(),
			imath.V3f( 0, 10, 0 )
		)

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["aim"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		self.assertEqual( len( tool.selection() ), 1 )
		self.assertEqual( tool.selection()[0].path(), "/cube" )
		self.assertEqual( tool.selection()[0].upstreamPath(), "/cube" )
		self.assertEqual( tool.selection()[0].editTarget(), script["cube"]["transform"] )

		tool.translate( imath.V3f( 0, 0, 10 ) )
		self.assertEqual(
			script["aim"]["out"].transform( "/cube" ).translation(),
			imath.V3f( 0, 10, 10 )
		)

		# Reset back to ( 0, 10, 0 ) and check the same thing works with
		# an EditScope.

		script["cube"]["transform"]["translate"].setValue( imath.V3f( 0, 10, 0 ) )

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["parent"]["out"] )
		script["editScope"]["in"].setInput( script["parent"]["out"] )
		script["aim"]["in"].setInput( script["editScope"]["out"] )

		view["editScope"].setInput( script["editScope"]["out"] )

		self.assertEqual( len( tool.selection() ), 1 )
		self.assertTrue( tool.selectionEditable() )
		self.assertEqual( tool.selection()[0].path(), "/cube" )
		self.assertEqual( tool.selection()[0].upstreamPath(), "/cube" )
		self.assertEqual( tool.selection()[0].editTarget(), script["editScope"] )

		tool.translate( imath.V3f( 0, 0, 10 ) )
		self.assertEqual(
			script["aim"]["out"].transform( "/cube" ).translation(),
			imath.V3f( 0, 10, 10 )
		)

	def testInteractionWithParentConstraints( self ) :

		script = Gaffer.ScriptNode()

		# Cube with identity transform, parent constrained to sphere
		# rotated 90 around X and translated to ( 5, 5, 0 ).

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["transform"]["rotate"]["x"].setValue( 90 )
		script["sphere"]["transform"]["translate"].setValue( imath.V3f( 5, 5, 0 ) )

		script["cube"] = GafferScene.Cube()

		script["parent"] = GafferScene.Parent()
		script["parent"]["parent"].setValue( "/" )
		script["parent"]["in"].setInput( script["sphere"]["out"] )
		script["parent"]["children"][0].setInput( script["cube"]["out"] )

		script["cubeFilter"] = GafferScene.PathFilter()
		script["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )

		script["constraint"] = GafferScene.ParentConstraint()
		script["constraint"]["in"].setInput( script["parent"]["out"] )
		script["constraint"]["filter"].setInput( script["cubeFilter"]["out"] )
		script["constraint"]["target"].setValue( "/sphere" )

		self.assertEqual(
			script["constraint"]["out"].fullTransform( "/cube" ),
			script["constraint"]["out"].fullTransform( "/sphere" )
		)

		# View and Tool

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["constraint"]["out"] )
		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		# Check handle orientation

		tool["orientation"].setValue( tool.Orientation.Local )
		self.assertEqual( tool.handlesTransform(), script["constraint"]["out"].fullTransform( "/cube" ) )

		tool["orientation"].setValue( tool.Orientation.Parent )
		self.assertEqual(
			tool.handlesTransform(),
			imath.M44f().translate(
				script["constraint"]["out"].fullTransform( "/cube" ).translation()
			)
		)

		# Check translation operation

		tool["orientation"].setValue( tool.Orientation.Local )
		tool.translate( imath.V3f( 1, 2, 3 ) )
		self.assertEqual(
			script["cube"]["transform"]["translate"].getValue(),
			imath.V3f( 1, 2, 3 )
		)

	def testMultipleSelectionWithEditScope( self ) :

		script = Gaffer.ScriptNode()

		script["cube1"] = GafferScene.Cube()
		script["cube2"] = GafferScene.Cube()
		script["cube3"] = GafferScene.Cube()

		script["parent"] = GafferScene.Parent()
		script["parent"]["parent"].setValue( "/" )
		script["parent"]["children"][0].setInput( script["cube1"]["out"] )
		script["parent"]["children"][1].setInput( script["cube2"]["out"] )
		script["parent"]["children"][2].setInput( script["cube3"]["out"] )

		script["editScope"] = Gaffer.EditScope()
		script["editScope"].setup( script["parent"]["out"] )
		script["editScope"]["in"].setInput( script["parent"]["out"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["editScope"]["out"] )
		view["editScope"].setInput( script["editScope"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube", "/cube1", "/cube2" ] ) )
		GafferSceneUI.ContextAlgo.setLastSelectedPath( view.getContext(), "/cube" )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		with Gaffer.UndoScope( script ) :
			tool.translate( imath.V3f( 10, 0, 0 ) )

		with view.getContext() :
			self.assertEqual( script["editScope"]["out"].transform( "/cube" ).translation(), imath.V3f( 10, 0, 0 ) )
			self.assertEqual( script["editScope"]["out"].transform( "/cube1" ).translation(), imath.V3f( 10, 0, 0 ) )
			self.assertEqual( script["editScope"]["out"].transform( "/cube2" ).translation(), imath.V3f( 10, 0, 0 ) )

	def testIndividualComponentConnections( self ) :

		script = Gaffer.ScriptNode()
		script["box"] = Gaffer.Box()
		script["box"]["cube"] = GafferScene.Cube()

		promotedX = Gaffer.PlugAlgo.promote( script["box"]["cube"]["transform"]["translate"]["x"] )
		promotedY = Gaffer.PlugAlgo.promote( script["box"]["cube"]["transform"]["translate"]["y"] )
		promotedZ = Gaffer.PlugAlgo.promote( script["box"]["cube"]["transform"]["translate"]["z"] )

		view = GafferSceneUI.SceneView( script )
		view["in"].setInput( script["box"]["cube"]["out"] )

		GafferSceneUI.ContextAlgo.setSelectedPaths( view.getContext(), IECore.PathMatcher( [ "/cube" ] ) )

		tool = GafferSceneUI.TranslateTool( view )
		tool["active"].setValue( True )

		tool.translate( imath.V3f( 1, 2, 3 ) )
		self.assertEqual( script["box"]["cube"]["transform"]["translate"].getValue(), imath.V3f( 1, 2, 3 ) )
		self.assertEqual( promotedX.getValue(), 1 )
		self.assertEqual( promotedY.getValue(), 2 )
		self.assertEqual( promotedZ.getValue(), 3 )

if __name__ == "__main__":
	unittest.main()
