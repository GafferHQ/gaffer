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

class TestOp (IECore.Op) :

	def __init__( self ) :

		IECore.Op.__init__( self, "Test op", IECore.IntParameter( "result", "", 0 ) )
		self.counter = 0

	def doOperation( self, args ) :

		self.counter += 1
		return IECore.IntData( self.counter )

class ExecutableOpHolderTest( unittest.TestCase ) :

	def testType( self ) :
	
		n = Gaffer.ExecutableOpHolder()
		self.assertEqual( n.typeName(), "Gaffer::ExecutableOpHolder" )
		self.failUnless( n.isInstanceOf( Gaffer.ParameterisedHolderNode.staticTypeId() ) )
		self.failUnless( n.isInstanceOf( Gaffer.Node.staticTypeId() ) )

	def testIsExecutable( self ) :

		self.assertTrue( Gaffer.ExecutableNode.isExecutable( Gaffer.ExecutableOpHolder ) )
		n = Gaffer.ExecutableOpHolder()
		self.assertTrue( Gaffer.ExecutableNode.isExecutable( n ) )

	def testExecutablePlugs( self ) :

		n = Gaffer.ExecutableOpHolder()
		self.assertEqual( n['requirement'].direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( n['requirements'].direction(), Gaffer.Plug.Direction.In )

	def testSetOp( self ) :
	
		n = Gaffer.ExecutableOpHolder()
		opSpec = GafferTest.ParameterisedHolderTest.classSpecification( "primitive/renameVariables", "IECORE_OP_PATHS" )[:-1]
		n.setOp( *opSpec )

	def testExecutableMethods( self ) :
		
		n = Gaffer.ExecutableOpHolder()
		opSpec = GafferTest.ParameterisedHolderTest.classSpecification( "primitive/renameVariables", "IECORE_OP_PATHS" )[:-1]
		n.setOp( *opSpec )
		c = Gaffer.Context()
		h = n.executionHash(c)
		self.assertEqual( n.executionHash(c), h )

	def testSetParameterised( self ) :
	
		n = Gaffer.ExecutableOpHolder()
		op = TestOp()
		n.setParameterised( op )
		self.assertEqual( op, n.getOp() )

	def testExecute( self ) :
	
		n = Gaffer.ExecutableOpHolder()
		op = TestOp()
		n.setParameterised( op )
		script = n.scriptNode()
		self.assertEqual( op.counter, 0 )
		n.execute( [ Gaffer.Context() ] )
		self.assertEqual( op.counter, 1 )

	def testRequirements( self ) :

		n1 = Gaffer.ExecutableOpHolder()
		n2 = Gaffer.ExecutableOpHolder()
		n2a = Gaffer.ExecutableOpHolder()
		n2b = Gaffer.ExecutableOpHolder()

		r1 = Gaffer.Plug( name = "r1" )
		n1['requirements'].addChild( r1 )
		r1.setInput( n2['requirement'] )

		r1 = Gaffer.Plug( name = "r1" )
		n2['requirements'].addChild( r1 )
		r1.setInput( n2a['requirement'] )
		
		r2 = Gaffer.Plug( name = "r2" )
		n2['requirements'].addChild( r2 )
		r2.setInput( n2b['requirement'] )

		c = Gaffer.Context()
		self.assertEqual( n2a.executionRequirements(c), [] )
		self.assertEqual( n2b.executionRequirements(c), [] )
		n2Requirements = n2.executionRequirements(c)
		self.assertEqual( n2Requirements[0].node, n2a )
		self.assertEqual( n2Requirements[0].context, c )
		self.assertEqual( n2Requirements[1].node, n2b )
		self.assertEqual( n2Requirements[1].context, c )
		t1 = Gaffer.ExecutableNode.Task(n2a,c)
		t2 = Gaffer.ExecutableNode.Task(n2b,c)
		self.assertEqual( n2Requirements[0], t1 )
		self.assertEqual( n2Requirements[1], t2 )
		self.assertEqual( len(set(n2.executionRequirements(c)).difference([ t1, t2])), 0 )
		self.assertEqual( n1.executionRequirements(c), [ Gaffer.ExecutableNode.Task(n2,c) ] )
	
	def testSerialise( self ) :
	
		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.ExecutableOpHolder()
	
		opSpec = GafferTest.ParameterisedHolderTest.classSpecification( "primitive/renameVariables", "IECORE_OP_PATHS" )[:-1]
		s["n"].setOp( *opSpec )
		
		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		
		self.assertEqual( s["n"]["parameters"].keys(), s2["n"]["parameters"].keys() )
			
if __name__ == "__main__":
	unittest.main()
	
