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

import Gaffer
import GafferTest

class TaskSwitchTest( GafferTest.TestCase ) :

	def __dispatcher( self ) :

		result = Gaffer.LocalDispatcher()
		result["jobsDirectory"].setValue( self.temporaryDirectory() + "/jobs" )

		return result

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["c1"] = GafferTest.CountingExecutableNode()
		s["c2"] = GafferTest.CountingExecutableNode()

		s["s"] = Gaffer.TaskSwitch()
		self.assertEqual( s["s"]["index"].getValue(), 0 )

		s["s"]["requirements"][0].setInput( s["c1"]["requirement"] )
		s["s"]["requirements"][1].setInput( s["c2"]["requirement"] )

		d = self.__dispatcher()
		d.dispatch( [ s["s"] ] )

		self.assertEqual( s["c1"].executionCount, 1 )
		self.assertEqual( s["c2"].executionCount, 0 )

		s["s"]["index"].setValue( 1 )
		d.dispatch( [ s["s"] ] )

		self.assertEqual( s["c1"].executionCount, 1 )
		self.assertEqual( s["c2"].executionCount, 1 )

		s["s"]["index"].setValue( 2 )
		d.dispatch( [ s["s"] ] )

		self.assertEqual( s["c1"].executionCount, 2 )
		self.assertEqual( s["c2"].executionCount, 1 )

	def testIndexExpression( self ) :

		s = Gaffer.ScriptNode()

		s["c1"] = GafferTest.CountingExecutableNode()
		s["c2"] = GafferTest.CountingExecutableNode()
		s["c3"] = GafferTest.CountingExecutableNode()

		s["s"] = Gaffer.TaskSwitch()
		s["s"]["requirements"][0].setInput( s["c1"]["requirement"] )
		s["s"]["requirements"][1].setInput( s["c2"]["requirement"] )
		s["s"]["requirements"][2].setInput( s["c3"]["requirement"] )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['s']['index'] = context.getFrame()" )

		d = self.__dispatcher()
		with Gaffer.Context() as c :

			c.setFrame( 0 )
			d.dispatch( [ s["s"] ] )

			self.assertEqual( s["c1"].executionCount, 1 )
			self.assertEqual( s["c2"].executionCount, 0 )
			self.assertEqual( s["c3"].executionCount, 0 )

			c.setFrame( 1 )
			d.dispatch( [ s["s"] ] )

			self.assertEqual( s["c1"].executionCount, 1 )
			self.assertEqual( s["c2"].executionCount, 1 )
			self.assertEqual( s["c3"].executionCount, 0 )

			c.setFrame( 2 )
			d.dispatch( [ s["s"] ] )

			self.assertEqual( s["c1"].executionCount, 1 )
			self.assertEqual( s["c2"].executionCount, 1 )
			self.assertEqual( s["c3"].executionCount, 1 )

			c.setFrame( 3 )
			d.dispatch( [ s["s"] ] )

			self.assertEqual( s["c1"].executionCount, 2 )
			self.assertEqual( s["c2"].executionCount, 1 )
			self.assertEqual( s["c3"].executionCount, 1 )

	def testUnconnectedIndex( self ) :

		s = Gaffer.ScriptNode()

		s["c1"] = GafferTest.CountingExecutableNode()
		s["c2"] = GafferTest.CountingExecutableNode()

		s["s"] = Gaffer.TaskSwitch()
		s["s"]["requirements"][0].setInput( s["c1"]["requirement"] )
		s["s"]["requirements"][1].setInput( s["c2"]["requirement"] )
		s["s"]["requirements"][0].setInput( None )
		s["s"]["index"].setValue( 0 )

		d = self.__dispatcher()

		d.dispatch( [ s["s"] ] )

		self.assertEqual( s["c1"].executionCount, 0 )
		self.assertEqual( s["c2"].executionCount, 0 )

if __name__ == "__main__":
	unittest.main()

