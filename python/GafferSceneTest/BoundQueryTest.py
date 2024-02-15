##########################################################################
#
#  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

import random
import unittest
import imath

import Gaffer
import GafferScene
import GafferSceneTest

def randomName( gen, mnc, mxc ):

	from string import ascii_lowercase

	return ''.join( gen.choice( ascii_lowercase )
		for _ in range( gen.randrange( mnc, mxc ) ) )

class BoundQueryTest( GafferSceneTest.SceneTestCase ):

	def testDefault( self ):

		v = imath.V3f( 0.0, 0.0, 0.0 )
		b = imath.Box3f( v, v )

		bq = GafferScene.BoundQuery()

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

	def testSpaceLocal( self ):

		r = random.Random()

		name1 = randomName( r, 5, 10 )
		s1 = GafferScene.Sphere()
		s1["name"].setValue( name1 )
		s1["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		s1["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		s1["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )

		name2 = randomName( r, 5, 10 )
		s2 = GafferScene.Sphere()
		s2["name"].setValue( name2 )
		s2["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		s2["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		s2["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )

		g = GafferScene.Group()
		g["name"].setValue( "group" )
		g["in"][0].setInput( s1["out"] )
		g["in"][1].setInput( s2["out"] )
		g["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		g["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		g["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )

		bq = GafferScene.BoundQuery()
		bq["space"].setValue( GafferScene.BoundQuery.Space.Local )
		bq["location"].setValue( "/" )

		v = imath.V3f( 0.0, 0.0, 0.0 )
		b = imath.Box3f( v, v )

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

		bq["location"].setValue( "/" + name1 )

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

		bq["scene"].setInput( g["out"] )
		bq["location"].setValue( '/group/' + name1 )

		b = bq["scene"].bound( '/group/' + name1 )

		self.assertTrue( bq["__internalBound"].getValue() == b )
		self.assertTrue( bq["bound"]["min"].getValue() == b.min() )
		self.assertTrue( bq["bound"]["max"].getValue() == b.max() )
		self.assertTrue( bq["center"].getValue() == b.center() )
		self.assertTrue( bq["size"].getValue() == b.size() )

		bq["location"].setValue( '/group/' + name2 )

		b = bq["scene"].bound( '/group/' + name2 )

		self.assertTrue( bq["__internalBound"].getValue() == b )
		self.assertTrue( bq["bound"]["min"].getValue() == b.min() )
		self.assertTrue( bq["bound"]["max"].getValue() == b.max() )
		self.assertTrue( bq["center"].getValue() == b.center() )
		self.assertTrue( bq["size"].getValue() == b.size() )

		bq["location"].setValue( '/group' )

		b = bq["scene"].bound( '/group' )

		self.assertTrue( bq["__internalBound"].getValue() == b )
		self.assertTrue( bq["bound"]["min"].getValue() == b.min() )
		self.assertTrue( bq["bound"]["max"].getValue() == b.max() )
		self.assertTrue( bq["center"].getValue() == b.center() )
		self.assertTrue( bq["size"].getValue() == b.size() )

	def testSpaceWorld( self ):

		r = random.Random()

		name1 = randomName( r, 5, 10 )
		s1 = GafferScene.Sphere()
		s1["name"].setValue( name1 )
		s1["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		s1["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		s1["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )
		m1 = s1["transform"].matrix()

		name2 = randomName( r, 5, 10 )
		s2 = GafferScene.Sphere()
		s2["name"].setValue( name2 )
		s2["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		s2["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		s2["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )
		m2 = s2["transform"].matrix()

		g = GafferScene.Group()
		g["name"].setValue( "group" )
		g["in"][0].setInput( s1["out"] )
		g["in"][1].setInput( s2["out"] )
		g["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		g["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		g["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )
		m3 = g["transform"].matrix()

		bq = GafferScene.BoundQuery()
		bq["space"].setValue( GafferScene.BoundQuery.Space.World )
		bq["location"].setValue( "/" )

		v = imath.V3f( 0.0, 0.0, 0.0 )
		b = imath.Box3f( v, v )

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

		bq["location"].setValue( "/" + name1 )

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

		bq["scene"].setInput( g["out"] )
		bq["location"].setValue( '/group/' + name1 )

		b = bq["scene"].bound( '/group/' + name1 ) * ( m1 * m3 )

		self.assertTrue( bq["__internalBound"].getValue().min().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["__internalBound"].getValue().max().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["bound"]["min"].getValue().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["bound"]["max"].getValue().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["center"].getValue().equalWithAbsError( b.center(), 0.000001 ) )
		self.assertTrue( bq["size"].getValue().equalWithAbsError( b.size(), 0.000001 ) )

		bq["location"].setValue( '/group/' + name2 )

		b = bq["scene"].bound( '/group/' + name2 ) * ( m2 * m3 )

		self.assertTrue( bq["__internalBound"].getValue().min().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["__internalBound"].getValue().max().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["bound"]["min"].getValue().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["bound"]["max"].getValue().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["center"].getValue().equalWithAbsError( b.center(), 0.000001 ) )
		self.assertTrue( bq["size"].getValue().equalWithAbsError( b.size(), 0.000001 ) )

	def testSpaceRelative( self ):

		r = random.Random()

		name1 = randomName( r, 5, 10 )
		s1 = GafferScene.Sphere()
		s1["name"].setValue( name1 )
		s1["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		s1["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		s1["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )
		m1 = s1["transform"].matrix()

		name2 = randomName( r, 5, 10 )
		s2 = GafferScene.Sphere()
		s2["name"].setValue( name2 )
		s2["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		s2["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		s2["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )
		m2 = s2["transform"].matrix()

		g = GafferScene.Group()
		g["name"].setValue( "group" )
		g["in"][0].setInput( s1["out"] )
		g["in"][1].setInput( s2["out"] )
		g["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		g["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		g["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )
		m3 = g["transform"].matrix()

		bq = GafferScene.BoundQuery()
		bq["space"].setValue( GafferScene.BoundQuery.Space.Relative )
		bq["location"].setValue( "/" )
		bq["relativeLocation"].setValue( "" )

		v = imath.V3f( 0.0, 0.0, 0.0 )
		b = imath.Box3f( v, v )

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

		bq["relativeLocation"].setValue( "/" )

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

		bq["location"].setValue( "/" + name1 )
		bq["relativeLocation"].setValue( "" )

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

		bq["relativeLocation"].setValue( "/" + name2 )

		self.assertEqual( bq["__internalBound"].getValue(), b )
		self.assertEqual( bq["bound"]["min"].getValue(), v )
		self.assertEqual( bq["bound"]["max"].getValue(), v )
		self.assertEqual( bq["center"].getValue(), v )
		self.assertEqual( bq["size"].getValue(), v )

		bq["scene"].setInput( g["out"] )
		bq["location"].setValue( '/group/' + name1 )
		bq["relativeLocation"].setValue( '/group/' + name2 )

		m = ( m1 * m3 ) * ( m2 * m3 ).inverse()
		b = bq["scene"].bound( '/group/' + name1 ) * m

		self.assertTrue( bq["__internalBound"].getValue().min().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["__internalBound"].getValue().max().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["bound"]["min"].getValue().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["bound"]["max"].getValue().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["center"].getValue().equalWithAbsError( b.center(), 0.000001 ) )
		self.assertTrue( bq["size"].getValue().equalWithAbsError( b.size(), 0.000001 ) )

	def testSpaceRelativeLocationSameAsLocationEmpty( self ):

		r = random.Random()

		name = randomName( r, 5, 10 )

		s = GafferScene.Sphere()
		s["name"].setValue( name )

		bq = GafferScene.BoundQuery()
		bq["scene"].setInput( s["out"] )
		bq["location"].setValue( "" )
		bq["relativeLocation"].setValue( "" )
		bq["space"].setValue( GafferScene.BoundQuery.Space.Relative )

		v = imath.V3f( 0.0, 0.0, 0.0 )
		b = imath.Box3f( v, v )

		self.assertTrue( bq["__internalBound"].getValue().min().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["__internalBound"].getValue().max().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["bound"]["min"].getValue().equalWithAbsError( v, 0.000001 ) )
		self.assertTrue( bq["bound"]["max"].getValue().equalWithAbsError( v, 0.000001 ) )
		self.assertTrue( bq["center"].getValue().equalWithAbsError( v, 0.000001 ) )
		self.assertTrue( bq["size"].getValue().equalWithAbsError( v, 0.000001 ) )

	def testSpaceRelativeLocationSameAsLocationInvalid( self ):

		r = random.Random()

		name1 = 'a' + randomName( r, 4, 9 )
		name2 = 'b' + randomName( r, 4, 9 )

		s = GafferScene.Sphere()
		s["name"].setValue( name1 )

		bq = GafferScene.BoundQuery()
		bq["scene"].setInput( s["out"] )
		bq["location"].setValue( name2 )
		bq["relativeLocation"].setValue( name2 )
		bq["space"].setValue( GafferScene.BoundQuery.Space.Relative )

		v = imath.V3f( 0.0, 0.0, 0.0 )
		b = imath.Box3f( v, v )

		self.assertTrue( bq["__internalBound"].getValue().min().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["__internalBound"].getValue().max().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["bound"]["min"].getValue().equalWithAbsError( v, 0.000001 ) )
		self.assertTrue( bq["bound"]["max"].getValue().equalWithAbsError( v, 0.000001 ) )
		self.assertTrue( bq["center"].getValue().equalWithAbsError( v, 0.000001 ) )
		self.assertTrue( bq["size"].getValue().equalWithAbsError( v, 0.000001 ) )

	def testSpaceRelativeLocationSameAsLocationValid( self ):

		r = random.Random()

		name = randomName( r, 5, 10 )

		s = GafferScene.Sphere()
		s["name"].setValue( name )
		s["transform"]["scale"].setValue( imath.V3f(
			r.random() * 10.0,
			r.random() * 10.0,
			r.random() * 10.0 ) )
		s["transform"]["translate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0,
			( r.random() - 0.5 ) * 10.0 ) )
		s["transform"]["rotate"].setValue( imath.V3f(
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0,
			( r.random() - 0.5 ) * 360.0 ) )

		bq = GafferScene.BoundQuery()
		bq["scene"].setInput( s["out"] )
		bq["location"].setValue( name )
		bq["relativeLocation"].setValue( name )
		bq["space"].setValue( GafferScene.BoundQuery.Space.Relative )

		b = bq["scene"].bound( name )

		self.assertTrue( bq["__internalBound"].getValue().min().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["__internalBound"].getValue().max().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["bound"]["min"].getValue().equalWithAbsError( b.min(), 0.000001 ) )
		self.assertTrue( bq["bound"]["max"].getValue().equalWithAbsError( b.max(), 0.000001 ) )
		self.assertTrue( bq["center"].getValue().equalWithAbsError( b.center(), 0.000001 ) )
		self.assertTrue( bq["size"].getValue().equalWithAbsError( b.size(), 0.000001 ) )

if __name__ == "__main__":
	unittest.main()
