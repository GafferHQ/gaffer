##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import GafferTest
import GafferUI
import GafferUITest

class ViewportGadgetTest( GafferUITest.TestCase ) :

	def testViewportChangedSignal( self ) :

		v = GafferUI.ViewportGadget()

		cs = GafferTest.CapturingSlot( v.viewportChangedSignal() )

		v.setViewport( v.getViewport() )
		self.assertEqual( len( cs ), 0 )

		v.setViewport( v.getViewport() + IECore.V2i( 10 ) )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( v, ) )

		v.setViewport( v.getViewport() )
		self.assertEqual( len( cs ), 1 )

	def testCameraChangedSignal( self ) :

		v = GafferUI.ViewportGadget()

		cs = GafferTest.CapturingSlot( v.cameraChangedSignal() )

		v.setCamera( v.getCamera() )
		self.assertEqual( len( cs ), 0 )

		c = v.getCamera()
		c.parameters()["perspective:fov"] = IECore.FloatData( 10 )

		v.setCamera( c )
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( v, ) )

		v.setCamera( v.getCamera() )
		self.assertEqual( len( cs ), 1 )

if __name__ == "__main__":
	unittest.main()

