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

class GroupScenesTest( unittest.TestCase ) :

	def testOneLevel( self ) :
	
		sphere = IECore.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"object" : sphere,
				"bound" : IECore.Box3fData( sphere.bound() ),
				"transform" : IECore.M44fData( IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) ) ),
			} )
		)
		
		group = GafferScene.GroupScenes( inputs = { "in" : input["out"] } )
		self.assertEqual( group["name"].getValue(), "group" )
		
		rootBound = sphere.bound()
		rootBound.min += IECore.V3f( 1, 2, 3 )
		rootBound.max += IECore.V3f( 1, 2, 3 )
		
		self.assertEqual( group["out"].object( "/" ), None )
		self.assertEqual( group["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/" ), rootBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.StringVectorData( [ "group" ] ) )
		
		self.assertEqual( group["out"].object( "/group" ), sphere )
		self.assertEqual( group["out"].transform( "/group" ), IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) ) )
		self.assertEqual( group["out"].bound( "/group" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/group" ), None )
		
	def testTwoLevels( self ) :
	
		sphere = IECore.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( sphere.bound() ),
				"children" : {
					"group" : {
						"bound" : IECore.Box3fData( sphere.bound() ),
						"children" : {
							"sphere" : {
								"bound" : IECore.Box3fData( sphere.bound() ),
								"object" : sphere,
							},
						},
					},
				},
			} ),
		)
		
		group = GafferScene.GroupScenes( inputs = { "in" : input["out"], "name" : "topLevel" } )
		self.assertEqual( group["name"].getValue(), "topLevel" )
		
		self.assertEqual( group["out"].object( "/" ), None )
		self.assertEqual( group["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/" ), IECore.StringVectorData( [ "topLevel" ] ) )

		self.assertEqual( group["out"].object( "/topLevel" ), None )
		self.assertEqual( group["out"].transform( "/topLevel" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel" ), IECore.StringVectorData( [ "group" ] ) )
		
		self.assertEqual( group["out"].object( "/topLevel/group" ), None )
		self.assertEqual( group["out"].transform( "/topLevel/group" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/group" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/group" ), IECore.StringVectorData( [ "sphere" ] ) )
		
		self.assertEqual( group["out"].object( "/topLevel/group/sphere" ), sphere )
		self.assertEqual( group["out"].transform( "/topLevel/group/sphere" ), IECore.M44f() )
		self.assertEqual( group["out"].bound( "/topLevel/group/sphere" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/topLevel/group/sphere" ), None )
	
	def testTransform( self ) :
	
		sphere = IECore.SpherePrimitive()
		input = GafferSceneTest.CompoundObjectSource()
		input["in"].setValue(
			IECore.CompoundObject( {
				"object" : sphere,
				"bound" : IECore.Box3fData( sphere.bound() ),
				"transform" : IECore.M44fData( IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) ) ),
			} )
		)
		
		group = GafferScene.GroupScenes( inputs = { "in" : input["out"], "transform.translate" : IECore.V3f( 1, 2, 3 ) } )
		self.assertEqual( group["name"].getValue(), "group" )
		
		rootBound = sphere.bound()
		rootBound.min += IECore.V3f( 1, 2, 3 )
		rootBound.max += IECore.V3f( 1, 2, 3 )
		
		self.assertEqual( group["out"].object( "/" ), None )
		self.assertEqual( group["out"].transform( "/" ), IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) ) )
		self.assertEqual( group["out"].bound( "/" ), rootBound )
		self.assertEqual( group["out"].childNames( "/" ), IECore.StringVectorData( [ "group" ] ) )
		
		self.assertEqual( group["out"].object( "/group" ), sphere )
		self.assertEqual( group["out"].transform( "/group" ), IECore.M44f.createTranslated( IECore.V3f( 1, 2, 3 ) ) )
		self.assertEqual( group["out"].bound( "/group" ), sphere.bound() )
		self.assertEqual( group["out"].childNames( "/group" ), None )
	
if __name__ == "__main__":
	unittest.main()
