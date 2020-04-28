##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

class UndoTest( GafferTest.TestCase ) :

	def testSetName( self ) :

		s = Gaffer.ScriptNode()
		self.assertEqual( s.undoAvailable(), False )
		self.assertEqual( s.redoAvailable(), False )
		self.assertRaises( Exception, s.undo )

		n = Gaffer.Node()

		s["a"] = n
		self.assertEqual( n.getName(), "a" )

		n.setName( "b" )
		self.assertEqual( n.getName(), "b" )
		self.assertEqual( s.undoAvailable(), False )
		self.assertEqual( s.redoAvailable(), False )
		self.assertRaises( Exception, s.undo )

		with Gaffer.UndoScope( s ) :
			n.setName( "c" )

		self.assertEqual( s.undoAvailable(), True )
		self.assertEqual( s.redoAvailable(), False )
		s.undo()
		self.assertEqual( s.undoAvailable(), False )
		self.assertEqual( s.redoAvailable(), True )
		self.assertEqual( n.getName(), "b" )

		s.redo()
		self.assertEqual( s.undoAvailable(), True )
		self.assertEqual( s.redoAvailable(), False )
		self.assertEqual( n.getName(), "c" )
		self.assertRaises( Exception, s.redo )

	def testSetInput( self ) :

		s = Gaffer.ScriptNode()

		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()

		s["n1"] = n1
		s["n2"] = n2

		with Gaffer.UndoScope( s ) :
			n1["op1"].setInput( n2["sum"] )

		self.assertTrue( n1["op1"].getInput().isSame( n2["sum"] ) )

		s.undo()
		self.assertEqual( n1["op1"].getInput(), None )

		s.redo()
		self.assertTrue( n1["op1"].getInput().isSame( n2["sum"] ) )

	def testChildren( self ) :

		s = Gaffer.ScriptNode()
		n = Gaffer.Node()

		self.assertEqual( n.parent(), None )

		with Gaffer.UndoScope( s ) :
			s["n"] = n
		self.assertTrue( n.parent().isSame( s ) )
		s.undo()
		self.assertEqual( n.parent(), None )
		s.redo()
		self.assertTrue( n.parent().isSame( s ) )

	def testDelete( self ) :

		s = Gaffer.ScriptNode()
		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()
		n3 = GafferTest.AddNode()

		s.addChild( n1 )
		s.addChild( n2 )
		s.addChild( n3 )

		n2["op1"].setInput( n1["sum"] )
		n2["op2"].setInput( n1["sum"] )
		n3["op1"].setInput( n2["sum"] )
		n3["op2"].setInput( n2["sum"] )
		self.assertTrue( n2["op1"].getInput().isSame( n1["sum"] ) )
		self.assertTrue( n2["op2"].getInput().isSame( n1["sum"] ) )
		self.assertTrue( n3["op1"].getInput().isSame( n2["sum"] ) )
		self.assertTrue( n3["op2"].getInput().isSame( n2["sum"] ) )

		with Gaffer.UndoScope( s ) :
			s.deleteNodes( filter = Gaffer.StandardSet( [ n2 ] ) )

		self.assertEqual( n2["op1"].getInput(), None )
		self.assertEqual( n2["op2"].getInput(), None )
		self.assertTrue( n3["op1"].getInput().isSame( n1["sum"] ) )
		self.assertTrue( n3["op2"].getInput().isSame( n1["sum"] ) )

		s.undo()

		self.assertTrue( n2["op1"].getInput().isSame( n1["sum"] ) )
		self.assertTrue( n2["op2"].getInput().isSame( n1["sum"] ) )
		self.assertTrue( n3["op1"].getInput().isSame( n2["sum"] ) )
		self.assertTrue( n3["op2"].getInput().isSame( n2["sum"] ) )

		with Gaffer.UndoScope( s ) :
			s.deleteNodes( filter = Gaffer.StandardSet( [ n2 ] ), reconnect = False )

		self.assertEqual( n2["op1"].getInput(), None )
		self.assertEqual( n2["op2"].getInput(), None )
		self.assertEqual( n3["op1"].getInput(), None )
		self.assertEqual( n3["op2"].getInput(), None )

		s.undo()

		self.assertTrue( n2["op1"].getInput().isSame( n1["sum"] ) )
		self.assertTrue( n2["op2"].getInput().isSame( n1["sum"] ) )
		self.assertTrue( n3["op1"].getInput().isSame( n2["sum"] ) )
		self.assertTrue( n3["op2"].getInput().isSame( n2["sum"] ) )

	def testDisable( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		with Gaffer.UndoScope( s, Gaffer.UndoScope.State.Disabled ) :
			s["n"]["op1"].setValue( 10 )

		self.assertFalse( s.undoAvailable() )

		with Gaffer.UndoScope( s, Gaffer.UndoScope.State.Enabled ) :
			with Gaffer.UndoScope( s, Gaffer.UndoScope.State.Disabled ) :
				s["n"]["op1"].setValue( 20 )

		self.assertFalse( s.undoAvailable() )

if __name__ == "__main__":
	unittest.main()
