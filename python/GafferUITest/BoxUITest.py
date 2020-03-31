##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class BoxUITest( GafferUITest.TestCase ) :

	class NodulePositionNode( GafferTest.AddNode ) :

		def __init__( self, name = "NodulePositionNode" ) :

			GafferTest.AddNode.__init__( self, name )

	IECore.registerRunTimeTyped( NodulePositionNode )

	Gaffer.Metadata.registerValue( NodulePositionNode, "op1", "noduleLayout:section", "left" )
	Gaffer.Metadata.registerValue( NodulePositionNode, "sum", "noduleLayout:section", "right" )

	Gaffer.Metadata.registerValue( NodulePositionNode, "op2", "nodule:type", "" )

	def testNodulePositions( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["a"] = GafferTest.AddNode()
		s["n"] = self.NodulePositionNode()
		s["r"] = GafferTest.AddNode()

		s["n"]["op1"].setInput( s["a"]["sum"] )
		s["r"]["op1"].setInput( s["n"]["sum"] )

		box = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n"] ] ) )

		boxGadget = g.nodeGadget( box )

		self.assertEqual( boxGadget.connectionTangent( boxGadget.nodule( box["op1"] ) ), imath.V3f( -1, 0, 0 ) )
		self.assertEqual( boxGadget.connectionTangent( boxGadget.nodule( box["sum"] ) ), imath.V3f( 1, 0, 0 ) )

		# Now test that a copy/paste of the box maintains the tangents in the copy.

		s2 = Gaffer.ScriptNode()
		g2 = GafferUI.GraphGadget( s2 )

		s2.execute( s.serialise() )

		box2 = s2[box.getName()]
		boxGadget2 = g2.nodeGadget( box2 )

		self.assertEqual( boxGadget2.connectionTangent( boxGadget2.nodule( box2["op1"] ) ), imath.V3f( -1, 0, 0 ) )
		self.assertEqual( boxGadget2.connectionTangent( boxGadget2.nodule( box2["sum"] ) ), imath.V3f( 1, 0, 0 ) )

	def testNodulePositionsForPromotedPlugs( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["b"] = Gaffer.Box()
		s["b"]["n"] = self.NodulePositionNode()

		boxGadget = g.nodeGadget( s["b"] )

		p1 = Gaffer.PlugAlgo.promote( s["b"]["n"]["op1"] )
		p2 = Gaffer.PlugAlgo.promote( s["b"]["n"]["sum"] )

		self.assertEqual( boxGadget.connectionTangent( boxGadget.nodule( p1 ) ), imath.V3f( -1, 0, 0 ) )
		self.assertEqual( boxGadget.connectionTangent( boxGadget.nodule( p2 ) ), imath.V3f( 1, 0, 0 ) )

	def testDisabledNodulesForPromotedPlugs( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["b"] = Gaffer.Box()
		s["b"]["n"] = self.NodulePositionNode()

		boxGadget = g.nodeGadget( s["b"] )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["op2"] )
		self.assertEqual( boxGadget.nodule( p ), None )

	def testRenamingPlugs( self ) :

		box = Gaffer.Box()
		box["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		ui = GafferUI.NodeUI.create( box )

		w = ui.plugValueWidget( box["user"]["a"] )
		self.assertTrue( w is not None )

		box["user"]["a"].setName( "b" )

		w2 = ui.plugValueWidget( box["user"]["b"] )
		self.assertTrue( w2 is not None )
		self.assertTrue( w2 is w )

	def testUIForNonMatchingPromotedPlugTypes( self ) :

		box = Gaffer.Box()
		box["user"]["b"] = Gaffer.BoolPlug()
		box["node"] = Gaffer.Node()
		box["node"]["i"] = Gaffer.IntPlug()
		box["node"]["i"].setInput( box["user"]["b"] )

		ui = GafferUI.NodeUI.create( box )
		w = ui.plugValueWidget( box["user"]["b"] )

		self.assertTrue( isinstance( w, GafferUI.BoolPlugValueWidget ) )

	def testUIForOutputPlugTypes( self ) :

		box = Gaffer.Box()
		box["node"] = Gaffer.Random()
		p = Gaffer.PlugAlgo.promote( box["node"]["outColor"] )

		nodeUI = GafferUI.NodeUI.create( box["node"] )
		boxUI = GafferUI.NodeUI.create( box )

		nodeWidget = nodeUI.plugValueWidget( box["node"]["outColor"] )
		boxWidget = boxUI.plugValueWidget( p )

		self.assertTrue( type( boxWidget ) is type( nodeWidget ) )

	def testDisabledNodulesAfterCutAndPaste( self ) :

		s = Gaffer.ScriptNode()
		g = GafferUI.GraphGadget( s )

		s["b"] = Gaffer.Box()
		s["b"]["n"] = self.NodulePositionNode()

		g = GafferUI.GraphGadget( s )

		Gaffer.PlugAlgo.promote( s["b"]["n"]["op1"] )
		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["op2"] )
		p.setName( "p" )

		self.assertEqual( g.nodeGadget( s["b"] ).nodule( s["b"]["p"] ), None )

		s.execute( s.serialise( filter = Gaffer.StandardSet( [ s["b"] ] ) ) )

		self.assertEqual( g.nodeGadget( s["b1"] ).nodule( s["b1"]["p"] ), None )

	def testPromotionIgnoresLayoutSection( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()

		s["b"]["n"]["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.Metadata.registerValue( s["b"]["n"]["user"]["p"], "layout:section", "SomeWeirdSection" )

		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["user"]["p"] )
		self.assertNotEqual( Gaffer.Metadata.value( p, "layout:section" ), "SomeWeirdSection" )

if __name__ == "__main__":
	unittest.main()
