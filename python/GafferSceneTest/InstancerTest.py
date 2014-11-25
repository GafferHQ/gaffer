##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import GafferTest
import GafferScene
import GafferSceneTest

class InstancerTest( GafferSceneTest.SceneTestCase ) :

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

	def testAffects( self ) :

		n = GafferScene.Instancer()
		a = n.affects( n["name"] )
		self.assertEqual( [ x.relativeName( n ) for x in a ], [ "out.childNames" ] )

	def testParentBoundsWhenNoInstances( self ) :

		sphere = GafferScene.Sphere()
		sphere["type"].setValue( sphere.Type.Primitive ) # no points, so we can't instance onto it

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/sphere" )
		instancer["instance"].setInput( sphere["out"] )

		self.assertSceneValid( instancer["out"] )
		self.assertEqual( instancer["out"].bound( "/sphere" ), sphere["out"].bound( "/sphere" ) )

	def testEmptyName( self ) :

		plane = GafferScene.Plane()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["parent"].setValue( "/plane" )
		instancer["name"].setValue( "" )

		self.assertScenesEqual( instancer["out"], plane["out"] )
		self.assertSceneHashesEqual( instancer["out"], plane["out"] )

	def testEmptyParent( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["instance"].setInput( sphere["out"] )

		instancer["parent"].setValue( "" )

		self.assertScenesEqual( instancer["out"], plane["out"] )
		self.assertSceneHashesEqual( instancer["out"], plane["out"] )

	def testSeedsAffectBound( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["instance"].setInput( sphere["out"] )

		instancer["parent"].setValue( "/plane" )

		h1 = instancer["out"].boundHash( "/plane/instances" )
		b1 = instancer["out"].bound( "/plane/instances" )

		plane["dimensions"].setValue( plane["dimensions"].getValue() * 2 )

		h2 = instancer["out"].boundHash( "/plane/instances" )
		b2 = instancer["out"].bound( "/plane/instances" )

		self.assertNotEqual( h1, h2 )
		self.assertNotEqual( b1, b2 )

	def testBoundHashIsStable( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["instance"].setInput( sphere["out"] )

		instancer["parent"].setValue( "/plane" )

		h = instancer["out"].boundHash( "/plane/instances" )
		for i in range( 0, 100 ) :
			self.assertEqual( instancer["out"].boundHash( "/plane/instances" ), h )

	def testObjectAffectsChildNames( self ) :

		plane = GafferScene.Plane()
		sphere = GafferScene.Sphere()

		instancer = GafferScene.Instancer()
		instancer["in"].setInput( plane["out"] )
		instancer["instance"].setInput( sphere["out"] )
		instancer["parent"].setValue( "/plane" )

		cs = GafferTest.CapturingSlot( instancer.plugDirtiedSignal() )
		plane["divisions"]["x"].setValue( 2 )

		dirtiedPlugs = [ s[0] for s in cs ]

		self.assertTrue( instancer["out"]["childNames"] in dirtiedPlugs )
		self.assertTrue( instancer["out"]["bound"] in dirtiedPlugs )
		self.assertTrue( instancer["out"]["transform"] in dirtiedPlugs )

	def testPythonExpressionAndGIL( self ) :
	
		script = Gaffer.ScriptNode()
		
		script["plane"] = GafferScene.Plane()
		script["plane"]["divisions"].setValue( IECore.V2i( 20 ) )
		
		script["sphere"] = GafferScene.Sphere()
		
		script["expression"] = Gaffer.Expression()
		script["expression"]["engine"].setValue( "python" )
		script["expression"]["expression"].setValue( "parent['sphere']['radius'] = context.getFrame() + float( context['instancer:id'] )" )
		
		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["instance"].setInput( script["sphere"]["out"] )
		script["instancer"]["parent"].setValue( "/plane" )
		
		# The Instancer spawns its own threads, so if we don't release the GIL
		# when invoking it, and an upstream node enters Python, we'll end up
		# with a deadlock. Test that isn't the case. We increment the frame
		# between each test to ensure the expression result is not cached and
		# we do truly enter python.
		with Gaffer.Context() as c :
		
			c["scene:path"] = IECore.InternedStringVectorData( [ "plane" ] )
			
			c.setFrame( 1 )
			script["instancer"]["out"]["globals"].getValue()
			c.setFrame( 2 )
			script["instancer"]["out"]["bound"].getValue()
			c.setFrame( 3 )
			script["instancer"]["out"]["transform"].getValue()
			c.setFrame( 4 )
			script["instancer"]["out"]["object"].getValue()
			c.setFrame( 5 )
			script["instancer"]["out"]["attributes"].getValue()
			c.setFrame( 6 )
			script["instancer"]["out"]["childNames"].getValue()
			c.setFrame( 7 )
			
			c.setFrame( 101 )
			script["instancer"]["out"]["globals"].hash()
			c.setFrame( 102 )
			script["instancer"]["out"]["bound"].hash()
			c.setFrame( 103 )
			script["instancer"]["out"]["transform"].hash()
			c.setFrame( 104 )
			script["instancer"]["out"]["object"].hash()
			c.setFrame( 105 )
			script["instancer"]["out"]["attributes"].hash()
			c.setFrame( 106 )
			script["instancer"]["out"]["childNames"].hash()
			c.setFrame( 107 )
			
			# The same applies for the higher level helper functions on ScenePlug	
			
			c.setFrame( 200 )
			script["instancer"]["out"].bound( "/plane" )
			c.setFrame( 201 )
			script["instancer"]["out"].transform( "/plane" )
			c.setFrame( 202 )
			script["instancer"]["out"].fullTransform( "/plane" )
			c.setFrame( 203 )
			script["instancer"]["out"].attributes( "/plane" )
			c.setFrame( 204 )
			script["instancer"]["out"].fullAttributes( "/plane" )
			c.setFrame( 205 )
			script["instancer"]["out"].object( "/plane" )
			c.setFrame( 206 )
			script["instancer"]["out"].childNames( "/plane" )
			c.setFrame( 207 )

			c.setFrame( 300 )
			script["instancer"]["out"].boundHash( "/plane" )
			c.setFrame( 301 )
			script["instancer"]["out"].transformHash( "/plane" )
			c.setFrame( 302 )
			script["instancer"]["out"].fullTransformHash( "/plane" )
			c.setFrame( 303 )
			script["instancer"]["out"].attributesHash( "/plane" )
			c.setFrame( 304 )
			script["instancer"]["out"].fullAttributesHash( "/plane" )
			c.setFrame( 305 )
			script["instancer"]["out"].objectHash( "/plane" )
			c.setFrame( 306 )
			script["instancer"]["out"].childNamesHash( "/plane" )
			c.setFrame( 307 )

if __name__ == "__main__":
	unittest.main()
