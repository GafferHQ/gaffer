##########################################################################
#  
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

import StringIO
import unittest
import weakref
import sys
import gc

import IECore

import Gaffer

class SignalsTest( unittest.TestCase ) :

	def test( self ) :
	
		def f( a ) :
		
			return int( a )
	
		s = Gaffer.Signal1()
		c = s.connect( f )
		self.assertEqual( c.blocked(), False )
		self.assertEqual( c.connected(), True )
		self.assert_( c.slot is f )
		
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
		self.assert_( c.connected() )
		del s
		self.assert_( not c.connected() )
		
	def test2( self ) :
	
		def f( a, b ) :
		
			return a * b
	
		s = Gaffer.Signal2()
		c = s.connect( f )
		self.assertEqual( s( 2.0, 4.0 ), 8.0 )
	
	def testCircularRef( self ) :
	
		def default( a ) :
		
			return -1
	
		class A( IECore.V3f ) :
		
			def __init__( self ) :
			
				IECore.V3f.__init__( self )
				self.signal = Gaffer.Signal1()
				
			def f( self, n ) :
				
				return int( n * 2 )
				
		a1 = A()
		a2 = A()
		
		# connect a signal to always return a value of -1
		defaultConnection = a2.signal.connect( default )
		self.assertEqual( a2.signal( 2 ), -1 )
		
		# connect a method in
		a1.c = a2.signal.connect( a1.f )
		self.assertEqual( a2.signal( 2 ), 4 )
		
		# connect a method of a2 to the signal on a1
		a2.c = a1.signal.connect( a2.f )
		self.assert_( a2.c.connected() )
		
		#self.assert_( a1.signal( 2 ), 4 )
		
		# just deleting a1 won't destroy it yet, as it has a
		# circular reference (a1.connection holds a1.f which
		# holds a1 which holds a1.connection)
		del a1
		self.assertEqual( a2.signal( 2 ), 4 )
		# running the garbage collector will destroy a1
		# and remove the signal
		gc.collect()
		self.assertEqual( a2.signal( 2 ), -1 )
		
		# as a1 is now dead, a2's connection to a1.signal
		# should have died.
		self.assert_( not a2.c.connected() )
			
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

	def testMany( self ) :
	
		class S( IECore.V3f ) :
		
			instances = 0
		
			def __init__( self, parent ) :
			
				IECore.V3f.__init__( self )
			
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
			
		class T :
		
			def __init__( self, s ) :
			
				self.connection = s.memberAddedSignal().connect( self.callback )
				
			def callback( self, s, n ) :
			
				raise Exception
	
		s = Gaffer.StandardSet()
		t = T( s )
		w = weakref.ref( t )
		
		realStdErr = sys.stderr
		sio = StringIO.StringIO()
		try :
			sys.stderr = sio
			s.add( Gaffer.Node() )
		finally :
			sys.stderr = realStdErr
			
		del t
		while gc.collect() :
			pass
			
		self.assert_( w() is None )
		self.assert_( "Exception" in sio.getvalue() )
		
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
			
if __name__ == "__main__":
	unittest.main()
	
