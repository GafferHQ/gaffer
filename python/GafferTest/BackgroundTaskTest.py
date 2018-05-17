##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

import functools
import thread
import threading
import time

import IECore

import Gaffer
import GafferTest

class BackgroundTaskTest( GafferTest.TestCase ) :

	def testManualCancellation( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		def f( canceller ) :

			s["n"]["sum"].getValue()
			with self.assertRaises( IECore.Cancelled ) :
				while True :
					IECore.Canceller.check( canceller )

		t = Gaffer.BackgroundTask( s["n"]["sum"], f )
		t.cancelAndWait()

		self.assertTrue( t.done() )

	def testGraphEditCancellation( self ) :

		operations = []

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		c = s["n"].plugSetSignal().connect(
			lambda plug : operations.append( "set" )
		)

		def f( canceller ) :

			operations.append( "background" )
			with self.assertRaises( IECore.Cancelled ) :
				while True :
					s["n"]["sum"].getValue()
					IECore.Canceller.check( canceller )

		s["n"]["op1"].setValue( 10 )
		t = Gaffer.BackgroundTask( s["n"]["sum"], f )
		s["n"]["op1"].setValue( 20 )

		self.assertEqual( operations, [ "set", "background", "set" ] )

	def testUndoRedoCancellation( self ) :

		operations = []

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		with Gaffer.UndoScope( s ) :
			s["n"]["op1"].setValue( 10 )

		def f( canceller ) :

			operations.append( "background" )
			with self.assertRaises( IECore.Cancelled ) :
				while True :
					s["n"]["sum"].getValue()
					IECore.Canceller.check( canceller )

		c = s["n"].plugSetSignal().connect(
			lambda plug : operations.append( "undo" )
		)
		t = Gaffer.BackgroundTask( s["n"]["sum"], f )
		s.undo()

		self.assertEqual( operations, [ "background", "undo" ] )

		del operations[:]
		c = s["n"].plugSetSignal().connect(
			lambda plug : operations.append( "redo" )
		)
		t = Gaffer.BackgroundTask( s["n"]["sum"], f )
		s.redo()

		self.assertEqual( operations, [ "background", "redo" ] )

	def testExceptionHandling( self ) :

		def f( canceller ) :

			raise RuntimeError( "Oops!" )

		originalMessageHandler = IECore.MessageHandler.getDefaultHandler()
		mh = IECore.CapturingMessageHandler()
		IECore.MessageHandler.setDefaultHandler( mh )

		try :
			t = Gaffer.BackgroundTask( None, f )
			t.wait()
		finally :
			IECore.MessageHandler.setDefaultHandler( originalMessageHandler )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Error )
		self.assertEqual( mh.messages[0].context, "BackgroundTask" )
		self.assertIn( "Oops!", mh.messages[0].message )

	def testScriptNodeLifetime( self ) :

		def f( canceller, plug ) :

			while True :
				self.assertIsNotNone( plug.ancestor( Gaffer.ScriptNode ) )
				self.assertEqual( plug.getValue(), 0 )
				IECore.Canceller.check( canceller )

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		t = Gaffer.BackgroundTask( s["n"]["sum"], functools.partial( f, plug = s["n"]["sum"] ) )

		# Drop our reference to the script, and sleep for
		# a bit to demonstrate that the background task can
		# still operate.
		del s
		time.sleep( 0.25 )

		# Cancel the task. This should drop the final reference
		# to the script.
		t.cancelAndWait()

	def testScriptNodeRemovalCancellation( self ) :

		def f( canceller ) :

			while True :
				IECore.Canceller.check( canceller )

		a = Gaffer.ApplicationRoot()
		a["scripts"]["s"] = Gaffer.ScriptNode()
		a["scripts"]["s"]["n"] = GafferTest.AddNode()

		# If not cancelled, this task will spin forever.
		t = Gaffer.BackgroundTask( a["scripts"]["s"]["n"]["sum"], f )
		# But removing the script from the application should cancel it.
		del a["scripts"]["s"]
		t.wait()

if __name__ == "__main__":
	unittest.main()
