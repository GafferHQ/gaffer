##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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
import GafferTest
import GafferUI
import GafferUITest

class GadgetTest( GafferUITest.TestCase ) :

	def testTransform( self ) :

		g = GafferUI.TextGadget( "hello" )
		self.assertEqual( g.getTransform(), IECore.M44f() )

		t = IECore.M44f.createScaled( IECore.V3f( 2 ) )
		g.setTransform( t )
		self.assertEqual( g.getTransform(), t )

		c1 = GafferUI.LinearContainer()
		c1.addChild( g )

		c2 = GafferUI.LinearContainer()
		c2.addChild( c1 )
		t2 = IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) )
		c2.setTransform( t2 )

		self.assertEqual( g.fullTransform(), t * t2 )
		self.assertEqual( g.fullTransform( c1 ), t )

	def testToolTip( self ) :

		g = GafferUI.TextGadget( "hello" )

		self.assertEqual( g.getToolTip( IECore.LineSegment3f() ), "" )
		g.setToolTip( "hi" )
		self.assertEqual( g.getToolTip( IECore.LineSegment3f() ), "hi" )

	def testDerivationInPython( self ) :

		class MyGadget( GafferUI.Gadget ) :

			def __init__( self ) :

				GafferUI.Gadget.__init__( self )

			def bound( self ) :

				return IECore.Box3f( IECore.V3f( -20, 10, 2 ), IECore.V3f( 10, 15, 5 ) )

		mg = MyGadget()

		# we can't call the methods of the gadget directly in python to test the
		# bindings, as that doesn't prove anything (we're no exercising the virtual
		# method override code in the wrapper). instead cause c++ to call through
		# for us by adding our gadget to a parent and making calls to the parent.

		c = GafferUI.IndividualContainer()
		c.addChild( mg )

		self.assertEqual( c.bound().size(), mg.bound().size() )

	def testStyle( self ) :

		g = GafferUI.TextGadget( "test" )
		l = GafferUI.LinearContainer()
		l.addChild( g )

		self.assertEqual( g.getStyle(), None )
		self.assertEqual( l.getStyle(), None )

		self.failUnless( g.style().isSame( GafferUI.Style.getDefaultStyle() ) )
		self.failUnless( l.style().isSame( GafferUI.Style.getDefaultStyle() ) )

		s = GafferUI.StandardStyle()
		l.setStyle( s )

		self.failUnless( l.getStyle().isSame( s ) )
		self.assertEqual( g.getStyle(), None )

		self.failUnless( g.style().isSame( s ) )
		self.failUnless( l.style().isSame( s ) )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed( GafferUI )
		self.assertTypeNamesArePrefixed( GafferUITest )

	def testRenderRequestOnStyleChange( self ) :

		g = GafferUI.Gadget()

		cs = GafferTest.CapturingSlot( g.renderRequestSignal() )
		self.assertEqual( len( cs ), 0 )

		s = GafferUI.StandardStyle()

		g.setStyle( s )
		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( g ) )

		s2 = GafferUI.StandardStyle()
		g.setStyle( s2 )
		self.assertEqual( len( cs ), 2 )
		self.assertTrue( cs[1][0].isSame( g ) )

		s2.setColor( GafferUI.StandardStyle.Color.BackgroundColor, IECore.Color3f( 1 ) )
		self.assertEqual( len( cs ), 3 )
		self.assertTrue( cs[2][0].isSame( g ) )

	def testHighlighting( self ) :

		g = GafferUI.Gadget()
		self.assertEqual( g.getHighlighted(), False )

		g.setHighlighted( True )
		self.assertEqual( g.getHighlighted(), True )

		g.setHighlighted( False )
		self.assertEqual( g.getHighlighted(), False )

		cs = GafferTest.CapturingSlot( g.renderRequestSignal() )

		g.setHighlighted( False )
		self.assertEqual( len( cs ), 0 )

		g.setHighlighted( True )
		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( g ) )

	def testVisibility( self ) :

		g1 = GafferUI.Gadget()
		self.assertEqual( g1.getVisible(), True )
		self.assertEqual( g1.visible(), True )

		g1.setVisible( False )
		self.assertEqual( g1.getVisible(), False )
		self.assertEqual( g1.visible(), False )

		g2 = GafferUI.Gadget()
		g1.addChild( g2 )

		self.assertEqual( g2.getVisible(), True )
		self.assertEqual( g2.visible(), False )

		g1.setVisible( True )
		self.assertEqual( g2.visible(), True )

		g3 = GafferUI.Gadget()
		g2.addChild( g3 )

		self.assertEqual( g3.getVisible(), True )
		self.assertEqual( g3.visible(), True )

		g1.setVisible( False )
		self.assertEqual( g3.getVisible(), True )
		self.assertEqual( g3.visible(), False )
		self.assertEqual( g3.visible( relativeTo = g2 ), True )
		self.assertEqual( g3.visible( relativeTo = g1 ), True )

	def testVisibilitySignals( self ) :

		g = GafferUI.Gadget()
		cs = GafferTest.CapturingSlot( g.renderRequestSignal() )
		self.assertEqual( len( cs ), 0 )

		g.setVisible( True )
		self.assertEqual( len( cs ), 0 )

		g.setVisible( False )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0][0], g )

		g.setVisible( False )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0][0], g )

		g.setVisible( True )
		self.assertEqual( len( cs ), 2 )
		self.assertEqual( cs[1][0], g )

	def testBoundIgnoresHiddenChildren( self ) :

		g = GafferUI.Gadget()
		t = GafferUI.TextGadget( "text" )
		g.addChild( t )

		b = t.bound()
		self.assertEqual( g.bound(), b )

		t.setVisible( False )
		# we still want to know what the bound would be for t,
		# even when it's hidden.
		self.assertEqual( t.bound(), b )
		# but we don't want it taken into account when computing
		# the parent bound.
		self.assertEqual( g.bound(), IECore.Box3f() )

	def testVisibilityChangedSignal( self ) :

		g = GafferUI.Gadget()
		g["a"] = GafferUI.Gadget()
		g["a"]["c"] = GafferUI.Gadget()
		g["b"] = GafferUI.Gadget()

		events = []
		def visibilityChanged( gadget ) :

			events.append( ( gadget, gadget.visible() ) )

		connnections = [
			g.visibilityChangedSignal().connect( visibilityChanged ),
			g["a"].visibilityChangedSignal().connect( visibilityChanged ),
			g["a"]["c"].visibilityChangedSignal().connect( visibilityChanged ),
			g["b"].visibilityChangedSignal().connect( visibilityChanged ),
		]

		g["b"].setVisible( True )
		self.assertEqual( len( events ), 0 )

		g["b"].setVisible( False )
		self.assertEqual( len( events ), 1 )
		self.assertEqual( events[0], ( g["b"], False ) )

		g["b"].setVisible( True )
		self.assertEqual( len( events ), 2 )
		self.assertEqual( events[1], ( g["b"], True ) )

		g["a"].setVisible( True )
		self.assertEqual( len( events ), 2 )

		g["a"].setVisible( False )
		self.assertEqual( len( events ), 4 )
		self.assertEqual( events[-2], ( g["a"]["c"], False ) )
		self.assertEqual( events[-1], ( g["a"], False ) )

		g["a"].setVisible( True )
		self.assertEqual( len( events ), 6 )
		self.assertEqual( events[-2], ( g["a"]["c"], True ) )
		self.assertEqual( events[-1], ( g["a"], True ) )

		g["a"]["c"].setVisible( False )
		self.assertEqual( len( events ), 7 )
		self.assertEqual( events[-1], ( g["a"]["c"], False ) )

		g.setVisible( False )
		self.assertEqual( len( events ), 10 )
		self.assertEqual( events[-3], ( g["a"], False ) )
		self.assertEqual( events[-2], ( g["b"], False ) )
		self.assertEqual( events[-1], ( g, False ) )

		g["a"]["c"].setVisible( True )
		self.assertEqual( len( events ), 10 )

	def testEnabled( self ) :

		g1 = GafferUI.Gadget()
		self.assertEqual( g1.getEnabled(), True )
		self.assertEqual( g1.enabled(), True )

		g1.setEnabled( False )
		self.assertEqual( g1.getEnabled(), False )
		self.assertEqual( g1.enabled(), False )

		g2 = GafferUI.Gadget()
		g1.addChild( g2 )

		self.assertEqual( g2.getEnabled(), True )
		self.assertEqual( g2.enabled(), False )

		g1.setEnabled( True )
		self.assertEqual( g2.enabled(), True )

		g3 = GafferUI.Gadget()
		g2.addChild( g3 )

		self.assertEqual( g3.getEnabled(), True )
		self.assertEqual( g3.enabled(), True )

		g1.setEnabled( False )
		self.assertEqual( g3.getEnabled(), True )
		self.assertEqual( g3.enabled(), False )
		self.assertEqual( g3.enabled( relativeTo = g2 ), True )
		self.assertEqual( g3.enabled( relativeTo = g1 ), True )

if __name__ == "__main__":
	unittest.main()
