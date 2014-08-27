##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

class SpeedTest( GafferTest.TestCase ) :

	# original (r335):
	#
	#	15.110s
	#	15.088s
	#	15.102s
	#
	# interned string :
	#
	#	17.288s
	#	17.216s
	#	17.213s
	#
	# no setName in addChildInternal (still interned string) :
	#
	#	0.104s
	#	0.099s
	#	0.099s
	#
	# no setName in addChildInternal (std::string) :
	#
	#	0.103s
	#	0.098s
	#	0.098s
	#
	# replace string comparisons with InternedString comparisons (r336):
	#
	#	5.161s
	#	5.140s
	#	5.138s
	#
	def testMakeNamesUnique( self ) :

		s = Gaffer.ScriptNode()

		for i in range( 0, 1000 ) :
			n = GafferTest.AddNode()
			s.addChild( n )

	#
	# this test checks it doesn't take a ludicrous amount of time
	# to retrieve children from their parents by name. even though
	# we're currently doing a linear search to achieve this it doesn't
	# seem to be a particularly pressing issue, perhaps because comparison
	# against many InternedStrings is much cheaper than comparison
	# against many std::strings. if necessary we can improve things by
	# storing a map from name to children in GraphComponent.
	#
	# r338 (linear search with string comparisons)
	#
	#	0.214s
	#	0.183s
	#	0.172s
	#
	# r339 (linear search with InternedString comparisons)
	#
	#	0.146s
	#	0.136s
	#	0.140s
	def testGetChild( self ) :

		s = Gaffer.ScriptNode()

		for i in range( 0, 1000 ) :
			# explicitly setting the name to something unique
			# avoids the overhead incurred by the example
			# in testMakeNamesUnique
			n = GafferTest.AddNode( "AddNode" + str( i ) )
			s.addChild( n )

		for i in range( 0, 1000 ) :
			n = "AddNode" + str( i )
			c = s[n]
			self.assertEqual( c.getName(), n )

if __name__ == "__main__":
	unittest.main()

