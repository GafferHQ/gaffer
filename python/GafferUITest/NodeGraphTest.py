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

class NodeGraphTest( GafferUITest.TestCase ) :

	def testCreateWithExistingGraph( self ) :

		s = Gaffer.ScriptNode()

		s["add1"] = GafferTest.AddNode()
		s["add2"] = GafferTest.AddNode()

		s["add1"]["op1"].setInput( s["add2"]["sum"] )

		g = GafferUI.NodeGraph( s )

		self.failUnless( g.graphGadget().nodeGadget( s["add1"] ).node() is s["add1"] )
		self.failUnless( g.graphGadget().nodeGadget( s["add2"] ).node() is s["add2"] )

		self.failUnless( g.graphGadget().connectionGadget( s["add1"]["op1"] ).dstNodule().plug().isSame( s["add1"]["op1"] ) )

	def testGraphGadgetAccess( self ) :

		s = Gaffer.ScriptNode()
		ge = GafferUI.NodeGraph( s )

		g = ge.graphGadget()

		self.failUnless( isinstance( g, GafferUI.GraphGadget ) )

	def testLifetime( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		e = GafferUI.NodeGraph( s )

		we = weakref.ref( e )
		del e

		self.assertEqual( we(), None )

	def testTitle( self ) :

		s = Gaffer.ScriptNode()

		g = GafferUI.NodeGraph( s )

		self.assertEqual( g.getTitle(), "Node Graph" )

		g.setTitle( "This is a test!" )

		self.assertEqual( g.getTitle(), "This is a test!" )

if __name__ == "__main__":
	unittest.main()
