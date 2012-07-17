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

import os
import unittest

import IECore

import Gaffer
import GafferScene

class ObjectToSceneTest( unittest.TestCase ) :

	def test( self ) :
	
		fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/cobs/pSphereShape1.cob" )
		
		read = Gaffer.ReadNode( inputs = { "fileName" : fileName } )
		object = IECore.Reader.create( fileName ).read()
		
		objectToScene = GafferScene.ObjectToScene( inputs = { "object" : read["output"] } )
		
		self.assertEqual( objectToScene["out"].bound( "/" ), object.bound() )
		self.assertEqual( objectToScene["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( objectToScene["out"].object( "/" ), None )
		self.assertEqual( objectToScene["out"].childNames( "/" ), IECore.StringVectorData( [ "object" ] ) )
		
		self.assertEqual( objectToScene["out"].bound( "/object" ), object.bound() )
		self.assertEqual( objectToScene["out"].transform( "/object" ), IECore.M44f() )
		self.assertEqual( objectToScene["out"].object( "/object" ), object )
		self.assertEqual( objectToScene["out"].childNames( "/object" ), None )
		
if __name__ == "__main__":
	unittest.main()
