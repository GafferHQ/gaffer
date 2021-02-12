##########################################################################
#
#  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
import GafferDispatch
import GafferScene
import GafferSceneTest

class FilterResultsTest( GafferSceneTest.SceneTestCase ) :

	def testChangingFilter( self ) :

		p = GafferScene.Plane()
		s = GafferScene.Sphere()
		g = GafferScene.Group()
		g["in"][0].setInput( p["out"] )
		g["in"][1].setInput( s["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/group/*" ] ) )

		n = GafferScene.FilterResults()
		n["scene"].setInput( g["out"] )
		n["filter"].setInput( f["out"] )

		self.assertEqual(
			n["out"].getValue().value,
			IECore.PathMatcher( [
				"/group/sphere",
				"/group/plane"
			] )
		)

		f["paths"].setValue( IECore.StringVectorData( [ "/group/p*" ] ) )

		self.assertEqual(
			n["out"].getValue().value,
			IECore.PathMatcher( [
				"/group/plane"
			] )
		)

	def testChangingScene( self ) :

		p = GafferScene.Plane()
		g = GafferScene.Group()
		g["in"][0].setInput( p["out"] )

		f = GafferScene.PathFilter()
		f["paths"].setValue( IECore.StringVectorData( [ "/group/plain" ] ) )

		n = GafferScene.FilterResults()
		n["scene"].setInput( g["out"] )
		n["filter"].setInput( f["out"] )

		self.assertEqual( n["out"].getValue().value, IECore.PathMatcher() )

		p["name"].setValue( "plain" )

		self.assertEqual(
			n["out"].getValue().value,
			IECore.PathMatcher( [
				"/group/plain"
			] )
		)

	def testDirtyPropagation( self ) :

		p = GafferScene.Plane()
		p["sets"].setValue( "A" )

		f = GafferScene.SetFilter()
		f["setExpression"].setValue( "A" )

		n = GafferScene.FilterResults()
		n["scene"].setInput( p["out"] )
		n["filter"].setInput( f["out"] )

		cs = GafferTest.CapturingSlot( n.plugDirtiedSignal() )

		f["setExpression"].setValue( "planeSet" )
		self.assertTrue( n["out"] in { x[0] for x in cs } )
		del cs[:]

		p["name"].setValue( "thing" )
		self.assertTrue( n["out"] in { x[0] for x in cs } )

	def testOutputIntoExpression( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["sphere"] = GafferScene.Sphere()

		script["instancer"] = GafferScene.Instancer()
		script["instancer"]["in"].setInput( script["plane"]["out"] )
		script["instancer"]["prototypes"].setInput( script["sphere"]["out"] )
		script["instancer"]["parent"].setValue( "/plane" )

		script["filter"] = GafferScene.PathFilter()
		script["filter"]["paths"].setValue( IECore.StringVectorData( [ "/plane/instances/sphere/*" ] ) )

		script["filterResults"] = GafferScene.FilterResults()
		script["filterResults"]["scene"].setInput( script["instancer"]["out"] )
		script["filterResults"]["filter"].setInput( script["filter"]["out"] )

		script["filterResults"]["user"]["strings"] = Gaffer.StringVectorDataPlug( defaultValue = IECore.StringVectorData() )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( "parent['filterResults']['user']['strings'] = IECore.StringVectorData( sorted( parent['filterResults']['out'].value.paths() ) )" )

		self.assertEqual(
			script["filterResults"]["user"]["strings"].getValue(),
			IECore.StringVectorData( [
				"/plane/instances/sphere/0",
				"/plane/instances/sphere/1",
				"/plane/instances/sphere/2",
				"/plane/instances/sphere/3",
			] )
		)

	def testComputeCacheRecursion( self ) :

		script = Gaffer.ScriptNode()

		script["plane"] = GafferScene.Plane()

		script["filter1"] = GafferScene.PathFilter()
		script["filter1"]["paths"].setValue( IECore.StringVectorData( [ "/*" ] ) )

		script["filterResults1"] = GafferScene.FilterResults()
		script["filterResults1"]["scene"].setInput( script["plane"]["out"] )
		script["filterResults1"]["filter"].setInput( script["filter1"]["out"] )

		script["filter2"] = GafferScene.PathFilter()
		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["filter2"]["paths"] = IECore.StringVectorData( parent["filterResults1"]["out"].value.paths() )')

		script["filterResults2"] = GafferScene.FilterResults()
		script["filterResults2"]["scene"].setInput( script["plane"]["out"] )
		script["filterResults2"]["filter"].setInput( script["filter2"]["out"] )

		h = script["filterResults2"]["out"].hash()
		Gaffer.ValuePlug.clearCache()
		script["filterResults2"]["out"].getValue( h )

	@unittest.skipIf( GafferTest.inCI(), "Performance not relevant on CI platform" )
	@GafferTest.TestRunner.PerformanceTestMethod()
	def testHashPerf( self ):

		sphere = GafferScene.Sphere()

		duplicate = GafferScene.Duplicate()
		duplicate["in"].setInput( sphere["out"] )
		duplicate["target"].setValue( '/sphere' )
		duplicate["copies"].setValue( 1000000 )

		pathFilter = GafferScene.PathFilter()
		pathFilter["paths"].setValue( IECore.StringVectorData( [ '...' ] ) )

		filterResults = GafferScene.FilterResults()
		filterResults["scene"].setInput( duplicate["out"] )
		filterResults["filter"].setInput( pathFilter["out"] )

		# Evaluate the root childNames beforehand to focus our timing on the hash
		duplicate["out"].childNames( "/" )

		with GafferTest.TestRunner.PerformanceScope():
			filterResults["out"].hash()



if __name__ == "__main__":
	unittest.main()
