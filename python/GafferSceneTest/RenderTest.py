##########################################################################
#  
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

class RenderTest( GafferSceneTest.SceneTestCase ) :

	def __allState( self, group, type, state=None ) :
	
		if state is None :
			state = []
		
		state.extend( [ s for s in group.state() if isinstance( s, type ) ] )
		for child in group.children() :
			if isinstance( child, IECore.Group ) :
				self.__allState( child, type, state )
				
		return state

	def testLightOutput( self ) :
	
		s = Gaffer.ScriptNode()
		s["fileName"].setValue( "/tmp/test.gfr" )
		
		s["l"] = GafferSceneTest.TestLight()
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["l"]["out"] )
		
		self.assertSceneValid( s["g"]["out"] )
	
		s["r"] = GafferSceneTest.TestRender()
		s["r"]["in"].setInput( s["g"]["out"] )
		
		# CapturingRenderer outputs some spurious errors which
		# we suppress by capturing them.
		with IECore.CapturingMessageHandler() :
			s["r"].execute( [ Gaffer.Context.current() ] )
		
		w = s["r"].world()
		lights = self.__allState( s["r"].world(), IECore.Light )
		
		self.assertEqual( len( lights ), 1 )
		self.assertEqual( lights[0].handle, "/group/light" )
		
	def testLightVisibility( self ) :
	
		s = Gaffer.ScriptNode()
		s["fileName"].setValue( "/tmp/test.gfr" )
		
		s["l"] = GafferSceneTest.TestLight()
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["l"]["out"] )
		
		s["v"] = GafferScene.StandardAttributes()
		s["v"]["in"].setInput( s["g"]["out"] )
		s["v"]["attributes"]["visibility"]["enabled"].setValue( True )
		s["v"]["attributes"]["visibility"]["value"].setValue( True )

		self.assertSceneValid( s["v"]["out"] )
	
		s["r"] = GafferSceneTest.TestRender()
		s["r"]["in"].setInput( s["v"]["out"] )
		
		# CapturingRenderer outputs some spurious errors which
		# we suppress by capturing them.
		with IECore.CapturingMessageHandler() :
			s["r"].execute( [ Gaffer.Context.current() ] )
		
		w = s["r"].world()
		lights = self.__allState( s["r"].world(), IECore.Light )
				
		self.assertEqual( len( lights ), 1 )
		self.assertEqual( lights[0].handle, "/group/light" )	
		
		s["v"]["attributes"]["visibility"]["value"].setValue( False )
		with IECore.CapturingMessageHandler() :
			s["r"].execute( [ Gaffer.Context.current() ] )
		
		w = s["r"].world()
		lights = self.__allState( s["r"].world(), IECore.Light )
		self.assertEqual( len( lights ), 0 )
	
	def testLightAttributes( self ) :
	
		s = Gaffer.ScriptNode()
		s["fileName"].setValue( "/tmp/test.gfr" )
		
		s["l"] = GafferSceneTest.TestLight()
		
		s["a"] = GafferScene.Attributes()
		s["a"]["in"].setInput( s["l"]["out"] )
		s["a"]["attributes"].addMember( "user:test", IECore.IntData( 10 ) )

		s["r"] = GafferSceneTest.TestRender()
		s["r"]["in"].setInput( s["a"]["out"] )
		
		# CapturingRenderer outputs some spurious errors which
		# we suppress by capturing them.
		with IECore.CapturingMessageHandler() :
			s["r"].execute( [ Gaffer.Context.current() ] )
			
		w = s["r"].world()
		l = w.children()[0].state()
		self.assertTrue( isinstance( l[0], IECore.AttributeState ) )
		self.assertEqual( l[0].attributes["user:test"], IECore.IntData( 10 ) )
		self.assertTrue( isinstance( l[1], IECore.Light ) )
	
	def testLightName( self ) :
	
		s = Gaffer.ScriptNode()
		s["fileName"].setValue( "/tmp/test.gfr" )
		
		s["l"] = GafferSceneTest.TestLight()
		s["g"] = GafferScene.Group()
		s["g"]["in"].setInput( s["l"]["out"] )
		
		self.assertSceneValid( s["g"]["out"] )
	
		s["r"] = GafferSceneTest.TestRender()
		s["r"]["in"].setInput( s["g"]["out"] )
		
		# CapturingRenderer outputs some spurious errors which
		# we suppress by capturing them.
		with IECore.CapturingMessageHandler() :
			s["r"].execute( [ Gaffer.Context.current() ] )
		
		w = s["r"].world()
		self.assertEqual( w.children()[0].state()[0].attributes["name"].value, "/group/light" )
		self.assertEqual( w.children()[0].state()[1].handle, "/group/light" )
					
if __name__ == "__main__":
	unittest.main()
