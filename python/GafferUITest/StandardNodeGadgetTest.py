##########################################################################
#
#  Copyright (c) 2011-2014, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferUI
import GafferUITest

class StandardNodeGadgetTest( GafferUITest.TestCase ) :

	def testContents( self ) :

		n = Gaffer.Node()

		g = GafferUI.StandardNodeGadget( n )

		self.assertIsInstance( g.getContents(), GafferUI.NameGadget )
		self.assertEqual( g.getContents().getText(), n.getName() )

		t = GafferUI.TextGadget( "I'll choose my own label thanks" )
		g.setContents( t )

		self.assertTrue( g.getContents().isSame( t ) )

	def testNestedNodules( self ) :

		class DeeplyNestedNode( Gaffer.Node ) :

			def __init__( self, name = "DeeplyNestedNode" ) :

				Gaffer.Node.__init__( self, name )

				self["c1"] = Gaffer.Plug()
				self["c1"]["i1"] = Gaffer.IntPlug()
				self["c1"]["c2"] = Gaffer.Plug()
				self["c1"]["c2"]["i2"] = Gaffer.IntPlug()
				self["c1"]["c2"]["c3"] = Gaffer.Plug()
				self["c1"]["c2"]["c3"]["i3"] = Gaffer.IntPlug()

		IECore.registerRunTimeTyped( DeeplyNestedNode )

		n = DeeplyNestedNode()

		def noduleType( plug ) :
			if plug.typeId() == Gaffer.Plug.staticTypeId() :
				return "GafferUI::CompoundNodule"
			else :
				return "GafferUI::StandardNodule"

		Gaffer.Metadata.registerValue( DeeplyNestedNode, "...", "nodule:type", noduleType )

		g = GafferUI.StandardNodeGadget( n )

		self.assertTrue( g.nodule( n["c1"] ).plug().isSame( n["c1"] ) )
		self.assertTrue( g.nodule( n["c1"]["i1"] ).plug().isSame( n["c1"]["i1"] ) )
		self.assertTrue( g.nodule( n["c1"]["c2"] ).plug().isSame( n["c1"]["c2"] ) )
		self.assertTrue( g.nodule( n["c1"]["c2"]["i2"] ).plug().isSame( n["c1"]["c2"]["i2"] ) )
		self.assertTrue( g.nodule( n["c1"]["c2"]["c3"] ).plug().isSame( n["c1"]["c2"]["c3"] ) )
		self.assertTrue( g.nodule( n["c1"]["c2"]["c3"]["i3"] ).plug().isSame( n["c1"]["c2"]["c3"]["i3"] ) )

	def testAddAndRemovePlugs( self ) :

		n = Gaffer.Node()
		g = GafferUI.StandardNodeGadget( n )

		p = Gaffer.IntPlug()
		n["p"] = p

		nodule = g.nodule( p )
		self.assertTrue( nodule is not None )

		del n["p"]

		self.assertTrue( g.nodule( p ) is None )
		self.assertTrue( nodule.parent() is None )

	def testNoduleTangents( self ) :

		n = GafferTest.AddNode()
		g = GafferUI.StandardNodeGadget( n )

		self.assertEqual( g.connectionTangent( g.nodule( n["op1"] ) ), imath.V3f( 0, 1, 0 ) )
		self.assertEqual( g.connectionTangent( g.nodule( n["op2"] ) ), imath.V3f( 0, 1, 0 ) )
		self.assertEqual( g.connectionTangent( g.nodule( n["sum"] ) ), imath.V3f( 0, -1, 0 ) )

	def testNodulePositionMetadata( self ) :

		n = GafferTest.MultiplyNode()

		g = GafferUI.StandardNodeGadget( n )
		self.assertEqual( g.connectionTangent( g.nodule( n["op1"] ) ), imath.V3f( 0, 1, 0 ) )

		Gaffer.Metadata.registerValue( n.typeId(), "op1", "noduleLayout:section", "left" )

		g = GafferUI.StandardNodeGadget( n )
		self.assertEqual( g.connectionTangent( g.nodule( n["op1"] ) ), imath.V3f( -1, 0, 0 ) )

	def testNameDoesntAffectHeight( self ) :

		n = GafferTest.MultiplyNode( "a" )
		g = GafferUI.StandardNodeGadget( n )
		h = g.bound().size().y

		n.setName( "hg" )
		self.assertEqual( g.bound().size().y, h )

	def testEdgeGadgets( self ) :

		n = GafferTest.MultiplyNode()
		g = GafferUI.StandardNodeGadget( n )

		for name, edge in g.Edge.names.items() :
			self.assertTrue( g.getEdgeGadget( edge ) is None )
			eg = GafferUI.TextGadget( name )
			g.setEdgeGadget( edge, eg )
			self.assertTrue( g.getEdgeGadget( edge ).isSame( eg ) )
			g.setEdgeGadget( edge, None )
			self.assertTrue( g.getEdgeGadget( edge ) is None )
			self.assertTrue( eg.parent() is None )

	def testEdgeGadgetsAndNoduleAddition( self ) :

		n = Gaffer.Node()
		g = GafferUI.StandardNodeGadget( n )

		e = GafferUI.TextGadget( "test" )
		g.setEdgeGadget( g.Edge.TopEdge, e )
		self.assertTrue( g.getEdgeGadget( g.Edge.TopEdge ).isSame( e ) )

		n["p"] = Gaffer.IntPlug()
		self.assertTrue( g.nodule( n["p"] ) is not None )
		self.assertTrue( g.getEdgeGadget( g.Edge.TopEdge ).isSame( e ) )

	def testEdgeMetadataChange( self ) :

		n = GafferTest.MultiplyNode()

		g = GafferUI.StandardNodeGadget( n )
		self.assertEqual( g.connectionTangent( g.nodule( n["op2"] ) ), imath.V3f( 0, 1, 0 ) )

		Gaffer.Metadata.registerValue( n["op2"], "noduleLayout:section", "left" )
		self.assertEqual( g.connectionTangent( g.nodule( n["op2"] ) ), imath.V3f( -1, 0, 0 ) )

	def testRemoveNoduleAfterCreation( self ) :

		n = Gaffer.Node()
		n["p"] = Gaffer.IntPlug()

		g = GafferUI.StandardNodeGadget( n )
		self.assertEqual( g.connectionTangent( g.nodule( n["p"] ) ), imath.V3f( 0, 1, 0 ) )

		Gaffer.Metadata.registerValue( n["p"], "nodule:type", "" )
		self.assertEqual( g.nodule( n["p"] ), None )

	def testPlugReferences( self ) :

		n = Gaffer.Node()
		p = Gaffer.Plug()
		r = p.refCount()

		g = GafferUI.StandardNodeGadget( n )
		n["p"] = p
		self.assertTrue( g.nodule( p ) is not None )

		del n["p"]
		self.assertTrue( g.nodule( p ) is None )

		# The StandardNodeGadget should retain no references
		# to the plug once it has been removed.
		self.assertEqual( p.refCount(), r )

	def testChangeNoduleType( self ) :

		n = Gaffer.Node()
		n["p1"] = Gaffer.Plug()
		n["p2"] = Gaffer.Plug()

		g = GafferUI.StandardNodeGadget( n )
		n1 = g.nodule( n["p1"] )
		n2 = g.nodule( n["p2"] )

		self.assertTrue( isinstance( n1, GafferUI.StandardNodule ) )
		self.assertTrue( isinstance( n2, GafferUI.StandardNodule ) )

		Gaffer.Metadata.registerValue( n["p1"], "nodule:type", "GafferUI::CompoundNodule" )

		self.assertTrue( isinstance( g.nodule( n["p1"] ), GafferUI.CompoundNodule ) )
		self.assertTrue( g.nodule( n["p2"] ).isSame( n2 ) )
		self.assertTrue( n1.parent() is None )

	def testNoduleSignals( self ) :

		n = Gaffer.Node()
		g = GafferUI.StandardNodeGadget( n )

		added = GafferTest.CapturingSlot( g.noduleAddedSignal() )
		removed = GafferTest.CapturingSlot( g.noduleRemovedSignal() )

		n["p"] = Gaffer.Plug()
		self.assertEqual( len( added ), 1 )
		self.assertTrue( added[0][0].isSame( g ) )
		self.assertTrue( added[0][1].isSame( g.nodule( n["p"] ) ) )
		self.assertEqual( len( removed ), 0 )

		del added[:]

		Gaffer.Metadata.registerValue( n["p"], "nodule:type", "" )
		self.assertEqual( len( added ), 0 )
		self.assertEqual( len( removed ), 1 )
		self.assertTrue( removed[0][0].isSame( g ) )
		self.assertTrue( removed[0][1].plug().isSame( n["p"] ) )

		del removed[:]

		Gaffer.Metadata.registerValue( n["p"], "nodule:type", "GafferUI::StandardNodule" )
		self.assertEqual( len( added ), 1 )
		self.assertTrue( added[0][0].isSame( g ) )
		self.assertTrue( added[0][1].isSame( g.nodule( n["p"] ) ) )
		self.assertEqual( len( removed ), 0 )

		del added[:]

		p = n["p"]
		del n["p"]
		self.assertEqual( len( added ), 0 )
		self.assertEqual( len( removed ), 1 )
		self.assertTrue( removed[0][0].isSame( g ) )
		self.assertTrue( removed[0][1].plug().isSame( p ) )

	def testNoduleOrdering( self ) :

		n = Gaffer.Node()
		n["a"] = Gaffer.IntPlug()
		n["b"] = Gaffer.IntPlug()

		g = GafferUI.StandardNodeGadget( n )

		g.bound()
		self.assertLess(
			g.nodule( n["a"] ).transformedBound().center().x,
			g.nodule( n["b"] ).transformedBound().center().x
		)

		Gaffer.Metadata.registerValue( n["a"], "noduleLayout:index", 1 )
		Gaffer.Metadata.registerValue( n["b"], "noduleLayout:index", 0 )

		g.bound()
		self.assertGreater(
			g.nodule( n["a"] ).transformedBound().center().x,
			g.nodule( n["b"] ).transformedBound().center().x
		)

	def testMinWidth( self ) :

		def assertMinWidth( gadget, minWidth ) :

			# Min width applies to central frame, but there is additional
			# spacing for the left/right nodules, and an additional fudge
			# in `StandardNodeGadget::bound()`. The `+ 1.0` accounts for this.
			self.assertEqual( gadget.bound().size().x, minWidth + 1.0 )

		n = Gaffer.Node( "I" )
		g = GafferUI.StandardNodeGadget( n )
		assertMinWidth( g, 10.0 ) # Default min is 10

		Gaffer.Metadata.registerValue( n, "nodeGadget:minWidth", 20.0 )
		assertMinWidth( g, 20.0 )

		Gaffer.Metadata.deregisterValue( n, "nodeGadget:minWidth" )
		assertMinWidth( g, 10.0 )

if __name__ == "__main__":
	unittest.main()
