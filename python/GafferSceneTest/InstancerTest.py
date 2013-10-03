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

class InstancerTest( unittest.TestCase ) :

	def test( self ) :
	
		sphere = IECore.SpherePrimitive()
		instanceInput = GafferSceneTest.CompoundObjectSource()
		instanceInput["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( IECore.Box3f( IECore.V3f( -2 ), IECore.V3f( 2 ) ) ),
				"children" : {
					"sphere" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
						"transform" : IECore.M44fData( IECore.M44f.createScaled( IECore.V3f( 2 ) ) ),
					},
				}
			} )
		)
		
		seeds = IECore.PointsPrimitive(
			IECore.V3fVectorData(
				[ IECore.V3f( 1, 0, 0 ), IECore.V3f( 1, 1, 0 ), IECore.V3f( 0, 1, 0 ), IECore.V3f( 0, 0, 0 ) ]
			)
		)
		seedsInput = GafferSceneTest.CompoundObjectSource()
		seedsInput["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( IECore.Box3f( IECore.V3f( 1, 0, 0 ), IECore.V3f( 2, 1, 0 ) ) ),
				"children" : {
					"seeds" : {
						"bound" : IECore.Box3fData( seeds.bound() ),
						"transform" : IECore.M44fData( IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) ),
						"object" : seeds,
					},
				},
			}, )
		)

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( seedsInput["out"] )
		instancer["instance"].setInput( instanceInput["out"] )
		instancer["parent"].setValue( "/seeds" )
		instancer["name"].setValue( "instances" )
		
		self.assertEqual( instancer["out"].object( "/" ), IECore.NullObject() )
		self.assertEqual( instancer["out"].transform( "/" ), IECore.M44f() )
		self.assertEqual( instancer["out"].bound( "/" ), IECore.Box3f( IECore.V3f( -1, -2, -2 ), IECore.V3f( 4, 3, 2 ) ) )
		self.assertEqual( instancer["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "seeds" ] ) )
		
		self.assertEqual( instancer["out"].object( "/seeds" ), seeds )
		self.assertEqual( instancer["out"].transform( "/seeds" ), IECore.M44f().createTranslated( IECore.V3f( 1, 0, 0 ) ) )
		self.assertEqual( instancer["out"].bound( "/seeds" ), IECore.Box3f( IECore.V3f( -2, -2, -2 ), IECore.V3f( 3, 3, 2 ) ) )
		self.assertEqual( instancer["out"].childNames( "/seeds" ), IECore.InternedStringVectorData( [ "instances" ] ) )

		self.assertEqual( instancer["out"].object( "/seeds/instances" ), IECore.NullObject() )
		self.assertEqual( instancer["out"].transform( "/seeds/instances" ), IECore.M44f() )
		self.assertEqual( instancer["out"].bound( "/seeds/instances" ), IECore.Box3f( IECore.V3f( -2, -2, -2 ), IECore.V3f( 3, 3, 2 ) ) )
		self.assertEqual( instancer["out"].childNames( "/seeds/instances" ), IECore.InternedStringVectorData( [ "0", "1", "2", "3" ] ) )
		
		for i in range( 0, 4 ) :
		
			instancePath = "/seeds/instances/%d" % i
			
			self.assertEqual( instancer["out"].object( instancePath ), IECore.NullObject() )
			self.assertEqual( instancer["out"].transform( instancePath ), IECore.M44f.createTranslated( seeds["P"].data[i] ) )
			self.assertEqual( instancer["out"].bound( instancePath ), IECore.Box3f( IECore.V3f( -2 ), IECore.V3f( 2 ) ) )
			self.assertEqual( instancer["out"].childNames( instancePath ), IECore.InternedStringVectorData( [ "sphere" ] ) )
			
			self.assertEqual( instancer["out"].object( instancePath + "/sphere" ), sphere )
			self.assertEqual( instancer["out"].transform( instancePath + "/sphere" ), IECore.M44f.createScaled( IECore.V3f( 2 ) ) )
			self.assertEqual( instancer["out"].bound( instancePath + "/sphere" ), sphere.bound() )
			self.assertEqual( instancer["out"].childNames( instancePath + "/sphere" ), IECore.InternedStringVectorData() )

	def testThreading( self ) :
	
		sphere = IECore.SpherePrimitive()
		instanceInput = GafferSceneTest.CompoundObjectSource()
		instanceInput["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( IECore.Box3f( IECore.V3f( -2 ), IECore.V3f( 2 ) ) ),
				"children" : {
					"sphere" : {
						"object" : sphere,
						"bound" : IECore.Box3fData( sphere.bound() ),
						"transform" : IECore.M44fData( IECore.M44f.createScaled( IECore.V3f( 2 ) ) ),
					},
				}
			} )
		)
		
		seeds = IECore.PointsPrimitive(
			IECore.V3fVectorData(
				[ IECore.V3f( 1, 0, 0 ), IECore.V3f( 1, 1, 0 ), IECore.V3f( 0, 1, 0 ), IECore.V3f( 0, 0, 0 ) ]
			)
		)
		seedsInput = GafferSceneTest.CompoundObjectSource()
		seedsInput["in"].setValue(
			IECore.CompoundObject( {
				"bound" : IECore.Box3fData( IECore.Box3f( IECore.V3f( 1, 0, 0 ), IECore.V3f( 2, 1, 0 ) ) ),
				"children" : {
					"seeds" : {
						"bound" : IECore.Box3fData( seeds.bound() ),
						"transform" : IECore.M44fData( IECore.M44f.createTranslated( IECore.V3f( 1, 0, 0 ) ) ),
						"object" : seeds,
					},
				},
			}, )
		)

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( seedsInput["out"] )
		instancer["instance"].setInput( instanceInput["out"] )
		instancer["parent"].setValue( "/seeds" )
		instancer["name"].setValue( "instances" )
		
		GafferSceneTest.traverseScene( instancer["out"], Gaffer.Context() )

	def testNamePlugDefaultValue( self ) :
	
		n = GafferScene.Instancer()
		self.assertEqual( n["name"].defaultValue(), "instances" )
		self.assertEqual( n["name"].getValue(), "instances" )

if __name__ == "__main__":
	unittest.main()
