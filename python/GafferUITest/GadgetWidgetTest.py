##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

import GafferUI
import GafferUITest

class GadgetWidgetTest( GafferUITest.TestCase ) :

	def testViewportVisibility( self ) :

		with GafferUI.Window() as w :
			gw = GafferUI.GadgetWidget()

		vg1 = gw.getViewportGadget()

		self.assertFalse( gw.visible() )
		self.assertFalse( vg1.visible() )

		w.setVisible( True )
		self.assertTrue( gw.visible() )
		self.assertTrue( vg1.visible() )

		vg2 = GafferUI.ViewportGadget()
		self.assertFalse( vg2.visible() )

		gw.setViewportGadget( vg2 )
		self.assertTrue( vg2.visible() )
		self.assertFalse( vg1.visible() )

		w.setVisible( False )
		self.assertFalse( vg1.visible() )
		self.assertFalse( vg2.visible() )

	def testConnectionLifetime( self ) :

		gadgetWidget = GafferUI.GadgetWidget()
		viewportGadget1 = gadgetWidget.getViewportGadget()
		self.assertEqual( viewportGadget1.renderRequestSignal().numSlots(), 1 )

		viewportGadget2 = GafferUI.ViewportGadget()
		self.assertEqual( viewportGadget2.renderRequestSignal().numSlots(), 0 )

		gadgetWidget.setViewportGadget( viewportGadget2 )
		self.assertEqual( viewportGadget1.renderRequestSignal().numSlots(), 0 )
		self.assertEqual( viewportGadget2.renderRequestSignal().numSlots(), 1 )

if __name__ == "__main__":
	unittest.main()
