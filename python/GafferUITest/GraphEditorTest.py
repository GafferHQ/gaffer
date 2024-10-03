##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import weakref

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class GraphEditorTest( GafferUITest.TestCase ) :

	def testCreateWithExistingGraph( self ) :

		s = Gaffer.ScriptNode()

		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()

		s["add1"]["op1"].setInput( s["add2"]["sum"] )

		g = GafferUI.GraphEditor( s )

		self.assertTrue( g.graphGadget().nodeGadget( s["add1"] ).node() is s["add1"] )
		self.assertTrue( g.graphGadget().nodeGadget( s["add2"] ).node() is s["add2"] )

		self.assertTrue( g.graphGadget().connectionGadget( s["add1"]["op1"] ).dstNodule().plug().isSame( s["add1"]["op1"] ) )

	def testGraphGadgetAccess( self ) :

		s = Gaffer.ScriptNode()
		ge = GafferUI.GraphEditor( s )

		g = ge.graphGadget()

		self.assertIsInstance( g, GafferUI.GraphGadget )

	def testLifetime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		e = GafferUI.GraphEditor( s )

		we = weakref.ref( e )
		del e

		self.assertEqual( we(), None )

	def testTitle( self ) :

		s = Gaffer.ScriptNode()

		g = GafferUI.GraphEditor( s )

		self.assertEqual( g.getTitle(), "Graph Editor" )

		b1 = Gaffer.Box()
		b2 = Gaffer.Box()

		s["a"] = b1
		s["a"]["b"] = b2

		self.__signalUpdatedTitle = g.getTitle()

		def titleChangedHandler( widget ) :
			self.__signalUpdatedTitle = widget.getTitle()
		g.titleChangedSignal().connect( titleChangedHandler )

		g.graphGadget().setRoot( b1 )
		self.assertEqual( self.__signalUpdatedTitle, "Graph Editor : a" )

		g.graphGadget().setRoot( b2 )
		self.assertEqual( self.__signalUpdatedTitle, "Graph Editor : a / b" )

		b1.setName( "c" )
		self.assertEqual( self.__signalUpdatedTitle, "Graph Editor : c / b" )

		b2.setName( "d" )
		self.assertEqual( self.__signalUpdatedTitle, "Graph Editor : c / d" )

		g.setTitle( "This is a test!" )
		self.assertEqual( self.__signalUpdatedTitle, "This is a test!" )

	def testAutomaticLayout( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		s["b"] = Gaffer.Box()
		s["b"]["n1"] = GafferTest.AddNode()
		s["b"]["n2"] = GafferTest.AddNode()
		s["b"]["n2"]["op1"].setInput( s["b"]["n1"]["sum"] )

		with GafferUI.Window() as w :
			graphEditor = GafferUI.GraphEditor( s )

		w.setVisible( True )
		self.waitForIdle( 10000 )

		def assertLower( graphGadget, n1, n2 ) :

			self.assertLess( graphGadget.getNodePosition( n1 ).y, graphGadget.getNodePosition( n2 ).y )

		self.assertEqual( graphEditor.graphGadget().unpositionedNodeGadgets(), [] )
		assertLower( graphEditor.graphGadget(), s["n2"], s["n1"] )

		graphEditor.graphGadget().setRoot( s["b"] )
		self.waitForIdle( 10000 )

		self.assertEqual( graphEditor.graphGadget().unpositionedNodeGadgets(), [] )
		assertLower( graphEditor.graphGadget(), s["b"]["n2"], s["b"]["n1"] )

		s["b"]["n3"] = GafferTest.AddNode()
		s["b"]["n3"]["op1"].setInput( s["b"]["n2"]["sum"] )
		self.waitForIdle( 10000 )

		self.assertEqual( graphEditor.graphGadget().unpositionedNodeGadgets(), [] )
		assertLower( graphEditor.graphGadget(), s["b"]["n3"], s["b"]["n2"] )

	def testRootReparenting( self ) :

		# This test deliberately keeps b alive to mimic
		# the effects of an UndoScope or similar.

		s = Gaffer.ScriptNode()
		e = GafferUI.GraphEditor( s )

		b = Gaffer.Box()
		s["b"] = b

		e.graphGadget().setRoot( b )
		self.assertEqual( e.graphGadget().getRoot(), b )

		s.removeChild( b )
		self.assertEqual( e.graphGadget().getRoot(), s )

		s["b"] = b
		b["bb"] = Gaffer.Box()

		e.graphGadget().setRoot( b["bb"] )
		self.assertEqual( e.graphGadget().getRoot(), b["bb"] )

		s.removeChild( b )
		self.assertEqual( e.graphGadget().getRoot(), s )

		# Test with actually deleted nodes too

		s["b"] = b
		e.graphGadget().setRoot( b["bb"] )
		self.assertEqual( e.graphGadget().getRoot(), b["bb"] )

		del b
		del s["b"]

		self.assertEqual( e.graphGadget().getRoot(), s )

if __name__ == "__main__":
	unittest.main()
