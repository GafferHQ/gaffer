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
import GafferDispatch
import GafferCortex
import GafferCortexTest

class TestOp (IECore.Op) :

	def __init__( self ) :

		IECore.Op.__init__( self, "Test op", IECore.IntParameter( "result", "", 0 ) )
		self.parameters().addParameter( IECore.StringParameter( "stringParm", "testing context substitution", "" ) )
		self.counter = 0
		self.stringValue = ""

	def doOperation( self, args ) :

		self.counter += 1
		self.stringValue = args["stringParm"].value
		return IECore.IntData( self.counter )

class ExecutableOpHolderTest( GafferTest.TestCase ) :

	def testType( self ) :

		n = GafferCortex.ExecutableOpHolder()
		self.assertEqual( n.typeName(), "GafferCortex::ExecutableOpHolder" )
		self.assertTrue( n.isInstanceOf( GafferCortex.ParameterisedHolderTaskNode.staticTypeId() ) )
		self.assertTrue( n.isInstanceOf( Gaffer.Node.staticTypeId() ) )

	def testIsTaskNode( self ) :

		self.assertTrue( isinstance( GafferCortex.ExecutableOpHolder(), GafferDispatch.TaskNode ) )

	def testTaskPlugs( self ) :

		n = GafferCortex.ExecutableOpHolder()
		self.assertEqual( n["task"].direction(), Gaffer.Plug.Direction.Out )
		self.assertEqual( n["preTasks"].direction(), Gaffer.Plug.Direction.In )

	def testSetOp( self ) :

		n = GafferCortex.ExecutableOpHolder()
		opSpec = GafferCortexTest.ParameterisedHolderTest.classSpecification( "files/sequenceRenumber", "IECORE_OP_PATHS" )[:-1]
		n.setOp( *opSpec )

	def testHash( self ) :

		n = GafferCortex.ExecutableOpHolder()
		opSpec = GafferCortexTest.ParameterisedHolderTest.classSpecification( "files/sequenceRenumber", "IECORE_OP_PATHS" )[:-1]
		n.setOp( *opSpec )
		c = Gaffer.Context()
		h = n.hash(c)
		self.assertEqual( n.hash(c), h )

	def testSetParameterised( self ) :

		n = GafferCortex.ExecutableOpHolder()
		op = TestOp()
		n.setParameterised( op )
		self.assertEqual( op, n.getOp() )

	def testExecute( self ) :

		n = GafferCortex.ExecutableOpHolder()
		op = TestOp()
		n.setParameterised( op )
		script = n.scriptNode()
		self.assertEqual( op.counter, 0 )
		with Gaffer.Context() :
			n["task"].execute()
		self.assertEqual( op.counter, 1 )

	def testContextSubstitutions( self ) :

		n = GafferCortex.ExecutableOpHolder()
		op = TestOp()
		n.setParameterised( op )
		self.assertEqual( op.counter, 0 )
		self.assertEqual( op.stringValue, "" )

		c = Gaffer.Context()
		c.setFrame( 1 )
		with c :
			n["task"].execute()
		self.assertEqual( op.counter, 1 )
		self.assertEqual( op.stringValue, "" )

		n["parameters"]["stringParm"].setValue( "${frame}" )
		with c :
			n["task"].execute()
		self.assertEqual( op.counter, 2 )
		self.assertEqual( op.stringValue, "1" )

		# variable outside the context (and environment) get removed
		n["parameters"]["stringParm"].setValue( "${test}" )
		with c :
			n["task"].execute()
		self.assertEqual( op.counter, 3 )
		self.assertEqual( op.stringValue, "" )

		c["test"] = "passed"
		with c :
			n["task"].execute()
		self.assertEqual( op.counter, 4 )
		self.assertEqual( op.stringValue, "passed" )

	def testSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferCortex.ExecutableOpHolder()

		opSpec = GafferCortexTest.ParameterisedHolderTest.classSpecification( "files/sequenceRenumber", "IECORE_OP_PATHS" )[:-1]
		s["n"].setOp( *opSpec )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s["n"]["parameters"].keys(), s2["n"]["parameters"].keys() )

	def testHash( self ) :

		c = Gaffer.Context()
		c.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		n = GafferCortex.ExecutableOpHolder()
		op = TestOp()

		# output doesn't vary until we set an op
		self.assertEqual( n["task"].hash(), IECore.MurmurHash() )

		# output varies if any op is set
		n.setParameterised( op )
		self.assertNotEqual( n["task"].hash(), IECore.MurmurHash() )

		# output doesn't vary by time unless ${frame} is used by the parameters
		with c :
			h1 = n["task"].hash()
		with c2 :
			h2 = n["task"].hash()
		self.assertEqual( h1, h2 )

		# output varies by time because ${frame} is used by the parameters
		n["parameters"]["stringParm"].setValue( "${frame}" )
		with c :
			h1 = n["task"].hash()
		with c2 :
			h2 = n["task"].hash()
		self.assertNotEqual( h1, h2 )

		# output varies any context entry used by the parameters
		n["parameters"]["stringParm"].setValue( "${test}" )
		with c :
			h1 = n["task"].hash()
		with c2 :
			h2 = n["task"].hash()
		self.assertEqual( h1, h2 )

		with c :
			c["test"] = "a"
			h1 = n["task"].hash()
			self.assertNotEqual( h1, h2 )
		with c2 :
			c2["test"] = "b"
			h2 = n["task"].hash()
			self.assertNotEqual( h1, h2 )
			c2["test"] = "a"
			h2 = n["task"].hash()
			self.assertEqual( h1, h2 )

if __name__ == "__main__":
	unittest.main()
