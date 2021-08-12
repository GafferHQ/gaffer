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

class AuxiliaryNodeGadgetTest( GafferUITest.TestCase ) :

	def testContents( self ) :

		n = Gaffer.Node()

		g = GafferUI.AuxiliaryNodeGadget( n )

		self.assertFalse( g.getContents() )

	def testNodules( self ) :
		# Test a bunch of things not supported on AuxiliaryGadgets, just to make sure that they return
		# None instead of crashing

		n = Gaffer.Node()
		n["i"] = Gaffer.IntPlug()

		g = GafferUI.AuxiliaryNodeGadget( n )

		self.assertFalse( g.nodule( n["i"] ) )

	def testNoduleTangents( self ) :

		n = GafferTest.AddNode()
		g = GafferUI.AuxiliaryNodeGadget( n )

		self.assertEqual( g.connectionTangent( g.nodule( n["op1"] ) ), imath.V3f( 0, 0, 0 ) )

	def testEdgeGadgets( self ) :

		n = GafferTest.MultiplyNode()
		g = GafferUI.AuxiliaryNodeGadget( n )

		for name, edge in g.Edge.names.items() :
			self.assertTrue( g.getEdgeGadget( edge ) is None )
			eg = GafferUI.TextGadget( name )
			g.setEdgeGadget( edge, eg )
			self.assertTrue( g.getEdgeGadget( edge ) is None )

if __name__ == "__main__":
	unittest.main()
