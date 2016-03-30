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

import unittest

import Gaffer
import GafferTest

class PerformanceMonitorTest( GafferTest.TestCase ) :

	def testActiveStatus( self ) :

		m = Gaffer.PerformanceMonitor()

		self.assertEqual( m.getActive(), False )
		m.setActive( True )
		self.assertEqual( m.getActive(), True )
		m.setActive( False )
		self.assertEqual( m.getActive(), False )

		with m :
			self.assertEqual( m.getActive(), True )

		self.assertEqual( m.getActive(), False )

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
			m.plugStatistics( a["sum"] ),
			m.Statistics( hashCount = 1, computeCount = 1 )
		)

		# Redo the computation - the caches should ensure
		# that we don't do anything at all.
		with m :
			self.assertEqual( a["sum"].getValue(), -2003 )

		self.assertEqual(
			m.plugStatistics( a["sum"] ),
			m.Statistics( hashCount = 1, computeCount = 1 )
		)

		# Force a rehash by making a new context. We should
		# still be using the cache for the value though.
		with m :
			with Gaffer.Context() as c :
				c["myVariable"] = 1 # Force a rehash
				self.assertEqual( a["sum"].getValue(), -2003 )


		self.assertEqual(
			m.plugStatistics( a["sum"] ),
			m.Statistics( hashCount = 2, computeCount = 1 )
		)

		# Check the dictionary of all statistics.
		self.assertEqual(
			m.allStatistics(),
			{
				a["sum"] : m.Statistics( hashCount = 2, computeCount = 1 )
			}
		)

	def testEnterReturnValue( self ) :

		m = Gaffer.PerformanceMonitor()
		with m as n :
			pass

		self.assertTrue( m is n )

if __name__ == "__main__":
	unittest.main()
