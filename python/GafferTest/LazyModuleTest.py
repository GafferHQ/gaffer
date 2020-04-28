##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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
import types
import unittest

import Gaffer
import GafferTest

class LazyModuleTest( GafferTest.TestCase ) :

	def test( self ) :

		# lazy loading something already loaded should just return the module
		# directly.
		ut = Gaffer.lazyImport( "unittest" )
		self.assertTrue( ut is unittest )
		self.assertTrue( type( ut ) is types.ModuleType )

		# lazy loading something not yet loaded should give us a nice
		# lazy module. hopefully nobody is loading the dummy_threading
		# module for any other purpose.

		self.assertNotIn( "dummy_threading", sys.modules )

		lazyDT = Gaffer.lazyImport( "dummy_threading" )
		self.assertIn( "dummy_threading", sys.modules )
		self.assertIsInstance( lazyDT, Gaffer.LazyModule )

		# check we can still get stuff out

		t = lazyDT.Thread()
		s = lazyDT.Semaphore()

if __name__ == "__main__":
	unittest.main()
