##########################################################################
#
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

import Gaffer
import GafferTest

class WeakMethodTest( GafferTest.TestCase ) :

	def test( self ) :

		class A( object ) :

			def f( self ) :

				return 10

		a = A()
		w = weakref.ref( a )
		wm = Gaffer.WeakMethod( a.f )

		self.assertEqual( w(), a )
		self.assertEqual( wm(), 10 )

		self.assertTrue( wm.instance() is a )
		self.assertTrue( wm.method() is A.f.__func__ )

		del a

		self.assertEqual( w(), None )
		self.assertRaises( ReferenceError, wm )
		self.assertEqual( wm.instance(), None )

		try :
			wm()
		except ReferenceError as e :
			self.assertIn( "f()", str( e ) )

	def testFallbackResult( self ) :

		class A( object ) :

			def f( self ) :

				return 10

		a = A()
		wm = Gaffer.WeakMethod( a.f, fallbackResult = 20 )

		self.assertEqual( wm(), 10 )

		del a

		self.assertEqual( wm(), 20 )

if __name__ == "__main__":
	unittest.main()
