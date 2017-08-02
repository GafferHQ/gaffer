##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import weakref

import Gaffer
import GafferUI
import GafferUITest

class ScriptWidgetTest( GafferUITest.TestCase ) :

	def testLifetimeOfManuallyAcquiredWindows( self ) :

		s = Gaffer.ScriptNode()
		sw = GafferUI.ScriptWidget.acquire( s )

		wsw = weakref.ref( sw )
		del sw

		self.assertEqual( wsw(), None )

	def testLifetimeOfDirectlyConstructedWindows( self ) :

		s = Gaffer.ScriptNode()
		sw = GafferUI.ScriptWidget( s )

		wsw = weakref.ref( sw )
		del sw

		self.assertEqual( wsw(), None )

	def testAcquire( self ) :

		s1 = Gaffer.ScriptNode()
		s2 = Gaffer.ScriptNode()
		s3 = Gaffer.ScriptNode()

		w1 = GafferUI.ScriptWidget.acquire( s1 )
		self.failUnless( w1.scriptNode().isSame( s1 ) )

		w2 = GafferUI.ScriptWidget.acquire( s2 )
		self.failUnless( w2.scriptNode().isSame( s2 ) )

		w3 = GafferUI.ScriptWidget.acquire( s1 )
		self.failUnless( w3 is w1 )

		w4 = GafferUI.ScriptWidget.acquire( s1, createIfNecessary = False )
		self.assertTrue( w4 is w1 )

		w5 = GafferUI.ScriptWidget.acquire( s3, createIfNecessary = False )
		self.assertTrue( w5 is None )

		w6 = GafferUI.ScriptWidget.acquire( s3, createIfNecessary = True )
		self.assertTrue( w6.scriptNode().isSame( s3 ) )

if __name__ == "__main__":
	unittest.main()
