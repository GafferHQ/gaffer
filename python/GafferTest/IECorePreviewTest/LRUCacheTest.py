##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import GafferTest

class LRUCacheTest( GafferTest.TestCase ) :

	def test100PercentOfWorkingSetSerial( self ) :

		GafferTest.testLRUCache( "serial", numIterations = 100000, numValues = 100, maxCost = 100 )

	def test100PercentOfWorkingSetParallel( self ) :

		GafferTest.testLRUCache( "parallel", numIterations = 100000, numValues = 100, maxCost = 100 )

	def test100PercentOfWorkingSetTaskParallel( self ) :

		GafferTest.testLRUCache( "taskParallel", numIterations = 100000, numValues = 100, maxCost = 100 )

	def test90PercentOfWorkingSetSerial( self ) :

		GafferTest.testLRUCache( "serial", numIterations = 100000, numValues = 100, maxCost = 90 )

	def test90PercentOfWorkingSetParallel( self ) :

		GafferTest.testLRUCache( "parallel", numIterations = 100000, numValues = 100, maxCost = 90 )

	def test90PercentOfWorkingSetTaskParallel( self ) :

		GafferTest.testLRUCache( "taskParallel", numIterations = 100000, numValues = 100, maxCost = 90 )

	def test2PercentOfWorkingSetSerial( self ) :

		GafferTest.testLRUCache( "serial", numIterations = 100000, numValues = 100, maxCost = 2 )

	def test2PercentOfWorkingSetParallel( self ) :

		GafferTest.testLRUCache( "parallel", numIterations = 100000, numValues = 100, maxCost = 2 )

	def test2PercentOfWorkingSetTaskParallel( self ) :

		GafferTest.testLRUCache( "taskParallel", numIterations = 10000, numValues = 100, maxCost = 2 )

	def testRemovalCallbackSerial( self ) :

		GafferTest.testLRUCacheRemovalCallback( "serial" )

	def testRemovalCallbackParallel( self ) :

		GafferTest.testLRUCacheRemovalCallback( "parallel" )

	def testRemovalCallbackTaskParallel( self ) :

		GafferTest.testLRUCacheRemovalCallback( "taskParallel" )

	def testClearAndGetSerial( self ) :

		GafferTest.testLRUCache( "serial", numIterations = 100000, numValues = 1000, maxCost = 90, clearFrequency = 20 )

	def testClearAndGetParallel( self ) :

		GafferTest.testLRUCache( "parallel", numIterations = 100000, numValues = 1000, maxCost = 90, clearFrequency = 20 )

	def testClearAndGetTaskParallel( self ) :

		GafferTest.testLRUCache( "taskParallel", numIterations = 10000, numValues = 1000, maxCost = 90, clearFrequency = 20 )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testContentionForOneItemSerial( self ) :

		GafferTest.testLRUCacheContentionForOneItem( "serial" )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testContentionForOneItemParallel( self ) :

		GafferTest.testLRUCacheContentionForOneItem( "parallel" )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testContentionForOneItemTaskParallel( self ) :

		GafferTest.testLRUCacheContentionForOneItem( "taskParallel" )

	def testRecursionSerial( self ) :

		GafferTest.testLRUCacheRecursion( "serial", numIterations = 100000, numValues = 10000, maxCost = 10000 )

	def testRecursionParallel( self ) :

		GafferTest.testLRUCacheRecursion( "parallel", numIterations = 100000, numValues = 10000, maxCost = 10000 )

	def testRecursionTaskParallel( self ) :

		GafferTest.testLRUCacheRecursion( "taskParallel", numIterations = 100000, numValues = 10000, maxCost = 10000 )

	def testRecursionWithEvictionsSerial( self ) :

		GafferTest.testLRUCacheRecursion( "serial", numIterations = 100000, numValues = 1000, maxCost = 100 )

	def testRecursionWithEvictionsParallel( self ) :

		GafferTest.testLRUCacheRecursion( "parallel", numIterations = 100000, numValues = 1000, maxCost = 100 )

	def testRecursionWithEvictionsTaskParallel( self ) :

		GafferTest.testLRUCacheRecursion( "taskParallel", numIterations = 100000, numValues = 1000, maxCost = 100 )

	def testRecursionOnOneItemSerial( self ) :

		GafferTest.testLRUCacheRecursionOnOneItem( "serial" )

	def testRecursionOnOneItemTaskParallel( self ) :

		GafferTest.testLRUCacheRecursionOnOneItem( "taskParallel" )

	def testClearFromGetSerial( self ) :

		GafferTest.testLRUCacheClearFromGet( "serial" )

	def testClearFromGetParallel( self ) :

		GafferTest.testLRUCacheClearFromGet( "parallel" )

	def testClearFromGetTaskParallel( self ) :

		GafferTest.testLRUCacheClearFromGet( "taskParallel" )

	def testExceptionsSerial( self ) :

		GafferTest.testLRUCacheExceptions( "serial" )

	def testExceptionsParallel( self ) :

		GafferTest.testLRUCacheExceptions( "parallel" )

	def testExceptionsTaskParallel( self ) :

		GafferTest.testLRUCacheExceptions( "taskParallel" )

	def testCancellationSerial( self ) :

		GafferTest.testLRUCacheCancellation( "serial" )

	def testCancellationParallel( self ) :

		GafferTest.testLRUCacheCancellation( "parallel" )

	def testCancellationTaskParallel( self ) :

		GafferTest.testLRUCacheCancellation( "taskParallel" )

	def testUncacheableItemSerial( self ) :

		GafferTest.testLRUCacheUncacheableItem( "serial" )

	def testUncacheableItemParallel( self ) :

		GafferTest.testLRUCacheUncacheableItem( "parallel" )

	def testUncacheableItemTaskParallel( self ) :

		GafferTest.testLRUCacheUncacheableItem( "taskParallel" )

	def testGetIfCachedSerial( self ) :

		GafferTest.testLRUCacheGetIfCached( "serial" )

	def testGetIfCachedParallel( self ) :

		GafferTest.testLRUCacheGetIfCached( "parallel" )

	def testGetIfCachedTaskParallel( self ) :

		GafferTest.testLRUCacheGetIfCached( "taskParallel" )

if __name__ == "__main__":
	unittest.main()
