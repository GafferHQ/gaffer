##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

class ExpressionTest( GafferTest.TestCase ) :

	def test( self ) :

		s = Gaffer.ScriptNode()

		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )

		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )

		s["e"]["expression"].setValue( "parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2" )

		self.assertEqual( s["m2"]["product"].getValue(), 400 )

	def testContextAccess( self ) :

		s = Gaffer.ScriptNode()

		s["m"] = GafferTest.MultiplyNode()
		s["m"]["op1"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent[\"m\"][\"op2\"] = int( context[\"frame\"] * 2 )" )

		context = Gaffer.Context()
		context.setFrame( 10 )
		with context :
			self.assertEqual( s["m"]["product"].getValue(), 20 )

	def testSetExpressionWithNoEngine( self ) :

		s = Gaffer.ScriptNode()

		s["m"] = GafferTest.MultiplyNode()

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "" )
		s["e"]["expression"].setValue( "parent[\"m\"][\"op2\"] = int( context[\"frame\"] * 2 )" )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )

		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )

		s["e"]["expression"].setValue( "parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2" )

		self.assertEqual( s["m2"]["product"].getValue(), 400 )

		ss = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertEqual( s2["m2"]["product"].getValue(), 400 )

	def testStringOutput( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.StringPlug()

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent['n']['p'] = '#%d' % int( context['frame'] )" )

		context = Gaffer.Context()
		for i in range( 0, 10 ) :
			context.setFrame( i )
			with context :
				self.assertEqual( s["n"]["p"].getValue(), "#%d" % i )

	def testRegisteredEngines( self ) :

		e = Gaffer.Expression.Engine.registeredEngines()
		self.failUnless( isinstance( e, tuple ) )
		self.failUnless( "python" in e )

	def testDefaultEngine( self ) :

		e = Gaffer.Expression()
		self.assertEqual( e["engine"].getValue(), "python" )

	def testCreateExpressionWithWatchers( self ) :

		s = Gaffer.ScriptNode()

		def f( plug ) :

			plug.getValue()

		s["m1"] = GafferTest.MultiplyNode()

		c = s["m1"].plugDirtiedSignal().connect( f )

		s["e"] = Gaffer.Expression()
		s["e"]["expression"].setValue( "parent[\"m1\"][\"op1\"] = 2" )

	def testCompoundNumericPlugs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["v"] = Gaffer.V2fPlug()

		s["e"] = Gaffer.Expression()
		s["e"]["expression"].setValue( 'parent["n"]["v"]["x"] = parent["n"]["v"]["y"]' )

		s["n"]["v"]["y"].setValue( 21 )

		self.assertEqual( s["n"]["v"]["x"].getValue(), 21 )

	def testInputsAsInputs( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["i1"] = Gaffer.IntPlug()
		s["n"]["i2"] = Gaffer.IntPlug()

		s["e"] = Gaffer.Expression()
		s["e"]["expression"].setValue( 'parent["n"]["i1"] = parent["n"]["i2"]' )

		s["n"]["i2"].setValue( 11 )

		self.assertEqual( s["n"]["i1"].getValue(), 11 )

	def testDeleteExpressionText( self ) :

		s = Gaffer.ScriptNode()

		s["m1"] = GafferTest.MultiplyNode()
		s["m1"]["op1"].setValue( 10 )
		s["m1"]["op2"].setValue( 20 )

		s["m2"] = GafferTest.MultiplyNode()
		s["m2"]["op2"].setValue( 1 )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )

		s["e"]["expression"].setValue( "parent[\"m2\"][\"op1\"] = parent[\"m1\"][\"product\"] * 2" )

		self.failUnless( s["m2"]["op1"].getInput().isSame( s["e"]["out"] ) )
		self.assertEqual( s["m2"]["product"].getValue(), 400 )

		# deleting the expression text should just keep the connections and compute
		# a default value (no exceptions thrown). otherwise the ui will have a hard time
		# and undo will fail.

		s["e"]["expression"].setValue( "" )
		self.failUnless( s["m2"]["op1"].getInput().isSame( s["e"]["out"] ) )
		self.assertEqual( s["m2"]["product"].getValue(), 0 )

	def testContextGetFrameMethod( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n"]["op1"].setValue( 0 )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent['n']['op2'] = int( context.getFrame() )" )

		with Gaffer.Context() as c :
			for i in range( 0, 10 ) :
				c.setFrame( i )
				self.assertEqual( s["n"]["sum"].getValue(), i )

	def testContextGetMethod( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n"]["op1"].setValue( 0 )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent['n']['op2'] = int( context.get( 'frame' ) )" )

		with Gaffer.Context() as c :
			for i in range( 0, 10 ) :
				c.setFrame( i )
				self.assertEqual( s["n"]["sum"].getValue(), i )

	def testContextGetWithDefault( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n"]["op1"].setValue( 0 )

		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent['n']['op2'] = context.get( 'iDontExist', 101 )" )

		self.assertEqual( s["n"]["sum"].getValue(), 101 )

if __name__ == "__main__":
	unittest.main()
