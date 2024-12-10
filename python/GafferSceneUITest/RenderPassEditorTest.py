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
import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneUI
import GafferUITest

from GafferSceneUI import _GafferSceneUI

class RenderPassEditorTest( GafferUITest.TestCase ) :

	def testRenderPassPathSimpleChildren( self ) :

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( ["A", "B", "C", "D"] ) )

		context = Gaffer.Context()
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( renderPasses["out"], context, "/" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		children = path.children()
		self.assertEqual( [ str( c ) for c in children ], [ "/A", "/B", "/C", "/D" ] )
		for child in children :
			self.assertIsInstance( child, _GafferSceneUI._RenderPassEditor.RenderPassPath )
			self.assertTrue( child.getContext().isSame( context ) )
			self.assertTrue( child.getScene().isSame( renderPasses["out"] ) )
			self.assertTrue( child.isLeaf() )
			self.assertTrue( child.isValid() )
			self.assertEqual( child.children(), [] )

	def testRenderPassPathIsValid( self ) :

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( ["A", "B", "C", "D"] ) )

		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( renderPasses["out"], Gaffer.Context(), "/" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		for parent, valid in [
			( "/", True ),
			( "/A", True ),
			( "/A/B", False ),
			( "/B", True ),
			( "/C", True ),
			( "/D", True ),
			( "/E", False ),
			( "/E/F", False ),
		] :

			path.setFromString( parent )
			self.assertEqual( path.isValid(), valid )

	def testRenderPassPathIsLeaf( self ) :

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( ["A", "B", "C", "D"] ) )

		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( renderPasses["out"], Gaffer.Context(), "/" )
		self.assertTrue( path.isValid() )
		self.assertFalse( path.isLeaf() )

		for parent, leaf in [
			( "/", False ),
			( "/A", True ),
			( "/A/B", False ),
			( "/B", True ),
			( "/C", True ),
			( "/D", True ),
			( "/E", False ),
			( "/E/F", False ),
		] :

			path.setFromString( parent )
			self.assertEqual( path.isLeaf(), leaf )

	def testRenderPassPathCancellation( self ) :

		plane = GafferScene.Plane()
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( plane["out"], Gaffer.Context(), "/" )

		canceller = IECore.Canceller()
		canceller.cancel()

		with self.assertRaises( IECore.Cancelled ) :
			path.children( canceller )

		with self.assertRaises( IECore.Cancelled ) :
			path.isValid( canceller )

		with self.assertRaises( IECore.Cancelled ) :
			path.isLeaf( canceller )

		with self.assertRaises( IECore.Cancelled ) :
			path.property( "renderPassPath:enabled", canceller )

	def testRenderPassPathInspectionContext( self ) :

		def testFn( name ) :
			return "/".join( name.split( "_" )[:-1] )

		GafferSceneUI.RenderPassEditor.registerPathGroupingFunction( testFn )

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( ["A", "A_A", "B"] ) )

		for path, renderPass, grouped in (
			( "/A_A", "A_A", False ),
			( "/A_A", None, True ),
			( "/A", "A", False ),
			( "/A", "A", True ),
			( "/A/A_A", None, False ),
			( "/A/A_A", "A_A", True ),
			( "/B", "B", False ),
			( "/B", "B", True ),
			( "/BOGUS", None, False ),
			( "/BOGUS", None, True ),
			( "/B/OGUS", None, False ),
			( "/B/OGUS", None, True ),
		) :

			path = _GafferSceneUI._RenderPassEditor.RenderPassPath( renderPasses["out"], Gaffer.Context(), path, grouped = grouped )
			inspectionContext = path.inspectionContext()
			if renderPass is not None :
				self.assertIn( "renderPass", inspectionContext )
				self.assertEqual( inspectionContext["renderPass"], renderPass )
			else :
				self.assertIsNone( inspectionContext )

	def testRenderPassPathAdaptorDisablingPasses( self ) :

		def createAdaptor() :

			node = GafferScene.SceneProcessor()
			node["options"] = GafferScene.CustomOptions()
			node["options"]["in"].setInput( node["in"] )
			node["options"]["options"].addChild( Gaffer.NameValuePlug( "renderPass:enabled", False ) )

			node["switch"] = Gaffer.NameSwitch()
			node["switch"].setup( node["options"]["out"] )
			node["switch"]["in"][0]["value"].setInput( node["in"] )
			node["switch"]["in"][1]["value"].setInput( node["options"]["out"] )
			node["switch"]["in"][1]["name"].setValue( "B C" )
			node["switch"]["selector"].setValue( "${renderPass}" )

			node["out"].setInput( node["switch"]["out"]["value"] )

			return node

		GafferScene.SceneAlgo.registerRenderAdaptor( "RenderPassEditorTest", createAdaptor, client = "RenderPassWedge" )
		self.addCleanup( GafferScene.SceneAlgo.deregisterRenderAdaptor, "RenderPassEditorTest" )

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( [ "A", "B", "C", "D" ] ) )

		adaptors = GafferSceneUI.RenderPassEditor._createRenderAdaptors()
		adaptors["in"].setInput( renderPasses["out"] )

		context = Gaffer.Context()
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( adaptors["out"], context, "/" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D" ] )

		pathCopy = path.copy()

		for p in [ "/A", "/B", "/C", "/D" ] :
			pathCopy.setFromString( p )
			self.assertEqual( pathCopy.property( "renderPassPath:enabled" ), p in ( "/A", "/D" ) )
			self.assertTrue( pathCopy.property( "renderPassPath:enabledWithoutAdaptors" ) )

	def testRenderPassPathAdaptorDeletingPasses( self ) :

		def createAdaptor() :

			node = GafferScene.DeleteRenderPasses()
			node["names"].setValue( "B C" )
			return node

		GafferScene.SceneAlgo.registerRenderAdaptor( "RenderPassEditorTest", createAdaptor, client = "RenderPassWedge" )
		self.addCleanup( GafferScene.SceneAlgo.deregisterRenderAdaptor, "RenderPassEditorTest" )

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( [ "A", "B", "C", "D" ] ) )

		adaptors = GafferSceneUI.RenderPassEditor._createRenderAdaptors()
		adaptors["in"].setInput( renderPasses["out"] )

		context = Gaffer.Context()
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( adaptors["out"], context, "/" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D" ] )

		pathCopy = path.copy()

		for p in [ "/A", "/B", "/C", "/D" ] :
			pathCopy.setFromString( p )
			self.assertEqual( pathCopy.property( "renderPassPath:enabled" ), p in ( "/A", "/D" ) )
			self.assertTrue( pathCopy.property( "renderPassPath:enabledWithoutAdaptors" ) )

	def testSearchFilter( self ) :

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( ["A", "B", "C", "D"] ) )

		context = Gaffer.Context()
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( renderPasses["out"], context, "/" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D" ] )

		searchFilter = _GafferSceneUI._RenderPassEditor.SearchFilter()
		searchFilter.setMatchPattern( "A" )
		path.setFilter( searchFilter )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A" ] )

		searchFilter.setMatchPattern( "A D" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/D" ] )

	def testDisabledRenderPassFilter( self ) :

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( ["A", "B", "C", "D"] ) )

		disablePass = GafferScene.CustomOptions( "disablePass" )
		disablePass["in"].setInput( renderPasses["out"] )
		disablePass["options"].addChild( Gaffer.NameValuePlug( "renderPass:enabled", Gaffer.BoolPlug( "value", defaultValue = False ), True, "member1" ) )

		# disable A & D
		switch = Gaffer.NameSwitch()
		switch.setup( renderPasses["out"] )
		switch["selector"].setValue( "${renderPass}" )
		switch["in"]["in0"]["value"].setInput( renderPasses["out"] )
		switch["in"]["in1"]["value"].setInput( disablePass["out"] )
		switch["in"]["in1"]["name"].setValue( "A D" )

		context = Gaffer.Context()
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( switch["out"]["value"], context, "/" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D" ] )

		pathCopy = path.copy()

		for p in [ "/A", "/B", "/C", "/D" ] :
			pathCopy.setFromString( p )
			self.assertEqual( pathCopy.property( "renderPassPath:enabled" ), p in ( "/B", "/C" ) )

		disabledRenderPassFilter = _GafferSceneUI._RenderPassEditor.DisabledRenderPassFilter()
		path.setFilter( disabledRenderPassFilter )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/B", "/C" ] )

		disabledRenderPassFilter.setEnabled( False )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B", "/C", "/D" ] )

	def testPathGroupingFunction( self ) :

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( ["char_bot_beauty", "char_bot_shadow"] ) )

		context = Gaffer.Context()
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( renderPasses["out"], context, "/" )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/char_bot_beauty", "/char_bot_shadow" ] )

		def testFn( name ) :
			return "/".join( name.split( "_" )[:-1] )

		# Register our grouping function and test a grouped path
		GafferSceneUI.RenderPassEditor.registerPathGroupingFunction( testFn )
		self.assertEqual( testFn( "/char_bot_beauty" ), GafferSceneUI.RenderPassEditor.pathGroupingFunction()( "/char_bot_beauty" ) )

		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( renderPasses["out"], context, "/", grouped = True )

		for parent, children in [
			( "/", [ "/char" ] ),
			( "/char", [ "/char/bot" ] ),
			( "/char/bot", [ "/char/bot/char_bot_beauty", "/char/bot/char_bot_shadow" ] ),
			( "/char/bot/char_bot_beauty", [] ),
			( "/char/bot/char_bot_shadow", [] ),
		] :

			path.setFromString( parent )
			self.assertTrue( path.isValid() )
			self.assertEqual( path.isLeaf(), children == [] )
			self.assertEqual( [ str( c ) for c in path.children() ], children )

		# Ensure we can still get a flat output
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( renderPasses["out"], context, "/", grouped = False )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/char_bot_beauty", "/char_bot_shadow" ] )

	def testDisabledRenderPassFilterWithPathGroupingFunction( self ) :

		renderPasses = GafferScene.RenderPasses()
		renderPasses["names"].setValue( IECore.StringVectorData( ["A_A", "A_B", "B_C", "B_D"] ) )

		disablePass = GafferScene.CustomOptions( "disablePass" )
		disablePass["in"].setInput( renderPasses["out"] )
		disablePass["options"].addChild( Gaffer.NameValuePlug( "renderPass:enabled", Gaffer.BoolPlug( "value", defaultValue = False ), True, "member1" ) )

		# disable A_B, B_C, B_D
		switch = Gaffer.NameSwitch()
		switch.setup( renderPasses["out"] )
		switch["selector"].setValue( "${renderPass}" )
		switch["in"]["in0"]["value"].setInput( renderPasses["out"] )
		switch["in"]["in1"]["value"].setInput( disablePass["out"] )
		switch["in"]["in1"]["name"].setValue( "A_B B_C B_D" )

		def testFn( name ) :
			return name.split( "_" )[:-1]

		GafferSceneUI.RenderPassEditor.registerPathGroupingFunction( testFn )
		context = Gaffer.Context()
		path = _GafferSceneUI._RenderPassEditor.RenderPassPath( switch["out"]["value"], context, "/", grouped = True )

		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B" ] )

		pathCopy = path.copy()
		for p in [ "/A/A_A", "/A/A_B", "/B/B_C", "/B/B_D" ] :
			pathCopy.setFromString( p )
			self.assertEqual( pathCopy.property( "renderPassPath:enabled" ), p == "/A/A_A" )

		disabledRenderPassFilter = _GafferSceneUI._RenderPassEditor.DisabledRenderPassFilter()
		path.setFilter( disabledRenderPassFilter )
		# We should only see /A, as both of /B's children are disabled
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A" ] )
		path.setFromString( "/A" )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A/A_A" ] )

		# Disabling the filter should restore all paths
		disabledRenderPassFilter.setEnabled( False )
		path.setFromString( "/" )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A", "/B" ] )
		path.setFromString( "/A" )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/A/A_A", "/A/A_B" ] )
		path.setFromString( "/B" )
		self.assertEqual( [ str( c ) for c in path.children() ], [ "/B/B_C", "/B/B_D" ] )
