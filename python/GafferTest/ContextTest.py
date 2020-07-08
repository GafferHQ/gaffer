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
			changes.append( ( name, context.get( name, None ) ) )

		cn = c.changedSignal().connect( f )

		c["a"] = 2
		self.assertEqual( changes, [ ( "a", 2 ) ] )

		c["a"] = 3
		self.assertEqual( changes, [ ( "a", 2 ), ( "a", 3 ) ] )

		c["b"] = 1
		self.assertEqual( changes, [ ( "a", 2 ), ( "a", 3 ), ( "b", 1 ) ] )

		# when an assignment makes no actual change, the signal should not
		# be triggered again.
		c["b"] = 1
		self.assertEqual( changes, [ ( "a", 2 ), ( "a", 3 ), ( "b", 1 ) ] )

		# Removing variables should also trigger the changed signal.

		del changes[:]

		c.remove( "a" )
		self.assertEqual( changes, [ ( "a", None ) ] )

		del c["b"]
		self.assertEqual( changes, [ ( "a", None ), ( "b", None ) ] )

	def testTypes( self ) :

		c = Gaffer.Context()

		c["int"] = 1
		self.assertEqual( c["int"], 1 )
		self.assertEqual( c.get( "int" ), 1 )
		c.set( "int", 2 )
		self.assertEqual( c["int"], 2 )
		self.assertIsInstance( c["int"], int )

		c["float"] = 1.0
		self.assertEqual( c["float"], 1.0 )
		self.assertEqual( c.get( "float" ), 1.0 )
		c.set( "float", 2.0 )
		self.assertEqual( c["float"], 2.0 )
		self.assertIsInstance( c["float"], float )

		c["string"] = "hi"
		self.assertEqual( c["string"], "hi" )
		self.assertEqual( c.get( "string" ), "hi" )
		c.set( "string", "bye" )
		self.assertEqual( c["string"], "bye" )
		self.assertIsInstance( c["string"], str )

		c["v2i"] = imath.V2i( 1, 2 )
		self.assertEqual( c["v2i"], imath.V2i( 1, 2 ) )
		self.assertEqual( c.get( "v2i" ), imath.V2i( 1, 2 ) )
		c.set( "v2i", imath.V2i( 1, 2 ) )
		self.assertEqual( c["v2i"], imath.V2i( 1, 2 ) )
		self.assertIsInstance( c["v2i"], imath.V2i )

		c["v3i"] = imath.V3i( 1, 2, 3 )
		self.assertEqual( c["v3i"], imath.V3i( 1, 2, 3 ) )
		self.assertEqual( c.get( "v3i" ), imath.V3i( 1, 2, 3 ) )
		c.set( "v3i", imath.V3i( 1, 2, 3 ) )
		self.assertEqual( c["v3i"], imath.V3i( 1, 2, 3 ) )
		self.assertIsInstance( c["v3i"], imath.V3i )

		c["v2f"] = imath.V2f( 1, 2 )
		self.assertEqual( c["v2f"], imath.V2f( 1, 2 ) )
		self.assertEqual( c.get( "v2f" ), imath.V2f( 1, 2 ) )
		c.set( "v2f", imath.V2f( 1, 2 ) )
		self.assertEqual( c["v2f"], imath.V2f( 1, 2 ) )
		self.assertIsInstance( c["v2f"], imath.V2f )

		c["v3f"] = imath.V3f( 1, 2, 3 )
		self.assertEqual( c["v3f"], imath.V3f( 1, 2, 3 ) )
		self.assertEqual( c.get( "v3f" ), imath.V3f( 1, 2, 3 ) )
		c.set( "v3f", imath.V3f( 1, 2, 3 ) )
		self.assertEqual( c["v3f"], imath.V3f( 1, 2, 3 ) )
		self.assertIsInstance( c["v3f"], imath.V3f )

	def testCopying( self ) :

		c = Gaffer.Context()
		c["i"] = 10

		c2 = Gaffer.Context( c )
		self.assertEqual( c2["i"], 10 )

		c["i"] = 1
		self.assertEqual( c["i"], 1 )
		self.assertEqual( c2["i"], 10 )

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

	def testGetWithAndWithoutCopying( self ) :

		c = Gaffer.Context()
		c["test"] = IECore.IntVectorData( [ 1, 2 ] )

		# we should be getting a copy each time by default
		self.assertFalse( c["test"].isSame( c["test"] ) )
		# meaning that if we modify the returned value, no harm is done
		c["test"].append( 10 )
		self.assertEqual( c["test"], IECore.IntVectorData( [ 1, 2 ] ) )

		# if we ask nicely, we can get a reference to the internal
		# value without any copying.
		self.assertTrue( c.get( "test", _copy=False ).isSame( c.get( "test", _copy=False ) ) )
		# but then if we modify the returned value, we are changing the
		# context itself too. this should be avoided - we're just doing it
		# here to test that we are indeed referencing the internal value.
		c.get( "test", _copy=False ).append( 10 )
		self.assertEqual( c["test"], IECore.IntVectorData( [ 1, 2, 10 ] ) )

	def testGetWithDefaultAndCopyArgs( self ) :

		c = Gaffer.Context()
		c["test"] = IECore.IntVectorData( [ 1, 2 ] )

		self.assertTrue( c.get( "test", 10, _copy=False ).isSame( c.get( "test", 20, _copy=False ) ) )
		self.assertTrue( c.get( "test", defaultValue=10, _copy=False ).isSame( c.get( "test", defaultValue=20, _copy=False ) ) )

	def testCopyWithSharedOwnership( self ) :

		c1 = Gaffer.Context()

		c1["testInt"] = 10
		c1["testIntVector"] = IECore.IntVectorData( [ 10 ] )

		self.assertEqual( c1["testInt"], 10 )
		self.assertEqual( c1["testIntVector"], IECore.IntVectorData( [ 10 ] ) )

		r = c1.get( "testIntVector", _copy=False ).refCount()

		c2 = Gaffer.Context( c1, ownership = Gaffer.Context.Ownership.Shared )

		self.assertEqual( c2["testInt"], 10 )
		self.assertEqual( c2["testIntVector"], IECore.IntVectorData( [ 10 ] ) )

		c1["testInt"] = 20
		self.assertEqual( c1["testInt"], 20 )
		# c2 has changed too! with slightly improved performance comes
		# great responsibility!
		self.assertEqual( c2["testInt"], 20 )

		# both contexts reference the same object, but c2 at least owns
		# a reference to its values, and can be used after c1 has been
		# deleted.
		self.assertTrue( c2.get( "testIntVector", _copy=False ).isSame( c1.get( "testIntVector", _copy=False ) ) )
		self.assertEqual( c2.get( "testIntVector", _copy=False ).refCount(), r + 1 )

		del c1

		self.assertEqual( c2["testInt"], 20 )
		self.assertEqual( c2["testIntVector"], IECore.IntVectorData( [ 10 ] ) )
		self.assertEqual( c2.get( "testIntVector", _copy=False ).refCount(), r )

	def testCopyWithBorrowedOwnership( self ) :

		c1 = Gaffer.Context()

		c1["testInt"] = 10
		c1["testIntVector"] = IECore.IntVectorData( [ 10 ] )

		self.assertEqual( c1["testInt"], 10 )
		self.assertEqual( c1["testIntVector"], IECore.IntVectorData( [ 10 ] ) )

		r = c1.get( "testIntVector", _copy=False ).refCount()

		c2 = Gaffer.Context( c1, ownership = Gaffer.Context.Ownership.Borrowed )

		self.assertEqual( c2["testInt"], 10 )
		self.assertEqual( c2["testIntVector"], IECore.IntVectorData( [ 10 ] ) )

		c1["testInt"] = 20
		self.assertEqual( c1["testInt"], 20 )
		# c2 has changed too! with slightly improved performance comes
		# great responsibility!
		self.assertEqual( c2["testInt"], 20 )

		# check that c2 doesn't own a reference
		self.assertTrue( c2.get( "testIntVector", _copy=False ).isSame( c1.get( "testIntVector", _copy=False ) ) )
		self.assertEqual( c2.get( "testIntVector", _copy=False ).refCount(), r )

		# make sure we delete c2 before we delete c1
		del c2

		# check that we're ok to access c1 after deleting c2
		self.assertEqual( c1["testInt"], 20 )
		self.assertEqual( c1["testIntVector"], IECore.IntVectorData( [ 10 ] ) )

	def testSetOnBorrowedContextsDoesntAffectOriginal( self ) :

		c1 = Gaffer.Context()

		c1["testInt"] = 10
		c1["testIntVector"] = IECore.IntVectorData( [ 10 ] )

		c2 = Gaffer.Context( c1, ownership = Gaffer.Context.Ownership.Borrowed )
		c2["testInt"] = 20
		c2["testIntVector"] = IECore.IntVectorData( [ 20 ] )

		self.assertEqual( c1["testInt"], 10 )
		self.assertEqual( c1["testIntVector"], IECore.IntVectorData( [ 10 ] ) )

		self.assertEqual( c2["testInt"], 20 )
		self.assertEqual( c2["testIntVector"], IECore.IntVectorData( [ 20 ] ) )

	def testSetOnSharedContextsDoesntAffectOriginal( self ) :

		c1 = Gaffer.Context()

		c1["testInt"] = 10
		c1["testIntVector"] = IECore.IntVectorData( [ 10 ] )

		c2 = Gaffer.Context( c1, ownership = Gaffer.Context.Ownership.Shared )
		c2["testInt"] = 20
		c2["testIntVector"] = IECore.IntVectorData( [ 20 ] )

		self.assertEqual( c1["testInt"], 10 )
		self.assertEqual( c1["testIntVector"], IECore.IntVectorData( [ 10 ] ) )

		self.assertEqual( c2["testInt"], 20 )
		self.assertEqual( c2["testIntVector"], IECore.IntVectorData( [ 20 ] ) )

	def testSetOnSharedContextsReleasesReference( self ) :

		c1 = Gaffer.Context()
		c1["testIntVector"] = IECore.IntVectorData( [ 10 ] )

		r = c1.get( "testIntVector", _copy=False ).refCount()

		c2 = Gaffer.Context( c1, ownership = Gaffer.Context.Ownership.Shared )
		c2["testIntVector"] = IECore.IntVectorData( [ 20 ] )

		self.assertEqual( c1.get( "testIntVector", _copy=False ).refCount(), r )

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

	def testChanged( self ) :

		c = Gaffer.Context()
		c["test"] = IECore.StringVectorData( [ "one" ] )
		h = c.hash()

		cs = GafferTest.CapturingSlot( c.changedSignal() )

		d = c.get( "test", _copy = False ) # dangerous! the context won't know if we make changes
		d.append( "two" )
		self.assertEqual( c.get( "test" ), IECore.StringVectorData( [ "one", "two" ] ) )
		self.assertEqual( len( cs ), 0 )

		c.changed( "test" ) # let the context know what we've been up to
		self.assertEqual( len( cs ), 1 )
		self.assertEqual( cs[0], ( c, "test" ) )
		self.assertNotEqual( c.hash(), h )

	def testHashIgnoresUIEntries( self ) :

		c = Gaffer.Context()
		h = c.hash()

		c["ui:test"] = 1
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

if __name__ == "__main__":
	unittest.main()
