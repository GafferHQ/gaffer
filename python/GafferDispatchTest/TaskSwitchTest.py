##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import GafferDispatch
import GafferDispatchTest

class TaskSwitchTest( GafferTest.TestCase ) :

	def __dispatcher( self ) :

		result = GafferDispatch.LocalDispatcher( jobPool = GafferDispatch.LocalDispatcher.JobPool() )
		result["jobsDirectory"].setValue( self.temporaryDirectory() / "jobs" )

		return result

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["c1"] = GafferDispatchTest.LoggingTaskNode()
		s["c2"] = GafferDispatchTest.LoggingTaskNode()

		s["s"] = GafferDispatch.TaskSwitch()
		self.assertEqual( s["s"]["index"].getValue(), 0 )

		s["s"]["preTasks"][0].setInput( s["c1"]["task"] )
		s["s"]["preTasks"][1].setInput( s["c2"]["task"] )

		s["d"] = self.__dispatcher()
		s["d"]["tasks"][0].setInput( s["s"]["task"] )
		s["d"]["task"].execute()

		self.assertEqual( len( s["c1"].log ), 1 )
		self.assertEqual( len( s["c2"].log ), 0 )

		s["s"]["index"].setValue( 1 )
		s["d"]["task"].execute()

		self.assertEqual( len( s["c1"].log ), 1 )
		self.assertEqual( len( s["c2"].log ), 1 )

		s["s"]["index"].setValue( 2 )
		s["d"]["task"].execute()

		self.assertEqual( len( s["c1"].log ), 2 )
		self.assertEqual( len( s["c2"].log ), 1 )

	def testIndexExpression( self ) :

		s = Gaffer.ScriptNode()

		s["c1"] = GafferDispatchTest.LoggingTaskNode()
		s["c2"] = GafferDispatchTest.LoggingTaskNode()
		s["c3"] = GafferDispatchTest.LoggingTaskNode()

		s["s"] = GafferDispatch.TaskSwitch()
		s["s"]["preTasks"][0].setInput( s["c1"]["task"] )
		s["s"]["preTasks"][1].setInput( s["c2"]["task"] )
		s["s"]["preTasks"][2].setInput( s["c3"]["task"] )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['s']['index'] = context.getFrame()" )

		s["d"] = self.__dispatcher()
		s["d"]["tasks"][0].setInput( s["s"]["task"] )

		with Gaffer.Context() as c :

			c.setFrame( 0 )
			s["d"]["task"].execute()

			self.assertEqual( len( s["c1"].log ), 1 )
			self.assertEqual( len( s["c2"].log ), 0 )
			self.assertEqual( len( s["c3"].log ), 0 )

			c.setFrame( 1 )
			s["d"]["task"].execute()

			self.assertEqual( len( s["c1"].log ), 1 )
			self.assertEqual( len( s["c2"].log ), 1 )
			self.assertEqual( len( s["c3"].log ), 0 )

			c.setFrame( 2 )
			s["d"]["task"].execute()

			self.assertEqual( len( s["c1"].log ), 1 )
			self.assertEqual( len( s["c2"].log ), 1 )
			self.assertEqual( len( s["c3"].log ), 1 )

			c.setFrame( 3 )
			s["d"]["task"].execute()

			self.assertEqual( len( s["c1"].log ), 2 )
			self.assertEqual( len( s["c2"].log ), 1 )
			self.assertEqual( len( s["c3"].log ), 1 )

	def testUnconnectedIndex( self ) :

		s = Gaffer.ScriptNode()

		s["c1"] = GafferDispatchTest.LoggingTaskNode()
		s["c2"] = GafferDispatchTest.LoggingTaskNode()

		s["s"] = GafferDispatch.TaskSwitch()
		s["s"]["preTasks"][0].setInput( s["c1"]["task"] )
		s["s"]["preTasks"][1].setInput( s["c2"]["task"] )
		s["s"]["preTasks"][0].setInput( None )
		s["s"]["index"].setValue( 0 )

		s["d"] = self.__dispatcher()
		s["d"]["tasks"][0].setInput( s["s"]["task"] )

		s["d"]["task"].execute()

		self.assertEqual( len( s["c1"].log ), 0 )
		self.assertEqual( len( s["c1"].log ), 0 )

	def testDirectCycles( self ) :

		s = Gaffer.ScriptNode()
		s["s"] = GafferDispatch.TaskSwitch()

		with IECore.CapturingMessageHandler() as mh :
			s["s"]["preTasks"][0].setInput( s["s"]["task"] )
		self.assertEqual( len( mh.messages ), 1 )
		self.assertRegex( mh.messages[0].message, "Cycle detected between ScriptNode.s.preTasks.preTask0 and ScriptNode.s.task" )

		s["d"] = self.__dispatcher()
		s["d"]["tasks"][0].setInput( s["s"]["task"] )
		self.assertRaisesRegex( RuntimeError, "cannot have cyclic dependencies", s["d"]["task"].execute )

if __name__ == "__main__":
	unittest.main()
