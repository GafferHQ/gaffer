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

import os
import unittest

import IECore

import Gaffer
import GafferTest
import GafferScene
import GafferSceneTest

class ObjectToSceneTest( GafferSceneTest.SceneTestCase ) :

	def testFileInput( self ) :
	
		fileName = os.path.expandvars( "$GAFFER_ROOT/python/GafferTest/cobs/pSphereShape1.cob" )
		
		read = Gaffer.ObjectReader()
		read["fileName"].setValue( fileName )
		object = IECore.Reader.create( fileName ).read()
		
		objectToScene = GafferScene.ObjectToScene()
		objectToScene["object"].setInput( read["out"] )
		
		self.assertEqual( objectToScene["out"].bound( "/" ), object.bound() )
		self.assertEqual( objectToScene["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( objectToScene["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( objectToScene["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "object" ] ) )
		
		self.assertEqual( objectToScene["out"].bound( "/object" ), object.bound() )
		self.assertEqual( objectToScene["out"].transform( "/object" ), IECore.M44f() )
		self.assertEqual( objectToScene["out"].object( "/object" ), object )
		self.assertEqual( objectToScene["out"].childNames( "/object" ), IECore.InternedStringVectorData() )

		self.assertSceneValid( objectToScene["out"] )		
	
	def testMeshInput( self ) :
	
		p = GafferScene.ObjectToScene()
		p["object"].setValue( IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
		
		self.assertSceneValid( p["out"] )		
		self.assertEqual( p["out"].object( "/object" ),  IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -1 ), IECore.V2f( 1 ) ) ) )
	
		p["object"].setValue( IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -2 ), IECore.V2f( 2 ) ) ) )

		self.assertSceneValid( p["out"] )		
		self.assertEqual( p["out"].object( "/object" ),  IECore.MeshPrimitive.createPlane( IECore.Box2f( IECore.V2f( -2 ), IECore.V2f( 2 ) ) ) )
	
	def testProceduralInput( self ) :
	
		p = Gaffer.ProceduralHolder()
		classSpec = GafferTest.ParameterisedHolderTest.classSpecification( "read", "IECORE_PROCEDURAL_PATHS" )[:-1]
		p.setProcedural( *classSpec )
		
		s = GafferScene.ObjectToScene()
		s["object"].setInput( p["output"] )
		
		self.failUnless( isinstance( s["out"].object( "/object" ), IECore.ParameterisedProcedural ) )
	
		p = s["out"].object( "/object" )
	
if __name__ == "__main__":
	unittest.main()
