##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import imath

import IECore

import Gaffer
import GafferUI
import GafferUITest

class GLWidgetTest( GafferUITest.TestCase ) :

	def testOverlayParenting( self ) :

		w = GafferUI.Window()
		g = GafferUI.GLWidget()
		f = GafferUI.Frame()
		b = GafferUI.Button()

		w.setChild( g )
		g.addOverlay( f )
		f.setChild( b )

		self.assertTrue( b.parent() is f )
		self.assertTrue( f.parent() is g )
		self.assertTrue( g.parent() is w )
		self.assertTrue( b.ancestor( GafferUI.GLWidget ) is g )
		self.assertTrue( b.ancestor( GafferUI.Frame ) is f )
		self.assertTrue( b.ancestor( GafferUI.Window ) is w )

	def testOverlayWidgetAt( self ) :

		w = GafferUI.Window()
		g = GafferUI.GLWidget()
		c = GafferUI.GridContainer()
		b = GafferUI.Button()

		w.setChild( g )
		g.addOverlay( c )
		c.addChild( b, alignment = ( GafferUI.HorizontalAlignment.None_, GafferUI.VerticalAlignment.Top ) )

		w.setVisible( True )

		self.waitForIdle( 10000 )

		self.assertTrue( GafferUI.Widget.widgetAt( w.bound().min() + imath.V2i( 4 ) ) is b )

	def testOverlayBound( self ) :

		w = GafferUI.Window()
		g = GafferUI.GLWidget()
		f = GafferUI.Frame()
		b = GafferUI.Button()

		w.setChild( g )
		g.addOverlay( f )
		f.setChild( b )

		w.setVisible( True )
		self.waitForIdle( 10000 )

		w.setPosition( imath.V2i( 100 ) )
		self.waitForIdle( 10000 )
		b1 = b.bound()

		w.setPosition( imath.V2i( 200 ) )
		self.waitForIdle( 10000 )
		b2 = b.bound()

		self.assertEqual( b2.min(), b1.min() + imath.V2i( 100 ) )
		self.assertEqual( b2.max(), b1.max() + imath.V2i( 100 ) )

	def testOverlayMousePosition( self ) :

		w = GafferUI.Window( borderWidth = 10 )
		g = GafferUI.GLWidget()
		f = GafferUI.Frame()
		b = GafferUI.Button()

		w.setChild( g )
		g.addOverlay( f )
		f.setChild( b )

		w.setVisible( True )

		w.setPosition( imath.V2i( 100 ) )
		self.waitForIdle( 1000 )

		wBound = w.bound()
		bBound = b.bound()

		wP = GafferUI.Widget.mousePosition( relativeTo = w )
		bP = GafferUI.Widget.mousePosition( relativeTo = b )

		self.assertEqual( bBound.min() - wBound.min(), wP - bP )

	def testOverlayAccessors( self ) :

		g = GafferUI.GLWidget()

		b1 = GafferUI.Button()
		b2 = GafferUI.Button()
		self.assertEqual( b1.parent(), None )
		self.assertEqual( b2.parent(), None )

		g.addOverlay( b1 )
		self.assertEqual( b1.parent(), g )
		self.assertEqual( b2.parent(), None )

		g.addOverlay( b2 )
		self.assertEqual( b1.parent(), g )
		self.assertEqual( b2.parent(), g )

		g.removeOverlay( b1 )
		self.assertEqual( b1.parent(), None )
		self.assertEqual( b2.parent(), g )

		g.removeOverlay( b2 )
		self.assertEqual( b1.parent(), None )
		self.assertEqual( b2.parent(), None )

if __name__ == "__main__":
	unittest.main()
