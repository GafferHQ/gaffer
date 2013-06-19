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

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class AttributeCacheTest( GafferSceneTest.SceneTestCase ) :

	def testConstructWithInputs( self ) :
	
		m = GafferScene.SceneReader()
		a = GafferScene.AttributeCache()
		a["in"]["bound"].setInput( m["out"]["bound"] )
		a["in"]["transform"].setInput( m["out"]["transform"] )
		a["in"]["object"].setInput( m["out"]["object"] )
		a["in"]["childNames"].setInput( m["out"]["childNames"] )
	
	def testSerialisationOfMasterConnection( self ) :
	
		s = Gaffer.ScriptNode()
		s["m"] = GafferScene.SceneReader()
		s["a"] = GafferScene.AttributeCache()
		
		s["a"]["in"].setInput( s["m"]["out"] )
		self.failUnless( s["a"]["in"].getInput().isSame( s["m"]["out"] ) )
		
		ss = s.serialise()
		
		s = Gaffer.ScriptNode()
		s.execute( ss )	

		self.failUnless( s["a"]["in"].getInput().isSame( s["m"]["out"] ) )

	def testSerialisationOfMasterConnectionWhenInputNotSerialised( self ) :
	
		s = Gaffer.ScriptNode()
		s["m"] = GafferScene.SceneReader()
		s["a"] = GafferScene.AttributeCache()
		
		s["a"]["in"].setInput( s["m"]["out"] )
		self.failUnless( s["a"]["in"].getInput().isSame( s["m"]["out"] ) )
		
		ss = s.serialise( filter = Gaffer.StandardSet( [ s["a"] ] ) )
		
		s = Gaffer.ScriptNode()
		s.execute( ss )	

		self.assertEqual( s["a"]["in"].getInput(), None )

	def testProcessNonPrimitiveObject( self ) :
	
		c = GafferScene.Camera()
		
		a = GafferScene.AttributeCache()
		a["in"].setInput( c["out"] )
	
		self.assertSceneValid( a["out"] )
		self.failUnless( isinstance( a["out"].object( "/camera" ), IECore.Camera ) )
		
if __name__ == "__main__":
	unittest.main()
