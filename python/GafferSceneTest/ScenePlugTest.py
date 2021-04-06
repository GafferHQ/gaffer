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
import imath

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class ScenePlugTest( GafferSceneTest.SceneTestCase ) :

	def testRunTimeTyped( self ) :

		p = GafferScene.ScenePlug()

		self.assertTrue( p.isInstanceOf( Gaffer.ValuePlug.staticTypeId() ) )
		self.assertEqual( IECore.RunTimeTyped.baseTypeId( p.typeId() ), Gaffer.ValuePlug.staticTypeId() )

	def testDynamicSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = GafferScene.ScenePlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		ss = s.serialise()

		s = Gaffer.ScriptNode()
		s.execute( ss )

	def testFullTransform( self ) :

		translation = imath.M44f().translate( imath.V3f( 1 ) )
		scaling = imath.M44f().scale( imath.V3f( 10 ) )

		n = GafferSceneTest.CompoundObjectSource()
		n["in"].setValue(
			IECore.CompoundObject( {
				"children" : {
					"group" : {
						"transform" : IECore.M44fData( translation ),
						"children" : {
							"ball" : {
								"transform" : IECore.M44fData( scaling ),
							}
						}
					},
				},
			} )
		)

		self.assertEqual( n["out"].transform( "/" ), imath.M44f() )
		self.assertEqual( n["out"].transform( "/group" ), translation )
		self.assertEqual( n["out"].transform( "/group/ball" ), scaling )

		self.assertEqual( n["out"].fullTransform( "/" ), imath.M44f() )
		self.assertEqual( n["out"].fullTransform( "/group" ), translation )

		m = n["out"].fullTransform( "/group/ball" )
		self.assertEqual( m.translation(), imath.V3f( 1 ) )

		extractedScaling = imath.V3f()
		m.extractScaling( extractedScaling )
		self.assertEqual( extractedScaling, imath.V3f( 10 ) )
		self.assertEqual( m, scaling * translation )

	def testFullAttributes( self ) :

		n = GafferSceneTest.CompoundObjectSource()
		n["in"].setValue(
			IECore.CompoundObject( {
				"children" : {
					"group" : {
						"attributes" : {
							"a" : IECore.StringData( "a" ),
							"b" : IECore.StringData( "b" ),
						},
						"children" : {
							"ball" : {
								"attributes" : {
									"b" : IECore.StringData( "bOverride" ),
									"c" : IECore.StringData( "c" ),
								 },
							}
						}
					},
				},
			} )
		)

		self.assertEqual(
			n["out"].fullAttributes( "/group" ),
			IECore.CompoundObject( {
				"a" : IECore.StringData( "a" ),
				"b" : IECore.StringData( "b" ),
			} )
		)

		self.assertEqual(
			n["out"].fullAttributes( "/group/ball" ),
			IECore.CompoundObject( {
				"a" : IECore.StringData( "a" ),
				"b" : IECore.StringData( "bOverride" ),
				"c" : IECore.StringData( "c" ),
			} )
		)

	def testCreateCounterpart( self ) :

		s1 = GafferScene.ScenePlug( "a", Gaffer.Plug.Direction.Out )
		s2 = s1.createCounterpart( "b", Gaffer.Plug.Direction.In )

		self.assertEqual( s2.getName(), "b" )
		self.assertEqual( s2.getFlags(), s1.getFlags() )
		self.assertEqual( s2.direction(), Gaffer.Plug.Direction.In )

	def testAccessorOverloads( self ) :

		p = GafferScene.Plane()

		self.assertEqual( p["out"].attributes( "/plane" ), p["out"].attributes( IECore.InternedStringVectorData( [ "plane" ] ) ) )
		self.assertEqual( p["out"].transform( "/plane" ), p["out"].transform( IECore.InternedStringVectorData( [ "plane" ] ) ) )
		self.assertEqual( p["out"].object( "/plane" ), p["out"].object( IECore.InternedStringVectorData( [ "plane" ] ) ) )
		self.assertEqual( p["out"].bound( "/plane" ), p["out"].bound( IECore.InternedStringVectorData( [ "plane" ] ) ) )
		self.assertEqual( p["out"].childNames( "/plane" ), p["out"].childNames( IECore.InternedStringVectorData( [ "plane" ] ) ) )

		self.assertEqual( p["out"].attributesHash( "/plane" ), p["out"].attributesHash( IECore.InternedStringVectorData( [ "plane" ] ) ) )
		self.assertEqual( p["out"].transformHash( "/plane" ), p["out"].transformHash( IECore.InternedStringVectorData( [ "plane" ] ) ) )
		self.assertEqual( p["out"].objectHash( "/plane" ), p["out"].objectHash( IECore.InternedStringVectorData( [ "plane" ] ) ) )
		self.assertEqual( p["out"].boundHash( "/plane" ), p["out"].boundHash( IECore.InternedStringVectorData( [ "plane" ] ) ) )
		self.assertEqual( p["out"].childNamesHash( "/plane" ), p["out"].childNamesHash( IECore.InternedStringVectorData( [ "plane" ] ) ) )

		self.assertRaises( TypeError, p["out"].boundHash, 10 )

	def testBoxPromotion( self ) :

		b = Gaffer.Box()
		b["n"] = GafferScene.StandardAttributes()

		self.assertTrue( Gaffer.PlugAlgo.canPromote( b["n"]["in"] ) )
		self.assertTrue( Gaffer.PlugAlgo.canPromote( b["n"]["out"] ) )

		i = Gaffer.PlugAlgo.promote( b["n"]["in"] )
		o = Gaffer.PlugAlgo.promote( b["n"]["out"] )

		self.assertEqual( b["n"]["in"].getInput(), i )
		self.assertEqual( o.getInput(), b["n"]["out"] )

		self.assertTrue( Gaffer.PlugAlgo.isPromoted( b["n"]["in"] ) )
		self.assertTrue( Gaffer.PlugAlgo.isPromoted( b["n"]["out"] ) )

	def testNoneAsPath( self ) :

		p = GafferScene.Plane()
		self.assertRaises( Exception, p["out"].transform, None )

	def testStringToPath( self ) :

		self.assertEqual( GafferScene.ScenePlug.stringToPath( "" ), IECore.InternedStringVectorData() )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "/" ), IECore.InternedStringVectorData() )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "/a" ), IECore.InternedStringVectorData( [ "a" ] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "a" ), IECore.InternedStringVectorData( [ "a" ] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "/a/b" ), IECore.InternedStringVectorData( [ "a", "b" ] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "/a/b/" ), IECore.InternedStringVectorData( [ "a", "b" ] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "//a//b//" ), IECore.InternedStringVectorData( [ "a", "b" ] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "/foo/bar/" ), IECore.InternedStringVectorData( [ "foo", "bar" ] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "foo/bar/" ), IECore.InternedStringVectorData( [ "foo", "bar" ] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "foo/bar/.." ), IECore.InternedStringVectorData( [ "foo" ] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "foo/bar/../.." ), IECore.InternedStringVectorData( [] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "foo/bar/../../.." ), IECore.InternedStringVectorData( [] ) )
		self.assertEqual( GafferScene.ScenePlug.stringToPath( "foo/bar/../toto" ), IECore.InternedStringVectorData( [ "foo", "toto" ] ) )

	def testPathToString( self ) :

		self.assertEqual( GafferScene.ScenePlug.pathToString( IECore.InternedStringVectorData() ), "/" )
		self.assertEqual( GafferScene.ScenePlug.pathToString( IECore.InternedStringVectorData( [ "a" ] ) ), "/a" )
		self.assertEqual( GafferScene.ScenePlug.pathToString( IECore.InternedStringVectorData( [ "a", "b" ] ) ), "/a/b" )

	def testManyStringToPathCalls( self ) :

		GafferSceneTest.testManyStringToPathCalls()

	def testSetPlugs( self ) :

		p = GafferScene.ScenePlug()

		self.assertTrue( isinstance( p["setNames"], Gaffer.InternedStringVectorDataPlug ) )
		self.assertEqual( p["setNames"].defaultValue(), IECore.InternedStringVectorData() )

		self.assertTrue( isinstance( p["set"], Gaffer.PathMatcherDataPlug ) )
		self.assertEqual( p["set"].defaultValue(), IECore.PathMatcherData() )

	def testGlobalsAccessors( self ) :

		p = GafferScene.ScenePlug()

		self.assertEqual( p.globals(), p["globals"].getValue() )
		self.assertFalse( p.globals().isSame( p["globals"].getValue() ) )
		self.assertTrue( p.globals( _copy = False ).isSame( p["globals"].getValue( _copy = False ) ) )

		self.assertEqual( p.setNames(), p["setNames"].getValue() )
		self.assertFalse( p.setNames().isSame( p["setNames"].getValue() ) )
		self.assertTrue( p.setNames( _copy = False ).isSame( p["setNames"].getValue( _copy = False ) ) )

		self.assertEqual( p.globalsHash(), p["globals"].hash() )
		self.assertEqual( p.setNamesHash(), p["setNames"].hash() )

if __name__ == "__main__":
	unittest.main()
