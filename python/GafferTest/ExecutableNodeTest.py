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

		def __init__( self, withHash ) :

			Gaffer.ExecutableNode.__init__( self )
			self.__withHash = withHash
			self.executionCount = 0

		def execute( self, contexts ):
			
			self.executionCount += 1

		def executionHash( self, context ) :

			if not self.__withHash :
				return IECore.MurmurHash()
			
			h = Gaffer.ExecutableNode.executionHash( self, context )
			h.append( self.typeId() )
			h.append( context['time'] )
			return h
		
	IECore.registerRunTimeTyped( MyNode )

	def testIsExecutable( self ) :

		self.assertTrue( issubclass( self.MyNode, Gaffer.ExecutableNode ) )
		self.assertTrue( isinstance( self.MyNode( True ), Gaffer.ExecutableNode ) )

	def testExecutionHash( self ) :

		c1 = Gaffer.Context()
		c1['time'] = 1.0
		c2 = Gaffer.Context()
		c2['time'] = 2.0
		c3 = Gaffer.Context()
		c3['time'] = 3.0

		# hashes that don't use the context are equivalent
		n = ExecutableNodeTest.MyNode(False)
		self.assertEqual( n.executionHash( c1 ), n.executionHash( c1 ) )
		self.assertEqual( n.executionHash( c1 ), n.executionHash( c2 ) )
		self.assertEqual( n.executionHash( c1 ), n.executionHash( c3 ) )
		
		# hashes that do use the context differ
		n2 = ExecutableNodeTest.MyNode(True)
		self.assertEqual( n2.executionHash( c1 ), n2.executionHash( c1 ) )
		self.assertNotEqual( n2.executionHash( c1 ), n2.executionHash( c2 ) )
		self.assertNotEqual( n2.executionHash( c1 ), n2.executionHash( c3 ) )
		
		# hashes match across the same node type
		n3 = ExecutableNodeTest.MyNode(True)
		self.assertEqual( n2.executionHash( c1 ), n3.executionHash( c1 ) )
		self.assertEqual( n2.executionHash( c2 ), n3.executionHash( c2 ) )
		self.assertEqual( n2.executionHash( c3 ), n3.executionHash( c3 ) )
		
		# hashes differ across different node types
		class MyNode2( ExecutableNodeTest.MyNode ) :
			def __init__( self ) :
				ExecutableNodeTest.MyNode.__init__( self, True )
		
		IECore.registerRunTimeTyped( MyNode2 )
		
		n4 = MyNode2()
		
		self.assertNotEqual( n4.executionHash( c1 ), n3.executionHash( c1 ) )
		self.assertNotEqual( n4.executionHash( c2 ), n3.executionHash( c2 ) )
		self.assertNotEqual( n4.executionHash( c3 ), n3.executionHash( c3 ) )

	def testExecutionRequirements( self ) :
		"""Test the function executionRequirements and Executable::defaultRequirements """

		c1 = Gaffer.Context()
		c1['time'] = 1.0
		c2 = Gaffer.Context()
		c2['time'] = 2.0

		n = ExecutableNodeTest.MyNode(True)
		n2 = ExecutableNodeTest.MyNode(True)

		# make n2 require n
		n2["requirements"][0].setInput( n['requirement'] )

		self.assertEqual( n.executionRequirements(c1), [] )
		self.assertEqual( n2.executionRequirements(c1), [ Gaffer.ExecutableNode.Task( n, c1 ) ] )
		self.assertEqual( n2.executionRequirements(c2), [ Gaffer.ExecutableNode.Task( n, c2 ) ] )
	
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
		
		# MyNode.executionHash() depends on the context time, so tasks will vary
		my = ExecutableNodeTest.MyNode( True )
		c["time"] = 1.0
		t1 = Gaffer.ExecutableNode.Task( my, c )
		t2 = Gaffer.ExecutableNode.Task( my, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2["time"] = 2.0
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

if __name__ == "__main__":
	unittest.main()
	
