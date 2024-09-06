##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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
import weakref

import IECore

import Gaffer
import GafferUI
import GafferUITest

class WidgetSignalTest( GafferUITest.TestCase ) :

	def test( self ) :

		w = GafferUI.TabbedContainer()

		s = GafferUI.WidgetSignal()
		self.assertEqual( s( w ), False )

		self.__widget = None
		def f( ww ) :

			self.__widget = ww
			return True

		s.connect( f )
		self.assertEqual( s( w ), True )
		self.assertTrue( self.__widget is w )

	def testDeletionOfScopedConnectionDisconnects( self ) :

		w = GafferUI.TabbedContainer()

		s = GafferUI.WidgetSignal()
		self.assertEqual( s( w ), False )

		def f( ww ) :

			return True

		c = s.connect( f, scoped = True )

		self.assertEqual( s( w ), True )

		del c

		self.assertEqual( s( w ), False )

	def testCircularRef( self ) :

		class A( GafferUI.TabbedContainer ) :

			def __init__( self ) :

				GafferUI.TabbedContainer.__init__( self )

				self.signal = GafferUI.WidgetSignal()

			@staticmethod
			def f( widget ) :

				return True

			def ff( self, other ) :

				return True

		a = A()
		self.assertEqual( a.signal( a ), False )

		a.c = a.signal.connect( A.f, scoped = True )
		self.assertEqual( a.signal( a ), True )

		w = weakref.ref( a )
		self.assertTrue( w() is a )
		del a
		self.assertEqual( w(), None )

		a2 = A()
		self.assertEqual( a2.signal( a2 ), False )

		# it is imperative to connect to a WeakMethod to prevent
		# unbreakable circular references from forming.
		a2.c = a2.signal.connect( Gaffer.WeakMethod( a2.ff ), scoped = True )
		self.assertEqual( a2.signal( a2 ), True )

		w = weakref.ref( a2 )
		self.assertTrue( w() is a2 )
		del a2
		self.assertEqual( w(), None )

	def tearDown( self ) :

		self.__widget = None

		GafferUITest.TestCase.tearDown( self )

if __name__ == "__main__":
	unittest.main()
