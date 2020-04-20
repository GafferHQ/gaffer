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

import os
import unittest
import imath

import IECore

import GafferUI
import GafferUITest

class ButtonTest( GafferUITest.TestCase ) :

	def testConstructor( self ) :

		b = GafferUI.Button( "" )
		self.assertEqual( b.getText(), "" )
		self.assertEqual( b.getImage(), None )

		b = GafferUI.Button( "OK" )
		self.assertEqual( b.getText(), "OK" )
		self.assertEqual( b.getImage(), None )

		b = GafferUI.Button( "", "arrowRight10.png" )
		self.assertEqual( b.getText(), "" )
		self.assertIsInstance( b.getImage(), GafferUI.Image )

	def testAccessors( self ) :

		b = GafferUI.Button()

		b.setText( "a" )
		self.assertEqual( b.getText(), "a" )

		i = GafferUI.Image( "arrowRight10.png" )
		b.setImage( i )
		self.assertTrue( b.getImage() is i )

		b.setImage( "arrowRight10.png" )
		self.assertIsInstance( b.getImage(), GafferUI.Image )

		b.setImage( None )
		self.assertEqual( b.getImage(), None )

		self.assertEqual( b.getHasFrame(), True )

		b.setHasFrame( False )
		self.assertEqual( b.getHasFrame(), False )

	def testAccessorTypeChecking( self ) :

		b = GafferUI.Button()

		self.assertRaises( Exception, b.setText, 1 )
		self.assertRaises( Exception, b.setImage, 1 )

	def testImageSize( self ) :

		with GafferUI.Window( "Test" ) as w :
			b = GafferUI.Button( image = "arrowRight10.png", hasFrame=False )

		w.setVisible( True )
		self.waitForIdle()

		self.assertEqual( b.bound().size(), imath.V2i( 10 ) )

		b.setHasFrame( True )
		self.waitForIdle( 1000 )

		self.assertGreater( b.bound().size().x, 10 )
		self.assertGreater( b.bound().size().y, 10 )

	def testToolTip( self ) :

		b = GafferUI.Button( image = "arrowRight10.png", toolTip = "Test" )
		self.assertEqual( b.getToolTip(), "Test" )

	def testUnknownConstructorArguments( self ) :

		self.assertRaises( TypeError, GafferUI.Button, notAnArgument = 1 )

if __name__ == "__main__":
	unittest.main()
