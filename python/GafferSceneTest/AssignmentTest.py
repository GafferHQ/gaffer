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
import GafferSceneTest

class AssignmentTest( unittest.TestCase ) :

	def testFilter( self ) :
	
		sphere = IECore.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"ball1" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
					"ball2" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
					},
				},
			} )
		)
	
		a = GafferScene.Assignment()
		a["in"].setInput( input["out"] )
		
		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/ball1" ] ) )
		a["filter"].setInput( f["match"] )
		
		self.assertEqual( a["out"].state( "/" ), None )
		self.assertNotEqual( len( a["out"].state( "/ball1" ) ), None )
		self.assertEqual( a["out"].state( "/ball2" ), None )		
	
	def testFilterSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		s["a"] = GafferScene.Assignment()
		s["a"]["f"] = GafferScene.PathFilter()
		s["a"]["f"]["paths"].setValue( IECore.StringVectorData( [ "/ball1" ] ) )
		s["a"]["filter"].setInput( s["a"]["f"]["match"] )
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )
		
		self.failUnless( isinstance( s["a"]["f"], GafferScene.PathFilter ) )
		self.assertEqual( s["a"]["f"]["paths"].getValue( IECore.StringVectorData( [ "/ball1" ] ) ) )
		self.failUnless( s["a"]["filter"].getInput().isSame( s["a"]["f"]["match"] ) )
		
if __name__ == "__main__":
	unittest.main()
