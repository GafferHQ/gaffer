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

			self.failUnless( context.isSame( c ) )
			changes.append( ( name, context[name] ) )

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

	def testTypes( self ) :

		c = Gaffer.Context()

		c["int"] = 1
		self.assertEqual( c["int"], 1 )
		self.assertEqual( c.get( "int" ), 1 )
		c.set( "int", 2 )
		self.assertEqual( c["int"], 2 )
		self.failUnless( isinstance( c["int"], int ) )

		c["float"] = 1.0
		self.assertEqual( c["float"], 1.0 )
		self.assertEqual( c.get( "float" ), 1.0 )
		c.set( "float", 2.0 )
		self.assertEqual( c["float"], 2.0 )
		self.failUnless( isinstance( c["float"], float ) )

		c["string"] = "hi"
		self.assertEqual( c["string"], "hi" )
		self.assertEqual( c.get( "string" ), "hi" )
		c.set( "string", "bye" )
		self.assertEqual( c["string"], "bye" )
		self.failUnless( isinstance( c["string"], basestring ) )

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
		self.failIf( c != c2 )

		c["somethingElse"] = 1

		self.assertNotEqual( c, c2 )
		self.failIf( c == c2 )

	def testCurrent( self ) :

		# if nothing has been made current then there should be a default
		# constructed context in place.
		c = Gaffer.Context.current()
		c2 = Gaffer.Context()
		self.assertEqual( c, c2 )

		# and we should be able to change that using the with statement
		c2["something"] = 1
		with c2 :

			self.failUnless( Gaffer.Context.current().isSame( c2 ) )
			self.assertEqual( Gaffer.Context.current()["something"], 1 )

		# and bounce back to the original
		self.failUnless( Gaffer.Context.current().isSame( c ) )

	def testCurrentIsThreadSpecific( self ) :

		c = Gaffer.Context()
		self.failIf( c.isSame( Gaffer.Context.current() ) )

		def f() :

			self.failIf( c.isSame( Gaffer.Context.current() ) )
			with Gaffer.Context() :
				pass

		with c :

			self.failUnless( c.isSame( Gaffer.Context.current() ) )
			t = threading.Thread( target = f )
			t.start()
			t.join()
			self.failUnless( c.isSame( Gaffer.Context.current() ) )

		self.failIf( c.isSame( Gaffer.Context.current() ) )

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
		self.failIf( c.get( "v" ).isSame( v ) )

		self.assertEqual( c["v"], v )
		self.failIf( c["v"].isSame( v ) )

	def testGetWithDefault( self ) :

		c = Gaffer.Context()
		self.assertRaises( RuntimeError, c.get, "f" )
		self.assertEqual( c.get( "f", 10 ), 10 )
		c["f"] = 1.0
		self.assertEqual( c.get( "f" ), 1.0 )

	def testReentrancy( self ) :

		c = Gaffer.Context()
		with c :
			self.failUnless( c.isSame( Gaffer.Context.current() ) )
			with c :
				self.failUnless( c.isSame( Gaffer.Context.current() ) )

	def testLifeTime( self ) :

		c = Gaffer.Context()
		w = weakref.ref( c )

		self.failUnless( w() is c )

		with c :
			pass

		del c

		self.failUnless( w() is None )

	def testWithBlockReturnValue( self ) :

		with Gaffer.Context() as c :
			self.failUnless( isinstance( c, Gaffer.Context ) )
			self.failUnless( c.isSame( Gaffer.Context.current() ) )

	def testSubstitute( self ) :

		c = Gaffer.Context()
		c.setFrame( 20 )
		c["a"] = "apple"
		c["b"] = "bear"

		self.assertEqual( c.substitute( "$a/$b/something.###.tif" ), "apple/bear/something.020.tif" )
		self.assertEqual( c.substitute( "$a/$dontExist/something.###.tif" ), "apple//something.020.tif" )
		self.assertEqual( c.substitute( "${badlyFormed" ), "" )

	def testHasSubstitutions( self ) :

		c = Gaffer.Context()
		self.assertFalse( c.hasSubstitutions( "a" ) )
		self.assertTrue( c.hasSubstitutions( "~something" ) )
		self.assertTrue( c.hasSubstitutions( "$a" ) )
		self.assertTrue( c.hasSubstitutions( "${a}" ) )
		self.assertTrue( c.hasSubstitutions( "###" ) )

	def testNames( self ) :

		c = Gaffer.Context()
		self.assertEqual( set( c.names() ), set( [ "frame" ] ) )

		c["a"] = 10
		self.assertEqual( set( c.names() ), set( [ "frame", "a" ] ) )

		cc = Gaffer.Context( c )
		self.assertEqual( set( cc.names() ), set( [ "frame", "a" ] ) )

		cc["b"] = 20
		self.assertEqual( set( cc.names() ), set( [ "frame", "a", "b" ] ) )
		self.assertEqual( set( c.names() ), set( [ "frame", "a" ] ) )

		self.assertEqual( cc.names(), cc.keys() )

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

	def testManySubstitutions( self ) :

		GafferTest.testManySubstitutions()

	def testEscapedSubstitutions( self ) :

		c = Gaffer.Context()
		c.setFrame( 20 )
		c["a"] = "apple"
		c["b"] = "bear"

		self.assertEqual( c.substitute( "\${a}.\$b" ), "${a}.$b" )
		self.assertEqual( c.substitute( "\~" ), "~" )
		self.assertEqual( c.substitute( "\#\#\#\#" ), "####" )
		# really we're passing \\ to substitute and getting back \ -
		# the extra slashes are escaping for the python interpreter.
		self.assertEqual( c.substitute( "\\\\" ), "\\" )
		self.assertEqual( c.substitute( "\\" ), "" )

		self.assertTrue( c.hasSubstitutions( "\\" ) ) # must return true, because escaping affects substitution
		self.assertTrue( c.hasSubstitutions( "\\\\" ) ) # must return true, because escaping affects substitution
	
	def testRemove( self ) :
	
		c = Gaffer.Context()
		c["a"] = "apple"
		c["b"] = "bear"
		c["c"] = "cat"
		
		h = c.hash()
		self.assertEqual( set( c.names() ), set( [ "a", "b", "c", "frame" ] ) )
		
		# test Context.remove()
		c.remove( "a" )
		self.assertNotEqual( c.hash(), h )
		self.assertEqual( set( c.names() ), set( [ "b", "c", "frame" ] ) )
		h = c.hash()
		
		# test Context.__delitem__()
		del c[ "c" ]
		self.assertNotEqual( c.hash(), h )
		self.assertEqual( set( c.names() ), set( [ "b", "frame" ] ) )
		
		self.assertEqual( c["b"], "bear" )
		
		
if __name__ == "__main__":
	unittest.main()

