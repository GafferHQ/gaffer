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
import GafferTest
import GafferUI
import GafferUITest

class ScriptWindowTest( GafferUITest.TestCase ) :

	def testLifetimeOfManuallyAcquiredWindows( self ) :

		s = Gaffer.ScriptNode()
		sw = GafferUI.ScriptWindow.acquire( s )

		wsw = weakref.ref( sw )
		del sw

		self.assertEqual( wsw(), None )

	def testLifetimeOfDirectlyConstructedWindows( self ) :

		s = Gaffer.ScriptNode()
		sw = GafferUI.ScriptWindow( s )

		wsw = weakref.ref( sw )
		del sw

		self.assertEqual( wsw(), None )

	def testAcquire( self ) :

		s1 = Gaffer.ScriptNode()
		s2 = Gaffer.ScriptNode()
		s3 = Gaffer.ScriptNode()

		w1 = GafferUI.ScriptWindow.acquire( s1 )
		self.assertTrue( w1.scriptNode().isSame( s1 ) )

		w2 = GafferUI.ScriptWindow.acquire( s2 )
		self.assertTrue( w2.scriptNode().isSame( s2 ) )

		w3 = GafferUI.ScriptWindow.acquire( s1 )
		self.assertTrue( w3 is w1 )

		w4 = GafferUI.ScriptWindow.acquire( s1, createIfNecessary = False )
		self.assertTrue( w4 is w1 )

		w5 = GafferUI.ScriptWindow.acquire( s3, createIfNecessary = False )
		self.assertTrue( w5 is None )

		w6 = GafferUI.ScriptWindow.acquire( s3, createIfNecessary = True )
		self.assertTrue( w6.scriptNode().isSame( s3 ) )

	def testLifetimeOfApplicationScriptWindows( self ) :

		class testApp( Gaffer.Application ) :

			def __init__( self ) :

				Gaffer.Application.__init__( self )

		def __scriptAdded( scriptContainer, script ) :

			w = GafferUI.ScriptWindow.acquire( script )
			w.setTitle( "modified" )
			self.assertEqual( w.getTitle(), "modified" )

		a = testApp().root()
		GafferUI.ScriptWindow.connect( a )

		# Acquire and modify the ScriptWindow before it is
		# shown by the application to ensure that our modified
		# ScriptWindow survives to be the one shown.
		a["scripts"].childAddedSignal().connectFront( __scriptAdded )

		s = Gaffer.ScriptNode()
		a["scripts"]["s"] = s

		self.waitForIdle( 1000 )

		w = GafferUI.ScriptWindow.acquire( s )
		self.assertEqual( w.getTitle(), "modified" )

		del a["scripts"]["s"]

	def testTitleChangedSignal( self ) :

		self.__title = ""

		s = Gaffer.ScriptNode()
		w = GafferUI.ScriptWindow.acquire( s )

		initialTitle = w.setTitle( "a" )
		self.assertEqual( w.getTitle(), "a" )

		def grabTitle( window, newTitle ) :
			self.__title = newTitle

		w.titleChangedSignal().connect( grabTitle )

		w.setTitle( "b" )
		self.assertEqual( self.__title, "b" )

	def testInstanceCreatedSignal( self ) :

		cs = GafferTest.CapturingSlot( GafferUI.ScriptWindow.instanceCreatedSignal() )

		script1 = Gaffer.ScriptNode()
		script2 = Gaffer.ScriptNode()
		self.assertEqual( len( cs ), 0 )

		scriptWindow1 = GafferUI.ScriptWindow( script1 )
		self.assertEqual( len( cs ), 1 )
		self.assertIs( cs[0][0], scriptWindow1 )

		scriptWindow2 = GafferUI.ScriptWindow.acquire( script2 )
		self.assertEqual( len( cs ), 2 )
		self.assertIs( cs[1][0], scriptWindow2 )

		application = Gaffer.Application()
		GafferUI.ScriptWindow.connect( application.root() )
		application.root()["scripts"].addChild( Gaffer.ScriptNode() )
		self.assertEqual( len( cs ), 3 )
		self.assertIs(
			cs[2][0],
			GafferUI.ScriptWindow.acquire( application.root()["scripts"][0], createIfNecessary = False )
		)

		del application.root()["scripts"][0]

if __name__ == "__main__":
	unittest.main()
