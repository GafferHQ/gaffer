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
import six
import weakref

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class PlugValueWidgetTest( GafferUITest.TestCase ) :

	def testContext( self ) :

		s = Gaffer.ScriptNode()
		s["m"] = GafferTest.MultiplyNode()
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent[\"m\"][\"op1\"] = int( context[\"frame\"] )" )

		w = GafferUI.NumericPlugValueWidget( s["m"]["op1"] )
		self.assertTrue( w.getContext().isSame( s.context() ) )

		s.context().setFrame( 10 )
		self.assertEqual( w.numericWidget().getValue(), 10 )

		context = Gaffer.Context()
		context.setFrame( 20 )
		w.setContext( context )
		self.assertTrue( w.getContext().isSame( context ) )
		self.assertEqual( w.numericWidget().getValue(), 20 )

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

		with six.assertRaisesRegex( self, ValueError, "Plugs have different types" ) :
			GafferUI.NumericPlugValueWidget( n["user"].children() )

		w = GafferUI.NumericPlugValueWidget( n["user"]["p1"] )
		with six.assertRaisesRegex( self, ValueError, "Plugs have different types" ) :
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

		with six.assertRaisesRegex( self, Exception, "Multiple widget creators" ) :
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

	def tearDown( self ) :

		GafferUITest.TestCase.tearDown( self )

		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "op1", "presetNames" )
		Gaffer.Metadata.deregisterValue( GafferTest.AddNode, "op1", "presetValues" )

if __name__ == "__main__":
	unittest.main()
