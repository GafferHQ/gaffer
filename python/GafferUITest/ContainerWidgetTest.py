##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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
import GafferUI
import GafferUITest

class ContainerWidgetTest( GafferUITest.TestCase ) :

	def testWithContext( self ) :

		with GafferUI.Window() as window :

			with GafferUI.ListContainer( GafferUI.ListContainer.Orientation.Vertical ) as column :

				with GafferUI.Frame() as frame :

					button1 = GafferUI.Button()

				with GafferUI.Collapsible() as collapsible :

					button2 = GafferUI.Button()

				with GafferUI.TabbedContainer() as tabbed :

					button3 = GafferUI.Button()
					button4 = GafferUI.Button()

				with GafferUI.ScrolledContainer() as scrolled :

					button5 = GafferUI.Button()

				with GafferUI.SplitContainer() as split :

					button6 = GafferUI.Button()
					button7 = GafferUI.Button()

		self.assertIsInstance( window, GafferUI.Window )
		self.assertIsInstance( column, GafferUI.ListContainer )
		self.assertIsInstance( frame, GafferUI.Frame )
		self.assertIsInstance( collapsible, GafferUI.Collapsible )
		self.assertIsInstance( tabbed, GafferUI.TabbedContainer )
		self.assertIsInstance( scrolled, GafferUI.ScrolledContainer )
		self.assertIsInstance( split, GafferUI.SplitContainer )

		self.assertTrue( column.parent() is window )
		self.assertTrue( frame.parent() is column )
		self.assertTrue( button1.parent() is frame )
		self.assertTrue( collapsible.parent() is column )
		self.assertTrue( button2.parent() is collapsible )
		self.assertTrue( tabbed.parent() is column )
		self.assertTrue( button3.parent() is tabbed )
		self.assertTrue( button4.parent() is tabbed )
		self.assertTrue( button5.parent() is scrolled )
		self.assertTrue( button6.parent() is split )
		self.assertTrue( button7.parent() is split )

	def testWithContextDoesntBlockExceptions( self ) :

		def raiser() :
			with GafferUI.Window() :
				raise RuntimeError( "EEK" )

		self.assertRaises( RuntimeError, raiser )

	def testWithContextRaisesOnTooManyChildren( self ) :

		def raiser() :

			with GafferUI.Window() :
				GafferUI.Button()
				GafferUI.Button()

		self.assertRaises( Exception, raiser )

	def testWithContextAndButtonWithImage( self ) :

		with GafferUI.ListContainer() as l :
			GafferUI.Button( image="arrowDown10.png" )

		self.assertEqual( len( l ), 1 )

	def testWithContextInsideWidgetConstructor( self ) :

		class TestWindow( GafferUI.Window ) :

			def __init__( self ) :

				GafferUI.Window.__init__( self )

				with GafferUI.ListContainer() as l :
					GafferUI.TextWidget( "hello" )
					GafferUI.Button( image="arrowDown10.png" )

				self.setChild( l )

		w = TestWindow()

		self.assertIsInstance( w.getChild(), GafferUI.ListContainer )
		self.assertEqual( len( w.getChild() ), 2 )
		self.assertIsInstance( w.getChild()[0], GafferUI.TextWidget )
		self.assertIsInstance( w.getChild()[1], GafferUI.Button )

if __name__ == "__main__":
	unittest.main()
