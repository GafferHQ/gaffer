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

import IECore

import Gaffer
import GafferScene

class PathFilterTest( unittest.TestCase ) :

	def testConstruct( self ) :
	
		f = GafferScene.PathFilter()
	
	def testAffects( self ) :
	
		f = GafferScene.PathFilter()
		a = f.affects( f["paths"] )
		self.assertEqual( len( a ), 1 )
		self.failUnless( a[0].isSame( f["match"] ) )
	
	def testMatch( self ) :
	
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/a", "/red", "/b/c/d" ] ) )
	
		with Gaffer.Context() as c :
		
			c["scene:path"] = "/a"
			self.assertEqual( f["match"].getValue(), int( f.Result.Match ) )
		
			c["scene:path"] = "/red"
			self.assertEqual( f["match"].getValue(), int( f.Result.Match ) )
			
			c["scene:path"] = "/re"
			self.assertEqual( f["match"].getValue(), int( f.Result.NoMatch ) )
			
			c["scene:path"] = "/redThing"
			self.assertEqual( f["match"].getValue(), int( f.Result.NoMatch ) )
			
			c["scene:path"] = "/b/c/d"
			self.assertEqual( f["match"].getValue(), int( f.Result.Match ) )
		
			c["scene:path"] = "/c"
			self.assertEqual( f["match"].getValue(), int( f.Result.NoMatch ) )
		
			c["scene:path"] = "/a/b"
			self.assertEqual( f["match"].getValue(), int( f.Result.NoMatch ) )
		
			c["scene:path"] = "/blue"
			self.assertEqual( f["match"].getValue(), int( f.Result.NoMatch ) )
		
			c["scene:path"] = "/b/c"
			self.assertEqual( f["match"].getValue(), int( f.Result.DescendantMatch ) )
	
	def testNullPaths( self ) :
	
		f = GafferScene.PathFilter()
		with Gaffer.Context() as c :
			c["scene:path"] = "/a"
			self.assertEqual( f["match"].getValue(), int( f.Result.NoMatch ) )
			
if __name__ == "__main__":
	unittest.main()
