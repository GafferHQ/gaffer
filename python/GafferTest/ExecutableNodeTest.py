##########################################################################
#
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

class ExecutableNodeTest( GafferTest.TestCase ) :

	class MyNode( Gaffer.ExecutableNode ) :

		def __init__( self, withHash, requiresSequenceExecution = False ) :

			Gaffer.ExecutableNode.__init__( self )

			self.__requiresSequenceExecution = requiresSequenceExecution

			self.__withHash = withHash
			self.executionCount = 0

		def execute( self ) :

			self.executionCount += 1

		def executeSequence( self, frames ) :

			if not self.__requiresSequenceExecution :
				Gaffer.ExecutableNode.executeSequence( self, frames )
				return

			self.executionCount += 1

		def hash( self, context ) :

			if not self.__withHash :
				return IECore.MurmurHash()

			h = Gaffer.ExecutableNode.hash( self, context )
			h.append( context.getFrame() )
			return h

		def requiresSequenceExecution( self ) :

			return self.__requiresSequenceExecution

	IECore.registerRunTimeTyped( MyNode )

	def testIsExecutable( self ) :

		self.assertTrue( issubclass( self.MyNode, Gaffer.ExecutableNode ) )
		self.assertTrue( isinstance( self.MyNode( True ), Gaffer.ExecutableNode ) )

	def testHash( self ) :

		c1 = Gaffer.Context()
		c1.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )
		c3 = Gaffer.Context()
		c3.setFrame( 3.0 )

		# hashes that don't use the context are equivalent
		n = ExecutableNodeTest.MyNode(False)
		self.assertEqual( n.hash( c1 ), n.hash( c1 ) )
		self.assertEqual( n.hash( c1 ), n.hash( c2 ) )
		self.assertEqual( n.hash( c1 ), n.hash( c3 ) )

		# hashes that do use the context differ
		n2 = ExecutableNodeTest.MyNode(True)
		self.assertEqual( n2.hash( c1 ), n2.hash( c1 ) )
		self.assertNotEqual( n2.hash( c1 ), n2.hash( c2 ) )
		self.assertNotEqual( n2.hash( c1 ), n2.hash( c3 ) )

		# hashes match across the same node type
		n3 = ExecutableNodeTest.MyNode(True)
		self.assertEqual( n2.hash( c1 ), n3.hash( c1 ) )
		self.assertEqual( n2.hash( c2 ), n3.hash( c2 ) )
		self.assertEqual( n2.hash( c3 ), n3.hash( c3 ) )

		# hashes differ across different node types
		class MyNode2( ExecutableNodeTest.MyNode ) :
			def __init__( self ) :
				ExecutableNodeTest.MyNode.__init__( self, True )

		IECore.registerRunTimeTyped( MyNode2 )

		n4 = MyNode2()

		self.assertNotEqual( n4.hash( c1 ), n3.hash( c1 ) )
		self.assertNotEqual( n4.hash( c2 ), n3.hash( c2 ) )
		self.assertNotEqual( n4.hash( c3 ), n3.hash( c3 ) )

	def testExecute( self ) :

		n = ExecutableNodeTest.MyNode(True)
		self.assertEqual( n.executionCount, 0 )

		n.execute()
		self.assertEqual( n.executionCount, 1 )

		n.execute()
		self.assertEqual( n.executionCount, 2 )

		c = Gaffer.Context()
		c.setFrame( Gaffer.Context.current().getFrame() + 1 )
		with c :
			n.execute()
		self.assertEqual( n.executionCount, 3 )

	def testExecuteSequence( self ) :

		n = ExecutableNodeTest.MyNode(True)
		self.assertEqual( n.executionCount, 0 )

		n.executeSequence( [ 1, 2, 3 ] )
		self.assertEqual( n.executionCount, 3 )

		n.executeSequence( [ 1, 5, 10 ] )
		self.assertEqual( n.executionCount, 6 )

		# requiring execution doesn't tally the count per frame
		n2 = ExecutableNodeTest.MyNode( True, requiresSequenceExecution = True )
		self.assertEqual( n2.executionCount, 0 )

		n2.executeSequence( [ 1, 2, 3 ] )
		self.assertEqual( n2.executionCount, 1 )

		n2.executeSequence( [ 1, 5, 10 ] )
		self.assertEqual( n2.executionCount, 2 )

	def testRequiresSequenceExecution( self ) :

		n = ExecutableNodeTest.MyNode(True)
		self.assertEqual( n.requiresSequenceExecution(), False )

	def testRequirements( self ) :
		"""Test the function requirements and Executable::defaultRequirements """

		c1 = Gaffer.Context()
		c1.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		n = ExecutableNodeTest.MyNode(True)
		n2 = ExecutableNodeTest.MyNode(True)

		# make n2 require n
		n2["requirements"][0].setInput( n['requirement'] )

		self.assertEqual( n.requirements(c1), [] )
		self.assertEqual( n2.requirements(c1), [ Gaffer.ExecutableNode.Task( n, c1 ) ] )
		self.assertEqual( n2.requirements(c2), [ Gaffer.ExecutableNode.Task( n, c2 ) ] )

	def testTaskConstructors( self ) :

		c = Gaffer.Context()

		n = Gaffer.ExecutableOpHolder()
		t = Gaffer.ExecutableNode.Task( n, c )
		t2 = Gaffer.ExecutableNode.Task( n, c )
		t3 = Gaffer.ExecutableNode.Task( t2 )

		self.assertEqual( t.node(), n )
		self.assertEqual( t.context(), c )
		self.assertEqual( t2.node(), n )
		self.assertEqual( t2.context(), c )
		self.assertEqual( t3.node(), n )
		self.assertEqual( t3.context(), c )

	def testTaskComparison( self ) :

		c = Gaffer.Context()
		n = Gaffer.ExecutableOpHolder()
		t1 = Gaffer.ExecutableNode.Task( n, c )
		t2 = Gaffer.ExecutableNode.Task( n, c )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = Gaffer.ExecutableNode.Task( n, c2 )
		n2 = Gaffer.ExecutableOpHolder()
		t4 = Gaffer.ExecutableNode.Task( n2, c2 )

		self.assertEqual( t1, t1 )
		self.assertEqual( t1, t2 )
		self.assertEqual( t2, t1 )
		self.assertNotEqual( t1, t3 )
		self.assertNotEqual( t3, t1 )
		self.assertNotEqual( t3, t4 )
		self.assertNotEqual( t4, t3 )

	def testTaskSet( self ) :

		# an empty ExecutableOpHolder doesn't actually compute anything, so all tasks are the same
		c = Gaffer.Context()
		n = Gaffer.ExecutableOpHolder()
		t1 = Gaffer.ExecutableNode.Task( n, c )
		t2 = Gaffer.ExecutableNode.Task( n, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = Gaffer.ExecutableNode.Task( n, c2 )
		self.assertEqual( t1, t3 )
		n2 = Gaffer.ExecutableOpHolder()
		t4 = Gaffer.ExecutableNode.Task( n2, c2 )
		self.assertEqual( t1, t4 )
		t5 = Gaffer.ExecutableNode.Task( n2, c )
		self.assertEqual( t1, t5 )

		s = set( [ t1, t2, t3, t4, t4, t4, t1, t2, t4, t3, t2 ] )
		# there should only be 1 task because they all have identical results
		self.assertEqual( len(s), 1 )
		self.assertEqual( s, set( [ t1 ] ) )
		self.assertTrue( t1 in s )
		self.assertTrue( t2 in s )
		self.assertTrue( t3 in s )
		self.assertTrue( t4 in s )
		# even t5 is in there, because it's really the same task
		self.assertTrue( t5 in s )

		# MyNode.hash() depends on the context time, so tasks will vary
		my = ExecutableNodeTest.MyNode( True )
		c.setFrame( 1 )
		t1 = Gaffer.ExecutableNode.Task( my, c )
		t2 = Gaffer.ExecutableNode.Task( my, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )
		t3 = Gaffer.ExecutableNode.Task( my, c2 )
		self.assertNotEqual( t1, t3 )
		my2 = ExecutableNodeTest.MyNode( True )
		t4 = Gaffer.ExecutableNode.Task( my2, c2 )
		self.assertNotEqual( t1, t4 )
		self.assertEqual( t3, t4 )
		t5 = Gaffer.ExecutableNode.Task( my2, c )
		self.assertEqual( t1, t5 )
		self.assertNotEqual( t3, t5 )

		s = set( [ t1, t2, t3, t4, t4, t4, t1, t2, t4, t3, t2 ] )
		# t1 and t3 are the only distinct tasks
		self.assertEqual( len(s), 2 )
		self.assertEqual( s, set( [ t1, t3 ] ) )
		# but they still all have equivalent tasks in the set
		self.assertTrue( t1 in s )
		self.assertTrue( t2 in s )
		self.assertTrue( t3 in s )
		self.assertTrue( t4 in s )
		self.assertTrue( t5 in s )

	def testInputAcceptanceInsideBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["a"] = GafferTest.TextWriter()
		s["b"] = GafferTest.TextWriter()
		s["n"] = Gaffer.Node()
		s["n"]["requirement"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )

		# the ExecutableNode shouldn't accept inputs from any old node

		self.assertTrue( s["b"]["requirements"][0].acceptsInput( s["a"]["requirement"] ) )
		self.assertFalse( s["b"]["requirements"][0].acceptsInput( s["n"]["requirement"] ) )

		# and that shouldn't change just because we happen to be inside a box

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["a"], s["b"], s["n"] ] ) )

		self.assertTrue( b["b"]["requirements"][0].acceptsInput( b["a"]["requirement"] ) )
		self.assertFalse( b["b"]["requirements"][0].acceptsInput( b["n"]["requirement"] ) )

	def testInputAcceptanceFromBoxes( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["requirement"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["a"] = GafferTest.TextWriter()

		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferTest.TextWriter()
		s["b"]["b"] = GafferTest.TextWriter()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["requirement"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out )
		s["b"]["in"] = s["b"]["a"]["requirements"][0].createCounterpart( "in", Gaffer.Plug.Direction.In )
		s["b"]["out"] = s["b"]["a"]["requirement"].createCounterpart( "out", Gaffer.Plug.Direction.Out )

		# ExecutableNodes should accept connections speculatively from unconnected box inputs and outputs

		self.assertTrue( s["b"]["a"]["requirements"][0].acceptsInput( s["b"]["in"] ) )
		self.assertTrue( s["a"]["requirements"][0].acceptsInput( s["b"]["out"] ) )

		# but should reject connections to connected box inputs and outputs if they're unsuitable.

		s["b"]["in"].setInput( s["n"]["requirement"] )
		self.assertFalse( s["b"]["a"]["requirements"][0].acceptsInput( s["b"]["in"] ) )

		s["b"]["out"].setInput( s["b"]["n"]["requirement"] )
		self.assertFalse( s["a"]["requirements"][0].acceptsInput( s["b"]["out"] ) )

		# and accept them again if they provide indirect access to an ExecutableNode

		s["c"] = GafferTest.TextWriter()
		s["b"]["in"].setInput( s["c"]["requirement"] )
		self.assertTrue( s["b"]["a"]["requirements"][0].acceptsInput( s["b"]["in"] ) )

		s["b"]["out"].setInput( s["b"]["b"]["requirement"] )
		self.assertTrue( s["a"]["requirements"][0].acceptsInput( s["b"]["out"] ) )

if __name__ == "__main__":
	unittest.main()

