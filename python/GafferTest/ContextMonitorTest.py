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
import time
import unittest

import IECore

import Gaffer
import GafferTest

class ContextMonitorTest( GafferTest.TestCase ) :

	def test( self ) :

		c = Gaffer.Context()
		defaultVariableNames = c.keys()

		a1 = GafferTest.AddNode()
		a2 = GafferTest.AddNode()

		m = Gaffer.ContextMonitor()
		with c, m :
			a1["sum"].getValue()

		a1s = m.plugStatistics( a1["sum"] )
		self.assertEqual( a1s.numUniqueContexts(), 1 )
		self.assertEqual( set( a1s.variableNames() ), set( defaultVariableNames ) )
		for n in defaultVariableNames :
			self.assertEqual( a1s.numUniqueValues( n ), 1 )

		self.assertFalse( a2["sum"] in m.allStatistics() )

		with c, m :
			c.setFrame( 10 )
			a1["sum"].getValue()
			a2["sum"].getValue()

		a1s = m.plugStatistics( a1["sum"] )
		self.assertEqual( a1s.numUniqueContexts(), 2 )
		self.assertEqual( set( a1s.variableNames() ), set( defaultVariableNames ) )
		for n in defaultVariableNames :
			self.assertEqual( a1s.numUniqueValues( n ), 1 if n != "frame" else 2 )

		a2s = m.plugStatistics( a2["sum"] )
		self.assertEqual( a2s.numUniqueContexts(), 1 )
		self.assertEqual( set( a2s.variableNames() ), set( defaultVariableNames ) )
		for n in defaultVariableNames :
			self.assertEqual( a2s.numUniqueValues( n ), 1 )

		with c, m :
			c["test"] = 10
			a1["sum"].getValue()
			c["test"] = 20
			a2["sum"].getValue()

		cs = m.combinedStatistics()
		self.assertEqual( cs.numUniqueContexts(), 4 )
		self.assertEqual( set( cs.variableNames() ), set( defaultVariableNames + [ "test" ] ) )
		self.assertEqual( cs.numUniqueValues( "frame" ), 2 )
		self.assertEqual( cs.numUniqueValues( "test" ), 2 )

	def testRoot( self ) :

		a1 = GafferTest.AddNode()
		a2 = GafferTest.AddNode()

		with Gaffer.Context() as c :
			with Gaffer.ContextMonitor( a2 ) as m :
				a1["sum"].getValue()
				a2["sum"].getValue()

		self.assertFalse( a1["sum"] in m.allStatistics() )
		self.assertTrue( a2["sum"] in m.allStatistics() )

	def testVariableHashes( self ) :

		node = GafferTest.AddNode()

		context1 = Gaffer.Context()
		context1["test"] = 10

		context2 = Gaffer.Context()
		context2["test"] = 20

		with Gaffer.ContextMonitor() as monitor :

			with context1 :
				node["sum"].getValue()

			with context2 :
				node["sum"].getValue()

		statistics = monitor.plugStatistics( node["sum"] )
		hashes = statistics.variableHashes( "test" )
		self.assertEqual( len( hashes ), 2 )
		self.assertEqual( hashes.get( context1.variableHash( "test" ) ), 2 ) # A hash and a compute
		self.assertEqual( hashes.get( context2.variableHash( "test" ) ), 1 ) # Just a hash

		self.assertEqual( statistics.variableHashes( "nonExistentVariable" ), {} )

if __name__ == "__main__":
	unittest.main()
