##########################################################################
#  
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

class ExecutableNodeTest( unittest.TestCase ) :

	class MyNode( Gaffer.ExecutableNode ) :

		def __init__( self, withHash ) :

			Gaffer.ExecutableNode.__init__( self )
			self.__withHash = withHash
			self.executionCount = 0

		def execute( self, contexts ):
			
			self.executionCount += 1

		def executionHash( self, context ) :

			h = IECore.MurmurHash()

			if self.__withHash :

				h.append( context['time'] )

			return h

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

		n = ExecutableNodeTest.MyNode(False)

		taskList = list()
		taskList.append( Gaffer.ExecutableNode.Task( n, c1 ) )
		taskList.append( Gaffer.ExecutableNode.Task( n, c2 ) )
		taskList.append( Gaffer.ExecutableNode.Task( n, c3 ) )

		# since the hash is the same, no matter the context, it should return one single task
		self.assertEqual( Gaffer.Despatcher._uniqueTasks( taskList ), [ ( Gaffer.ExecutableNode.Task( n, c1 ), [] ) ] )

		n2 = ExecutableNodeTest.MyNode(True)

		taskList = list()
		taskList.append( Gaffer.ExecutableNode.Task( n2, c1 ) )
		taskList.append( Gaffer.ExecutableNode.Task( n2, c2 ) )
		taskList.append( Gaffer.ExecutableNode.Task( n2, c3 ) )

		# since the hash includes the 'time' each Task is considered diferent
		self.assertEqual( Gaffer.Despatcher._uniqueTasks( taskList ), [ ( Gaffer.ExecutableNode.Task( n2, c1 ), [] ), ( Gaffer.ExecutableNode.Task( n2, c2 ), [] ), ( Gaffer.ExecutableNode.Task( n2, c3 ), [] ) ] )

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

		# if we ask for executing n2 we should get n followed by n2
		l = list()
		l.append( Gaffer.ExecutableNode.Task( n2, c1 ) )
		Gaffer.Despatcher._uniqueTasks( l )
		( Gaffer.ExecutableNode.Task( n, c1 ), [] )
		( Gaffer.ExecutableNode.Task( n2, c1 ), [ Gaffer.ExecutableNode.Task( n, c1 ) ] )

		self.assertEqual( Gaffer.Despatcher._uniqueTasks( [ Gaffer.ExecutableNode.Task( n2, c1 ) ] ), [ ( Gaffer.ExecutableNode.Task( n, c1 ), [] ), ( Gaffer.ExecutableNode.Task( n2, c1 ), [ Gaffer.ExecutableNode.Task( n, c1 ) ] ) ] )

	def testExecute( self ):

		n = ExecutableNodeTest.MyNode(False)

		n2 = ExecutableNodeTest.MyNode(False)

		# make n3 requiring n
		r1 = Gaffer.Plug( name = "r1" )
		n2['requirements'].addChild( r1 )
		r1.setInput( n['requirement'] )

		despatcher = Gaffer.Despatcher.despatcher("local")

		self.assertEqual( n2.executionCount, 0 )
		self.assertEqual( n.executionCount, 0 )

		despatcher.despatch( [ n2 ] )

		self.assertEqual( n2.executionCount, 1 )
		self.assertEqual( n.executionCount, 1 )

	def testTaskConstructors( self ) :
	
		c = Gaffer.Context()

		t = Gaffer.ExecutableNode.Task()
		n = Gaffer.ExecutableOpHolder()
		t.node = n
		t.context = c
		
		t2 = Gaffer.ExecutableNode.Task( n, c )

		t3 = Gaffer.ExecutableNode.Task( t2 )

		self.assertEqual( t.node, n )
		self.assertEqual( t.context, c )
		self.assertEqual( t2.node, n )
		self.assertEqual( t2.context, c )
		self.assertEqual( t3.node, n )
		self.assertEqual( t3.context, c )

	def testTaskComparison( self ) :

		c = Gaffer.Context()
		n = Gaffer.ExecutableOpHolder()
		t1 = Gaffer.ExecutableNode.Task( n, c )
		t2 = Gaffer.ExecutableNode.Task()
		t2.node = n
		t2.context = c
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

		c = Gaffer.Context()
		n = Gaffer.ExecutableOpHolder()
		t1 = Gaffer.ExecutableNode.Task( n, c )
		t2 = Gaffer.ExecutableNode.Task( n, c )
		self.assertEqual( t1, t2 )
		c2 = Gaffer.Context()
		c2["a"] = 2
		t3 = Gaffer.ExecutableNode.Task( n, c2 )
		n2 = Gaffer.ExecutableOpHolder()
		t4 = Gaffer.ExecutableNode.Task( n2, c2 )
		t5 = Gaffer.ExecutableNode.Task( n2, c )

		s = set( [ t1, t2, t3, t4, t4, t4, t1, t2, t4, t3, t2 ] )
		self.assertEqual( len(s), 3 )
		self.assertEqual( s, set( [ t1, t3, t4 ] ) )
		self.assertTrue( t1 in s )
		self.assertTrue( t2 in s )
		self.assertTrue( t3 in s )
		self.assertTrue( t4 in s )
		self.assertFalse( t5 in s )

if __name__ == "__main__":
	unittest.main()
	
