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
import weakref

import GafferUI
import GafferUITest

class SplitContainerTest( GafferUITest.TestCase ) :

	def testConstructor( self ) :

		c = GafferUI.SplitContainer()
		self.assertEqual( c.getOrientation(), GafferUI.SplitContainer.Orientation.Vertical )

		c = GafferUI.SplitContainer( orientation = GafferUI.SplitContainer.Orientation.Horizontal )
		self.assertEqual( c.getOrientation(), GafferUI.SplitContainer.Orientation.Horizontal )

	def testOrientation( self ) :

		c = GafferUI.SplitContainer()
		self.assertEqual( c.getOrientation(), GafferUI.SplitContainer.Orientation.Vertical )

		c.setOrientation( GafferUI.SplitContainer.Orientation.Horizontal )
		self.assertEqual( c.getOrientation(), GafferUI.SplitContainer.Orientation.Horizontal )

	def testChildTransfer( self ) :

		p1 = GafferUI.SplitContainer()
		p2 = GafferUI.SplitContainer()

		self.assertEqual( len( p1 ), 0 )
		self.assertEqual( len( p2 ), 0 )

		b = GafferUI.Button()
		p1.append( b )
		self.assertTrue( p1[0] is b )
		self.assertEqual( len( p1 ), 1 )
		self.assertEqual( len( p2 ), 0 )
		self.assertTrue( b.parent() is p1 )

		p2.append( b )
		self.assertTrue( p2[0] is b )
		self.assertEqual( len( p1 ), 0 )
		self.assertEqual( len( p2 ), 1 )
		self.assertTrue( b.parent() is p2 )

	def testHandle( self ) :

		c = GafferUI.SplitContainer()

		c.append( GafferUI.Frame() )
		c.append( GafferUI.Frame() )

		self.assertRaises( IndexError, c.handle, -1 )
		self.assertRaises( IndexError, c.handle, 1 )

		self.assertIsInstance( c.handle( 0 ), GafferUI.Widget )
		self.assertEqual( c.handle( 0 ).parent(), c )

	def testGetHandleTwice( self ) :

		c = GafferUI.SplitContainer()

		c.append( GafferUI.Frame() )
		c.append( GafferUI.Frame() )

		self.assertTrue( c.handle( 0 ) is c.handle( 0 ) )

	def testCanDieAfterGetHandle( self ) :

		c = GafferUI.SplitContainer()

		c.append( GafferUI.Frame() )
		c.append( GafferUI.Frame() )

		w = weakref.ref( c )

		h = c.handle( 0 )

		del c

		self.assertEqual( w(), None )

	def testAccessHandleAfterContainerDeleted( self ) :

		c = GafferUI.SplitContainer()

		c.append( GafferUI.Frame() )
		c.append( GafferUI.Frame() )

		h = c.handle( 0 )

		del c

		# the internal handle has been deleted. there's not much we can do
		# except make sure that we get exceptions rather than crashes.
		self.assertRaises( RuntimeError, h.size )

	def testGetSizes( self ) :

		w = GafferUI.Window()
		c = GafferUI.SplitContainer()
		w.setChild( c )

		c.append( GafferUI.Frame() )
		c.append( GafferUI.Frame() )

		# SplitContainer must be visible on screen before we can
		# rely on size information.
		w.setVisible( True )

		sizes = c.getSizes()
		self.assertEqual( sum( sizes ) + c.handle( 0 ).size().y, c.size().y )

	def testSetSizes( self ) :

		c = GafferUI.SplitContainer()

		c.append( GafferUI.Frame() )
		c.append( GafferUI.Frame() )

		c.setVisible( True )
		originalSize = c.size()

		c.setSizes( [ 0.25, 0.75 ] )

		self.assertEqual( c.size(), originalSize )
		self.assertEqual( sum( c.getSizes() ) + c.handle( 0 ).size().y, originalSize.y )

		s = c.getSizes()
		self.assertAlmostEqual( float( s[0] ) / s[1], 1/3.0, 1 )

if __name__ == "__main__":
	unittest.main()
