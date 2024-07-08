##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class PlugLayoutTest( GafferUITest.TestCase ) :

	def testRenamingPlugs( self ) :

		n = Gaffer.Node()
		n["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		ui = GafferUI.PlugLayout( n )

		w = ui.plugValueWidget( n["a"] )
		self.assertTrue( w is not None )
		self.assertTrue( w.getPlug().isSame( n["a"] ) )

		n["a"].setName( "b" )

		w2 = ui.plugValueWidget( n["b"] )
		self.assertTrue( w2 is not None )
		self.assertTrue( w2 is w )
		self.assertTrue( w2.getPlug().isSame( n["b"] ) )

	def testLayoutOrder( self ) :

		n = Gaffer.Node()
		n["user"]["a"] = Gaffer.IntPlug()
		n["user"]["b"] = Gaffer.IntPlug()
		n["user"]["c"] = Gaffer.IntPlug()

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"] ),
			[ n["user"]["a"], n["user"]["b"], n["user"]["c"] ],
		)

		Gaffer.Metadata.registerValue( n["user"]["a"], "layout:index", 3 )
		Gaffer.Metadata.registerValue( n["user"]["b"], "layout:index", 2 )
		Gaffer.Metadata.registerValue( n["user"]["c"], "layout:index", 1 )

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"] ),
			[ n["user"]["c"], n["user"]["b"], n["user"]["a"] ],
		)

	class CustomWidget( GafferUI.Widget ) :

		def __init__( self, node ) :

			GafferUI.Widget.__init__( self, GafferUI.Label( "Custom Widget" ) )

			self.node = node

	def testCustomWidgets( self ) :

		n = Gaffer.Node()
		Gaffer.Metadata.registerValue( n, "layout:customWidget:test:widgetType", "GafferUITest.PlugLayoutTest.CustomWidget" )

		p = GafferUI.PlugLayout( n )

		self.assertTrue( isinstance( p.customWidget( "test" ), self.CustomWidget ) )
		self.assertTrue( p.customWidget( "test" ).node.isSame( n ) )

		Gaffer.Metadata.registerValue( n, "layout:customWidget:test:widgetType", "" )
		self.assertIsNone( p.customWidget( "test") )

	def testSectionQueries( self ) :

		n = Gaffer.Node()
		n["user"]["a"] = Gaffer.IntPlug()
		n["user"]["b"] = Gaffer.IntPlug()
		n["user"]["c"] = Gaffer.IntPlug()

		self.assertEqual( GafferUI.PlugLayout.layoutSections( n["user"] ), [ "" ] )

		Gaffer.Metadata.registerValue( n["user"]["a"], "layout:section", "A" )
		Gaffer.Metadata.registerValue( n["user"]["b"], "layout:section", "B" )
		Gaffer.Metadata.registerValue( n["user"]["c"], "layout:section", "C" )

		self.assertEqual( GafferUI.PlugLayout.layoutSections( n["user"] ), [ "A", "B", "C" ] )

		Gaffer.Metadata.registerValue( n["user"]["a"], "layout:index", 3 )
		self.assertEqual( GafferUI.PlugLayout.layoutSections( n["user"] ), [ "B", "C", "A" ] )

	def testLayoutOrderSectionArgument( self ) :

		n = Gaffer.Node()
		n["user"]["a"] = Gaffer.IntPlug()
		n["user"]["b"] = Gaffer.IntPlug()
		n["user"]["c"] = Gaffer.IntPlug()

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"], section = "" ),
			[ n["user"]["a"], n["user"]["b"], n["user"]["c"] ],
		)

		Gaffer.Metadata.registerValue( n["user"]["a"], "layout:section", "AB" )
		Gaffer.Metadata.registerValue( n["user"]["b"], "layout:section", "AB" )
		Gaffer.Metadata.registerValue( n["user"]["c"], "layout:section", "C" )

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"], section = "AB" ),
			[ n["user"]["a"], n["user"]["b"] ],
		)

		self.assertEqual(
			GafferUI.PlugLayout.layoutOrder( n["user"], section = "C" ),
			[ n["user"]["c"] ],
		)

	def testChangingWidgetType( self ) :

		n = Gaffer.Node()
		n["p1"] = Gaffer.IntPlug()
		n["p2"] = Gaffer.IntPlug()

		l = GafferUI.PlugLayout( n )
		self.assertTrue( isinstance( l.plugValueWidget( n["p1"] ), GafferUI.NumericPlugValueWidget ) )
		w2 = l.plugValueWidget( n["p2"] )
		self.assertTrue( isinstance( w2, GafferUI.NumericPlugValueWidget ) )

		Gaffer.Metadata.registerValue( n["p1"], "plugValueWidget:type", "GafferUI.ConnectionPlugValueWidget" )
		self.assertTrue( isinstance( l.plugValueWidget( n["p1"] ), GafferUI.ConnectionPlugValueWidget ) )
		self.assertTrue( w2 is l.plugValueWidget( n["p2"] ) )

		Gaffer.Metadata.deregisterValue( n["p1"], "plugValueWidget:type" )
		self.assertTrue( isinstance( l.plugValueWidget( n["p1"] ), GafferUI.NumericPlugValueWidget ) )
		self.assertTrue( w2 is l.plugValueWidget( n["p2"] ) )

	def testRemovingAndAddingWidget( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.IntPlug()

		l = GafferUI.PlugLayout( n )
		self.assertTrue( isinstance( l.plugValueWidget( n["p"] ), GafferUI.NumericPlugValueWidget ) )

		Gaffer.Metadata.registerValue( n["p"], "plugValueWidget:type", "" )
		self.assertTrue( l.plugValueWidget( n["p"] ) is None )

		Gaffer.Metadata.deregisterValue( n["p"], "plugValueWidget:type" )
		self.assertTrue( isinstance( l.plugValueWidget( n["p"] ), GafferUI.NumericPlugValueWidget ) )

	def testContext( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.IntPlug()

		l = GafferUI.PlugLayout( s["n"] )
		self.assertTrue( l.context().isSame( s.context() ) )
		self.assertTrue( l.plugValueWidget( s["n"]["p"] ).context().isSame( s.context() ) )

	def testContextWithoutScriptNode( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.Plug()

		l = GafferUI.PlugLayout( n )
		self.assertTrue( isinstance( l.context(), Gaffer.Context ) )

		l = GafferUI.PlugLayout( n["p"] )
		self.assertTrue( isinstance( l.context(), Gaffer.Context ) )

	def testContextSensitiveSummariesAndActivators( self ) :

		class SummaryAndActivatorTestNode( Gaffer.Node ) :

			def __init__( self, name = "SummaryAndActivatorTestNode" ) :

				Gaffer.Node.__init__( self, name )

				self["b"] = Gaffer.BoolPlug()
				self["s"] = Gaffer.StringPlug()

		IECore.registerRunTimeTyped( SummaryAndActivatorTestNode )

		Gaffer.Metadata.registerNode(

			SummaryAndActivatorTestNode,

			"layout:activator:bIsOn", lambda node : node["b"].getValue(),
			"layout:section:Settings:summary", lambda node : str( node["b"].getValue() ) + " " + node["s"].getValue(),

			plugs = {

				"s" : [

					"layout:activator", "bIsOn",

				]

			},

		)

		s = Gaffer.ScriptNode()
		p = Gaffer.NameValuePlug( "bVariable", False )
		s["variables"].addChild( p )

		s["n"] = SummaryAndActivatorTestNode()

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["n"]["b"] = context["bVariable"]' )

		l = GafferUI.PlugLayout( s["n"] )
		self.assertEqual( l.plugValueWidget( s["n"]["s"] ).enabled(), False )

		p["value"].setValue( True )
		self.assertEqual( l.plugValueWidget( s["n"]["s"] ).enabled(), True )

	def testMultipleLayouts( self ) :

		n = Gaffer.Node()
		n["p1"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p2"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( n, "layout1:activator:true", True )
		Gaffer.Metadata.registerValue( n, "layout1:activator:false", False )

		Gaffer.Metadata.registerValue( n, "layout2:activator:true", True )
		Gaffer.Metadata.registerValue( n, "layout2:activator:false", False )

		Gaffer.Metadata.registerValue( n["p1"], "layout1:activator", "true" )
		Gaffer.Metadata.registerValue( n["p1"], "layout2:activator", "false" )

		Gaffer.Metadata.registerValue( n["p2"], "layout1:activator", "false" )
		Gaffer.Metadata.registerValue( n["p2"], "layout2:activator", "true" )

		l1 = GafferUI.PlugLayout( n, layoutName = "layout1" )
		l2 = GafferUI.PlugLayout( n, layoutName = "layout2" )

		self.assertTrue( l1.plugValueWidget( n["p1"] ).enabled() )
		self.assertFalse( l1.plugValueWidget( n["p2"] ).enabled() )

		self.assertFalse( l2.plugValueWidget( n["p1"] ).enabled() )
		self.assertTrue( l2.plugValueWidget( n["p2"] ).enabled() )

	def testRootSection( self ) :

		n = Gaffer.Node()
		n["p1"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["p2"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( n["p2"], "layout:section", "sectionA" )

		l = GafferUI.PlugLayout( n, rootSection = "sectionA" )

		self.assertTrue( l.plugValueWidget( n["p1"] ) is None )
		self.assertTrue( l.plugValueWidget( n["p2"] ) is not None )

if __name__ == "__main__":
	unittest.main()
