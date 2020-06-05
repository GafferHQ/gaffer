##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import Gaffer
import GafferTest

import IECore

from Gaffer.Private.IECorePreview import Message
from Gaffer.Private.IECorePreview import Messages
from Gaffer.Private.IECorePreview import MessagesData

class MessagesTest( GafferTest.TestCase ) :

	def testMessage( self ) :

		m = Message( IECore.MessageHandler.Level.Debug, "context", "message" )

		self.assertEqual( m.level, IECore.MessageHandler.Level.Debug )
		self.assertEqual( m.context, "context" )
		self.assertEqual( m.message, "message" )

		with self.assertRaises( AttributeError ) :
			m.level = IECore.MessageHandler.Level.Info
		with self.assertRaises( AttributeError ) :
			m.context = ""
		with self.assertRaises( AttributeError ) :
			m.message = ""

	def testData( self ) :

		m1 = Messages()
		m1d = MessagesData( m1 )
		self.assertEqual( repr(m1d), "Gaffer.Private.IECorePreview.MessagesData()" )

		m2d = m1d.copy()
		m2 = m2d.value
		m2.add( Message( IECore.MessageHandler.Level.Info, "testData", "message" ) )

		self.assertEqual( m1.size(), 0 )
		self.assertEqual( m2.size(), 1 )

		with self.assertRaises( IECore.Exception ) :
			repr(m2d)

	def testMessageEquality( self ) :

		m1  = Message( IECore.MessageHandler.Level.Debug, "context", "message" )
		m2  = Message( IECore.MessageHandler.Level.Debug, "context", "message" )
		m3  = Message( IECore.MessageHandler.Level.Info, "context", "message" )
		m4  = Message( IECore.MessageHandler.Level.Debug, "context2", "message" )
		m5  = Message( IECore.MessageHandler.Level.Debug, "context", "message2" )

		self.assertEqual( m1, m2 )
		self.assertNotEqual( m1, m3 )
		self.assertTrue( m1 == m2 )
		self.assertTrue( m1 != m3 )

	def testMessageHash( self ) :

		h = IECore.MurmurHash()

		h1 = IECore.MurmurHash()
		m1 = Message( IECore.MessageHandler.Level.Debug, "context", "message" )
		m1.hash( h1 )

		h2 = IECore.MurmurHash()
		m2 = Message( IECore.MessageHandler.Level.Info, "context", "message" )
		m2.hash( h2 )

		h3 = IECore.MurmurHash()
		m3 = Message( IECore.MessageHandler.Level.Debug, "", "message" )
		m3.hash( h3 )

		h4 = IECore.MurmurHash()
		m4 = Message( IECore.MessageHandler.Level.Debug, "context", "" )
		m4.hash( h4 )

		# Check hashes are unique
		hashes = [ h, h1, h2, h3, h4 ]
		self.assertEqual( len(set(hashes)), len(hashes) )

		# Check are stable
		h4b = IECore.MurmurHash()
		m4.hash( h4b )
		self.assertEqual( h4b, h4 )

		h5 = IECore.MurmurHash()
		m5 = Message( IECore.MessageHandler.Level.Debug, "context", "" )
		m5.hash( h5 )

		self.assertEqual( h4, h5 )

		# Test python hashing

		allMessages = [ m1, m2, m3, m4, m5 ]
		differentMsgs = [ m1, m2, m3, m4 ]

		self.assertEqual( len(set(allMessages)), len(differentMsgs) )

	def testMessages( self ) :

		m = Messages()
		self.assertEqual( m.size(), 0 )
		self.assertEqual( len(m), 0 )

		Level = IECore.MessageHandler.Level

		for l in ( Level.Error, Level.Warning, Level.Info, Level.Debug ) :
			self.assertEqual( m.count( l ), 0 )

		for i in range( 20 ) :
			m.add( Message( IECore.MessageHandler.Level( i % 4 ), "testMessages", str(i) ) )
			self.assertEqual( m.size(), i + 1 )

		self.assertEqual( len(m), m.size() )

		for i in range( 20 ) :
			self.assertEqual( m[i].level, IECore.MessageHandler.Level( i % 4 ) )
			self.assertEqual( m[i].context, "testMessages" )
			self.assertEqual( m[i].message, str(i) )

		m.clear()

		self.assertEqual( m.size(), 0 )

	def testIndexing( self ) :

		messages = (
			Message( IECore.MessageHandler.Level.Debug, "testIndexing", "message1" ),
			Message( IECore.MessageHandler.Level.Info, "testIndexing", "message2" ),
			Message( IECore.MessageHandler.Level.Warning, "testIndexing", "message3" ),
			Message( IECore.MessageHandler.Level.Error, "testIndexing", "message4" )
		)

		m = Messages()

		for msg in messages :
			m.add( msg )

		for i in range( len(messages) ) :
			self.assertEqual( m[i], messages[i] )
			if i > 0 :
				self.assertEqual( m[-i], messages[-i] )

		with self.assertRaises( IndexError ) :
			m[ len(m) ]

		with self.assertRaises( IndexError ) :
			m[ - ( len(m) + 1 ) ]

	def testMessagesCopy( self ) :

		m1 = Messages()
		for i in range( 11 ) :
			m1.add( Message( IECore.MessageHandler.Level( i % 4 ), "testMessagesCopy", str(i)  ) )

		m2 = m1
		m3 = Messages( m1 )

		self.assertEqual( m1, m2 )
		self.assertEqual( m1, m3 )
		self.assertEqual( m2, m3 )

		# Check copies are de-coupled

		m2.add( Message( IECore.MessageHandler.Level.Info, "testMessagesCopy", "message"  ) )

		self.assertEqual( m1, m2 )
		self.assertNotEqual( m2, m3 )

		m3.add( Message( IECore.MessageHandler.Level.Error, "testMessagesCopy", "message"  ) )

		self.assertEqual( m1, m2 )
		self.assertNotEqual( m2, m3 )

	def testMessagesEquality( self ) :

		messages = [
			Message( IECore.MessageHandler.Level( i % 4 ), "testMessagesEquality", str(i) )
			for i in range( 10 )
		]

		m1 = Messages()
		m2 = Messages()

		for msg in messages :
			m1.add( msg )
			m2.add( msg )

		self.assertEqual( m1, m2 )
		self.assertFalse( m1 != m2 )

		m1.clear()

		self.assertNotEqual( m1, m2 )
		self.assertTrue( m1 != m2 )

	def testMessagesHash( self ) :

		m1 = Messages()
		h = m1.hash()

		lastHash = h
		for i in range( 10 ) :
			m1.add( Message( IECore.MessageHandler.Level.Debug, "testMessagesHash", "" ) )
			newHash = m1.hash()
			self.assertNotEqual( newHash, lastHash )
			lastHash = newHash

		# check stable
		self.assertEqual( m1.hash(), lastHash )

		m2 = Messages( m1 )
		self.assertEqual( m2.hash(), m1.hash() )

		m3 = Messages()
		for i in range( 10 ) :
			m3.add( Message( IECore.MessageHandler.Level.Debug, "testMessagesHash", "" ) )

		self.assertEqual( len(set( ( m1, m2, m3 ) ) ), 1 )

		m1.clear()
		self.assertEqual( m1.hash(), h )
		self.assertNotEqual( m1.hash(), m2.hash() )

	def testMessagesCount( self ) :

		Level = IECore.MessageHandler.Level
		messageCounts = ( ( Level.Error, 1 ), ( Level.Warning, 2 ), ( Level.Info, 3 ), ( Level.Debug, 4 ) )

		m = Messages()

		self.assertEqual( { m.count(l) for l, c in messageCounts }, { 0 } )
		self.assertEqual( m.count( Level.Invalid ), 0 )

		for level, count in messageCounts :
			for i in range( count ) :
				m.add( Message( level, "testMessagesCount", "Message %d" % i ) )

		self.assertEqual( [ m.count(l) for l, c in messageCounts ], [ c for l, c in messageCounts ] )

		m.clear()

		self.assertEqual( { m.count(l) for l, c in messageCounts }, { 0 } )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testFirstDifference( self ) :

		def generateMessages( count, context ) :
			m = Messages()
			appendMessages( m, count, context )
			return m

		def appendMessages( messages, count, context ) :
			for i in range( count ) :
				messages.add( Message( IECore.MessageHandler.Level( i % 4 ), context, "message %d" % i ) )

		# NB, bucketSize is 100 in the current implementation, we need to
		# definitely verify the results of this method in multi-bucket
		# scenarios, along with incomplete buckets.

		# Test one empty

		m1 = Messages()
		m2 = generateMessages( 10, "m" )

		self.assertIsNone( m1.firstDifference( m2 ) )
		self.assertEqual( m2.firstDifference( m1 ), 0 )

		# Test equal

		m1 = generateMessages( 1234, "m" )
		m2 = Messages( m1 )

		self.assertIsNone( m1.firstDifference( m2 ) )
		self.assertIsNone( m2.firstDifference( m1 ) )

		# Test all different

		m1 = generateMessages( 1234, "a" )
		m2 = generateMessages( 1234, "b" )

		self.assertEqual( m1.firstDifference( m2 ), 0 )
		self.assertEqual( m2.firstDifference( m1 ), 0 )

		# Test varying length

		m1 = generateMessages( 1102, "a" )
		m2 = Messages( m1 )
		appendMessages( m2, 100, "a" )

		self.assertIsNone( m1.firstDifference( m2 ) )
		self.assertEqual( m2.firstDifference( m1 ), 1102 )

		# Test some different

		m1 = generateMessages( 47, "a" )
		m2 = Messages( m1 )
		appendMessages( m1, 2, "a" )
		appendMessages( m2, 2, "b" )

		self.assertEqual( m1.firstDifference( m2 ), 47 )
		self.assertEqual( m2.firstDifference( m1 ), 47 )

		m1 = generateMessages( 1030, "a" )
		m2 = Messages( m1 )
		appendMessages( m1, 300, "b" )
		appendMessages( m2, 302, "a" )

		self.assertEqual( m1.firstDifference( m2 ), 1030 )
		self.assertEqual( m2.firstDifference( m1 ), 1030 )

		# Test comparison optimisation

		m1 = generateMessages( 30005, "a" )
		m2 = Messages( m1 )
		appendMessages( m1, 1, "a" )
		appendMessages( m2, 1, "b" )

		with GafferTest.TestRunner.PerformanceScope() :
			self.assertEqual( m1.firstDifference( m2 ), 30005 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMessagesCopyPerformanceS( self ) :

		numMessages = 5000
		numCopies = 100000

		m = Messages()
		for i in range( numMessages ) :
			m.add( Message( IECore.MessageHandler.Level( i % 4 ), "testMessagesCopyPerformanceS", str(i) ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferTest.testMessagesCopyPerformance( m, numCopies )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMessagesCopyPerformanceM( self ) :

		numMessages = 50000
		numCopies = 100000

		m = Messages()
		for i in range( numMessages ) :
			m.add( Message( IECore.MessageHandler.Level( i % 4 ), "testMessagesCopyPerformanceM", str(i) ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferTest.testMessagesCopyPerformance( m, numCopies )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMessagesCopyPerformanceL( self ) :

		numMessages = 500000
		numCopies = 1000

		m = Messages()
		for i in range( numMessages ) :
			m.add( Message( IECore.MessageHandler.Level( i % 4 ), "testMessagesCopyPerformanceL", str(i) ) )

		with GafferTest.TestRunner.PerformanceScope() :
			GafferTest.testMessagesCopyPerformance( m, numCopies )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMessagesAddPerformance( self ) :

		GafferTest.testMessagesAddPerformance( 1000000 )

	def testMessagesValueReuse( self ):

		GafferTest.testMessagesValueReuse()

	def testMessagesConstness( self ) :

		GafferTest.testMessagesConstness()

if __name__ == "__main__":
	unittest.main()
