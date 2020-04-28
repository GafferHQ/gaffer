##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import urllib2
import os
import glob

import IECore

import Gaffer
import GafferTest

class AboutTest( GafferTest.TestCase ) :

	def test( self ) :

		for d in Gaffer.About.dependencies() :

			if "license" in d :
				f = os.path.expandvars( d["license"] )
				self.assertTrue( os.path.exists( f ), "License file \"{0}\" does not exist".format( f ) )

			if "source" in d :
				self.assertTrue( urllib2.urlopen( d["source"] ) )

# Image Engine internal builds don't package all the dependencies with
# Gaffer, so the license tests above would fail. We try to detect such
# builds and mark the test as being an expected failure, so as to cut
# down on noise.
packagedWithDependencies = False
for f in glob.glob( os.path.expandvars( "$GAFFER_ROOT/lib/*" ) ) :
	if "Gaffer" not in os.path.basename( f ) :
		packagedWithDependencies = True

if not packagedWithDependencies :
	AboutTest.test = unittest.expectedFailure( AboutTest.test )

if __name__ == "__main__":
	unittest.main()
