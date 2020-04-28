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

class FrameTest( GafferUITest.TestCase ) :

	@GafferTest.expectedFailure
	def testGadget( self ) :

		# because we're not putting gadgets and widgets in different namespaces,
		# we have clashes where we want to name them the same. we need to resolve this.
		self.assertTrue( issubclass( GafferUI.Frame, GafferUI.Gadget ) )

	def testBorderStyle( self ) :

		f = GafferUI.Frame()
		self.assertEqual( f.getBorderStyle(), GafferUI.Frame.BorderStyle.Flat )

		f.setBorderStyle( GafferUI.Frame.BorderStyle.None )
		self.assertEqual( f.getBorderStyle(), GafferUI.Frame.BorderStyle.None )

	def testRemoveChild( self ) :

		f = GafferUI.Frame()
		b = GafferUI.Button()

		f.setChild( b )
		self.assertTrue( b.parent() is f )

		f.removeChild( b )
		self.assertIsNone( b.parent() )

	def testTransferChild( self ) :

		f = GafferUI.Frame()
		l = GafferUI.ListContainer()
		b = GafferUI.Button()

		l.append( b )
		self.assertEqual( len( l ), 1 )

		f.setChild( b )
		self.assertTrue( b.parent() is f )
		self.assertTrue( f.getChild() is b )
		self.assertEqual( len( l ), 0 )

if __name__ == "__main__":
	unittest.main()
