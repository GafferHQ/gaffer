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

class TestOp (IECore.Op) :

	def __init__( self, name, executionOrder ) :

		IECore.Op.__init__( self, "Test op", IECore.IntParameter( "result", "", 0 ) )
		self.counter = 0
		self.name = name
		self.executionOrder = executionOrder

	def doOperation( self, args ) :

		self.counter += 1
		self.executionOrder.append( self )
		return IECore.IntData( self.counter )

class DespatcherTest( unittest.TestCase ) :

	class MyDespatcher( Gaffer.Despatcher ) :

		def __init__( self ) :

			Gaffer.Despatcher.__init__( self )
			self.log = list()

		def _doDespatch( self, nodes ) :

			c = Gaffer.Context()
			c['time'] = 1.0
			taskList = map( lambda n: Gaffer.ExecutableNode.Task(n,c), nodes )
			allTasksAndRequirements = Gaffer.Despatcher._uniqueTasks( taskList )
			del self.log[:]
			for (task,requirements) in allTasksAndRequirements :
				task.node.execute( [ task.context ] )

		def _addPlugs( self, despatcherPlug ) :

			despatcherPlug["testDespatcherPlug"] = Gaffer.IntPlug(
				direction = Gaffer.Plug.Direction.In,
				flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
			)

	def setUp( self ) :

		if not "testDespatcher" in Gaffer.Despatcher.despatcherNames():
			IECore.registerRunTimeTyped( DespatcherTest.MyDespatcher )
			despatcher = DespatcherTest.MyDespatcher()
			Gaffer.Despatcher._registerDespatcher( "testDespatcher", despatcher )

	def testDerivedClass( self ) :

		despatcher = DespatcherTest.MyDespatcher()

		op1 = TestOp("1", despatcher.log)
		n1 = Gaffer.ExecutableOpHolder()
		n1.setParameterised( op1 )

		despatcher.despatch( [ n1 ] )

		self.assertEqual( op1.counter, 1 )

	def testLocalDespatcher( self ) :

		log = list()
		op1 = TestOp("1", log)
		n1 = Gaffer.ExecutableOpHolder()
		n1.setParameterised( op1 )

		Gaffer.Despatcher.despatcher('local').despatch( [ n1 ] )

		self.assertEqual( op1.counter, 1 )

	def testDespatcherRegistration( self ) :

		self.failUnless( "testDespatcher" in Gaffer.Despatcher.despatcherNames() )
		self.failUnless( Gaffer.Despatcher.despatcher( 'testDespatcher' ).isInstanceOf( DespatcherTest.MyDespatcher.staticTypeId() ) )

	def testDespatcherSignals( self ) :

		class CapturingSlot2( list ) :
	
			def __init__( self, *signals ) :
		
				self.__connections = []
				for s in signals :
					self.__connections.append( s.connect( Gaffer.WeakMethod( self.__slot ) ) )
		
			def __slot( self, d, nodes ) :
				self.append( (d,nodes) )
	
		preCs = CapturingSlot2( Gaffer.Despatcher.preDespatchSignal() )
		self.assertEqual( len( preCs ), 0 )
		postCs = GafferTest.CapturingSlot( Gaffer.Despatcher.postDespatchSignal() )
		self.assertEqual( len( postCs ), 0 )

		log = list()
		op1 = TestOp("1", log)
		n1 = Gaffer.ExecutableOpHolder()
		n1.setParameterised( op1 )
		despatcher = Gaffer.Despatcher.despatcher('local')
		despatcher.despatch( [ n1 ] )
		
		self.assertEqual( len( preCs ), 1 )
		self.failUnless( preCs[0][0].isSame( despatcher ) )
		self.assertEqual( preCs[0][1], [ n1 ] )

		self.assertEqual( len( postCs ), 1 )
		self.failUnless( postCs[0][0].isSame( despatcher ) )
		self.assertEqual( postCs[0][1], [ n1 ] )

	def testPlugs( self ) :

		n = Gaffer.ExecutableOpHolder()
		n['despatcher'].direction()
		n['despatcher']['testDespatcherPlug'].direction()
		self.assertEqual( n['despatcher']['testDespatcherPlug'].direction(), Gaffer.Plug.Direction.In )

	def testDespatch( self ) :

		despatcher = Gaffer.Despatcher.despatcher( "testDespatcher" )

		# Create a tree of dependencies for execution:
		# n1 requires:
		# - n2 requires:
		#    -n2a
		#    -n2b
		op1 = TestOp("1", despatcher.log)
		n1 = Gaffer.ExecutableOpHolder()
		n1.setParameterised( op1 )
		n2 = Gaffer.ExecutableOpHolder()
		op2 = TestOp("2", despatcher.log)
		n2.setParameterised( op2 )
		n2a = Gaffer.ExecutableOpHolder()
		op2a = TestOp("2a", despatcher.log)
		n2a.setParameterised( op2a )
		n2b = Gaffer.ExecutableOpHolder()
		op2b = TestOp("2b", despatcher.log)
		n2b.setParameterised( op2b )

		r1 = Gaffer.Plug( name = "r1" )
		n1['requirements'].addChild( r1 )
		r1.setInput( n2['requirement'] )

		r1 = Gaffer.Plug( name = "r1" )
		n2['requirements'].addChild( r1 )
		r1.setInput( n2a['requirement'] )
		
		r2 = Gaffer.Plug( name = "r2" )
		n2['requirements'].addChild( r2 )
		r2.setInput( n2b['requirement'] )

		# Executing n1 should trigger execution of all of them
		despatcher.despatch( [ n1 ] )
		self.assertEqual( op1.counter, 1 )
		self.assertEqual( op2.counter, 1 )
		self.assertEqual( op2a.counter, 1 )
		self.assertEqual( op2b.counter, 1 )
		self.assertTrue( despatcher.log == [ op2a, op2b, op2, op1 ] or despatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing n1 and anything else, should be the same as just n1
		despatcher.despatch( [ n2b, n1 ] )
		self.assertEqual( op1.counter, 2 )
		self.assertEqual( op2.counter, 2 )
		self.assertEqual( op2a.counter, 2 )
		self.assertEqual( op2b.counter, 2 )
		self.assertTrue( despatcher.log == [ op2a, op2b, op2, op1 ] or despatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing all nodes should be the same as just n1
		despatcher.despatch( [ n2, n2b, n1, n2a ] )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 3 )
		self.assertEqual( op2a.counter, 3 )
		self.assertEqual( op2b.counter, 3 )
		self.assertTrue( despatcher.log == [ op2a, op2b, op2, op1 ] or despatcher.log == [ op2b, op2a, op2, op1 ] )

		# Executing a sub-branch (n2) should only trigger execution in that branch
		despatcher.despatch( [ n2 ] )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 4 )
		self.assertEqual( op2a.counter, 4 )
		self.assertEqual( op2b.counter, 4 )
		self.assertTrue( despatcher.log == [ op2a, op2b, op2 ] or despatcher.log == [ op2b, op2a, op2 ] )

		# Executing a leaf node, should not trigger other executions.		
		despatcher.despatch( [ n2b ] )
		self.assertEqual( op1.counter, 3 )
		self.assertEqual( op2.counter, 4 )
		self.assertEqual( op2a.counter, 4 )
		self.assertEqual( op2b.counter, 5 )
		self.assertTrue( despatcher.log == [ op2b ] )

if __name__ == "__main__":
	unittest.main()
	
