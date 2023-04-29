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

import imath
import unittest
import threading

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class ScatterTest( GafferSceneTest.SceneTestCase ) :

	def testChildNames( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Scatter()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "scatter" )

		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "scatter" ] ) )
		self.assertEqual( s["out"].childNames( "/plane/scatter" ), IECore.InternedStringVectorData() )

		s["name"].setValue( "points" )

		self.assertEqual( s["out"].childNames( "/" ), IECore.InternedStringVectorData( [ "plane" ] ) )
		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "points" ] ) )
		self.assertEqual( s["out"].childNames( "/plane/points" ), IECore.InternedStringVectorData() )

	def testObject( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Scatter()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "scatter" )

		self.assertEqual( s["out"].objectHash( "/plane" ), p["out"].objectHash( "/plane" ) )
		self.assertEqual( s["out"].object( "/plane" ), p["out"].object( "/plane" ) )

		self.assertIsInstance( s["out"].object( "/plane/scatter" ), IECoreScene.PointsPrimitive )
		numPoints = s["out"].object( "/plane/scatter" ).numPoints

		s["density"].setValue( 10 )
		self.assertGreater( s["out"].object( "/plane/scatter" ).numPoints, numPoints )

		h = s["out"].objectHash( "/plane/scatter" )
		m = s["out"].object( "/plane/scatter" )
		s["name"].setValue( "notScatter" )
		self.assertEqual( h, s["out"].objectHash( "/plane/notScatter" ) )
		self.assertEqual( m, s["out"].object( "/plane/notScatter" ) )

	def testSceneValidity( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Scatter()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "scatter" )

		self.assertSceneValid( s["out"] )

	def testDisabled( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Scatter()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "scatter" )

		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "scatter" ] ) )

		s["enabled"].setValue( False )

		self.assertEqual( s["out"].childNames( "/plane" ), IECore.InternedStringVectorData() )
		self.assertScenesEqual( s["out"], p["out"] )

	def testNamePlugDefaultValue( self ) :

		s = GafferScene.Scatter()
		self.assertEqual( s["name"].defaultValue(), "seeds" )
		self.assertEqual( s["name"].getValue(), "seeds" )

	def testAffects( self ) :

		s = GafferScene.Scatter()
		a = s.affects( s["name"] )
		self.assertGreaterEqual( { x.relativeName( s ) for x in a }, { "out.childNames" } )

	def testMultipleChildren( self ) :

		p = GafferScene.Plane()

		s = GafferScene.Scatter()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "scatter" )

		s2 = GafferScene.Scatter()
		s2["in"].setInput( s["out"] )
		s2["parent"].setValue( "/plane" )
		s2["name"].setValue( "scatter" )
		s2["density"].setValue( 10 )

		self.assertEqual( s2["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "scatter", "scatter1" ] ) )
		self.assertTrue( len( s2["out"].object( "/plane/scatter" )["P"].data ) < len( s2["out"].object( "/plane/scatter1" )["P"].data ) )

		self.assertSceneValid( s["out"] )
		self.assertSceneValid( s2["out"] )

		s["name"].setValue( "scatter1" )
		self.assertEqual( s2["out"].childNames( "/plane" ), IECore.InternedStringVectorData( [ "scatter1", "scatter" ] ) )
		self.assertTrue( len( s2["out"].object( "/plane/scatter1" )["P"].data ) < len( s2["out"].object( "/plane/scatter" )["P"].data ) )

		self.assertEqual( s2["out"].objectHash( "/plane/scatter1" ), s["out"].objectHash( "/plane/scatter1" ) )

		self.assertSceneValid( s["out"] )
		self.assertSceneValid( s2["out"] )

	def testEmptyName( self ) :

		p = GafferScene.Plane()

		s = GafferScene.Scatter()
		s["in"].setInput( p["out"] )
		s["parent"].setValue( "/plane" )
		s["name"].setValue( "" )

		self.assertScenesEqual( s["out"], p["out"] )

	def testEmptyParent( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Scatter()

		s["in"].setInput( p["out"] )
		s["parent"].setValue( "" )

		self.assertScenesEqual( s["out"], p["out"] )
		self.assertSceneHashesEqual( s["out"], p["out"] )

	def testGlobalsPassThrough( self ) :

		p = GafferScene.Plane()
		l = GafferSceneTest.TestLight()

		g = GafferScene.Group()
		g["in"][0].setInput( p["out"] )
		g["in"][1].setInput( l["out"] )

		s = GafferScene.Scatter()
		s["in"].setInput( g["out"] )
		s["parent"].setValue( "/group/plane" )

		self.assertEqual( s["in"]["globals"].hash(), s["out"]["globals"].hash() )
		self.assertEqual( s["in"]["globals"].getValue(), s["out"]["globals"].getValue() )

	def testDensityPrimitiveVariable( self ) :

		plane = GafferScene.Plane()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		primitiveVariables = GafferScene.PrimitiveVariables()
		primitiveVariables["in"].setInput( plane["out"] )
		primitiveVariables["filter"].setInput( filter["out"] )

		scatter = GafferScene.Scatter()
		scatter["in"].setInput( primitiveVariables["out"] )
		scatter["parent"].setValue( "/plane" )
		scatter["name"].setValue( "scatter" )
		scatter["density"].setValue( 100 )

		p = scatter["out"].object( "/plane/scatter" )

		# Density variable doesn't exist, result should be
		# the same.

		scatter["densityPrimitiveVariable"].setValue( "d" )
		self.assertEqual( scatter["out"].object( "/plane/scatter" ), p )

		# Add the primitive variable, it should take effect.

		primitiveVariables["primitiveVariables"].addChild( Gaffer.NameValuePlug( "d", IECore.FloatData( 0.5 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )
		self.assertLess( scatter["out"].object( "/plane/scatter" ).numPoints, p.numPoints )

	def testReferencePosition( self ) :

		plane = GafferScene.Plane()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		freeze = GafferScene.FreezeTransform()
		freeze["in"].setInput( plane["out"] )
		freeze["filter"].setInput( filter["out"] )

		copyVars = GafferScene.CopyPrimitiveVariables()
		copyVars["in"].setInput( freeze["out"] )
		copyVars["source"].setInput( plane["out"] )
		copyVars["filter"].setInput( filter["out"] )
		copyVars["primitiveVariables"].setValue( 'P' )
		copyVars["sourceLocation"].setValue( '/plane' )
		copyVars["prefix"].setValue( 'ref' )

		scatter = GafferScene.Scatter()
		scatter["in"].setInput( copyVars["out"] )
		scatter["filter"].setInput( filter["out"] )
		scatter["name"].setValue( 'points' )
		scatter["density"].setValue( 10.0 )

		self.assertEqual( scatter["out"].object( "/plane/points" ).numPoints, 10 )
		plane["transform"]["scale"].setValue( imath.V3f( 3, 3, 3 ) )
		self.assertEqual( scatter["out"].object( "/plane/points" ).numPoints, 90 )
		scatter["referencePosition"].setValue( "refP" )
		self.assertEqual( scatter["out"].object( "/plane/points" ).numPoints, 10 )

	def testUV( self ) :

		plane = GafferScene.Plane()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ '/plane' ] ) )

		shuffle = GafferScene.ShufflePrimitiveVariables()
		shuffle["in"].setInput( plane["out"] )
		shuffle["filter"].setInput( filter["out"] )
		shuffle["shuffles"].addChild( Gaffer.ShufflePlug( "uv", "uvX", True ) )

		scatter = GafferScene.Scatter()
		scatter["in"].setInput( shuffle["out"] )
		scatter["filter"].setInput( filter["out"] )
		scatter["name"].setValue( 'points' )
		scatter["density"].setValue( 10.0 )

		with self.assertRaisesRegex( RuntimeError, 'MeshPrimitive has no uv primitive variable named "uv" of type FaceVarying or Vertex.' ) :
			scatter["out"].object( "/plane/points" )

		scatter["uv"].setValue( "uvX" )

		self.assertEqual( scatter["out"].object( "/plane/points" ).numPoints, 10 )

	def testPrimitiveVariables( self ) :

		plane = GafferScene.Plane()

		filter = GafferScene.PathFilter()
		filter["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )

		scatter = GafferScene.Scatter()
		scatter["in"].setInput( plane["out"] )
		scatter["parent"].setValue( "/plane" )
		scatter["name"].setValue( "scatter" )
		scatter["density"].setValue( 10 )

		self.assertEqual( scatter["out"].object( "/plane/scatter" ).keys(), ["P", "type"] )

		scatter["primitiveVariables"].setValue( "*" )

		points = scatter["out"].object( "/plane/scatter" )
		self.assertEqual( points.keys(), ["N", "P", "type", "uv" ] )
		for a, b in zip( points["uv"].data, points["P"].data ):
			self.assertTrue( a.equalWithRelError( imath.V2f( b[0], b[1] ) + 0.5, 0.00001 ) )

		for a in points["N"].data:
			self.assertEqual( a, imath.V3f( 0, 0, 1 ) )

		scatter["primitiveVariables"].setValue( "N" )

		self.assertEqual( scatter["out"].object( "/plane/scatter" ).keys(), ["N", "P", "type"] )

	def testInternalConnectionsNotSerialised( self ) :

		s = Gaffer.ScriptNode()
		s["scatter"] = GafferScene.Scatter()
		self.assertNotIn( "setInput", s.serialise() )

if __name__ == "__main__":
	unittest.main()
