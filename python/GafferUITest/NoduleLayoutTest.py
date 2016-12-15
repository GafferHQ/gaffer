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

if __name__ == "__main__":
	unittest.main()
