##########################################################################
#
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

import IECore

import GafferTest
import GafferUI

class RenderableGadgetTest( unittest.TestCase ) :

	class TestProcedural( IECore.ParameterisedProcedural ) :

		def __init__( self, level = 0 ) :

			IECore.ParameterisedProcedural.__init__( self, "" )

			self.__level = level

		def doBound( self, args ) :

			return IECore.Box3f( IECore.V3f( -1 ), IECore.V3f( 1 ) )

		def doRender( self, renderer, args ) :

			if self.__level < 3 :
				RenderableGadgetTest.TestProcedural( self.__level + 1 ).render( renderer )

	def testSetRenderableWithThreadedProcedural( self ) :

		for i in range( 0, 100 ) :
			b = GafferUI.RenderableGadget( None )
			b.setRenderable( self.TestProcedural() )

	def testConstructWithThreadedProcedural( self ) :

		for i in range( 0, 100 ) :
			b = GafferUI.RenderableGadget( self.TestProcedural() )

	def testDefaultConstructor( self ) :

		b = GafferUI.RenderableGadget()
		self.assertEqual( b.getRenderable(), None )

	def testRenderRequestSignal( self ) :

		g = GafferUI.RenderableGadget()

		def f( gg ) :

			self.failUnless( g.isSame( gg ) )

		c = g.renderRequestSignal().connect( f )
		g.setRenderable( IECore.SpherePrimitive() )

	def testSelection( self ) :

		g = GafferUI.RenderableGadget()

		selection = g.getSelection()
		self.assertEqual( selection, set() )
		w = weakref.ref( selection )
		del selection
		self.failUnless( w() is None )

		cs = GafferTest.CapturingSlot( g.selectionChangedSignal() )

		g.setSelection( set( [ "/one", "/two" ] ) )
		self.assertEqual( g.getSelection(), set( [ "/one", "/two" ] ) )

		self.assertEqual( len( cs ), 1 )

		g.setSelection( set( [ "/one", "/two" ] ) )
		self.assertEqual( g.getSelection(), set( [ "/one", "/two" ] ) )

		# should be no new signal triggered as they were the same
		self.assertEqual( len( cs ), 1 )

		g.setSelection( set( [ "/one" ] ) )
		self.assertEqual( g.getSelection(), set( [ "/one" ] ) )

		self.assertEqual( len( cs ), 2 )

if __name__ == "__main__":
	unittest.main()

