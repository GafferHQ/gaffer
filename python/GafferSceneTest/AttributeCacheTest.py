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

import Gaffer
import GafferScene

class AttributeCacheTest( unittest.TestCase ) :

	def testConstructWithInputs( self ) :
	
		# this used to crash
		m = GafferScene.ModelCacheSource()
		a = GafferScene.AttributeCache(
			inputs = {
				"in.bound.min.x" : m["out.bound.min.x"],
				"in.bound.min.y" : m["out.bound.min.y"],
				"in.bound.min.z" : m["out.bound.min.z"],
				"in.bound.max.x" : m["out.bound.max.x"],
				"in.bound.max.y" : m["out.bound.max.y"],
				"in.bound.max.z" : m["out.bound.max.z"],
				"in.transform" : m["out.transform"],
				"in.geometry" : m["out.geometry"],
				"in.childNames" : m["out.childNames"],
			}
		)
	
	def testSerialisationOfMasterConnection( self ) :
	
		s = Gaffer.ScriptNode()
		s["m"] = GafferScene.ModelCacheSource()
		s["a"] = GafferScene.AttributeCache()
		
		s["a"]["in"].setInput( s["m"]["out"] )
		self.failUnless( s["a"]["in"].getInput().isSame( s["m"]["out"] ) )
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )	

		self.failUnless( s["a"]["in"].getInput().isSame( s["m"]["out"] ) )

if __name__ == "__main__":
	unittest.main()
