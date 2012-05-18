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

import Gaffer

class WeakMethodTest( unittest.TestCase ) :

	def test( self ) :
	
		p = Gaffer.Path( "/" )
		pw = weakref.ref( p )
		self.failUnless( pw() is p )
		del p
		self.failUnless( pw() is None )
		
		p = Gaffer.Path( "/" )
		pw = weakref.ref( p )
		self.failUnless( pw() is p )
		
		setFromString = Gaffer.WeakMethod( p.setFromString )
		setFromString( "/a/b" )
		self.assertEqual( str( p ), "/a/b" )
		
		del p
		self.failUnless( pw() is None )
		self.assertRaises( weakref.ReferenceError, setFromString, "/g" )
		
		try :
			setFromString( "/g" )
		except weakref.ReferenceError as e :
			self.failUnless( "setFromString" in str( e ) )
		
if __name__ == "__main__":
	unittest.main()
