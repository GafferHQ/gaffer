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

		n = Gaffer.ExecutableOpHolder()
		self.assertEqual( n.typeName(), "Gaffer::ExecutableOpHolder" )
		self.failUnless( n.isInstanceOf( Gaffer.ParameterisedHolderExecutableNode.staticTypeId() ) )
		self.failUnless( n.isInstanceOf( Gaffer.Node.staticTypeId() ) )

	def testIsExecutable( self ) :

		self.assertTrue( isinstance( Gaffer.ExecutableOpHolder(), Gaffer.ExecutableNode ) )

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
		h = n.hash(c)
		self.assertEqual( n.hash(c), h )

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
		with Gaffer.Context() :
			n.execute()
		self.assertEqual( op.counter, 1 )

	def testContextSubstitutions( self ) :

		n = Gaffer.ExecutableOpHolder()
		op = TestOp()
		n.setParameterised( op )
		self.assertEqual( op.counter, 0 )
		self.assertEqual( op.stringValue, "" )

		c = Gaffer.Context()
		c.setFrame( 1 )
		with c :
			n.execute()
		self.assertEqual( op.counter, 1 )
		self.assertEqual( op.stringValue, "" )

		n["parameters"]["stringParm"].setValue( "${frame}" )
		with c :
			n.execute()
		self.assertEqual( op.counter, 2 )
		self.assertEqual( op.stringValue, "1" )

		# variable outside the context (and environment) get removed
		n["parameters"]["stringParm"].setValue( "${test}" )
		with c :
			n.execute()
		self.assertEqual( op.counter, 3 )
		self.assertEqual( op.stringValue, "" )

		c["test"] = "passed"
		with c :
			n.execute()
		self.assertEqual( op.counter, 4 )
		self.assertEqual( op.stringValue, "passed" )

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
		self.assertEqual( n2a.requirements(c), [] )
		self.assertEqual( n2b.requirements(c), [] )
		n2Requirements = n2.requirements(c)
		self.assertEqual( n2Requirements[0].node(), n2a )
		self.assertEqual( n2Requirements[0].context(), c )
		self.assertEqual( n2Requirements[1].node(), n2b )
		self.assertEqual( n2Requirements[1].context(), c )
		t1 = Gaffer.ExecutableNode.Task(n2a,c)
		t2 = Gaffer.ExecutableNode.Task(n2b,c)
		self.assertEqual( n2Requirements[0], t1 )
		self.assertEqual( n2Requirements[1], t2 )
		self.assertEqual( len(set(n2.requirements(c)).difference([ t1, t2])), 0 )
		self.assertEqual( n1.requirements(c), [ Gaffer.ExecutableNode.Task(n2,c) ] )

	def testSerialise( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.ExecutableOpHolder()

		opSpec = GafferTest.ParameterisedHolderTest.classSpecification( "primitive/renameVariables", "IECORE_OP_PATHS" )[:-1]
		s["n"].setOp( *opSpec )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s["n"]["parameters"].keys(), s2["n"]["parameters"].keys() )

	def testHash( self ) :

		c = Gaffer.Context()
		c.setFrame( 1 )
		c2 = Gaffer.Context()
		c2.setFrame( 2 )

		n = Gaffer.ExecutableOpHolder()
		op = TestOp()

		# output doesn't vary until we set an op
		self.assertEqual( n.hash( c ), IECore.MurmurHash() )

		# output varies if any op is set
		n.setParameterised( op )
		self.assertNotEqual( n.hash( c ), IECore.MurmurHash() )

		# output doesn't vary by time unless ${frame} is used by the parameters
		self.assertEqual( n.hash( c ), n.hash( c2 ) )

		# output varies by time because ${frame} is used by the parameters
		n["parameters"]["stringParm"].setValue( "${frame}" )
		self.assertNotEqual( n.hash( c ), n.hash( c2 ) )

		# output varies any context entry used by the parameters
		n["parameters"]["stringParm"].setValue( "${test}" )
		self.assertEqual( n.hash( c ), n.hash( c2 ) )
		c["test"] = "a"
		self.assertNotEqual( n.hash( c ), n.hash( c2 ) )
		c2["test"] = "b"
		self.assertNotEqual( n.hash( c ), n.hash( c2 ) )
		c2["test"] = "a"
		self.assertEqual( n.hash( c ), n.hash( c2 ) )

if __name__ == "__main__":
	unittest.main()

