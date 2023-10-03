##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

class ProcessTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )
		GafferTest.clearTestProcessCache()

	def testCollaboration( self ) :

		# We expect processes `1...n` to collaborate on
		# process 1000000.
		#
		#   n+1
		#  / | \
		# 1 ... n
		#  \ | /
		#    0

		n = 10000

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			GafferTest.runTestProcess(
				plug, 0,
				{ x : { n + 1 : {} } for x in range( 1, n + 1 ) }
			)

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, 1 + n + 1 )

	def testCollaborationFromNonCollaborativeProcesses( self ) :

		# As above, but the waiting processes are not themselves collaborative.
		#
		#     1
		#   / | \
		# -1 ... -n
		#   \ | /
		#     0

		n = 100000

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			GafferTest.runTestProcess(
				plug, 0,
				{ -x : { 1 : {} } for x in range( 1, n + 1 ) }
			)

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, 1 + n + 1 )

	def testNoCollaborationOnRecursion( self ) :

		# We don't expect any collaboration, because it would lead to
		# deadlock.
		#
		# 10
		# |
		# 10
		# |
		# 10
		# |
		# 10

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			GafferTest.runTestProcess( plug, 1, { 10 : { 10 : { 10 : {} } } } )

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, 4 )

	def testNoCollaborationOnIndirectRecursion( self ) :

		# We don't expect any collaboration, because it would lead to
		# deadlock.
		#
		# 1
		# |
		# 2
		# |
		# 1
		# |
		# 0

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			GafferTest.runTestProcess( plug, 0, { 1 : { 2 : { 1 : {} } } } )

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, 4 )

	def testNonCollaborativeProcessWithinRecursion( self ) :

		# As above, but using a non-collaborative task in the middle of the recursion.
		#
		# 1
		# |
		# -2
		# |
		# 1
		# |
		# 0

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			GafferTest.runTestProcess( plug, 0, { 1 : { -2 : { 1 : {} } } } )

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, 4 )

	def testNoCollaborationOnDiamondRecursion( self ) :

		# We don't expect any collaboration, because it would lead to
		# deadlock.
		#
		#     1
		#     |
		#     3
		#    / \
		#   1   2
		#    \ /
		#     0

		plug = Gaffer.Plug()

		for i in range( 0, 100 ) :
			GafferTest.clearTestProcessCache()
			with Gaffer.PerformanceMonitor() as monitor :
				GafferTest.runTestProcess(
					plug, 0,
					{
						1 : { 3 : { 1 : {} } },
						2 : { 3 : { 1 : {} } }
					}
				)

			# There are various possibilities for execution, based on different
			# thread timings.
			#
			# - The `0-2-3-1` branch completes first, so `1` is already cached by
			#   the time the `0-1` branch wants it. 4 computes total.
			# - The `0-1-3-1` branch completes first, with a duplicate compute for
			#   `1` to avoid deadlock. 5 computes total.
			# - The `0-2-3` branch waits on `1` from the `0-1` branch. The `0-1`
			#   branch performs duplicate computes for `3` and `1` to avoid deadlock.
			#   6 computes total.
			self.assertIn( monitor.plugStatistics( plug ).computeCount, { 4, 5, 6 } )

	def testNoCollaborationOnIndirectDiamondRecursion( self ) :

		# As above, but with an additional process (4), meaning we have
		# to track non-immediate dependencies between processes.
		#
		#     1
		#     |
		#     4
		#     |
		#     3
		#    / \
		#   1   2
		#    \ /
		#     0

		plug = Gaffer.Plug()

		for i in range( 0, 100 ) :
			GafferTest.clearTestProcessCache()
			with Gaffer.PerformanceMonitor() as monitor :
				GafferTest.runTestProcess(
					plug, 0,
					{
						1 : { 3 : { 4 : { 1 : {} } } },
						2 : { 3 : { 4 : { 1 : {} } } },
					}
				)

			self.assertIn( monitor.plugStatistics( plug ).computeCount, { 5, 6, 8 } )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testFanOutGatherPerformance( self ) :

		# Pathological case for cycle checking - huge permutations
		# of paths through the downstream graph.
		#
		#       0
		#     / | \
		#    1  2  3
		#     \ | /
		#       4
		#     / | \
		#    5  6  7
		#     \ | /
		#       8
		#     / | \
		#    9 10 11
		#     \ | /
		#      12        (for width 3 and depth 3)

		width = 64
		depth = 10

		dependencies = {}
		i = 0
		for d in range( 0, depth ) :
			dependencies = { i : dependencies }
			i += 1
			dependencies = { w : dependencies for w in range( i, i + width ) }
			i += width

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			GafferTest.clearTestProcessCache()
			with GafferTest.TestRunner.PerformanceScope() :
				GafferTest.runTestProcess( plug, i, dependencies )

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, i + 1 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testCollaborationPerformance( self ) :

		#  -(n+1)...-2n
		#       \ | /
		#         1
		#       / | \
		#     -1 ... -n
		#       \ | /
		#         0

		n = 100000

		upstreamDependencies = { -x : {} for x in range( n + 1, 2 * n + 1 ) }

		GafferTest.clearTestProcessCache()

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			with GafferTest.TestRunner.PerformanceScope() :
				GafferTest.runTestProcess(
					plug, 0,
					{ -x : { 1 : upstreamDependencies } for x in range( 1, n + 1 ) }
				)

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, 1 + n + 1 + n )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testCollaborationTransitionPerformance( self ) :

		# Case we think is probably pretty common - all threads need to migrate
		# through a series of collaborations.
		#
		#		  3
		#       / | \
		# -(2n+1)...-3n
		#       \ | /
		#         2
		#       / | \
		#  -(n+1)...-2n
		#       \ | /
		#         1
		#       / | \
		#     -1 ... -n
		#       \ | /
		#         0              (for depth 3)

		n = IECore.hardwareConcurrency()
		depth = 1000

		dependencies = {}
		for d in range( depth, 0, -1 ) :
			dependencies = { -x : { d : dependencies } for x in range( (d-1) * n + 1, d * n + 1 ) }

		GafferTest.clearTestProcessCache()

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			with GafferTest.TestRunner.PerformanceScope() :
				GafferTest.runTestProcess( plug, 0, dependencies )

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, depth * ( n + 1 ) + 1 )

if __name__ == "__main__":
	unittest.main()
