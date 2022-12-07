##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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
import weakref
import imath

import IECore
import IECoreImage

import GafferUI
import GafferUITest

import Qt
from Qt import QtWidgets

class WidgetAlgoTest( GafferUITest.TestCase ) :

	def testGrab( self ) :

		with GafferUI.Window() as w :
			b = GafferUI.Button( "HI!" )

		w.setVisible( True )
		self.waitForIdle( 1000 )

		GafferUI.WidgetAlgo.grab( b, str( self.temporaryDirectory() / "grab.png" ) )

		i = IECore.Reader.create( str( self.temporaryDirectory() / "grab.png" ) ).read()

		## \todo Should we have an official method for getting
		# physical pixel size like this? Or should `grab()` downsize
		# to return an image with the logical pixel size?
		expectedSize = imath.V2f( b.size() )
		if Qt.__binding__ in ( "PySide2", "PyQt5" ) :
			screen= QtWidgets.QApplication.primaryScreen()
			windowHandle = b._qtWidget().windowHandle()
			if windowHandle :
				screen = windowHandle.screen()
			expectedSize *= screen.devicePixelRatio()

		self.assertEqual( imath.V2f( i.displayWindow.size() ) + imath.V2f( 1 ), expectedSize )

	def testGrabWithEventLoopRunning( self ) :

		with GafferUI.Window() as w :
			b = GafferUI.Button( "HI!" )

		w.setVisible( True )
		self.waitForIdle( 100000 )

		def grab() :

			GafferUI.WidgetAlgo.grab( b, str( self.temporaryDirectory() / "grab.png" ) )
			GafferUI.EventLoop.mainEventLoop().stop()

		GafferUI.EventLoop.addIdleCallback( grab )
		GafferUI.EventLoop.mainEventLoop().start()

		self.assertTrue( ( self.temporaryDirectory() / "grab.png" ).exists() )

	def testKeepUntilIdle( self ) :

		widget = GafferUI.Label()
		weakWidget = weakref.ref( widget )

		GafferUI.WidgetAlgo.keepUntilIdle( widget )
		del widget
		self.assertIsNotNone( weakWidget() )

		self.waitForIdle()
		self.assertIsNone( weakWidget() )

if __name__ == "__main__":
	unittest.main()
