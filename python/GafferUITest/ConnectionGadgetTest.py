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

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class ConnectionGadgetTest( GafferUITest.TestCase ) :

	def testFactory( self ) :

		class MyPlug( Gaffer.Plug ) :

			def __init__(
				self,
				name = "MyPlug",
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default
			) :

				Gaffer.Plug.__init__( self, name, direction, flags )

		IECore.registerRunTimeTyped( MyPlug )

		myStyle = GafferUI.StandardStyle()
		def creator( srcNodule, dstNodule ) :

			result = GafferUI.StandardConnectionGadget( srcNodule, dstNodule )
			result.setStyle( myStyle )
			result.setToolTip( "myToolTip" )

			return result

		GafferUI.ConnectionGadget.registerConnectionGadget( MyPlug, creator )

		n1 = Gaffer.Node()
		n1["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		n1["myOut"] = MyPlug( direction = Gaffer.Plug.Direction.Out )

		n2 = Gaffer.Node()
		n2["in"] = Gaffer.Plug()
		n2["myIn"] = MyPlug()

		n2["in"].setInput( n1["out"] )
		n2["myIn"].setInput( n1["myOut"] )

		ng1 = GafferUI.NodeGadget.create( n1 )
		ng2 = GafferUI.NodeGadget.create( n2 )

		c = GafferUI.ConnectionGadget.create( ng1.nodule( n1["out"] ), ng2.nodule( n2["in"] ) )
		myC = GafferUI.ConnectionGadget.create( ng1.nodule( n1["myOut"] ), ng2.nodule( n2["myIn"] ) )

		self.assertTrue( isinstance( c, GafferUI.StandardConnectionGadget ) )
		self.assertTrue( c.getStyle() is None )
		self.assertNotEqual( c.getToolTip( IECore.LineSegment3f() ), "myToolTip" )

		self.assertTrue( isinstance( myC, GafferUI.StandardConnectionGadget ) )
		self.assertTrue( myC.getStyle().isSame( myStyle ) )
		self.assertEqual( myC.getToolTip( IECore.LineSegment3f() ), "myToolTip" )

	def testPerPlugFactory( self ) :

		def creator( srcNodule, dstNodule ) :

			result = GafferUI.StandardConnectionGadget( srcNodule, dstNodule )
			result.setToolTip( "myToolTip" )

			return result

		GafferUI.ConnectionGadget.registerConnectionGadget( GafferTest.AddNode, "op2", creator )

		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()

		n2["op1"].setInput( n1["sum"] )
		n2["op2"].setInput( n1["sum"] )

		ng1 = GafferUI.NodeGadget.create( n1 )
		ng2 = GafferUI.NodeGadget.create( n2 )

		c1 = GafferUI.ConnectionGadget.create( ng1.nodule( n1["sum"] ), ng2.nodule( n2["op1"] ) )
		self.assertTrue( isinstance( c1, GafferUI.StandardConnectionGadget ) )
		self.assertNotEqual( c1.getToolTip( IECore.LineSegment3f() ), "myToolTip" )

		c2 = GafferUI.ConnectionGadget.create( ng1.nodule( n1["sum"] ), ng2.nodule( n2["op2"] ) )
		self.assertTrue( isinstance( c2, GafferUI.StandardConnectionGadget ) )
		self.assertEqual( c2.getToolTip( IECore.LineSegment3f() ), "myToolTip" )

if __name__ == "__main__":
	unittest.main()

