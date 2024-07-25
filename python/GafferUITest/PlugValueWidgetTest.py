##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import warnings
import weakref

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class PlugValueWidgetTest( GafferUITest.TestCase ) :

	@staticmethod
	def waitForUpdate( widget ) :

		with GafferTest.ParallelAlgoTest.UIThreadCallHandler() as handler :

			# Updates are done lazily, so we need to flush any pending updates.
			widget._PlugValueWidget__callUpdateFromValues.flush( widget )

			# And updates for computed values are done in the background, so we
			# need to wait until they're done.
			if any( isinstance( p, Gaffer.ValuePlug ) and Gaffer.PlugAlgo.dependsOnCompute( p ) for p in widget.getPlugs() ) :
				handler.assertCalled()

	def testContext( self ) :

		s = Gaffer.ScriptNode()
		s["m"] = GafferTest.MultiplyNode()
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent[\"m\"][\"op1\"] = int( context[\"frame\"] )" )

		w = GafferUI.NumericPlugValueWidget( s["m"]["op1"] )
		self.assertTrue( w.context().isSame( s.context() ) )

		s.context().setFrame( 10 )
		self.waitForUpdate( w )
		self.assertEqual( w.numericWidget().getValue(), 10 )

	def testDisableCreationForSpecificTypes( self ) :

		class ValueWidgetTestPlug( Gaffer.ValuePlug ) :

			def __init__( self, name="TestPlug", direction=Gaffer.Plug.Direction.In, flags=Gaffer.Plug.Flags.Default ) :

				Gaffer.ValuePlug.__init__( self, name, direction, flags )

		IECore.registerRunTimeTyped( ValueWidgetTestPlug )

		n = Gaffer.Node()
		n["p"] = ValueWidgetTestPlug()

		w = GafferUI.PlugValueWidget.create( n["p"] )
		self.assertIsInstance( w, GafferUI.ConnectionPlugValueWidget )

		GafferUI.PlugValueWidget.registerType( ValueWidgetTestPlug, None )

		w = GafferUI.PlugValueWidget.create( n["p"] )
		self.assertEqual( w, None )

	def testCreate( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.IntPlug()

		w = GafferUI.PlugValueWidget.create( n["p"] )
		self.assertTrue( isinstance( w, GafferUI.NumericPlugValueWidget ) )
		self.assertTrue( w.getPlug().isSame( n["p"] ) )

		Gaffer.Metadata.registerValue( n["p"], "plugValueWidget:type", "GafferUI.ConnectionPlugValueWidget" )

		w = GafferUI.PlugValueWidget.create( n["p"] )
		self.assertTrue( isinstance( w, GafferUI.ConnectionPlugValueWidget ) )
		self.assertTrue( w.getPlug().isSame( n["p"] ) )

	def testPlugTypesMustMatch( self ) :

		n = Gaffer.Node()
		n["user"]["p1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["user"]["p2"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		with self.assertRaises( GafferUI.PlugValueWidget.MultiplePlugTypesError ) :
			GafferUI.NumericPlugValueWidget( n["user"].children() )

		w = GafferUI.NumericPlugValueWidget( n["user"]["p1"] )
		with self.assertRaises( GafferUI.PlugValueWidget.MultiplePlugTypesError ) :
			w.setPlugs( n["user"].children() )

	def testCreateReleasesReferenceWithMismatchedPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["user"]["p1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n"]["user"]["p2"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		p = GafferUI.PlugPopup( s["n"]["user"].children() )

		w = weakref.ref( p )

		del p

		self.assertEqual( w(), None )

	def testGetPlugWithMultiplePlugs( self ) :

		n = Gaffer.Node()
		n["user"]["p1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["user"]["p2"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		w = GafferUI.NumericPlugValueWidget( n["user"].children() )
		self.assertRaises( GafferUI.PlugValueWidget.MultiplePlugsError, w.getPlug )

	def testCreateThrowsIfMultipleWidgetCreators( self ) :

		n = Gaffer.Node()
		n["user"]["p1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["user"]["p2"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( n["user"]["p1"], "plugValueWidget:type", "GafferUI.ConnectionPlugValueWidget" )

		with self.assertRaises( GafferUI.PlugValueWidget.MultipleWidgetCreatorsError ) :
			GafferUI.PlugValueWidget.create( n["user"].children() )

	def testCreateSupportsLegacyWidgetsWithSinglePlugs( self ) :

		class SinglePlugOnlyWidget( GafferUI.PlugValueWidget ) :

			def __init__( self, plug, **kw  ) :

				GafferUI.PlugValueWidget.__init__( self, GafferUI.TextWidget(), plug, **kw )

				if not isinstance( plug, Gaffer.Plug ) :
					raise GafferUI.PlugValueWidget.MultiplePlugsError()

		class LegacyWidgetTestPlug( Gaffer.ValuePlug ) :
			pass

		IECore.registerRunTimeTyped( LegacyWidgetTestPlug )
		GafferUI.PlugValueWidget.registerType( LegacyWidgetTestPlug, SinglePlugOnlyWidget )

		n = Gaffer.Node()
		n["user"]["p1"] = LegacyWidgetTestPlug()
		n["user"]["p2"] = LegacyWidgetTestPlug()

		self.assertIsInstance( GafferUI.PlugValueWidget.create( n["user"]["p1"] ), SinglePlugOnlyWidget )
		self.assertIsInstance( GafferUI.PlugValueWidget.create( { n["user"]["p1"] } ), SinglePlugOnlyWidget )

		with self.assertRaises( GafferUI.PlugValueWidget.MultiplePlugsError ) :
			GafferUI.PlugValueWidget.create( { n["user"]["p1"], n["user"]["p2"] } )

	def testAcquire( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.IntPlug()

		# hold a reference to the ScriptWindow
		# to make sure it stays alive
		sw = GafferUI.ScriptWindow.acquire( s )

		w = GafferUI.PlugValueWidget.acquire( s["n"]["p"] )
		self.assertTrue( isinstance( w, GafferUI.NumericPlugValueWidget ) )
		self.assertTrue( w.getPlug().isSame( s["n"]["p"] ) )
		self.assertTrue( GafferUI.PlugValueWidget.acquire( s["n"]["p"] ) is w )

		pw = GafferUI.PlugWidget.acquire( s["n"]["p"] )
		self.assertTrue( isinstance( pw, GafferUI.PlugWidget ) )
		self.assertTrue( pw.plugValueWidget() is w )
		self.assertTrue( GafferUI.PlugWidget.acquire( s["n"]["p"] ) is pw )

	def testContextSensitivePresets( self ) :

		def presetNames( plug ) :

			c = Gaffer.Context.current()
			return IECore.StringVectorData(
				[ k for k in c.keys() if k.startswith( "preset" ) ]
			)

		def presetValues( plug ) :

			c = Gaffer.Context.current()
			return IECore.IntVectorData(
				[ c[k] for k in Gaffer.Context.current().keys() if k.startswith( "preset" ) ]
			)

		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "presetNames", presetNames )
		Gaffer.Metadata.registerValue( GafferTest.AddNode, "op1", "presetValues", presetValues )

		script = Gaffer.ScriptNode()
		script["variables"]["presetOne"] = Gaffer.NameValuePlug( "presetOne", 1 )
		script["variables"]["presetTwo"] = Gaffer.NameValuePlug( "presetTwo", 2 )

		script["n"] = GafferTest.AddNode()

		widget = GafferUI.PlugValueWidget.create( script["n"]["op1"] )
		self.assertIsInstance( widget, GafferUI.NumericPlugValueWidget )

		menu = widget._popupMenuDefinition().item( "/Preset" ).subMenu()
		self.assertEqual( { "/presetOne", "/presetTwo" }, { k for k, v in menu.items() } )

		menu.item( "/presetOne" ).command()
		self.assertEqual( script["n"]["op1"].getValue(), 1 )
		menu.item( "/presetTwo" ).command()
		self.assertEqual( script["n"]["op1"].getValue(), 2 )

	class UpdateCountPlugValueWidget( GafferUI.PlugValueWidget ) :

		def __init__( self, plugs, **kw ) :

			self.updateCount = 0
			self.updateContexts = []

			GafferUI.PlugValueWidget.__init__( self, GafferUI.Label( "" ), plugs, **kw )

		def _updateFromValues( self, values, exception ) :

			self.updateCount += 1
			self.updateContexts.append( self.context() )

	def testUpdates( self ) :

		script = Gaffer.ScriptNode()
		script["add"] = GafferTest.AddNode()

		# Should do no updates during construction, because the widget is
		# not visible yet.
		with GafferUI.Window() as window :
			widget = self.UpdateCountPlugValueWidget( script["add"]["op1"] )

		self.assertEqual( widget.updateCount, 0 )
		self.assertEqual( len( widget.updateContexts ), 0 )

		# First update should occur when we make the widget visible.
		window.setVisible( True )
		self.waitForIdle()
		self.assertEqual( widget.updateCount, 1 )
		self.assertTrue( widget.updateContexts[0].isSame( script.context() ) )

		# Changing the context shouldn't trigger an update, because the
		# plug value isn't computed.
		script.context().setFrame( 2 )
		self.waitForUpdate( widget )
		self.assertEqual( widget.updateCount, 1 )

		# Changing the plug should trigger an update.
		widget.setPlug( script["add"]["op2"] )
		self.waitForUpdate( widget )
		self.assertEqual( widget.updateCount, 2 )
		self.assertTrue( widget.updateContexts[1].isSame( script.context() ) )

		# Changing the context still shouldn't trigger an update, because the
		# plug value isn't computed.
		script.context().setFrame( 3 )
		self.waitForUpdate( widget )
		self.assertEqual( widget.updateCount, 2 )

		# Changing the plug again should trigger an update again. This time we
		# see two updates - one to denote the start of the background task, and
		# one when it completes. This is because the plug's value is computed
		# and we don't want to block the UI thread with computes.
		widget.setPlug( script["add"]["sum"] )
		self.waitForUpdate( widget )
		self.assertEqual( widget.updateCount, 4 )
		self.assertTrue( widget.updateContexts[2].isSame( script.context() ) )
		self.assertTrue( widget.updateContexts[3].isSame( script.context() ) )

		# And now changing the context should trigger an update, since computed
		# values may be context-sensitive.
		script.context().setFrame( 4 )
		self.waitForUpdate( widget )
		self.assertEqual( widget.updateCount, 6 )
		self.assertTrue( widget.updateContexts[4].isSame( script.context() ) )
		self.assertTrue( widget.updateContexts[5].isSame( script.context() ) )

	class LegacyUpdateCountPlugValueWidget( GafferUI.PlugValueWidget ) :

		def __init__( self, plugs, **kw ) :

			self.updateCount = 0
			self.updateContexts = []

			GafferUI.PlugValueWidget.__init__( self, GafferUI.Label( "" ), plugs, **kw )

			self._updateFromPlugs()

		def _updateFromPlugs( self ) :

			self.updateCount += 1
			self.updateContexts.append( self.context() )

	def testLegacyUpdates( self ) :

		script = Gaffer.ScriptNode()
		script["add"] = GafferTest.AddNode()

		with warnings.catch_warnings() :

			warnings.simplefilter( "ignore", DeprecationWarning )

			# Should do one update during construction.
			widget = self.LegacyUpdateCountPlugValueWidget( script["add"]["op1"] )
			self.assertEqual( widget.updateCount, 1 )
			self.assertTrue( widget.updateContexts[0].isSame( script.context() ) )

			# And shouldn't update when the context changes
			# because the value is static.
			script.context().setFrame( 2 )
			self.assertEqual( widget.updateCount, 1 )

			# Changing the plug should cause an update.
			widget.setPlug( script["add"]["op2"] )
			self.assertEqual( widget.updateCount, 2 )
			self.assertTrue( widget.updateContexts[1].isSame( script.context() ) )

			# But the value is still static, so changing the
			# context should have no effect.
			script.context().setFrame( 3 )
			self.assertEqual( widget.updateCount, 2 )

			# Changing the plug again should cause an update again.
			widget.setPlug( script["add"]["sum"] )
			self.assertEqual( widget.updateCount, 3 )
			self.assertTrue( widget.updateContexts[2].isSame( script.context() ) )

			# And now changing the context does cause an update, because
			# the plug's value is computed.
			script.context().setFrame( 4 )
			self.assertEqual( widget.updateCount, 4 )
			self.assertTrue( widget.updateContexts[3].isSame( script.context() ) )

	def tearDown( self ) :

		GafferUITest.TestCase.tearDown( self )

		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "op1", "presetNames" )
		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "op1", "presetValues" )

if __name__ == "__main__":
	unittest.main()
