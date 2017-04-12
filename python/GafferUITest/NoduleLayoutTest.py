##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class NoduleLayoutTest( GafferUITest.TestCase ) :

	def testChangingSection( self ) :

		n = GafferTest.AddNode()

		top = GafferUI.NoduleLayout( n, "top" )
		left = GafferUI.NoduleLayout( n, "left" )

		self.assertTrue( top.nodule( n["op1"] ) is not None )
		self.assertTrue( left.nodule( n["op1"] ) is None )

		Gaffer.Metadata.registerValue( n["op1"], "noduleLayout:section", "left" )

		self.assertTrue( top.nodule( n["op1"] ) is None )
		self.assertTrue( left.nodule( n["op1"] ) is not None )

	def testDefaultDirection( self ) :

		n = GafferTest.AddNode()

		top = GafferUI.NoduleLayout( n, "top" )
		self.assertGreater( top.bound().size().x, top.bound().size().y )

		self.assertGreater(
			top.nodule( n["op2"] ).transformedBound( None ).center().x,
			top.nodule( n["op1"] ).transformedBound( None ).center().x
		)

		Gaffer.Metadata.registerValue( n["op1"], "noduleLayout:section", "left" )
		Gaffer.Metadata.registerValue( n["op2"], "noduleLayout:section", "left" )

		left = GafferUI.NoduleLayout( n, "left" )
		self.assertGreater( left.bound().size().y, left.bound().size().x )

		self.assertGreater(
			left.nodule( n["op1"] ).transformedBound( None ).center().y,
			left.nodule( n["op2"] ).transformedBound( None ).center().y
		)

	def testExplicitDirection( self ) :

		n = GafferTest.AddNode()

		top = GafferUI.NoduleLayout( n, "top" )
		self.assertGreater( top.bound().size().x, top.bound().size().y )

		self.assertGreater(
			top.nodule( n["op2"] ).transformedBound( None ).center().x,
			top.nodule( n["op1"] ).transformedBound( None ).center().x
		)

		Gaffer.Metadata.registerValue( n, "noduleLayout:section:top:direction", "decreasing" )

		self.assertGreater( top.bound().size().x, top.bound().size().y )

		self.assertLess(
			top.nodule( n["op2"] ).transformedBound( None ).center().x,
			top.nodule( n["op1"] ).transformedBound( None ).center().x
		)

	def testVisible( self ) :

		n = GafferTest.AddNode()

		top = GafferUI.NoduleLayout( n, "top" )
		self.assertTrue( top.nodule( n["op1"] ) is not None )
		self.assertTrue( top.nodule( n["op2"] ) is not None )

		Gaffer.Metadata.registerValue( n["op1"], "noduleLayout:visible", False )
		self.assertTrue( top.nodule( n["op1"] ) is None )
		self.assertTrue( top.nodule( n["op2"] ) is not None )

		Gaffer.Metadata.registerValue( n["op1"], "noduleLayout:visible", True )
		self.assertTrue( top.nodule( n["op1"] ) is not None )
		self.assertTrue( top.nodule( n["op2"] ) is not None )

	def testCustomGadget( self ) :

		# Define a custom gadget

		class CustomGadget( GafferUI.Gadget ) :

			def __init__( self, node ) :

				GafferUI.Gadget.__init__( self )

				self.addChild( GafferUI.ImageGadget( "minus.png" ) )

				self.node = node

		GafferUI.NoduleLayout.registerCustomGadget( "CustomGadget", CustomGadget )

		# Create a node and make a top and bottom
		# nodule layout for it.

		n = GafferTest.AddNode()
		topLayout = GafferUI.NoduleLayout( n, "top" )
		bottomLayout = GafferUI.NoduleLayout( n, "bottom" )
		topLayoutBound = topLayout.bound()
		bottomLayoutBound = bottomLayout.bound()

		# These shouldn't contain any custom gadgets.

		self.assertEqual( topLayout.customGadget( "test" ), None )
		self.assertEqual( bottomLayout.customGadget( "test" ), None )

		# Register our custom gadget into the top layout

		Gaffer.Metadata.registerValue( n, "noduleLayout:customGadget:test:gadgetType", "CustomGadget" )
		Gaffer.Metadata.registerValue( n, "noduleLayout:customGadget:test:section", "top" )

		# Check that it appears

		gadget = topLayout.customGadget( "test" )
		self.assertTrue( isinstance( gadget, CustomGadget ) )
		self.assertTrue( gadget.node.isSame( n ) )
		self.assertGreater( topLayout.bound().size().x, topLayoutBound.size().x )

		# And is to the right of the nodules

		nodule = topLayout.nodule( n["op2"] )
		self.assertGreater( gadget.transformedBound().center().x, nodule.transformedBound().center().x )

		# Check that nothing has appeared in the bottom layout

		self.assertEqual( bottomLayout.customGadget( "test" ), None )
		self.assertEqual( bottomLayout.bound(), bottomLayout.bound() )

		# Change the index for our gadget, and check that
		# the same one is reused, but now appears to the left
		# of the nodules.

		topLayoutBound = topLayout.bound()
		Gaffer.Metadata.registerValue( n, "noduleLayout:customGadget:test:index", 0 )

		self.assertTrue( topLayout.customGadget( "test" ).isSame( gadget ) )
		self.assertEqual( topLayout.bound(), topLayoutBound )
		self.assertLess( gadget.transformedBound().center().x, nodule.transformedBound().center().x )

if __name__ == "__main__":
	unittest.main()
