##########################################################################
#
#  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

class EditScopeTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		def createIntProcessor() :

			n = Gaffer.ContextVariables()
			n.setup( Gaffer.IntPlug() )
			return n

		Gaffer.EditScope.registerProcessor( "Test", createIntProcessor )

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		Gaffer.EditScope.deregisterProcessor( "Test" )

	def testProcessorRegistry( self ) :

		self.assertIn( "Test", Gaffer.EditScope.registeredProcessors() )

		def createProcessor() :

			n = Gaffer.TimeWarp()
			n.setup( Gaffer.IntPlug() )
			return n

		Gaffer.EditScope.registerProcessor( "Test", createProcessor )
		self.assertEqual( Gaffer.EditScope.registeredProcessors().count( "Test" ), 1 )

		e = Gaffer.EditScope()
		e.setup( Gaffer.IntPlug() )
		self.assertIsInstance( e.acquireProcessor( "Test" ), Gaffer.TimeWarp )

		Gaffer.EditScope.deregisterProcessor( "Test" )
		self.assertEqual( Gaffer.EditScope.registeredProcessors().count( "Test" ), 0 )

	def testSetup( self ) :

		e = Gaffer.EditScope()
		self.assertNotIn( "in", e )
		self.assertNotIn( "out", e )

		e.setup( Gaffer.IntPlug() )

		self.assertIn( "in", e )
		self.assertIn( "out", e )

		self.assertIsInstance( e["in"], Gaffer.IntPlug )
		self.assertIsInstance( e["out"], Gaffer.IntPlug )
		self.assertEqual( e["out"].source(), e["in"] )

		self.assertEqual( e.correspondingInput( e["out"] ), e["in"] )

	def testAcquireProcessor( self ) :

		e = Gaffer.EditScope()
		e.setup( Gaffer.IntPlug() )

		self.assertIsNone( e.acquireProcessor( "Test", createIfNecessary = False ) )
		p = e.acquireProcessor( "Test" )
		self.assertIsInstance( p, Gaffer.ContextVariables )
		self.assertEqual( e["out"].source(), p["out"] )
		self.assertEqual( p["in"].source(), e["in"] )

		self.assertEqual( p, e.acquireProcessor( "Test" ) )

		# Remove processor from the main stream but keep it in the
		# EditScope. A new processor should be made for us by
		# `acquireProcessor()`.
		p["out"].outputs()[0].setInput( p["in"].getInput() )
		self.assertIsNone( e.acquireProcessor( "Test", createIfNecessary = False ) )
		p2 = e.acquireProcessor( "Test" )
		self.assertNotEqual( p, p2 )
		self.assertIsInstance( p2, Gaffer.ContextVariables )
		self.assertEqual( e["out"].source(), p2["out"] )
		self.assertEqual( p2["in"].source(), e["in"] )

	def testProcessors( self ) :

		e = Gaffer.EditScope()
		e.setup( Gaffer.IntPlug() )
		self.assertEqual( e.processors(), [] )

		p = e.acquireProcessor( "Test" )
		self.assertEqual( e.processors(), [ p ] )

		# Remove processor from the main stream but keep it in the
		# EditScope. It should no longer be returned by `processors()`.
		p["out"].outputs()[0].setInput( p["in"].getInput() )
		self.assertEqual( e.processors(), [] )

	def testBrokenInternalConnection( self ) :

		e = Gaffer.EditScope()
		e.setup( Gaffer.IntPlug() )

		p = e.acquireProcessor( "Test" )
		self.assertEqual( e.processors(), [ p ] )

		p["in"].setInput( None )
		with self.assertRaisesRegexp( RuntimeError, "Output not linked to input" ) :
			e.processors()

		with self.assertRaisesRegexp( RuntimeError, "Output not linked to input" ) :
			e.acquireProcessor( "Test" )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()
		s["e"] = Gaffer.EditScope()
		s["e"].setup( Gaffer.IntPlug() )
		p = s["e"].acquireProcessor( "Test" )
		p["variables"].addChild( Gaffer.NameValuePlug( "x", 10, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		p2 = s2["e"].acquireProcessor( "Test", createIfNecessary = False )
		self.assertIsNotNone( p2 )
		self.assertEqual( type( p2 ), type( p ) )
		self.assertEqual( p2["variables"][0]["name"].getValue(), p["variables"][0]["name"].getValue() )
		self.assertEqual( p2["variables"][0]["value"].getValue(), p["variables"][0]["value"].getValue() )
		self.assertEqual( s2["e"]["out"].getValue(), s["e"]["out"].getValue() )

if __name__ == "__main__":
	unittest.main()
