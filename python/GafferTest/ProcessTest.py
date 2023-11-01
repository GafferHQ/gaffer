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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration" } )
	def testCollaboration( self ) :

		# We expect processes `1...n` to collaborate on process `n+1`.
		#
		#   n+1
		#  / | \
		# 1 ... n
		#  \ | /
		#    0
		#
		# Note on conventions used throughout this file :
		#
		# - Processes are labelled with the value of their result.
		# - Lines connecting processes denote dependencies between them.
		# - Dependent processes appear below the processes they depend on,
		#   matching the typical top-to-bottom flow of a Gaffer graph.
		# - The root process is therefore always the bottom-most one.

		n = 10000

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			GafferTest.runTestProcess(
				plug, 0,
				{ x : { n + 1 : {} } for x in range( 1, n + 1 ) }
			)

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, 1 + n + 1 )

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration" } )
	def testCollaborationTaskDistribution( self ) :

		# -1 ... -n          plug4
		#   \ | /
		#    n+1             plug3
		#   / | \
		#  1 ... n           plug2
		#   \ | /
		#     0              plug1

		numWorkers = IECore.tbb_global_control.active_value( IECore.tbb_global_control.parameter.max_allowed_parallelism )
		n = 10000 * numWorkers

		plug1 = Gaffer.Plug()
		plug2 = Gaffer.Plug()
		plug3 = Gaffer.Plug()
		plug4 = Gaffer.Plug()
		plug1.setInput( plug2 )
		plug2.setInput( plug3 )
		plug3.setInput( plug4 )

		dependencies = { -x : {} for x in range( 1, n + 1 ) }
		dependencies = { x : { n + 1 : dependencies } for x in range( 1, n + 1 ) }

		intPlug = Gaffer.IntPlug()
		GafferTest.parallelGetValue( intPlug, 100000 ) # Get worker threads running in advance

		with Gaffer.PerformanceMonitor() as monitor, Gaffer.ThreadMonitor() as threadMonitor :
			GafferTest.runTestProcess( plug1, 0, dependencies )

		self.assertEqual( monitor.plugStatistics( plug1 ).computeCount, 1 )
		self.assertEqual( monitor.plugStatistics( plug2 ).computeCount, n )
		self.assertEqual( monitor.plugStatistics( plug3 ).computeCount, 1 )
		self.assertEqual( monitor.plugStatistics( plug4 ).computeCount, n )

		def assertExpectedThreading( plug, numTasks ) :

			s = threadMonitor.plugStatistics( plug ) # Dict mapping thread ID to number of computes
			self.assertEqual( sum( s.values() ), numTasks )

			if numTasks == 1 :
				self.assertEqual( len( s ), 1 )
			else :
				# Check that every worker thread contributed some work.
				self.assertEqual( len( s ), numWorkers )
				# Check that each worker thread did at least half of its fair
				# share of work. This assertion is too sensitive in CI so it is
				# disabled by default. On my local test machine (Dual 16 core
				# Xeon with hyperthreading) I see pretty reliable success up to
				# `-threads 32`, and regular failure at `-threads 64` (the
				# default).
				if False :
					for t in s.values() :
						self.assertGreaterEqual( t, 0.5 * numTasks / numWorkers )

		assertExpectedThreading( plug1, 1 )
		assertExpectedThreading( plug2, n )
		assertExpectedThreading( plug3, 1 )
		assertExpectedThreading( plug4, n )

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:performance" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:performance" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:performance" } )
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

	@GafferTest.TestRunner.CategorisedTestMethod( { "taskCollaboration:performance" } )
	@GafferTest.TestRunner.PerformanceTestMethod()
	def testDeepTreePerformance( self ) :

		# Models things like the recursive computation of bounding boxes in GafferScene
		#
		#   3   4 5   6
		#    \ /   \ /
		#     1     2
		#      \   /
		#       \ /
		#        0           (for maxDepth 2 and branchFactor 2)

		maxDepth = 14
		branchFactor = 2

		def makeDependencies( n, depth = 0 ) :

			if depth == maxDepth :
				return {}

			return { i : makeDependencies( i, depth + 1 ) for i in range( n * branchFactor + 1, (n + 1) * branchFactor + 1 ) }

		dependencies = makeDependencies( 0 )

		GafferTest.clearTestProcessCache()

		plug = Gaffer.Plug()
		with Gaffer.PerformanceMonitor() as monitor :
			with GafferTest.TestRunner.PerformanceScope() :
				GafferTest.runTestProcess( plug, 0, dependencies )

		self.assertEqual( monitor.plugStatistics( plug ).computeCount, sum( branchFactor ** d for d in range( 0, maxDepth + 1 ) ) )

if __name__ == "__main__":
	unittest.main()
