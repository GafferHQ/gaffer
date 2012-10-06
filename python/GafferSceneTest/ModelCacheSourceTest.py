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

class ModelCacheSourceTest( GafferSceneTest.SceneTestCase ) :

	def testGlobals( self ) :
	
		m = GafferScene.ModelCacheSource()
		self.assertEqual( m["out"]["globals"].getValue(), IECore.ObjectVector() )
	
	def testAttributes( self ) :
	
		m = GafferScene.ModelCacheSource()
		self.assertEqual( m["out"].attributes( "/somewhere" ), IECore.CompoundObject() )
	
	def testReadFile( self ) :
	
		mc = IECore.ModelCache( "/tmp/test.mdc", IECore.IndexedIOOpenMode.Write )
		
		t = mc.writableChild( "transform" )
		t.writeTransform( IECore.M44d.createTranslated( IECore.V3d( 1, 0, 0 ) ) )
		
		s = t.writableChild( "shape" )
		s.writeObject( IECore.SpherePrimitive( 10 ) )
		
		del mc, t, s
		
		m = GafferScene.ModelCacheSource()
		m["fileName"].setValue( "/tmp/test.mdc" )
		self.assertSceneValid( m["out"] )
	
		self.assertEqual( m["out"].transform( "/transform" ), IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) )
		self.assertEqual( m["out"].object( "/transform/shape" ), IECore.SpherePrimitive( 10 ) )
	
if __name__ == "__main__":
	unittest.main()
