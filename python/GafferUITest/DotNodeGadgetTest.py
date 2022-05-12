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

import unittest
import imath

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class DotNodeGadgetTest( GafferUITest.TestCase ) :

	def testDefaultNoduleTangents( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["d"] = Gaffer.Dot()

		g = GafferUI.NodeGadget.create( s["d"] )
		self.assertTrue( isinstance( g, GafferUI.DotNodeGadget ) )

		s["d"].setup( s["n"]["op1"] )

		self.assertTrue( g.nodule( s["d"]["in"] ) is not None )
		self.assertTrue( g.nodule( s["d"]["out"] ) is not None )

		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["in"] ) ), imath.V3f( 0, 1, 0 ) )
		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["out"] ) ), imath.V3f( 0, -1, 0 ) )

	def testCustomNoduleTangentsFromInput( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( s["n"]["sum"], "noduleLayout:section", "right" )

		s["d"] = Gaffer.Dot()

		g = GafferUI.NodeGadget.create( s["d"] )

		s["d"].setup( s["n"]["sum"] )

		self.assertTrue( g.nodule( s["d"]["in"] ) is not None )
		self.assertTrue( g.nodule( s["d"]["out"] ) is not None )

		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["in"] ) ), imath.V3f( -1, 0, 0 ) )
		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["out"] ) ), imath.V3f( 1, 0, 0 ) )

	def testCustomNoduleTangentsFromOutput( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( s["n"]["op1"], "noduleLayout:section", "left" )

		s["d"] = Gaffer.Dot()

		g = GafferUI.NodeGadget.create( s["d"] )

		s["d"].setup( s["n"]["op1"] )

		self.assertTrue( g.nodule( s["d"]["in"] ) is not None )
		self.assertTrue( g.nodule( s["d"]["out"] ) is not None )

		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["in"] ) ), imath.V3f( -1, 0, 0 ) )
		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["out"] ) ), imath.V3f( 1, 0, 0 ) )

	def testCustomNoduleTangentsPreferInputIfAvailable( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		Gaffer.Metadata.registerValue( s["n1"]["sum"], "noduleLayout:section", "right" )

		s["d"] = Gaffer.Dot()

		g = GafferUI.NodeGadget.create( s["d"] )

		# Even though we set up using the input plug "op1", we want the Dot to take
		# it's tangents from the output plug "sum", because the Dot is best thought of
		# as a way of conveniently making that output available at other places in the graph.
		s["d"].setup( s["n2"]["op1"] )

		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["in"] ) ), imath.V3f( -1, 0, 0 ) )
		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["out"] ) ), imath.V3f( 1, 0, 0 ) )

	def testCutAndPasteKeepsTangents( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		Gaffer.Metadata.registerValue( s["n"]["sum"], "noduleLayout:section", "right" )

		graphGadget = GafferUI.GraphGadget( s )

		s["d"] = Gaffer.Dot()
		s["d"].setup( s["n"]["sum"] )
		s["d"]["in"].setInput( s["n"]["sum"] )

		dotNodeGadget = graphGadget.nodeGadget( s["d"] )

		self.assertEqual( dotNodeGadget.connectionTangent( dotNodeGadget.nodule( s["d"]["in"] ) ), imath.V3f( -1, 0, 0 ) )

		s.execute( s.serialise( filter = Gaffer.StandardSet( [ s["n"], s["d"] ] ) ) )

		dot1NodeGadget = graphGadget.nodeGadget( s["d1"] )
		self.assertEqual( dot1NodeGadget.connectionTangent( dot1NodeGadget.nodule( s["d1"]["in"] ) ), imath.V3f( -1, 0, 0 ) )

	def testOutputPassthroughTangents( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		# Match the behavior of a BoxIn node which sets the internal `__in` nodule section to the right.
		Gaffer.Metadata.registerValue( s["n"]["op1"], "noduleLayout:section", "right" )

		Gaffer.Metadata.registerValue( s["n2"]["sum"], "noduleLayout:section", "right" )

		s["n2"]["sum"].setInput( s["n"]["op1"] )

		s["d"] = Gaffer.Dot()

		g = GafferUI.NodeGadget.create( s["d"] )

		s["d"].setup( s["n2"]["sum"] )

		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["in"] ) ), imath.V3f( -1, 0, 0 ) )
		self.assertEqual( g.connectionTangent( g.nodule( s["d"]["out"] ) ), imath.V3f( 1, 0, 0 ) )


if __name__ == "__main__":
	unittest.main()
