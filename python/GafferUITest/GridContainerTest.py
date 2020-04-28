##########################################################################
#
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
import imath

import IECore

import Gaffer
import GafferUI
import GafferUITest

from Qt import QtGui

class GridContainerTest( GafferUITest.TestCase ) :

	def testSimpleSetItem( self ) :

		c = GafferUI.GridContainer()

		b1 = GafferUI.Button( "b1" )
		b2 = GafferUI.Button( "b2" )
		b3 = GafferUI.Button( "b3" )
		b4 = GafferUI.Button( "b4" )

		self.assertEqual( b1.parent(), None )
		self.assertEqual( b2.parent(), None )
		self.assertEqual( b3.parent(), None )
		self.assertEqual( b4.parent(), None )

		self.assertEqual( c.gridSize(), imath.V2i( 0, 0 ) )

		c[0,0] = b1

		self.assertEqual( c.gridSize(), imath.V2i( 1, 1 ) )

		self.assertTrue( b1.parent() is c )
		self.assertTrue( c[0,0] is b1 )

		c[1,0] = b2

		self.assertEqual( c.gridSize(), imath.V2i( 2, 1 ) )

		self.assertTrue( b1.parent() is c )
		self.assertTrue( b2.parent() is c )
		self.assertTrue( c[0,0] is b1 )
		self.assertTrue( c[1,0] is b2 )

		c[0,1] = b3

		self.assertEqual( c.gridSize(), imath.V2i( 2, 2 ) )

		self.assertTrue( b1.parent() is c )
		self.assertTrue( b2.parent() is c )
		self.assertTrue( b3.parent() is c )
		self.assertTrue( c[0,0] is b1 )
		self.assertTrue( c[1,0] is b2 )
		self.assertTrue( c[0,1] is b3 )

		c[1,1] = b4

		self.assertEqual( c.gridSize(), imath.V2i( 2, 2 ) )

		self.assertTrue( b1.parent() is c )
		self.assertTrue( b2.parent() is c )
		self.assertTrue( b3.parent() is c )
		self.assertTrue( b4.parent() is c )
		self.assertTrue( c[0,0] is b1 )
		self.assertTrue( c[1,0] is b2 )
		self.assertTrue( c[0,1] is b3 )
		self.assertTrue( c[1,1] is b4 )

	def testTransferChild( self ) :

		c1 = GafferUI.GridContainer()
		c2 = GafferUI.GridContainer()

		b1 = GafferUI.Button( "b1" )

		c1[0,0] = b1

		self.assertTrue( b1.parent() is c1 )
		self.assertTrue( c1[0,0] is b1 )

		c2[0,0] = b1

		self.assertTrue( b1.parent() is c2 )
		self.assertIsNone( c1[0,0] )
		self.assertTrue( c2[0,0] is b1 )

	def testReplaceItem( self ) :

		c = GafferUI.GridContainer()

		b1 = GafferUI.Button()
		b2 = GafferUI.Button()

		self.assertIsNone( b1.parent() )
		self.assertIsNone( b2.parent() )

		c[0,0] = b1

		self.assertTrue( b1.parent() is c )
		self.assertIsNone( b2.parent() )

		c[0,0] = b2

		self.assertIsNone( b1.parent() )
		self.assertTrue( b2.parent() is c )

	def testRemoveChild( self ) :

		c1 = GafferUI.GridContainer()
		b1 = GafferUI.Button( "b1" )

		c1[0,0] = b1

		self.assertTrue( b1.parent() is c1 )
		self.assertTrue( c1[0,0] is b1 )

		c1.removeChild( b1 )

		self.assertIsNone( b1.parent() )
		self.assertIsNone( c1[0,0] )

	def testDelItem( self ) :

		c1 = GafferUI.GridContainer()
		b1 = GafferUI.Button( "b1" )

		c1[0,0] = b1

		self.assertTrue( b1.parent() is c1 )
		self.assertTrue( c1[0,0] is b1 )

		del c1[0,0]

		self.assertIsNone( b1.parent() )
		self.assertIsNone( c1[0,0] )

	def testGridSize( self ) :

		c1 = GafferUI.GridContainer()
		b1 = GafferUI.Button( "b1" )
		b2 = GafferUI.Button( "b2" )

		self.assertEqual( c1.gridSize(), imath.V2i( 0, 0 ) )

		c1[0,0] = b1

		self.assertEqual( c1.gridSize(), imath.V2i( 1, 1 ) )

		c1[1,0] = b2

		self.assertEqual( c1.gridSize(), imath.V2i( 2, 1 ) )

		del c1[1,0]

		self.assertEqual( c1.gridSize(), imath.V2i( 1, 1 ) )

		del c1[0,0]

		self.assertEqual( c1.gridSize(), imath.V2i( 0, 0 ) )

		c1[1,0] = b2

		self.assertEqual( c1.gridSize(), imath.V2i( 2, 1 ) )

		del c1[1,0]

		self.assertEqual( c1.gridSize(), imath.V2i( 0, 0 ) )

	def testRemoveRow( self ) :

		b00 = GafferUI.Button( "00" )
		b01 = GafferUI.Button( "01" )
		b11 = GafferUI.Button( "11" )
		b10 = GafferUI.Button( "10" )

		g = GafferUI.GridContainer()

		g[0,0] = b00
		g[0,1] = b01
		g[1,1] = b11
		g[1,0] = b10

		self.assertEqual( g.gridSize(), imath.V2i( 2, 2 ) )

		g.removeRow( 0 )

		self.assertEqual( g.gridSize(), imath.V2i( 2, 1 ) )

		self.assertTrue( g[0,0] is b01 )
		self.assertTrue( g[1,0] is b11 )

	def testRemoveColumn( self ) :

		b00 = GafferUI.Button( "00" )
		b01 = GafferUI.Button( "01" )
		b11 = GafferUI.Button( "11" )
		b10 = GafferUI.Button( "10" )

		g = GafferUI.GridContainer()

		g[0,0] = b00
		g[0,1] = b01
		g[1,1] = b11
		g[1,0] = b10

		self.assertEqual( g.gridSize(), imath.V2i( 2, 2 ) )

		g.removeColumn( 0 )

		self.assertEqual( g.gridSize(), imath.V2i( 1, 2 ) )

		self.assertTrue( g[0,0] is b10 )
		self.assertTrue( g[0,1] is b11 )

	def testDeleteMultipleCells( self ) :

		b00 = GafferUI.Button( "00" )
		b01 = GafferUI.Button( "01" )
		b11 = GafferUI.Button( "11" )
		b10 = GafferUI.Button( "10" )

		g = GafferUI.GridContainer()

		g[0,0] = b00
		g[0,1] = b01
		g[1,1] = b11
		g[1,0] = b10

		self.assertEqual( g.gridSize(), imath.V2i( 2, 2 ) )

		del g[0:2,0]

		self.assertEqual( g.gridSize(), imath.V2i( 2, 2 ) )

		self.assertIsNone( g[0,0] )
		self.assertIsNone( g[1,0] )
		self.assertTrue( g[0,1] is b01 )
		self.assertTrue( g[1,1] is b11 )
		self.assertIsNone( b00.parent() )
		self.assertIsNone( b10.parent() )

	def testMultiCellChild( self ) :

		g = GafferUI.GridContainer()

		b1 = GafferUI.Button()

		g[0:2,0:2] = b1

		self.assertTrue( b1.parent() is g )

		self.assertEqual( g.gridSize(), imath.V2i( 2, 2 ) )

		self.assertTrue( g[0,0] is b1 )
		self.assertTrue( g[0,1] is b1 )
		self.assertTrue( g[1,0] is b1 )
		self.assertTrue( g[1,1] is b1 )

		del g[0,0]

		self.assertIsNone( b1.parent() )
		self.assertEqual( g.gridSize(), imath.V2i( 0, 0 ) )

	def testSetChildOnTopOfMultiCellChild( self ) :

		g = GafferUI.GridContainer()

		b1 = GafferUI.Button()
		b2 = GafferUI.Button()

		g[0:2,0:2] = b1

		self.assertTrue( b1.parent() is g )

		self.assertEqual( g.gridSize(), imath.V2i( 2, 2 ) )

		g[0,0] = b2

		self.assertIsNone( b1.parent() )
		self.assertTrue( b2.parent() is g )
		self.assertEqual( g.gridSize(), imath.V2i( 1, 1 ) )

	def testRemoveRowContainingMultiCellChild( self ) :

		g = GafferUI.GridContainer()

		b1 = GafferUI.Button()

		g[0:2,0:2] = b1

		self.assertEqual( g.gridSize(), imath.V2i( 2, 2 ) )

		g.removeRow( 0 )

		self.assertIsNone( b1.parent() )
		self.assertEqual( g.gridSize(), imath.V2i( 0, 0 ) )

	def testRemoveColumnContainingMultiCellChild( self ) :

		g = GafferUI.GridContainer()

		b1 = GafferUI.Button()

		g[0:2,0:2] = b1

		self.assertEqual( g.gridSize(), imath.V2i( 2, 2 ) )

		g.removeColumn( 0 )

		self.assertIsNone( b1.parent() )
		self.assertEqual( g.gridSize(), imath.V2i( 0, 0 ) )

	def testAutomaticParenting( self ) :

		with GafferUI.GridContainer() as g :

			b = GafferUI.Button( "hi", parenting = { "index" : ( 1, 2 ) } )
			t = GafferUI.TextWidget( "hi", parenting = { "index" : ( 0, 0 ) } )

		self.assertTrue( b.parent() is g )
		self.assertTrue( t.parent() is g )

		self.assertTrue( g[1,2] is b )
		self.assertTrue( g[0,0] is t )

if __name__ == "__main__":
	unittest.main()
