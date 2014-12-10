##########################################################################
#
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

import Gaffer
import GafferTest

class DotTest( GafferTest.TestCase ) :

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["d"] = Gaffer.Dot()
		s["d"].setup( s["n2"]["op1"] )

		s["d"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["op1"].setInput( s["d"]["out"] )

		self.assertTrue( s["n2"]["op1"].source().isSame( s["n1"]["sum"] ) )

	def testUndo( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["d"] = Gaffer.Dot()
		self.assertTrue( "in" not in s["d"] )
		self.assertTrue( "out" not in s["d"] )

		with Gaffer.UndoContext( s ) :
			s["d"].setup( s["n2"]["op1"] )
			s["d"]["in"].setInput( s["n1"]["sum"] )
			s["n2"]["op1"].setInput( s["d"]["out"] )

		self.assertTrue( s["n2"]["op1"].source().isSame( s["n1"]["sum"] ) )

		s.undo()

		self.assertTrue( "in" not in s["d"] )
		self.assertTrue( "out" not in s["d"] )

		s.redo()

		self.assertTrue( s["n2"]["op1"].source().isSame( s["n1"]["sum"] ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["d"] = Gaffer.Dot()
		s["d"].setup( s["n2"]["op1"] )

		s["d"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["op1"].setInput( s["d"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["n2"]["op1"].source().isSame( s2["n1"]["sum"] ) )

	def testDeletion( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["d"] = Gaffer.Dot()
		s["d"].setup( s["n2"]["op1"] )

		s["d"]["in"].setInput( s["n1"]["sum"] )
		s["n2"]["op1"].setInput( s["d"]["out"] )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["d"] ] ) )

		self.assertTrue( s["n2"]["op1"].getInput().isSame( s["n1"]["sum"] ) )

if __name__ == "__main__":
	unittest.main()
