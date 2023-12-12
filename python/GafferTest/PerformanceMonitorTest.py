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

import os
import gc
import time
import unittest

import IECore

import Gaffer
import GafferTest

class PerformanceMonitorTest( GafferTest.TestCase ) :

	def testStatistics( self ) :

		m = Gaffer.PerformanceMonitor()

		a = GafferTest.AddNode()
		a["op1"].setValue( -1001 )
		a["op2"].setValue( -1002 )

		# Do a computation, and check we have one hash
		# and one compute.
		with m :
			self.assertEqual( a["sum"].getValue(), -2003 )

		self.assertEqual(
			( m.plugStatistics( a["sum"] ).hashCount, m.plugStatistics( a["sum"] ).computeCount ),
			( 1, 1 )
		)

		# Redo the computation - the caches should ensure
		# that we don't do anything at all.
		with m :
			self.assertEqual( a["sum"].getValue(), -2003 )

		self.assertEqual(
			( m.plugStatistics( a["sum"] ).hashCount, m.plugStatistics( a["sum"] ).computeCount ),
			( 1, 1 )
		)

		# Force a rehash by making a new context. We should
		# still be using the cache for the value though.
		with m :
			with Gaffer.Context() as c :
				c["myVariable"] = 1 # Force a rehash
				self.assertEqual( a["sum"].getValue(), -2003 )


		self.assertEqual(
			( m.plugStatistics( a["sum"] ).hashCount, m.plugStatistics( a["sum"] ).computeCount ),
			( 2, 1 )
		)

		# Check the dictionary of all statistics.
		self.assertEqual( len( m.allStatistics() ), 1 )
		self.assertEqual(
			m.allStatistics()[a["sum"]],
			m.plugStatistics( a["sum"] ),
		)

	def testStatisticsConstructorAndAccessors( self ) :

		s = Gaffer.PerformanceMonitor.Statistics(
			hashCount = 10,
			computeCount = 20,
			hashDuration = 100,
			computeDuration = 200
		)

		self.assertEqual( s.hashCount, 10 )
		self.assertEqual( s.computeCount, 20 )
		self.assertEqual( s.hashDuration, 100 )
		self.assertEqual( s.computeDuration, 200 )

		s.hashCount = 20
		s.computeCount = 30
		s.hashDuration = 200
		s.computeDuration = 300

		self.assertEqual( s.hashCount, 20 )
		self.assertEqual( s.computeCount, 30 )
		self.assertEqual( s.hashDuration, 200 )
		self.assertEqual( s.computeDuration, 300 )

	def testEnterReturnValue( self ) :

		m = Gaffer.PerformanceMonitor()
		with m as n :
			pass

		self.assertTrue( m is n )

	def testDurations( self ) :

		class DurationNode( Gaffer.ComputeNode ) :

			def __init__( self, name = "DurationNode" ) :

				Gaffer.ComputeNode.__init__( self, name )

				self["in"] = Gaffer.FloatPlug()
				self["out"] = Gaffer.FloatPlug( direction = Gaffer.Plug.Direction.Out )

				self["hashDuration"] = Gaffer.FloatPlug()
				self["computeDuration"] = Gaffer.FloatPlug()

			def affects( self, input ) :

				result = Gaffer.ComputeNode.affects( self, input )
				if input in ( self["in"], self["hashDuration"], self["computeDuration"] ) :
					result.append( self["out"] )

				return result

			def hash( self, output, context, h ) :

				if output.isSame( self["out"] ) :

					self["in"].hash( h )
					self["computeDuration"].hash( h )

					time.sleep( self["hashDuration"].getValue() )

			def compute( self, plug, context ) :

				if plug.isSame( self["out"] ) :

					d = self["computeDuration"].getValue()
					time.sleep( d )

					self["out"].setValue( self["in"].getValue() + d )

				else :

					ComputeNode.compute( self, plug, context )

		IECore.registerRunTimeTyped( DurationNode )

		n1 = DurationNode( "n1" )
		n1["hashDuration"].setValue( 0.2 )
		n1["computeDuration"].setValue( 0.4 )

		n2 = DurationNode( "n2" )
		n2["in"].setInput( n1["out"] )
		n2["hashDuration"].setValue( 0.1 )
		n2["computeDuration"].setValue( 0.2 )

		with Gaffer.PerformanceMonitor() as m :

			n2["out"].getValue()

		def seconds( n ) :

			return n / ( 1000000000.0 )

		self.assertEqual( len( m.allStatistics() ), 2 )

		# 1.0 is an excessively wide tolerance but we've seen huge variations
		# in CI due to machine contention. We're leaving the test in as it
		# would potentially still catch some catastrophic orders-of-magnitude
		# timing increase bug...
		delta = 1.0 if GafferTest.inCI() else 0.01

		self.assertEqual( m.plugStatistics( n1["out"] ).hashCount, 1 )
		self.assertEqual( m.plugStatistics( n1["out"] ).computeCount, 1 )
		self.assertAlmostEqual( seconds( m.plugStatistics( n1["out"] ).hashDuration ), 0.2, delta = delta )
		self.assertAlmostEqual( seconds( m.plugStatistics( n1["out"] ).computeDuration ), 0.4, delta = delta )

		self.assertEqual( m.plugStatistics( n2["out"] ).hashCount, 1 )
		self.assertEqual( m.plugStatistics( n2["out"] ).computeCount, 1 )
		self.assertAlmostEqual( seconds( m.plugStatistics( n2["out"] ).hashDuration ), 0.1, delta = delta )
		self.assertAlmostEqual( seconds( m.plugStatistics( n2["out"] ).computeDuration ), 0.2, delta = delta )

		with m :
			with Gaffer.Context() as c :
				c["test"] = 1 # force rehash, but not recompute
				n2["out"].getValue()

		self.assertEqual( m.plugStatistics( n1["out"] ).hashCount, 2 )
		self.assertEqual( m.plugStatistics( n1["out"] ).computeCount, 1 )
		self.assertAlmostEqual( seconds( m.plugStatistics( n1["out"] ).hashDuration ), 0.4, delta = delta )
		self.assertAlmostEqual( seconds( m.plugStatistics( n1["out"] ).computeDuration ), 0.4, delta = delta )

		self.assertEqual( m.plugStatistics( n2["out"] ).hashCount, 2 )
		self.assertEqual( m.plugStatistics( n2["out"] ).computeCount, 1 )
		self.assertAlmostEqual( seconds( m.plugStatistics( n2["out"] ).hashDuration ), 0.2, delta = delta )
		self.assertAlmostEqual( seconds( m.plugStatistics( n2["out"] ).computeDuration ), 0.2, delta = delta )

	def testDontMonitorPreExistingBackgroundTasks( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.MultiplyNode()
		s["n"]["op2"].setValue( 1 )
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( """parent["n"]["op1"] = context["op1"]""" )

		def backgroundFunction() :

			with Gaffer.Context() as c :
				for i in range( 0, 10000 ) :
					c["op1"] = i
					self.assertEqual( s["n"]["product"].getValue(), i )

		t = Gaffer.ParallelAlgo.callOnBackgroundThread(
			s["n"]["product"], backgroundFunction
		)

		with Gaffer.PerformanceMonitor() as m :
			t.wait()

		# We don't launch any computes from the thread
		# where the monitor is active, so we don't expect
		# to capture any.
		self.assertEqual( len( m.allStatistics() ), 0 )

if __name__ == "__main__":
	unittest.main()
