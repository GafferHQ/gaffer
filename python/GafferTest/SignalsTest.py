##########################################################################
#
#  Copyright (c) 2011-2013, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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
import weakref
import sys
import six
import gc
import functools
import imath

import IECore

import Gaffer
import GafferTest

class SignalsTest( GafferTest.TestCase ) :

	def test( self ) :

		def f( a ) :

			return int( a )

		s = Gaffer.Signal1()
		c = s.connect( f )
		self.assertEqual( c.connected(), True )
		self.assertEqual( c.blocked(), False )

		self.assertEqual( s( 5.5 ), 5 )

		c.block()
		self.assertEqual( c.blocked(), True )
		c.unblock()
		self.assertEqual( c.blocked(), False )
		c.disconnect()
		self.assertEqual( c.connected(), False )

	def testDisconnectWhenSignalDies( self ) :

		def f( a ) :

			return int( a )

		s = Gaffer.Signal1()
		c = s.connect( f )
		self.assertTrue( c.connected() )
		del s
		self.assertFalse( c.connected() )

	def test2( self ) :

		def f( a, b ) :

			return a * b

		s = Gaffer.Signal2()
		c = s.connect( f )
		self.assertEqual( s( 2.0, 4.0 ), 8.0 )

	def testCircularRef( self ) :

		def default( a ) :

			return -1

		class A( imath.V3f ) :

			def __init__( self ) :

				imath.V3f.__init__( self )
				self.signal = Gaffer.Signal1()

			def f( self, n ) :

				return int( n * 2 )

		a1 = A()
		a2 = A()

		# connect a signal to always return a value of -1
		defaultConnection = a2.signal.connect( default )
		self.assertEqual( a2.signal( 2 ), -1 )

		# connect a method in
		a1.c = a2.signal.connect( Gaffer.WeakMethod( a1.f ) )
		self.assertEqual( a2.signal( 2 ), 4 )

		# connect a method of a2 to the signal on a1
		a2.c = a1.signal.connect( Gaffer.WeakMethod( a2.f ) )
		self.assertTrue( a2.c.connected() )

		self.assertEqual( a1.signal( 2 ), 4 )

		# we should be able to delete a1 and have it die
		# straight away, because the use of WeakMethods in
		# the connections should prevent any circular references.
		del a1
		self.assertEqual( a2.signal( 2 ), -1 )

		# as a1 is now dead, a2's connection to a1.signal
		# should have died.
		self.assertFalse( a2.c.connected() )

	def testDeletionOfConnectionDisconnects( self ) :

		def default( a ) :

			return -1

		def f( a ) :

			return int( a * 10 )

		s = Gaffer.Signal1()
		dc = s.connect( default )
		self.assertEqual( s( 1 ), -1 )

		c = s.connect( f )
		self.assertEqual( s( 1 ), 10 )

		del c
		self.assertEqual( s( 1 ), -1 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMany( self ) :

		class S( imath.V3f ) :

			instances = 0

			def __init__( self, parent ) :

				imath.V3f.__init__( self )

				S.instances += 1

				self.children = []
				self.numConnections = 0
				self.signal = Gaffer.Signal1()
				if parent :
					self.c = parent.signal.connect( self.f )
					parent.numConnections += 1
					parent.children.append( self )

			def f( self, a ) :

				r = 1
				if self.numConnections!=0 :
					r += self.signal( a )

				return r

		def build( parent, depth=0 ) :

			if( depth > 15 ) :
				return
			else :
				s1 = S( parent )
				s2 = S( parent )
				build( s1, depth + 1 )
				build( s2, depth + 1 )

		s = S( None )
		build( s )

		s.signal( 1 )

	## Check that Exceptions being thrown in callbacks don't cause additional references
	# to be created which would stop or delay collection. This tests a bug whereby the use
	# of PyErr_Print caused tracebacks to be stored in sys.last_traceback, which meant that
	# references to the T instance below were kept until another exception was thrown.
	def testExceptionRefCounting( self ) :

		class T( object ) :

			def __init__( self, s ) :

				# note the use of Gaffer.WeakMethod to avoid creating a circular reference
				# from self -> self.connection -> self.callback -> self. this is critical
				# when connecting methods of class to a signal.
				self.connection = s.childAddedSignal().connect( Gaffer.WeakMethod( self.callback ) )

			def callback( self, n, c ) :

				raise Exception

		s = Gaffer.Node()
		t = T( s )
		w = weakref.ref( t )

		realStdErr = sys.stderr
		sio = six.moves.cStringIO()
		try :
			sys.stderr = sio
			s.addChild( Gaffer.Node() )
		finally :
			sys.stderr = realStdErr

		del t

		self.assertIsNone( w(), None )
		self.assertIn( "Exception", sio.getvalue() )

	def test0Arity( self ) :

		def one() :

			return 1

		s = Gaffer.Signal0()

		c = s.connect( one )
		self.assertEqual( s(), 1 )

	def testGenericPythonSignals( self ) :

		def one() :
			return "one"

		def two() :
			return "two"

		s = Gaffer.Signal0()
		c1 = s.connect( one )
		c2 = s.connect( two )

		self.assertEqual( s(), "two" )

	def testGenericPythonSignalsWithCombiner( self ) :

		def myCombiner( slotResults ) :

			l = []
			for r in slotResults :
				l.append( r )

			return l

		def add( a, b ) :

			return a + b

		def mult( a, b ) :

			return a * b

		s = Gaffer.Signal2( myCombiner )
		addConnection = s.connect( add )
		multConnection = s.connect( mult )

		self.assertEqual( s( 2, 4 ), [ 6, 8 ] )

	def testPythonResultCombinersCanSkipSlots( self ) :

		def myCombiner( slotResults ) :

			for r in slotResults :
				if r :
					return r

			return False

		def slot1() :

			self.numCalls += 1
			return True

		def slot2() :

			self.numCalls += 1
			return False

		s = Gaffer.Signal0( myCombiner )
		c1 = s.connect( slot1 )
		c2 = s.connect( slot2 )

		self.numCalls = 0
		self.assertEqual( s(), True )
		self.assertEqual( self.numCalls, 1 )

	def testPythonResultCombinerCanHandleExceptions( self ) :

		def myCombiner( slotResults ) :

			results = []
			exceptions = []

			while True :

				try :
					results.append( next( slotResults ) )
				except StopIteration :
					return results, exceptions
				except Exception as e :
					exceptions.append( e )

		def badSlot() :

			raise RuntimeError()

		s = Gaffer.Signal0( myCombiner )
		s.connect( lambda : 10, scoped = False )
		s.connect( badSlot, scoped = False )
		s.connect( lambda : 20, scoped = False )

		results, exceptions = s()
		self.assertEqual( results, [ 10, 20 ] )
		self.assertEqual( len( exceptions ), 1 )
		self.assertIsInstance( exceptions[0], RuntimeError )

	def testConnectFront( self ) :

		values = []
		def f( value ) :

			values.append( value )

		s = Gaffer.Signal0()
		c1 = s.connect( functools.partial( f, "one" ) )
		c2 = s.connect( functools.partial( f, "two" ) )
		s()

		self.assertEqual( values, [ "one", "two" ] )

		del values[:]

		c1 = s.connect( functools.partial( f, "one" ) )
		c2 = s.connectFront( functools.partial( f, "two" ) )
		s()

		self.assertEqual( values, [ "two", "one" ] )

		del values[:]

		c1 = s.connectFront( functools.partial( f, "one" ) )
		c2 = s.connectFront( functools.partial( f, "two" ) )
		s()

		self.assertEqual( values, [ "two", "one" ] )

	def testSlotQueries( self ) :

		def f() :
			pass

		s = Gaffer.Signal0()
		self.assertTrue( s.empty() )
		self.assertEqual( s.numSlots(), 0 )

		c = s.connect( f )
		self.assertFalse( s.empty() )
		self.assertEqual( s.numSlots(), 1 )

		del c
		self.assertTrue( s.empty() )
		self.assertEqual( s.numSlots(), 0 )

	def testNonScopedConnection( self ) :

		self.numCalls = 0
		def f() :
			self.numCalls += 1

		s = Gaffer.Signal0()
		c = s.connect( f, scoped = False )

		self.assertEqual( self.numCalls, 0 )
		s()
		self.assertEqual( self.numCalls, 1 )

		c.block( True )
		s()
		self.assertEqual( self.numCalls, 1 )
		c.block( False )
		s()
		self.assertEqual( self.numCalls, 2 )

		# If we drop our reference to the slot,
		# it should still be alive because the
		# signal is referencing it (because it
		# is connected).
		w = weakref.ref( f )
		del f
		self.assertTrue( w() is not None )

		# And it should still be triggered when
		# we call the signal.
		s()
		self.assertEqual( self.numCalls, 3 )

		# And it should finally die when the
		# signal dies.
		del s
		self.assertTrue( w() is None )

	def testTrackable( self ) :

		class TrackableTest( Gaffer.Trackable ) :

			def f( self ) :

				pass

		s = Gaffer.Signal0()
		t = TrackableTest()
		w = weakref.ref( t )

		c = s.connect( Gaffer.WeakMethod( t.f ), scoped = False )

		self.assertTrue( c.connected() )
		del t
		self.assertIsNone( w() )
		self.assertFalse( c.connected() )

		s() # Would throw if an expired WeakMethod remained connected

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testConstructionPerformance( self ) :

		GafferTest.testSignalConstructionPerformance()

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testConnectionPerformance( self ) :

		GafferTest.testSignalConnectionPerformance()

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testCallPerformance( self ) :

		GafferTest.testSignalCallPerformance()

	def testQueryConnectionCopy( self ) :

		s = Gaffer.Signal0()

		c1 = s.connect( lambda : None )
		self.assertTrue( c1.connected() )
		c2 = Gaffer.Connection( c1 )
		self.assertTrue( c2.connected() )

		c1.disconnect()
		self.assertFalse( c1.connected() )
		self.assertFalse( c2.connected() )

	def testDisconnectFreesSlot( self ) :

		def f() :
			pass

		s = Gaffer.Signal0()
		c = s.connect( f, scoped = False )

		# If we drop our reference to the slot,
		# it should still be alive because the
		# signal is referencing it (because it
		# is connected).
		w = weakref.ref( f )
		del f
		self.assertIsNotNone( w() )

		# And when we disconnect, the reference
		# to the slot should be dropped, even if
		# a copy of the connection exists.
		c2 = Gaffer.Connection( c )
		c.disconnect()
		self.assertIsNone( w() )

	def testDisconnectFromSlot( self ) :

		signal = Gaffer.Signal1()
		connection = None
		slotCalls = []

		def slot( arg ) :
			slotCalls.append( arg )
			self.assertEqual( signal.numSlots(), 1 )
			connection.disconnect()
			self.assertEqual( signal.numSlots(), 0 )

		connection = signal.connect( slot, scoped = False )

		signal( 1 )
		self.assertEqual( slotCalls, [ 1 ] )
		signal( 2 )
		self.assertEqual( slotCalls, [ 1 ] )

	def testDisconnectionOrder( self ) :

		s = Gaffer.Signal0()
		c1 = s.connect( lambda : None )
		c2 = s.connect( lambda : None )

		c1.disconnect()
		c2.disconnect()

	def testCallEmptySignal( self ) :

		s = Gaffer.Signal0()
		self.assertEqual( s(), None )

		c = s.connect( lambda : 10 )
		self.assertEqual( s(), 10 )

		c.disconnect()
		self.assertEqual( s(), None )

	def testDisconnectAllSlots( self ) :

		s = Gaffer.Signal0()
		self.assertTrue( s.empty() )

		capturingSlots = [
			GafferTest.CapturingSlot( s )
			for i in range( 0, 10 )
		]
		self.assertEqual( s.numSlots(), 10 )
		self.assertFalse( s.empty() )

		s.disconnectAllSlots()
		self.assertEqual( s.numSlots(), 0 )
		self.assertTrue( s.empty() )

		s()
		self.assertFalse( any( len( cs ) for cs in capturingSlots ) )

	def testSlotReferencingConnection( self ) :

		signal = Gaffer.Signal0()

		# Make a slot that holds a ScopedConnection for the connection
		# to itself. This is actually a fairly common pattern, used by
		# classes to manage connections to their methods.

		slot = lambda : None
		connection = signal.connect( slot, scoped = False )
		slot.connection = Gaffer.ScopedConnection( connection )

		# Now, disconnect the connection, which should release the slot.
		# Releasing the slot will release the ScopedConnection, which in
		# turn will call `disconnect()`, while the first call to `disconnect()`
		# _is still running_.

		del slot
		connection.disconnect()

		# If we've got here, we haven't crashed, and all is well :)

		self.assertFalse( connection.connected() )

	def testDisconnectMatchingLambda( self ) :

		GafferTest.testSignalDisconnectMatchingLambda()

	def testDisconnectMatchingBind( self ) :

		GafferTest.testSignalDisconnectMatchingBind()

	def testSelfDisconnectingSlot( self ) :

		GafferTest.testSignalSelfDisconnectingSlot()

if __name__ == "__main__":
	unittest.main()
