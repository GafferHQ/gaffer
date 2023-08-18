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

import threading
import unittest

import IECore

import Gaffer
import GafferTest

class ThreadMonitorTest( GafferTest.TestCase ) :

	def testConstruction( self ) :

		monitor = Gaffer.ThreadMonitor()
		self.assertEqual( monitor.allStatistics(), {} )
		self.assertEqual( monitor.plugStatistics( Gaffer.IntPlug() ), {} )
		self.assertEqual( monitor.combinedStatistics(), {} )

	def testThisThreadId( self ) :

		id = Gaffer.ThreadMonitor.thisThreadId()
		self.assertEqual( id, Gaffer.ThreadMonitor.thisThreadId() )

		ids = { id }
		lock = threading.Lock()

		def storeId() :
			id = Gaffer.ThreadMonitor.thisThreadId()
			self.assertEqual( id, Gaffer.ThreadMonitor.thisThreadId() )
			with lock :
				ids.add( id )

		threads = []
		for i in range( 0, 5 ) :
			thread = threading.Thread( target = storeId )
			threads.append( thread )
			thread.start()

		for thread in threads :
			thread.join()

		self.assertEqual( len( ids ), 6 )

	def testMonitoring( self ) :

		random = Gaffer.Random()
		monitor = Gaffer.ThreadMonitor()

		with monitor :
			random["outFloat"].getValue()

		self.assertEqual(
			monitor.allStatistics(),
			{
				random["outFloat"] : {
					monitor.thisThreadId() : 1
				}
			}
		)
		self.assertEqual(
			monitor.plugStatistics( random["outFloat"] ),
			{ monitor.thisThreadId() : 1 }
		)
		self.assertEqual(
			monitor.combinedStatistics(),
			{ monitor.thisThreadId() : 1 }
		)

		random["seedVariable"].setValue( "test" )
		with monitor :
			GafferTest.parallelGetValue( random["outFloat"], 100000, "test" )

		s = monitor.plugStatistics( random["outFloat"] )
		self.assertEqual( len( s ), IECore.tbb_global_control.active_value( IECore.tbb_global_control.parameter.max_allowed_parallelism ) )
		self.assertEqual( sum( s.values() ), 100001 )

		self.assertEqual( monitor.allStatistics(), { random["outFloat"] : s } )
		self.assertEqual( monitor.combinedStatistics(), s )

	def testProcessMask( self ) :

		for processType in [ "computeNode:hash", "computeNode:compute" ] :

			with self.subTest( processType = processType ) :

				Gaffer.ValuePlug.clearCache()
				Gaffer.ValuePlug.clearHashCache()

				random = Gaffer.Random()
				threadMonitor = Gaffer.ThreadMonitor( processMask = { processType } )
				performanceMonitor = Gaffer.PerformanceMonitor()
				context = Gaffer.Context()

				with threadMonitor, performanceMonitor, context :
					for i in range( 0, 5 ) :
						context["i"] = i # Unique context to force hashing
						random["outFloat"].getValue()

				self.assertEqual( performanceMonitor.plugStatistics( random["outFloat"] ).computeCount, 1 )
				self.assertEqual( performanceMonitor.plugStatistics( random["outFloat"] ).hashCount, 5 )

				self.assertEqual(
					sum( threadMonitor.plugStatistics( random["outFloat"] ).values() ),
					1 if processType == "computeNode:compute" else 5
				)

if __name__ == "__main__":
	unittest.main()
