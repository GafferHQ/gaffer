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

import IECore

import Gaffer

class FileSystemPathTest( unittest.TestCase ) :

	def test( self ) :
	
		p = Gaffer.FileSystemPath( __file__ )
		
		self.assert_( p.isValid() )
		self.assert_( p.isLeaf() )
	
		while len( p ) :
		
			del p[-1]
			self.assert_( p.isValid() )
			self.assert_( not p.isLeaf() )
			
	def testIsLeaf( self ) :
	
		path = Gaffer.FileSystemPath( "/this/path/doesnt/exist" )
		self.assert_( not path.isLeaf() )
		
	def testConstructWithFilter( self ) :
	
		p = Gaffer.FileSystemPath( __file__ )
		self.failUnless( p.getFilter() is None )
		
		f = Gaffer.FileNamePathFilter( [ "*.exr" ] )
		p = Gaffer.FileSystemPath( __file__, filter = f )
		self.failUnless( p.getFilter() is f )
		
if __name__ == "__main__":
	unittest.main()
	
