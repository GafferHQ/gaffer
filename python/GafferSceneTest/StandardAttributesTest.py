##########################################################################
#  
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferScene
import GafferSceneTest

class StandardAttributesTest( GafferSceneTest.SceneTestCase ) :
		
	def testDefaultValues( self ) :
	
		s = GafferScene.StandardAttributes()

		self.assertEqual( s["attributes"]["visibility"]["value"].getValue(), True )		
		self.assertEqual( s["attributes"]["doubleSided"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["transformBlur"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["transformBlurSegments"]["value"].getValue(), 1 )
		self.assertEqual( s["attributes"]["deformationBlur"]["value"].getValue(), True )
		self.assertEqual( s["attributes"]["deformationBlurSegments"]["value"].getValue(), 1 )

		self.assertEqual( s["attributes"]["visibility"]["value"].defaultValue(), True )		
		self.assertEqual( s["attributes"]["doubleSided"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["transformBlur"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["transformBlurSegments"]["value"].defaultValue(), 1 )
		self.assertEqual( s["attributes"]["deformationBlur"]["value"].defaultValue(), True )
		self.assertEqual( s["attributes"]["deformationBlurSegments"]["value"].defaultValue(), 1 )
	
	def testSerialisationWithInvisibility( self ) :
	
		s = Gaffer.ScriptNode()
		s["a"] = GafferScene.StandardAttributes()
		s["a"]["attributes"]["visibility"]["value"].setValue( False )
		
		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		
		self.assertEqual( s2["a"]["attributes"]["visibility"]["value"].getValue(), False )
		self.assertEqual( s2["a"]["attributes"]["visibility"]["value"].defaultValue(), True )
		
	def testVisibilityBackwardCompatibility( self ) :
		
		s = Gaffer.ScriptNode()
		s["a"] = GafferScene.StandardAttributes()
		s["a"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["a"]["attributes"]["visibility"]["value"].setValue( False )
		
		before = s["a"]["out"].attributes( "/yeah" )
		
		s["a"]["attributes"]["visibility"]["name"].setValue( "gaffer:visibility" )
		
		after = s["a"]["out"].attributes( "/yeah" )
		
		self.assertEqual( before, after )
		
		
if __name__ == "__main__":
	unittest.main()
