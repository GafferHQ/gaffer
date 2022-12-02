##########################################################################
#
#  Copyright (c) 2019, John Haddon. All rights reserved.
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

import os
import sys
import unittest
import functools

import Gaffer
import GafferTest

class ExtensionAlgoTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.addCleanup(
			functools.partial( setattr, sys, "path", sys.path[:] )
		)

	def testExport( self ) :

		# Export

		box = Gaffer.Box( "AddOne" )

		box["__add"] = GafferTest.AddNode()
		box["__add"]["op2"].setValue( 1 )
		Gaffer.PlugAlgo.promote( box["__add"]["op1"] ).setName( "in" )
		Gaffer.PlugAlgo.promote( box["__add"]["sum"] ).setName( "out" )

		Gaffer.Metadata.registerValue( box, "description", "Test" )
		Gaffer.Metadata.registerValue( box["in"], "description", "The input" )
		Gaffer.Metadata.registerValue( box["out"], "description", "The output" )
		Gaffer.Metadata.registerValue( box["in"], "test", 1 )

		Gaffer.ExtensionAlgo.exportExtension( "TestExtension", [ box ], self.temporaryDirectory() )
		self.assertTrue( ( self.temporaryDirectory() / "python" / "TestExtension" ).exists() )

		sys.path.append( str( self.temporaryDirectory() / "python" ) )

		# Import and test

		import TestExtension

		script = Gaffer.ScriptNode()
		script["node"] = TestExtension.AddOne()
		script["node"]["in"].setValue( 2 )
		self.assertEqual( script["node"]["out"].getValue(), 3 )

		import TestExtensionUI

		def assertExpectedMetadata( node ) :

			self.assertEqual( Gaffer.Metadata.registeredValues( node, instanceOnly = True ), [] )
			self.assertEqual( Gaffer.Metadata.registeredValues( node["in"], instanceOnly = True ), [] )
			self.assertEqual( Gaffer.Metadata.registeredValues( node["out"], instanceOnly = True ), [] )

			self.assertEqual( Gaffer.Metadata.value( node, "description" ), "Test" )
			self.assertEqual( Gaffer.Metadata.value( node["in"], "description" ), "The input" )
			self.assertEqual( Gaffer.Metadata.value( node["out"], "description" ), "The output" )
			self.assertEqual( Gaffer.Metadata.value( node["in"], "test" ), 1 )

		assertExpectedMetadata( script["node"] )

		# Copy/paste and test

		script.execute( script.serialise( filter = Gaffer.StandardSet( { script["node"] } ) ) )
		self.assertEqual( script["node1"].keys(), script["node"].keys() )
		self.assertEqual( script["node1"]["out"].getValue(), script["node"]["out"].getValue() )
		assertExpectedMetadata( script["node1"] )

	def testPlugTypes( self ) :

		box = Gaffer.Box( "PlugTypes" )
		box["int"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		box["float"] = Gaffer.FloatPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		box["string"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		box["v2i"] = Gaffer.V2iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		box["v3i"] = Gaffer.V3iPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		box["color4f"] = Gaffer.Color4fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		box["spline"] = Gaffer.SplinefColor3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.ExtensionAlgo.exportExtension( "PlugTypesExtension", [ box ], self.temporaryDirectory() )
		sys.path.append( str( self.temporaryDirectory() / "python" ) )

		import PlugTypesExtension
		node = PlugTypesExtension.PlugTypes()

		for plug in Gaffer.Plug.Range( node ) :
			self.assertIsInstance( plug, type( box[plug.getName() ] ) )
			if hasattr( plug, "getValue" ) :
				self.assertEqual( plug.getValue(), box[plug.getName()].getValue() )

		for plug in Gaffer.Plug.RecursiveRange( node ) :
			self.assertFalse( plug.getFlags( Gaffer.Plug.Flags.Dynamic ) )

	def testInternalExpression( self ) :

		box = Gaffer.Box( "AddOne" )

		box["in"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		box["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		box["__expression"] = Gaffer.Expression()
		box["__expression"].setExpression( """parent["out"] = parent["in"] + 1""" )

		Gaffer.ExtensionAlgo.exportExtension( "TestExtensionWithExpression", [ box ], self.temporaryDirectory() )

		sys.path.append( str( self.temporaryDirectory() / "python" ) )
		import TestExtensionWithExpression

		script = Gaffer.ScriptNode()
		script["node"] = TestExtensionWithExpression.AddOne()
		script["node"]["in"].setValue( 2 )
		self.assertEqual( script["node"]["out"].getValue(), 3 )

		# Test copy/paste

		script.execute( script.serialise( filter = Gaffer.StandardSet( { script["node"] } ) ) )
		self.assertEqual( script["node1"].keys(), script["node"].keys() )
		self.assertEqual( script["node1"]["out"].getValue(), 3 )

if __name__ == "__main__":
	unittest.main()
