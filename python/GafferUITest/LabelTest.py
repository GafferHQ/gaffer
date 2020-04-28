##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
#  Copyright (c) 2012, John Haddon. All rights reserved.
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

class LabelTest( GafferUITest.TestCase ) :

	def testAlignment( self ) :

		l = GafferUI.Label()
		self.assertEqual( l.getAlignment(), ( GafferUI.Label.HorizontalAlignment.Left, GafferUI.Label.VerticalAlignment.Center ) )

		l = GafferUI.Label( horizontalAlignment = GafferUI.Label.HorizontalAlignment.Right, verticalAlignment = GafferUI.Label.VerticalAlignment.Top )
		self.assertEqual( l.getAlignment(), ( GafferUI.Label.HorizontalAlignment.Right, GafferUI.Label.VerticalAlignment.Top ) )

		l.setAlignment( GafferUI.Label.HorizontalAlignment.Center, GafferUI.Label.VerticalAlignment.Center )
		self.assertEqual( l.getAlignment(), ( GafferUI.Label.HorizontalAlignment.Center, GafferUI.Label.VerticalAlignment.Center ) )

	def testLifespan( self ) :

		w = GafferUI.Label( "hi" )
		r = weakref.ref( w )

		w.linkActivatedSignal()

		self.assertTrue( r() is w )
		del w
		self.assertIsNone( r() )

	def testHtmlInText( self ) :

		w = GafferUI.Label( "<h3>hello</h3>" )
		self.assertEqual( w.getText(), "<h3>hello</h3>" )

		w.setText( "<h2>goodbye</h2>" )
		self.assertEqual( w.getText(), "<h2>goodbye</h2>" )

	def testTextSelectable( self ) :

		w = GafferUI.Label( "" )
		self.assertEqual( w.getTextSelectable(), False )

		w.setTextSelectable( True )
		self.assertEqual( w.getTextSelectable(), True )

		w.setTextSelectable( False )
		self.assertEqual( w.getTextSelectable(), False )

if __name__ == "__main__":
	unittest.main()
