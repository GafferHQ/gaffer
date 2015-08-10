##########################################################################
#
#  Copyright (c) 2015, Scene Engine Design Inc. All rights reserved.
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
import GafferScene

class SceneProcessorTest( GafferTest.TestCase ) :

	def testNumberOfInputs( self ) :

		n = GafferScene.SceneProcessor()
		self.assertTrue( isinstance( n["in"], GafferScene.ScenePlug ) )

		n = GafferScene.SceneProcessor( minInputs = 2, maxInputs = 2 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertTrue( isinstance( n["in"][0], GafferScene.ScenePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferScene.ScenePlug ) )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), 2 )

		n = GafferScene.SceneProcessor( minInputs = 2, maxInputs = 1000 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertTrue( isinstance( n["in"][0], GafferScene.ScenePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferScene.ScenePlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), 1000 )

		n = GafferScene.SceneProcessor( minInputs = 2 )
		self.assertTrue( isinstance( n["in"], Gaffer.ArrayPlug ) )
		self.assertTrue( isinstance( n["in"][0], GafferScene.ScenePlug ) )
		self.assertTrue( isinstance( n["in"][1], GafferScene.ScenePlug ) )
		self.assertEqual( len( n["in"] ), 2 )
		self.assertEqual( n["in"].minSize(), 2 )
		self.assertEqual( n["in"].maxSize(), Gaffer.ArrayPlug().maxSize() )

if __name__ == "__main__":
	unittest.main()
