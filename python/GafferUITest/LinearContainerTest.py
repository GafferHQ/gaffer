##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

class LinearContainerTest( GafferUITest.TestCase ) :

	def testConstruction( self ) :

		c = GafferUI.LinearContainer()
		self.assertEqual( c.getName(), "LinearContainer" )
		self.assertEqual( c.getOrientation(), GafferUI.LinearContainer.Orientation.X )
		self.assertEqual( c.getAlignment(), GafferUI.LinearContainer.Alignment.Centre )
		self.assertEqual( c.getSpacing(), 0 )
		self.assertEqual( c.getDirection(), GafferUI.LinearContainer.Direction.Increasing )

		c = GafferUI.LinearContainer( name="a" )
		self.assertEqual( c.getName(), "a" )
		self.assertEqual( c.getOrientation(), GafferUI.LinearContainer.Orientation.X )
		self.assertEqual( c.getAlignment(), GafferUI.LinearContainer.Alignment.Centre )
		self.assertEqual( c.getSpacing(), 0 )
		self.assertEqual( c.getDirection(), GafferUI.LinearContainer.Direction.Increasing )

		c = GafferUI.LinearContainer( spacing=10 )
		self.assertEqual( c.getName(), "LinearContainer" )
		self.assertEqual( c.getOrientation(), GafferUI.LinearContainer.Orientation.X )
		self.assertEqual( c.getAlignment(), GafferUI.LinearContainer.Alignment.Centre )
		self.assertEqual( c.getSpacing(), 10 )
		self.assertEqual( c.getDirection(), GafferUI.LinearContainer.Direction.Increasing )

		c = GafferUI.LinearContainer( orientation=GafferUI.LinearContainer.Orientation.Y )
		self.assertEqual( c.getName(), "LinearContainer" )
		self.assertEqual( c.getOrientation(), GafferUI.LinearContainer.Orientation.Y )
		self.assertEqual( c.getAlignment(), GafferUI.LinearContainer.Alignment.Centre )
		self.assertEqual( c.getSpacing(), 0 )
		self.assertEqual( c.getDirection(), GafferUI.LinearContainer.Direction.Increasing )

		c = GafferUI.LinearContainer( alignment=GafferUI.LinearContainer.Alignment.Min )
		self.assertEqual( c.getName(), "LinearContainer" )
		self.assertEqual( c.getOrientation(), GafferUI.LinearContainer.Orientation.X )
		self.assertEqual( c.getAlignment(), GafferUI.LinearContainer.Alignment.Min )
		self.assertEqual( c.getSpacing(), 0 )
		self.assertEqual( c.getDirection(), GafferUI.LinearContainer.Direction.Increasing )

		c = GafferUI.LinearContainer( direction=GafferUI.LinearContainer.Direction.Decreasing )
		self.assertEqual( c.getName(), "LinearContainer" )
		self.assertEqual( c.getOrientation(), GafferUI.LinearContainer.Orientation.X )
		self.assertEqual( c.getAlignment(), GafferUI.LinearContainer.Alignment.Centre )
		self.assertEqual( c.getSpacing(), 0 )
		self.assertEqual( c.getDirection(), GafferUI.LinearContainer.Direction.Decreasing )

		self.assertTrue( c.bound().isEmpty() )

	def testHorizontalCentred( self ) :

		twoByFour = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )
		fourByFour = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -2, -2, 0 ), imath.V3f( 2, 2, 0 ) ) )
		fourByTwo = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -2, -1, 0 ), imath.V3f( 2, 1, 0 ) ) )

		c = GafferUI.LinearContainer()

		c["c1"] = twoByFour
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )
		self.assertEqual( twoByFour.getTransform(), imath.M44f().translate( imath.V3f( 0 ) ) )

		c["c2"] = fourByFour
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -3, -2, 0 ), imath.V3f( 3, 2, 0 ) ) )
		self.assertEqual( twoByFour.getTransform(), imath.M44f().translate( imath.V3f( -2, 0, 0 ) ) )
		self.assertEqual( fourByFour.getTransform(), imath.M44f().translate( imath.V3f( 1, 0, 0 ) ) )

		c["c3"] = fourByTwo
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -5, -2, 0 ), imath.V3f( 5, 2, 0 ) ) )
		self.assertEqual( twoByFour.getTransform(), imath.M44f().translate( imath.V3f( -4, 0, 0 ) ) )
		self.assertEqual( fourByFour.getTransform(), imath.M44f().translate( imath.V3f( -1, 0, 0 ) ) )
		self.assertEqual( fourByTwo.getTransform(), imath.M44f().translate( imath.V3f( 3, 0, 0 ) ) )

	def testVerticalMin( self ) :

		twoByFour = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )
		fourByFour = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -2, -2, 0 ), imath.V3f( 2, 2, 0 ) ) )
		fourByTwo = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -2, -1, 0 ), imath.V3f( 2, 1, 0 ) ) )

		c = GafferUI.LinearContainer( orientation=GafferUI.LinearContainer.Orientation.Y, alignment=GafferUI.LinearContainer.Alignment.Min)

		c["c1"] = twoByFour
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )
		self.assertEqual( twoByFour.getTransform(), imath.M44f().translate( imath.V3f( 0 ) ) )

		c["c2"] = fourByFour
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -2, -4, 0 ), imath.V3f( 2, 4, 0 ) ) )
		self.assertEqual( twoByFour.getTransform(), imath.M44f().translate( imath.V3f( -1, -2, 0 ) ) )
		self.assertEqual( fourByFour.getTransform(), imath.M44f().translate( imath.V3f( 0, 2, 0 ) ) )

		c["c3"] = fourByTwo
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -2, -5, 0 ), imath.V3f( 2, 5, 0 ) ) )
		self.assertEqual( twoByFour.getTransform(), imath.M44f().translate( imath.V3f( -1, -3, 0 ) ) )
		self.assertEqual( fourByFour.getTransform(), imath.M44f().translate( imath.V3f( 0, 1, 0 ) ) )
		self.assertEqual( fourByTwo.getTransform(), imath.M44f().translate( imath.V3f( 0, 4, 0 ) ) )

	def testPadding( self ) :

		twoByFour = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )

		c = GafferUI.LinearContainer( orientation=GafferUI.LinearContainer.Orientation.Y )
		c.addChild( twoByFour )

		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )
		self.assertEqual( c.getPadding(), imath.Box3f( imath.V3f( 0 ), imath.V3f( 0 ) ) )

		c.setPadding( imath.Box3f( imath.V3f( -1, -2, -3 ), imath.V3f( 1, 2, 3 ) ) )
		self.assertEqual( c.getPadding(), imath.Box3f( imath.V3f( -1, -2, -3 ), imath.V3f( 1, 2, 3 ) ) )
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -2, -4, -3 ), imath.V3f( 2, 4, 3 ) ) )

	def testDirection( self ) :

		first = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )
		second = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )

		c = GafferUI.LinearContainer( orientation=GafferUI.LinearContainer.Orientation.Y )

		c["c1"] = first
		c["c2"] = second

		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -1, -4, 0 ), imath.V3f( 1, 4, 0 ) ) )
		self.assertEqual( first.getTransform(), imath.M44f().translate( imath.V3f( 0, -2, 0 ) ) )
		self.assertEqual( second.getTransform(), imath.M44f().translate( imath.V3f( 0, 2, 0 ) ) )

		c.setDirection( GafferUI.LinearContainer.Direction.Decreasing )

		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -1, -4, 0 ), imath.V3f( 1, 4, 0 ) ) )
		self.assertEqual( first.getTransform(), imath.M44f().translate( imath.V3f( 0, 2, 0 ) ) )
		self.assertEqual( second.getTransform(), imath.M44f().translate( imath.V3f( 0, -2, 0 ) ) )

	def testDirectionAndSpacing( self ) :

		c = GafferUI.LinearContainer( orientation = GafferUI.LinearContainer.Orientation.Y )
		c["g1"] = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -1, -1, 0 ), imath.V3f( 1, 1, 0 ) ) )
		c["g2"] = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( -1, -1, 0 ), imath.V3f( 1, 1, 0 ) ) )

		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -1, -2, 0 ), imath.V3f( 1, 2, 0 ) ) )

		c.setSpacing( 2 )
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -1, -3, 0 ), imath.V3f( 1, 3, 0 ) ) )

		c.setDirection( GafferUI.LinearContainer.Direction.Decreasing )
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -1, -3, 0 ), imath.V3f( 1, 3, 0 ) ) )

	def testChildVisibility( self ) :

		g1 = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( 0 ), imath.V3f( 1, 1, 0 ) ) )
		g2 = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( 0 ), imath.V3f( 2, 1, 0 ) ) )
		g3 = GafferUI.SpacerGadget( imath.Box3f( imath.V3f( 0 ), imath.V3f( 5, 1, 0 ) ) )

		c = GafferUI.LinearContainer( spacing = 1 )
		c.addChild( g1 )

		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )

		c.addChild( g2 )
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -2, -0.5, 0 ), imath.V3f( 2, 0.5, 0 ) ) )

		g2.setVisible( False )
		# should be as if the child didn't exist
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -0.5, -0.5, 0 ), imath.V3f( 0.5, 0.5, 0 ) ) )

		g2.setVisible( True )
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -2, -0.5, 0 ), imath.V3f( 2, 0.5, 0 ) ) )

		c.addChild( g3 )
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -5, -0.5, 0 ), imath.V3f( 5, 0.5, 0 ) ) )

		g1.setVisible( False )
		self.assertEqual( c.bound(), imath.Box3f( imath.V3f( -4, -0.5, 0 ), imath.V3f( 4, 0.5, 0 ) ) )

if __name__ == "__main__":
	unittest.main()
