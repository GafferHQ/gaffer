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
import threading
import weakref
import imath

import IECore

import Gaffer
import GafferTest

class ContextTest( GafferTest.TestCase ) :

	def testFrameAccess( self ) :

		c = Gaffer.Context()

		self.assertEqual( c.getFrame(), 1.0 )
		self.assertEqual( c["frame"], 1.0 )

		c.setFrame( 10.5 )
		self.assertEqual( c.getFrame(), 10.5 )
		self.assertEqual( c["frame"], 10.5 )

	def testChangedSignal( self ) :

		c = Gaffer.Context()

		changes = []
		def f( context, name ) :

			self.assertTrue( context.isSame( c ) )
			changes.append( ( name, context.get( name, None ), context.hash() ) )

		cn = c.changedSignal().connect( f )

		c["a"] = 2
		hash1 = c.hash()
		self.assertEqual( changes, [ ( "a", 2, hash1 ) ] )

		c["a"] = 3
		hash2 = c.hash()
		self.assertEqual( changes, [ ( "a", 2, hash1 ), ( "a", 3, hash2 ) ] )

		c["b"] = 1
		hash3 = c.hash()
		self.assertEqual( changes, [ ( "a", 2, hash1 ), ( "a", 3, hash2 ), ( "b", 1, hash3 ) ] )

		# Assigning the same value again should not trigger the change signal
		c["b"] = 1
		self.assertEqual( changes, [ ( "a", 2, hash1 ), ( "a", 3, hash2 ), ( "b", 1, hash3 ) ] )

		# Removing variables should also trigger the changed signal.

		del changes[:]

		c.remove( "a" )
		hash4 = c.hash()
		self.assertEqual( changes, [ ( "a", None, hash4 ) ] )

		del c["b"]
		hash5 = c.hash()
		self.assertEqual( changes, [ ( "a", None, hash4 ), ( "b", None, hash5 ) ] )

	def testTypes( self ) :

		c = Gaffer.Context()

		c["int"] = 1
		self.assertEqual( c["int"], 1 )
		self.assertEqual( c.get( "int" ), 1 )
		compare = c.hash()
		c.set( "int", 2 )
		self.assertEqual( c["int"], 2 )
		self.assertIsInstance( c["int"], int )
		self.assertNotEqual( compare, c.hash() )

		c["float"] = 1.0
		self.assertEqual( c["float"], 1.0 )
		self.assertEqual( c.get( "float" ), 1.0 )
		compare = c.hash()
		c.set( "float", 2.0 )
		self.assertEqual( c["float"], 2.0 )
		self.assertIsInstance( c["float"], float )
		self.assertNotEqual( compare, c.hash() )

		c["string"] = "hi"
		self.assertEqual( c["string"], "hi" )
		self.assertEqual( c.get( "string" ), "hi" )
		compare = c.hash()
		c.set( "string", "bye" )
		self.assertEqual( c["string"], "bye" )
		self.assertIsInstance( c["string"], str )
		self.assertNotEqual( compare, c.hash() )

		c["v2i"] = imath.V2i( 1, 2 )
		self.assertEqual( c["v2i"], imath.V2i( 1, 2 ) )
		self.assertEqual( c.get( "v2i" ), imath.V2i( 1, 2 ) )
		compare = c.hash()
		c.set( "v2i", imath.V2i( 3, 4 ) )
		self.assertEqual( c["v2i"], imath.V2i( 3, 4 ) )
		self.assertIsInstance( c["v2i"], imath.V2i )
		self.assertNotEqual( compare, c.hash() )

		c["v3i"] = imath.V3i( 1, 2, 3 )
		self.assertEqual( c["v3i"], imath.V3i( 1, 2, 3 ) )
		self.assertEqual( c.get( "v3i" ), imath.V3i( 1, 2, 3 ) )
		compare = c.hash()
		c.set( "v3i", imath.V3i( 4, 5, 6 ) )
		self.assertEqual( c["v3i"], imath.V3i( 4, 5, 6 ) )
		self.assertIsInstance( c["v3i"], imath.V3i )
		self.assertNotEqual( compare, c.hash() )

		c["v2f"] = imath.V2f( 1, 2 )
		self.assertEqual( c["v2f"], imath.V2f( 1, 2 ) )
		self.assertEqual( c.get( "v2f" ), imath.V2f( 1, 2 ) )
		compare = c.hash()
		c.set( "v2f", imath.V2f( 3, 4 ) )
		self.assertEqual( c["v2f"], imath.V2f( 3, 4 ) )
		self.assertIsInstance( c["v2f"], imath.V2f )
		self.assertNotEqual( compare, c.hash() )

		c["v3f"] = imath.V3f( 1, 2, 3 )
		self.assertEqual( c["v3f"], imath.V3f( 1, 2, 3 ) )
		self.assertEqual( c.get( "v3f" ), imath.V3f( 1, 2, 3 ) )
		compare = c.hash()
		c.set( "v3f", imath.V3f( 4, 5, 6 ) )
		self.assertEqual( c["v3f"], imath.V3f( 4, 5, 6 ) )
		self.assertIsInstance( c["v3f"], imath.V3f )
		self.assertNotEqual( compare, c.hash() )

	def testSwitchTypes( self ) :

		c = Gaffer.Context()

		c["x"] = 1
		self.assertEqual( c["x"], 1 )
		self.assertEqual( c.get( "x" ), 1 )
		c.set( "x", 2 )
		self.assertEqual( c["x"], 2 )
		self.assertIsInstance( c["x"], int )

		c["x"] = 1.0
		self.assertEqual( c["x"], 1.0 )
		self.assertEqual( c.get( "x" ), 1.0 )
		c.set( "x", 2.0 )
		self.assertEqual( c["x"], 2.0 )
		self.assertIsInstance( c["x"], float )

		c["x"] = "hi"
		self.assertEqual( c["x"], "hi" )
		self.assertEqual( c.get( "x" ), "hi" )
		c.set( "x", "bye" )
		self.assertEqual( c["x"], "bye" )
		self.assertIsInstance( c["x"], str )

		c["x"] = imath.V2i( 1, 2 )
		self.assertEqual( c["x"], imath.V2i( 1, 2 ) )
		self.assertEqual( c.get( "x" ), imath.V2i( 1, 2 ) )
		c.set( "x", imath.V2i( 1, 2 ) )
		self.assertEqual( c["x"], imath.V2i( 1, 2 ) )
		self.assertIsInstance( c["x"], imath.V2i )

		c["x"] = imath.V3i( 1, 2, 3 )
		self.assertEqual( c["x"], imath.V3i( 1, 2, 3 ) )
		self.assertEqual( c.get( "x" ), imath.V3i( 1, 2, 3 ) )
		c.set( "x", imath.V3i( 1, 2, 3 ) )
		self.assertEqual( c["x"], imath.V3i( 1, 2, 3 ) )
		self.assertIsInstance( c["x"], imath.V3i )

		c["x"] = imath.V2f( 1, 2 )
		self.assertEqual( c["x"], imath.V2f( 1, 2 ) )
		self.assertEqual( c.get( "x" ), imath.V2f( 1, 2 ) )
		c.set( "x", imath.V2f( 1, 2 ) )
		self.assertEqual( c["x"], imath.V2f( 1, 2 ) )
		self.assertIsInstance( c["x"], imath.V2f )

		c["x"] = imath.V3f( 1, 2, 3 )
		self.assertEqual( c["x"], imath.V3f( 1, 2, 3 ) )
		self.assertEqual( c.get( "x" ), imath.V3f( 1, 2, 3 ) )
		c.set( "x", imath.V3f( 1, 2, 3 ) )
		self.assertEqual( c["x"], imath.V3f( 1, 2, 3 ) )
		self.assertIsInstance( c["x"], imath.V3f )

	def testCopying( self ) :

		c = Gaffer.Context()
		c["i"] = 10
		c["testIntVector"] = IECore.IntVectorData( [ 10 ] )

		c2 = Gaffer.Context( c )
		self.assertEqual( c2["i"], 10 )
		self.assertEqual( c2["testIntVector"], IECore.IntVectorData( [ 10 ] ) )

		c["i"] = 1
		c2["testIntVector"] = IECore.IntVectorData( [ 20 ] )
		self.assertEqual( c["i"], 1 )
		self.assertEqual( c2["i"], 10 )
		self.assertEqual( c["testIntVector"], IECore.IntVectorData( [ 10 ] ) )
		self.assertEqual( c2["testIntVector"], IECore.IntVectorData( [ 20 ] ) )

	def testEquality( self ) :

		c = Gaffer.Context()
		c2 = Gaffer.Context()

		self.assertEqual( c, c2 )
		self.assertFalse( c != c2 )

		c["somethingElse"] = 1

		self.assertNotEqual( c, c2 )
		self.assertFalse( c == c2 )

	def testCurrent( self ) :

		# if nothing has been made current then there should be a default
		# constructed context in place.
		c = Gaffer.Context.current()
		c2 = Gaffer.Context()
		self.assertEqual( c, c2 )

		# and we should be able to change that using the with statement
		c2["something"] = 1
		with c2 :

			self.assertTrue( Gaffer.Context.current().isSame( c2 ) )
			self.assertEqual( Gaffer.Context.current()["something"], 1 )

		# and bounce back to the original
		self.assertTrue( Gaffer.Context.current().isSame( c ) )

	def testCurrentIsThreadSpecific( self ) :

		c = Gaffer.Context()
		self.assertFalse( c.isSame( Gaffer.Context.current() ) )

		def f() :

			self.assertFalse( c.isSame( Gaffer.Context.current() ) )
			with Gaffer.Context() :
				pass

		with c :

			self.assertTrue( c.isSame( Gaffer.Context.current() ) )
			t = threading.Thread( target = f )
			t.start()
			t.join()
			self.assertTrue( c.isSame( Gaffer.Context.current() ) )

		self.assertFalse( c.isSame( Gaffer.Context.current() ) )

	def testThreading( self ) :

		# for good measure, run testCurrent() in a load of threads at
		# the same time.

		threads = []
		for i in range( 0, 1000 ) :
			t = threading.Thread( target = self.testCurrent )
			t.start()
			threads.append( t )

		for t in threads :
			t.join()

	def testSetWithObject( self ) :

		c = Gaffer.Context()

		v = IECore.StringVectorData( [ "a", "b", "c" ] )
		c.set( "v", v )

		self.assertEqual( c.get( "v" ), v )
		self.assertFalse( c.get( "v" ).isSame( v ) )

		self.assertEqual( c["v"], v )
		self.assertFalse( c["v"].isSame( v ) )

	def testGetFallbackValue( self ) :

		c = Gaffer.Context()
		self.assertEqual( c.get( "f" ), None )
		self.assertEqual( c.get( "f", 10 ), 10 )
		c["f"] = 1.0
		self.assertEqual( c.get( "f" ), 1.0 )

	def testReentrancy( self ) :

		c = Gaffer.Context()
		with c :
			self.assertTrue( c.isSame( Gaffer.Context.current() ) )
			with c :
				self.assertTrue( c.isSame( Gaffer.Context.current() ) )

	def testLifeTime( self ) :

		c = Gaffer.Context()
		w = weakref.ref( c )

		self.assertTrue( w() is c )

		with c :
			pass

		del c

		self.assertIsNone( w() )

	def testWithBlockReturnValue( self ) :

		with Gaffer.Context() as c :
			self.assertIsInstance( c, Gaffer.Context )
			self.assertTrue( c.isSame( Gaffer.Context.current() ) )

	def testSubstitute( self ) :

		c = Gaffer.Context()
		c.setFrame( 20 )
		c["a"] = "apple"
		c["b"] = "bear"

		self.assertEqual( c.substitute( "$a/$b/something.###.tif" ), "apple/bear/something.020.tif" )
		self.assertEqual( c.substitute( "$a/$dontExist/something.###.tif" ), "apple//something.020.tif" )
		self.assertEqual( c.substitute( "${badlyFormed" ), "" )

	def testSubstituteTildeInMiddle( self ) :

		c = Gaffer.Context()
		self.assertEqual( c.substitute( "a~b" ), "a~b" )

	def testSubstituteWithMask( self ) :

		c = Gaffer.Context()
		c.setFrame( 20 )
		c["a"] = "apple"
		c["b"] = "bear"

		self.assertEqual( c.substitute( "~", IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.TildeSubstitutions ), "~" )
		self.assertEqual( c.substitute( "#", IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions ), "#" )
		self.assertEqual( c.substitute( "$a/${b}", IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.VariableSubstitutions ), "$a/${b}" )
		self.assertEqual( c.substitute( "\\", IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.EscapeSubstitutions ), "\\" )
		self.assertEqual( c.substitute( "\\$a", IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.EscapeSubstitutions ), "\\apple" )
		self.assertEqual( c.substitute( "#${a}", IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions ), "#apple" )
		self.assertEqual( c.substitute( "#${a}", IECore.StringAlgo.Substitutions.NoSubstitutions ), "#${a}" )

	def testFrameAndVariableSubstitutionsAreDifferent( self ) :

		c = Gaffer.Context()
		c.setFrame( 3 )

		# Turning off variable substitutions should have no effect on '#' substitutions.
		self.assertEqual( c.substitute( "###.$frame" ), "003.3" )
		self.assertEqual( c.substitute( "###.$frame", IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.VariableSubstitutions ), "003.$frame" )

		# Turning off '#' substitutions should have no effect on variable substitutions.
		self.assertEqual( c.substitute( "###.$frame" ), "003.3" )
		self.assertEqual( c.substitute( "###.$frame", IECore.StringAlgo.Substitutions.AllSubstitutions & ~IECore.StringAlgo.Substitutions.FrameSubstitutions ), "###.3" )

	def testInternedStringVectorDataSubstitutions( self ) :

		c = Gaffer.Context()
		c["test1"] = IECore.InternedStringVectorData( [ "a", "b" ] )
		c["test2"] = IECore.InternedStringVectorData()
		self.assertEqual( c.substitute( "${test1}" ), "/a/b" )
		self.assertEqual( c.substitute( "${test2}" ), "/" )

	def testNames( self ) :

		c = Gaffer.Context()
		self.assertEqual( set( c.names() ), set( [ "frame", "framesPerSecond" ] ) )

		c["a"] = 10
		self.assertEqual( set( c.names() ), set( [ "frame", "framesPerSecond", "a" ] ) )

		cc = Gaffer.Context( c )
		self.assertEqual( set( cc.names() ), set( [ "frame", "framesPerSecond", "a" ] ) )

		cc["b"] = 20
		self.assertEqual( set( cc.names() ), set( [ "frame", "framesPerSecond", "a", "b" ] ) )
		self.assertEqual( set( c.names() ), set( [ "frame", "framesPerSecond", "a" ] ) )

		self.assertEqual( cc.names(), cc.keys() )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testManyContexts( self ) :

		GafferTest.testManyContexts()

	def testGetCopies( self ) :

		c = Gaffer.Context()
		c["test"] = IECore.IntVectorData( [ 1, 2 ] )

		# we should be getting a copy each time by default
		self.assertFalse( c["test"].isSame( c["test"] ) )
		# meaning that if we modify the returned value, no harm is done
		c["test"].append( 10 )
		self.assertEqual( c["test"], IECore.IntVectorData( [ 1, 2 ] ) )

	def testGetWithDefault( self ) :

		c = Gaffer.Context()
		c["test"] = IECore.IntVectorData( [ 1, 2 ] )

		self.assertEqual( c.get( "test", 10 ), IECore.IntVectorData( [ 1, 2 ] ) )
		self.assertEqual( c.get( "testX", 10 ), 10 )

	def testHash( self ) :

		c = Gaffer.Context()
		hashes = [ c.hash() ]

		c["test"] = 1
		hashes.append( c.hash() )

		c["test"] = 2
		hashes.append( c.hash() )

		c["test2"] = "test2"
		hashes.append( c.hash() )

		self.assertEqual( len( hashes ), 4 )
		self.assertEqual( len( set( str( h ) for h in hashes ) ), len( hashes ) )

		c["test2"] = "test2" # no change
		self.assertEqual( c.hash(), hashes[-1] )

	def testHashIgnoresUIEntries( self ) :

		c = Gaffer.Context()
		h = c.hash()

		c["ui:test"] = 1
		self.assertEqual( h, c.hash() )

		del c["ui:test"]
		self.assertEqual( c.names(), Gaffer.Context().names() )
		self.assertEqual( h, c.hash() )

		c["ui:test"] = 1
		c["ui:test2"] = "foo"
		self.assertEqual( h, c.hash() )

		c.removeMatching( "ui:test*" )
		self.assertEqual( c.names(), Gaffer.Context().names() )
		self.assertEqual( h, c.hash() )


	@GafferTest.TestRunner.PerformanceTestMethod()
	def testManySubstitutions( self ) :

		GafferTest.testManySubstitutions()

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testManyEnvironmentSubstitutions( self ) :

		GafferTest.testManyEnvironmentSubstitutions()

	def testEscapedSubstitutions( self ) :

		c = Gaffer.Context()
		c.setFrame( 20 )
		c["a"] = "apple"
		c["b"] = "bear"

		self.assertEqual( c.substitute( r"\${a}.\$b" ), "${a}.$b" )
		self.assertEqual( c.substitute( r"\~" ), "~" )
		self.assertEqual( c.substitute( r"\#\#\#\#" ), "####" )
		# really we're passing \\ to substitute and getting back \ -
		# the extra slashes are escaping for the python interpreter.
		self.assertEqual( c.substitute( "\\\\" ), "\\" )
		self.assertEqual( c.substitute( "\\" ), "" )

	def testRemove( self ) :

		c = Gaffer.Context()
		c["a"] = "apple"
		c["b"] = "bear"
		c["c"] = "cat"

		h = c.hash()
		self.assertEqual( set( c.names() ), set( [ "a", "b", "c", "frame", "framesPerSecond" ] ) )

		# test Context.remove()
		c.remove( "a" )
		self.assertNotEqual( c.hash(), h )
		self.assertEqual( set( c.names() ), set( [ "b", "c", "frame", "framesPerSecond" ] ) )
		h = c.hash()

		# test Context.__delitem__()
		del c[ "c" ]
		self.assertNotEqual( c.hash(), h )
		self.assertEqual( set( c.names() ), set( [ "b", "frame", "framesPerSecond" ] ) )

		self.assertEqual( c["b"], "bear" )

	def testRemoveMatching( self ) :

		c = Gaffer.Context()
		c["a_1"] = "apple"
		c["a_2"] = "apple"
		c["b_1"] = "bear"
		c["b_2"] = "bear"
		c["c_1"] = "cat"
		c["c_2"] = "cat"

		h = c.hash()
		self.assertEqual( set( c.names() ), set( [ "a_1", "a_2", "b_1", "b_2", "c_1", "c_2", "frame", "framesPerSecond" ] ) )

		# test Context.removeMatching()
		c.removeMatching( "a* c*" )
		self.assertNotEqual( c.hash(), h )
		self.assertEqual( set( c.names() ), set( [ "b_1", "b_2", "frame", "framesPerSecond" ] ) )
		h = c.hash()


	def testContains( self ) :

		c = Gaffer.Context()
		self.assertFalse( "a" in c )
		self.assertTrue( "a" not in c )

		c["a"] = 1
		self.assertTrue( "a" in c )
		self.assertFalse( "a" not in c )

		del c["a"]
		self.assertFalse( "a" in c )
		self.assertTrue( "a" not in c )

	def testTime( self ) :

		c = Gaffer.Context()

		self.assertEqual( c.getFrame(), 1.0 )
		self.assertEqual( c.getFramesPerSecond(), 24.0 )
		self.assertAlmostEqual( c.getTime(), 1.0 / 24.0 )

		c.setFrame( 12.0 )
		self.assertEqual( c.getFrame(), 12.0 )
		self.assertEqual( c.getFramesPerSecond(), 24.0 )
		self.assertAlmostEqual( c.getTime(), 12.0 / 24.0 )

		c.setFramesPerSecond( 48.0 )
		self.assertEqual( c.getFrame(), 12.0 )
		self.assertEqual( c.getFramesPerSecond(), 48.0 )
		self.assertAlmostEqual( c.getTime(), 12.0 / 48.0 )

	def testEditableScope( self ) :

		GafferTest.testEditableScope()

	def testCanceller( self ) :

		c = Gaffer.Context()
		c["test"] = 1
		self.assertEqual( c.canceller(), None )

		canceller = IECore.Canceller()
		cc = Gaffer.Context( c, canceller )

		self.assertEqual( cc["test"], 1 )
		self.assertTrue( cc.canceller() is not None )

		canceller.cancel()
		with self.assertRaises( IECore.Cancelled ) :
			IECore.Canceller.check( cc.canceller() )

		contextCopy = Gaffer.Context( cc )
		self.assertTrue( contextCopy.canceller() is not None )
		with self.assertRaises( IECore.Cancelled ) :
			IECore.Canceller.check( cc.canceller() )

	def testCancellerLifetime( self ) :

		canceller = IECore.Canceller()
		context = Gaffer.Context( Gaffer.Context(), canceller )
		cancellerWeakRef = weakref.ref( canceller )

		del canceller
		self.assertIsNotNone( cancellerWeakRef() )

		del context
		self.assertIsNone( cancellerWeakRef() )

	def testOmitCanceller( self ) :

		context1 = Gaffer.Context( Gaffer.Context(), IECore.Canceller() )
		self.assertIsNotNone( context1.canceller() )

		context2 = Gaffer.Context( context1, omitCanceller = True )
		self.assertIsNone( context2.canceller() )

		context3 = Gaffer.Context( context1, omitCanceller = False )
		self.assertIsNotNone( context3.canceller() )

	def testVariableHash( self ) :

		context = Gaffer.Context()
		context["foo"] = 1
		context["bar"] = 1

		self.assertEqual( context.variableHash( "doesntExist" ), IECore.MurmurHash() )

		# Hash includes name, so the hash of different variables is different
		self.assertNotEqual( context.variableHash( "foo" ), context.variableHash( "bar" ) )

		initialHash = context.variableHash( "foo" )
		context["foo"] = 2
		self.assertNotEqual( context.variableHash( "foo" ), initialHash )

		# Hashing should include the type, so different types of 32bit zeros should compare different
		context["foo"] = 0
		zeroHash1 = context.variableHash( "foo" )
		context["foo"] = float(0)
		zeroHash2 = context.variableHash( "foo" )
		self.assertNotEqual( zeroHash1, zeroHash2 )

		# Check the intial value again
		context["foo"] = 1
		self.assertEqual( context.variableHash( "foo" ), initialHash )

		# With a single entry, the hash for the one variable is the same as the total hash of the context
		context.remove("bar")
		context.remove("framesPerSecond")
		context.remove("frame")
		self.assertEqual( context.variableHash( "foo" ), context.hash() )


	@staticmethod
	def collisionCountParallelHelper( seed, mode, countList ):
		r = GafferTest.countContextHash32Collisions( 2**20, mode, seed )
		for i in range(4):
			countList[i] = r[i]

	# TODO - add new test flag `gaffer test -type all|standard|performance|verySlow`, where "verySlow"
	# would enable tests like this
	@unittest.skipIf( True, "Too expensive to run currently" )
	def testContextHashCollisions( self ) :

		iters = 10
		# Test all 4 context creation modes ( see ContextTest.cpp for descriptions )
		for mode in [0,1,2,3]:
			# This would be much cleaner once we can use concurrent.futures
			import threading

			results = [ [0,0,0,0] for i in range( iters ) ]
			threads = []
			for i in range( iters ):
				x = threading.Thread( target=self.collisionCountParallelHelper, args=( i, mode, results[i] ) )
				x.start()
				threads.append( x )

			for x in threads:
				x.join()

			s = [0,0,0,0]
			for l in results:
				for i in range(4):
					s[i] += l[i]

			# countContextHash32Collisions return the number of collisions in each of four 32 bits chunks
			# of the hash independently - as long as as the uniformity of each chunk is good, the chance
			# of a full collision of all four chunks is extremely small.
			#
			# We test it with 2**20 entries.  We can approximate the number of expected 32 bit
			# collisions as a binomial distribution - the probability changes as entries are inserted, but
			# the average probability of a collision per item is when half the entries have been processed,
			# for a probability of `0.5 * 2**20 / 2**32 = 0.00012207`.  Using this probability, and N=2**20,
			# in a binomial distribution, yields a mean outcome of 128.0 collisions.
			# From: https://en.wikipedia.org/wiki/Birthday_problem, section "Collision Counting", the true
			# result is `2**20 - 2**32 + 2**32 * ( (2**32 - 1)/2**32 )**(2**20) = 127.989` .. close enough
			# to suggest our approximation works.  Based on our approximated binomial distribution then,
			# taking the number of iterations up to 10 * 2**20 for our sum over 10 trials, the sum should
			# have a mean of 1280, and be in the range [1170 .. 1390] 99.8% of the time.
			#
			# This means there is some chance of this test failing ( especially because this math is
			# approximate ), but it is too slow to run on CI anyway, and this test should provide some
			# assurance that our MurmurHash is performing extremely similarly to a theoretical ideal
			# uniformly distributed hash, even after a trick like summing the entry hashes.
			#
			# Because the bits of the hash are all evenly mixed, the rate of collisions should be identical
			# regardless of which 32bit chunk we test.
			#
			# One weird note for myself in the future: There is one weird pattern you will see if you
			# print s : If using 64bit sums of individual hashes, then the low 32 bit chunks
			# ( chunks 0 and 3 ) will always produce the same number of collisions in mode 0 and 1.
			# This is because most of the entries in mode 1 do not change, and the only source of variation
			# is the one entry which matches mode 0 ... but this is expected, and crucially, while the
			# number of collisions within mode 0 and mode 1 come out identical, this does not increase the
			# chances of a collision between contexts with one varying entry, and context with one varying
			# entry plus fixed entries ( mode 3 demonstrates this ).

			for i in range(4):
				self.assertLess( s[i], 1390.0 )
				self.assertGreater( s[i], 1170.0 )

	def testSetFrameSignalling( self ) :

		c = Gaffer.Context()
		cs = GafferTest.CapturingSlot( c.changedSignal() )

		c.setFrame( 10 )
		self.assertEqual( cs, [ ( c, "frame" ) ] )
		self.assertEqual( c.getFrame(), 10 )

		c.setFrame( 20 )
		self.assertEqual( cs, [ ( c, "frame" ) ] * 2 )
		self.assertEqual( c.getFrame(), 20 )

		c.setFrame( 20 )
		self.assertEqual( cs, [ ( c, "frame" ) ] * 2 )
		self.assertEqual( c.getFrame(), 20 )

		c.setFrame( 30 )
		self.assertEqual( cs, [ ( c, "frame" ) ] * 3 )
		self.assertEqual( c.getFrame(), 30 )

	@unittest.skipIf( not Gaffer.isDebug(), "Only valid for debug builds" )
	def testHashValidation( self ) :

		GafferTest.testContextHashValidation()

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testContextHashPerformance( self ) :

		GafferTest.testContextHashPerformance( 10, 10, False )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testContextHashPerformanceStartInitialized( self ) :

		GafferTest.testContextHashPerformance( 10, 10, True )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testContextCopyPerformance( self ) :

		GafferTest.testContextCopyPerformance( 10, 10 )

	def testCopyEditableScope( self ) :

		GafferTest.testCopyEditableScope()

	def testSubstituteInternedString( self ) :

		c = Gaffer.Context()
		c["test"] = IECore.InternedStringData( "value" )
		self.assertEqual( c.substitute( "${test}" ), "value" )

		c["test1"] = IECore.InternedStringData( "${test2}" )
		c["test2"] = IECore.InternedStringData( "recursion!" )
		self.assertEqual( c.substitute( "${test1}" ), "recursion!" )

if __name__ == "__main__":
	unittest.main()
