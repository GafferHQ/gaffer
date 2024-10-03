##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

class PopupWindowTest( GafferUITest.TestCase ) :

	def testDisplayTransform( self ) :

		displayTransform1 = lambda x : x * 2
		displayTransform2 = lambda x : x * 3

		window = GafferUI.Window()
		self.assertIs( window.displayTransform(), GafferUI.Widget.identityDisplayTransform )
		window.setDisplayTransform( displayTransform1 )
		self.assertIs( window.displayTransform(), displayTransform1 )

		popup = GafferUI.PopupWindow()
		self.assertEqual( popup.displayTransform(), GafferUI.Widget.identityDisplayTransform )
		popup.popup()
		self.assertEqual( popup.displayTransform(), GafferUI.Widget.identityDisplayTransform )

		popup.popup( parent = window )
		self.assertEqual( popup.displayTransform(), displayTransform1 )

		popup.setDisplayTransform( displayTransform2 )
		self.assertEqual( popup.displayTransform(), displayTransform2 )

	def testParentWindowLifetime( self ) :

		window = GafferUI.Window()
		popup = GafferUI.PopupWindow()
		popup.popup( parent = window )

		weakWindow = weakref.ref( window )
		weakPopup = weakref.ref( popup )
		del window, popup

		self.assertIsNone( weakWindow() )
		self.assertIsNone( weakPopup() )

if __name__ == "__main__":
	unittest.main()
