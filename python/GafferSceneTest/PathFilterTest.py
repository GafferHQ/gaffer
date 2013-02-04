##########################################################################
#  
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
import GafferSceneTest

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
	
		for path, result in [
			( "/a",  f.Result.Match ),
			( "/red", f.Result.Match ),
			( "/re", f.Result.NoMatch ),
			( "/redThing", f.Result.NoMatch ),
			( "/b/c/d", f.Result.Match ),
			( "/c", f.Result.NoMatch ),
			( "/a/b", f.Result.NoMatch ),
			( "/blue", f.Result.NoMatch ),
			( "/b/c", f.Result.DescendantMatch ),
		] :

			with Gaffer.Context() as c :
				c["scene:path"] = IECore.InternedStringVectorData( path[1:].split( "/" ) )
				self.assertEqual( f["match"].getValue(), int( result ) )
	
	def testNullPaths( self ) :
	
		f = GafferScene.PathFilter()
		with Gaffer.Context() as c :
			c["scene:path"] = IECore.InternedStringVectorData( [ "a" ] )
			self.assertEqual( f["match"].getValue(), int( f.Result.NoMatch ) )
	
	def testScaling( self ) :
	
		paths = GafferSceneTest.PathMatcherTest.generatePaths(
			seed = 1,
			depthRange = ( 4, 8 ),
			numChildrenRange = ( 5, 6 )
		)
					
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( paths ) )
		with Gaffer.Context() as c :
			for path in paths :
				c["scene:path"] = IECore.InternedStringVectorData( path[1:].split( "/" ) )
				self.assertEqual( f["match"].getValue(), int( f.Result.Match ) )
	
	def testInputsDenied( self ) :
	
		f = GafferScene.PathFilter()
		p = Gaffer.StringVectorDataPlug( direction = Gaffer.Plug.Direction.Out, defaultValue = IECore.StringVectorData() )
		self.failIf( f["paths"].acceptsInput( p ) )
		
		self.failUnless( f["paths"].getFlags( Gaffer.Plug.Flags.Serialisable ) )
		
if __name__ == "__main__":
	unittest.main()
