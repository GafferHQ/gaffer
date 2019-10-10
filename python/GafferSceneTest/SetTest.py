##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import GafferTest
import GafferScene
import GafferSceneTest

class SetTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Set()
		s["in"].setInput( p["out"] )

		s["paths"].setValue( IECore.StringVectorData( [ "/one", "/plane" ] ) )

		# Sets have nothing to do with globals.
		self.assertEqual( s["out"]["globals"].getValue(), p["out"]["globals"].getValue() )
		self.assertEqual( s["out"]["globals"].hash(), p["out"]["globals"].hash() )

		self.assertEqual( s["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( set( s["out"].set( "set" ).value.paths() ), set( [ "/one", "/plane" ] ) )

		s["name"].setValue( "shinyThings" )

		self.assertEqual( s["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "shinyThings" ] ) )
		self.assertEqual( set( s["out"].set( "shinyThings" ).value.paths() ), set( [ "/one", "/plane" ] ) )

		s["paths"].setValue( IECore.StringVectorData( [ "/two", "/sphere" ] ) )

		self.assertEqual( s["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "shinyThings" ] ) )
		self.assertEqual( set( s["out"].set( "shinyThings" ).value.paths() ), set( [ "/two", "/sphere" ] ) )

	def testInputNotModified( self ) :

		s1 = GafferScene.Set()
		s1["name"].setValue( "setOne" )
		s1["paths"].setValue( IECore.StringVectorData( [ "/one" ] ) )

		s2 = GafferScene.Set()
		s2["in"].setInput( s1["out"] )
		s2["name"].setValue( "setTwo" )
		s2["paths"].setValue( IECore.StringVectorData( [ "/two" ] ) )

		self.assertEqual( s1["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "setOne" ] ) )
		self.assertEqual( s1["out"].set( "setOne" ).value.paths(), [ "/one" ] )

		self.assertEqual( set( list( s2["out"]["setNames"].getValue() ) ), set( list( IECore.InternedStringVectorData( [ "setOne", "setTwo" ] ) ) ) )
		self.assertEqual( s2["out"].set( "setOne" ).value.paths(), [ "/one" ] )
		self.assertEqual( s2["out"].set( "setTwo" ).value.paths(), [ "/two" ] )
		self.assertTrue( s2["out"].set( "setOne", _copy = False ).isSame( s1["out"].set( "setOne", _copy = False ) ) )

	def testOverwrite( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/old"] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "/new"] ) )
		s2["in"].setInput( s1["out"] )

		self.assertEqual( s1["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( s1["out"].set( "set" ).value.paths(), [ "/old" ] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/new" ] )

	def testAdd( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/old"] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "/new"] ) )
		s2["mode"].setValue( s2.Mode.Add )
		s2["in"].setInput( s1["out"] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( set( s2["out"].set( "set" ).value.paths() ), set( [ "/old", "/new" ] ) )

		s1["enabled"].setValue( False )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/new" ] )

	def testRemove( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/a", "/b" ] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "/a"] ) )
		s2["mode"].setValue( s2.Mode.Remove )
		s2["in"].setInput( s1["out"] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/b" ] )

		s2["enabled"].setValue( False )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( set( s2["out"].set( "set" ).value.paths() ), set( [ "/a", "/b" ] ) )

	def testRemoveFromNonExistentSet( self ) :

		p = GafferScene.Plane()

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/a", "/b" ] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "/a"] ) )
		s2["name"].setValue( "thisSetDoesNotExist" )
		s2["mode"].setValue( s2.Mode.Remove )
		s2["in"].setInput( s1["out"] )

		self.assertEqual( s2["out"]["setNames"].getValue(), IECore.InternedStringVectorData( [ "set" ] ) )
		self.assertEqual( set( s2["out"].set( "set" ).value.paths() ), set( [ "/a", "/b" ] ) )

	def testDisabled( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )

		s2 = GafferScene.Set()
		s2["in"].setInput( s1["out"] )
		s2["paths"].setValue( IECore.StringVectorData( [ "/b" ] ) )
		s2["enabled"].setValue( False )

		self.assertEqual( s1["out"]["setNames"].hash(), s2["out"]["setNames"].hash() )
		self.assertEqual( s1["out"]["setNames"].getValue(), s2["out"]["setNames"].getValue() )
		self.assertEqual( s1["out"].setHash( "set" ), s2["out"].setHash( "set" ) )
		self.assertEqual( s1["out"].set( "set" ), s2["out"].set( "set" ) )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/a" ] )

	def testAffects( self ) :

		s = GafferScene.Set()

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		s["name"].setValue( "a" )

		self.assertTrue( s["out"]["setNames"] in [ p[0] for p in cs ] )
		self.assertTrue( s["out"]["globals"] not in [ p[0] for p in cs ] )

		del cs[:]
		s["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )

		self.assertTrue( s["out"]["set"] in [ p[0] for p in cs ] )
		self.assertTrue( s["out"]["globals"] not in [ p[0] for p in cs ] )

	def testNoWildcards( self ) :

		s = GafferScene.Set()

		s["paths"].setValue( IECore.StringVectorData( [ "/a/..." ] ) )
		self.assertRaises( RuntimeError, s["out"].set, "set" )

		s["paths"].setValue( IECore.StringVectorData( [ "/a/b*" ] ) )
		self.assertRaises( RuntimeError, s["out"].set, "set" )

	def testEmptyStringIsIgnored( self ) :

		s1 = GafferScene.Set()
		s1["paths"].setValue( IECore.StringVectorData( [ "/a" ] ) )

		s2 = GafferScene.Set()
		s2["paths"].setValue( IECore.StringVectorData( [ "" ] ) )
		s2["in"].setInput( s1["out"] )

		s2["mode"].setValue( s2.Mode.Create )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [] )

		s2["mode"].setValue( s2.Mode.Add )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/a" ] )

		s2["mode"].setValue( s2.Mode.Remove )
		self.assertEqual( s2["out"].set( "set" ).value.paths(), [ "/a" ] )

	def testMultipleNames( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Set()
		s["in"].setInput( p["out"] )

		s["paths"].setValue( IECore.StringVectorData( [ "/one", "/plane" ] ) )

		s["name"].setValue( "shinyThings dullThings" )

		self.assertEqual( set( list( s["out"]["setNames"].getValue() ) ), set( list( IECore.InternedStringVectorData( [ "shinyThings", "dullThings" ] ) ) ) )
		self.assertEqual( set( s["out"].set( "shinyThings" ).value.paths() ), set( [ "/one", "/plane" ] ) )
		self.assertEqual( set( s["out"].set( "dullThings" ).value.paths() ), set( [ "/one", "/plane" ] ) )

		s["paths"].setValue( IECore.StringVectorData( [ "/two", "/sphere" ] ) )

		self.assertEqual( set( list( s["out"]["setNames"].getValue() ) ), set( list( IECore.InternedStringVectorData( [ "shinyThings", "dullThings" ] ) ) ) )
		self.assertEqual( set( s["out"].set( "shinyThings" ).value.paths() ), set( [ "/two", "/sphere" ] ) )
		self.assertEqual( set( s["out"].set( "dullThings" ).value.paths() ), set( [ "/two", "/sphere" ] ) )

	def testFilter( self ) :

		p = GafferScene.Plane()
		g = GafferScene.Group()
		for i in range( 0, 30 ) :
			g["in"][i].setInput( p["out"] )

		f = GafferScene.PathFilter()

		s = GafferScene.Set()
		s["in"].setInput( g["out"] )
		s["name"].setValue( "n" )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )
		expectedFilterDependentPlugs = {
			s["filter"],
			s["out"]["set"],
			s["out"],
			s["__filterResults"],
			s["__pathMatcher"],
		}

		s["filter"].setInput( f["out"] )
		self.assertEqual( set( [ c[0] for c in cs ] ), expectedFilterDependentPlugs )

		del cs[:]

		f["paths"].setValue( IECore.StringVectorData( [ "/group/plane*1" ] ) )
		self.assertEqual( set( [ c[0] for c in cs ] ), expectedFilterDependentPlugs )
		self.assertEqual( set( s["out"].set( "n" ).value.paths() ), set( [ "/group/plane1", "/group/plane11", "/group/plane21" ] ) )

		f["paths"].setValue( IECore.StringVectorData( [ "/group/plane*2" ] ) )
		self.assertEqual( set( s["out"].set( "n" ).value.paths() ), set( [ "/group/plane2", "/group/plane12", "/group/plane22" ] ) )

	def testFilterWithChangingInputScene( self ) :

		p = GafferScene.Plane()
		g = GafferScene.Group()
		g["in"][0].setInput( p["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/group/plain" ] ) )

		s = GafferScene.Set()
		s["in"].setInput( g["out"] )
		s["filter"].setInput( f["out"] )

		self.assertEqual( s["out"].set( "set" ).value, IECore.PathMatcher() )

		p["name"].setValue( "plain" )
		self.assertEqual( s["out"].set( "set" ).value, IECore.PathMatcher( [ "/group/plain" ] ) )

	def testSetNamesDirtyPropagation( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Set()
		s["in"].setInput( p["out"] )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		p["sets"].setValue( "test" )
		self.assertTrue( s["out"]["setNames"] in { x[0] for x in cs } )

		del cs[:]

		s["mode"].setValue( s.Mode.Remove )
		self.assertTrue( s["out"]["setNames"] in { x[0] for x in cs } )

		del cs[:]

		s["name"].setValue( "test" )
		self.assertTrue( s["out"]["setNames"] in { x[0] for x in cs } )

		del cs[:]

		s["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		self.assertFalse( s["out"]["setNames"] in { x[0] for x in cs } )

	def testSetDirtyPropagation( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Set()
		s["in"].setInput( p["out"] )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )

		p["sets"].setValue( "test" )
		self.assertTrue( s["out"]["set"] in { x[0] for x in cs } )

		del cs[:]

		s["mode"].setValue( s.Mode.Remove )
		self.assertTrue( s["out"]["set"] in { x[0] for x in cs } )

		del cs[:]

		s["name"].setValue( "test" )
		self.assertTrue( s["out"]["set"] in { x[0] for x in cs } )

		del cs[:]

		s["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		self.assertTrue( s["out"]["set"] in { x[0] for x in cs } )

		del cs[:]

		s["enabled"].setValue( False )
		self.assertTrue( s["out"]["set"] in { x[0] for x in cs } )
		s["enabled"].setValue( True )

		del cs[:]

		f = GafferScene.PathFilter()
		s["filter"].setInput( f["out"] )
		self.assertTrue( s["out"]["set"] in { x[0] for x in cs } )

		del cs[:]

		f["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		self.assertTrue( s["out"]["set"] in { x[0] for x in cs } )

	def testRecursion( self ) :

		# Test the generation of a set from a SetFilter referencing
		# paths generated by an upstream set generated from a recursive
		# PathFilter. Naive implementations of locked compute can
		# deadlock here, so make sure our implementation isn't too
		# naive :)

		plane = GafferScene.Plane()

		collectScenes = GafferScene.CollectScenes()
		collectScenes["in"].setInput( plane["out"] )
		collectScenes["rootNames"].setValue(
			IECore.StringVectorData(
				[ str( x ) for x in range( 0, 10000 ) ]
			)
		)

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ "/.../plane" ] ) )

		setA = GafferScene.Set( "setA" )
		setA["in"].setInput( collectScenes["out"] )
		setA["filter"].setInput( pathFilter["out"] )
		setA["name"].setValue( "A" )

		setFilter = GafferScene.SetFilter()
		setFilter["setExpression"].setValue( "A - /0/plane" )

		setB = GafferScene.Set( "setB" )
		setB["in"].setInput( setA["out"] )
		setB["filter"].setInput( setFilter["out"] )
		setB["name"].setValue( "B" )

		with Gaffer.PerformanceMonitor() as pm :

			self.assertEqual(
				setB["out"].set( "B" ).value,
				IECore.PathMatcher(
					[ "/{}/plane".format( x ) for x in range( 1, 10000 ) ]
				)
			)

		self.assertEqual( pm.plugStatistics( setA["__FilterResults"]["__internalOut"] ).hashCount, 1 )
		self.assertEqual( pm.plugStatistics( setA["__FilterResults"]["__internalOut"] ).computeCount, 1 )

		self.assertEqual( pm.plugStatistics( setB["__FilterResults"]["__internalOut"] ).hashCount, 1 )
		self.assertEqual( pm.plugStatistics( setB["__FilterResults"]["__internalOut"] ).computeCount, 1 )

	def testFilterAndContextVariables( self ) :

		sphere = GafferScene.Sphere()
		sphere["name"].setValue( "${name}" )

		sphereFilter = GafferScene.PathFilter()
		sphereFilter["paths"].setValue( IECore.StringVectorData( [ "/sphere" ] ) )

		sphereSet = GafferScene.Set()
		sphereSet["in"].setInput( sphere["out"] )
		sphereSet["filter"].setInput( sphereFilter["out"] )

		expectedSet = IECore.PathMatcher( [ "/sphere" ] )

		# This exposed a ThreadState management problem triggered
		# by older versions of TBB.

		with Gaffer.Context() as c :

			c["name"] = "sphere"
			for i in range( 0, 10000 ) :

				Gaffer.ValuePlug.clearCache()
				self.assertEqual( sphereSet["out"].set( "set" ).value, expectedSet )

if __name__ == "__main__":
	unittest.main()
