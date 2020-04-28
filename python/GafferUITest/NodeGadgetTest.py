##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class NodeGadgetTest( GafferUITest.TestCase ) :

	def test( self ) :

		n = GafferTest.AddNode()
		g = GafferUI.NodeGadget.create( n )

		self.assertEqual( n, g.node() )
		self.assertIsNotNone( g.nodule( n["op1"] ) )
		self.assertIsNotNone( g.nodule( n["op2"] ) )
		self.assertIsNotNone( g.nodule( n["sum"] ) )

	def testDynamicPlugs( self ) :

		n = GafferTest.AddNode()
		g = GafferUI.NodeGadget.create( n )

		self.assertEqual( n, g.node() )
		self.assertIsNotNone( g.nodule( n["op1"] ) )
		self.assertIsNotNone( g.nodule( n["op2"] ) )
		self.assertIsNotNone( g.nodule( n["sum"] ) )

		d = Gaffer.FloatPlug()
		n["d"] = d

		self.assertIsNotNone( g.nodule( n["op1"] ) )
		self.assertIsNotNone( g.nodule( n["op2"] ) )
		self.assertIsNotNone( g.nodule( n["sum"] ) )
		self.assertIsNotNone( g.nodule( d ) )

		n.removeChild( d )

		self.assertIsNotNone( g.nodule( n["op1"] ) )
		self.assertIsNotNone( g.nodule( n["op2"] ) )
		self.assertIsNotNone( g.nodule( n["sum"] ) )
		self.assertIsNone( g.nodule( d ) )

	def testFactoryRegistration( self ) :

		class MyNode( Gaffer.Node ) :

			def __init__( self ) :

				Gaffer.Node.__init__( self )

		IECore.registerRunTimeTyped( MyNode )

		def creator( node ) :

			result = GafferUI.StandardNodeGadget( node )
			result.getContents().setText( "lovinglyHandCraftedInCreator" )

			return result

		GafferUI.NodeGadget.registerNodeGadget( MyNode, creator )

		n = MyNode()
		g = GafferUI.NodeGadget.create( n )
		self.assertTrue( g.node() is n )
		self.assertEqual( g.getContents().getText(), "lovinglyHandCraftedInCreator" )

	def testFactoryMetadata( self ) :

		n = Gaffer.Node()
		self.assertTrue( isinstance( GafferUI.NodeGadget.create( n ), GafferUI.StandardNodeGadget ) )

		Gaffer.Metadata.registerValue( n, "nodeGadget:type", "" )
		self.assertEqual( GafferUI.NodeGadget.create( n ), None )

		Gaffer.Metadata.registerValue( n, "nodeGadget:type", "GafferUI::StandardNodeGadget" )
		self.assertTrue( isinstance( GafferUI.NodeGadget.create( n ), GafferUI.StandardNodeGadget ) )

if __name__ == "__main__":
	unittest.main()
