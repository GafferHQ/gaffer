##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import sys
import unittest
import threading
import time

import Gaffer
import GafferTest

class OutputRedirectionTest( GafferTest.TestCase ) :

	def testRedirection( self ) :

		out = []
		err = []
		with Gaffer.OutputRedirection( stdOut = out.append, stdErr = err.append ) :

			sys.stdout.write( "OUT" )
			print( "PRINT" )
			sys.stderr.write( "ERR" )

		self.assertEqual( out, [ "OUT", "PRINT", "\n" ] )
		self.assertEqual( err, [ "ERR" ] )

		sys.stdout.write( "" )
		sys.stderr.write( "" )

		self.assertEqual( out, [ "OUT", "PRINT", "\n" ] )
		self.assertEqual( err, [ "ERR" ] )

	def testThreading( self ) :

		perThreadOuts = []
		perThreadErrs = []
		threads = []

		def f( threadIndex ) :

			with Gaffer.OutputRedirection( stdOut = perThreadOuts[threadIndex].append, stdErr = perThreadErrs[threadIndex].append ) :
				for i in range( 0, 100 ) :
					sys.stdout.write( "OUT %d %d" % ( threadIndex, i ) )
					sys.stderr.write( "ERR %d %d" % ( threadIndex, i ) )
			time.sleep( 0.001 )

		for i in range( 0, 100 ) :
			perThreadOuts.append( [] )
			perThreadErrs.append( [] )
			t = threading.Thread( target = f, args = ( i, ) )
			threads.append( t )
			t.start()

		for t in threads :
			t.join()

		for i in range( 0, 100 ) :
			self.assertEqual( len( perThreadOuts[i] ), 100 )
			self.assertEqual( len( perThreadErrs[i] ), 100 )
			for j in range( 0, 100 ) :
				self.assertEqual( perThreadOuts[i][j], "OUT %d %d" % ( i, j ) )
				self.assertEqual( perThreadErrs[i][j], "ERR %d %d" % ( i, j ) )

if __name__ == "__main__":
	unittest.main()
