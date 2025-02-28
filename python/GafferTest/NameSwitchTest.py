##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

class NameSwitchTest( GafferTest.TestCase ) :

	def testSetup( self ) :

		s = Gaffer.NameSwitch()
		s.setup( Gaffer.IntPlug() )

		self.assertIsInstance( s["in"][0], Gaffer.ValuePlug )
		self.assertEqual( s["in"][0]["name"].getValue(), "*" )
		self.assertIsInstance( s["in"][0]["value"], Gaffer.IntPlug )
		self.assertTrue( "enabled" in s["in"][0] )
		self.assertEqual( s["in"][0]["enabled"].getValue(), True )
		self.assertEqual( s["in"][0].getName(), "in0" )

		self.assertIsInstance( s["out"], Gaffer.ValuePlug )
		self.assertIsInstance( s["out"]["value"], Gaffer.IntPlug )

	def testMatch( self ) :

		s = Gaffer.NameSwitch()
		s.setup( Gaffer.IntPlug() )

		zero = Gaffer.IntPlug( defaultValue = 0 )
		one = Gaffer.IntPlug( defaultValue = 1 )
		two = Gaffer.IntPlug( defaultValue = 2 )

		s["in"].resize( 3 )
		s["in"][0]["value"].setInput( zero )
		s["in"][1]["name"].setValue( "on*" )
		s["in"][1]["value"].setInput( one )
		s["in"][2]["name"].setValue( "t[wx]o TOO" )
		s["in"][2]["value"].setInput( two )

		s["selector"].setValue( "one" )
		self.assertEqual( s["out"]["value"].getValue(), 1 )
		self.assertEqual( s["out"]["name"].getValue(), "on*" )
		self.assertEqual( s.activeInPlug(), s["in"][1] )

		s["selector"].setValue( "ona" )
		self.assertEqual( s["out"]["value"].getValue(), 1 )
		self.assertEqual( s["out"]["name"].getValue(), "on*" )
		self.assertEqual( s.activeInPlug(), s["in"][1] )

		s["selector"].setValue( "TOO" )
		self.assertEqual( s["out"]["value"].getValue(), 2 )
		self.assertEqual( s["out"]["name"].getValue(), "t[wx]o TOO" )
		self.assertEqual( s.activeInPlug(), s["in"][2] )

		s["selector"].setValue( "somethingElse" )
		self.assertEqual( s["out"]["value"].getValue(), 0 )
		self.assertEqual( s["out"]["name"].getValue(), "*" )
		self.assertEqual( s.activeInPlug(), s["in"][0] )

		s["selector"].setValue( "one" )
		self.assertEqual( s["out"]["value"].getValue(), 1 )
		s["in"][1]["enabled"].setValue( False )
		self.assertEqual( s["out"]["value"].getValue(), 0 )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["s"] = Gaffer.NameSwitch()
		s["s"].setup( s["n"]["sum"] )
		s["s"]["in"][0]["name"].setValue( "x" )
		s["s"]["in"][0]["value"].setInput( s["n"]["sum"] )
		s["s"]["in"][0]["enabled"].setValue( False )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertIsInstance( s2["s"]["in"][0], Gaffer.NameValuePlug )
		self.assertIsInstance( s2["s"]["in"][0]["value"], Gaffer.IntPlug )
		self.assertEqual( s2["s"]["in"][0]["name"].getValue(), s["s"]["in"][0]["name"].getValue() )
		self.assertEqual( s2["s"]["in"][0]["value"].getInput(), s2["n"]["sum"] )
		self.assertEqual( s2["s"]["in"][0]["enabled"].getValue(), s["s"]["in"][0]["enabled"].getValue() )

	def testNonSerialisablePlug( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferTest.AddNode()
		s["n"]["sum"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		s["s"] = Gaffer.NameSwitch()
		s["s"].setup( s["n"]["sum"] )
		s["s"]["in"][0]["name"].setValue( "x" )
		s["s"]["in"][0]["value"].setInput( s["n"]["sum"] )
		s["s"]["in"][0]["enabled"].setValue( False )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertIsInstance( s2["s"]["in"][0], Gaffer.NameValuePlug )
		self.assertIsInstance( s2["s"]["in"][0]["value"], Gaffer.IntPlug )
		self.assertEqual( s2["s"]["in"][0]["name"].getValue(), s["s"]["in"][0]["name"].getValue() )
		self.assertEqual( s2["s"]["in"][0]["value"].getInput(), s2["n"]["sum"] )
		self.assertEqual( s2["s"]["in"][0]["enabled"].getValue(), s["s"]["in"][0]["enabled"].getValue() )

	def testDirtyPropagation( self ) :

		s = Gaffer.NameSwitch()
		s.setup( Gaffer.IntPlug() )
		s["in"].resize( 2 )

		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )
		s["in"][1]["name"].setValue( "x" )
		self.assertIn( s["out"], { x[0] for x in cs } )

		del cs[:]
		s["in"][1]["enabled"].setValue( False )
		self.assertIn( s["out"], { x[0] for x in cs } )

		del cs[:]
		s["in"][1]["value"].setValue( 10 )
		self.assertIn( s["out"], { x[0] for x in cs } )

	def testUnnamedRowsNeverMatch( self ) :

		s = Gaffer.NameSwitch()
		s.setup( Gaffer.IntPlug() )

		zero = Gaffer.IntPlug( defaultValue = 0 )
		one = Gaffer.IntPlug( defaultValue = 1 )

		s["in"].resize( 2 )
		s["in"][0]["value"].setInput( zero )
		s["in"][1]["name"].setValue( "" )
		s["in"][1]["value"].setInput( one )

		# Selector is "", but we shouldn't match it to the unnamed row because
		# that is unintuitive. As a general rule in Gaffer, if something
		# hasn't been given a name then it is treated as if it was disabled.
		self.assertEqual( s["out"]["value"].getValue(), 0 )

		# The same should apply even when the selector receives the empty value
		# via a substitution.
		s["selector"].setValue( "${selector}" )
		with Gaffer.Context() as c :
			self.assertEqual( s["out"]["value"].getValue(), 0 )
			# If the variable exists but is empty, we _still_ don't want to
			# match the empty row. The existence of the variable is not what we
			# care about : the existence of the row is, and we treat unnamed
			# rows as non-existent.
			c["selector"] = ""
			self.assertEqual( s["out"]["value"].getValue(), 0 )
			# But by that logic, a row named '*' _should_ match the empty
			# variable.
			s["in"][1]["name"].setValue( "*" )
			self.assertEqual( s["out"]["value"].getValue(), 1 )
			# Even if the variable doesnt exist at all.
			del c["selector"]
			self.assertEqual( s["out"]["value"].getValue(), 1 )

	def testConnectedInputs( self ) :

		switch = Gaffer.NameSwitch()
		self.assertEqual( switch["connectedInputs"].getValue(), IECore.IntVectorData() )

		switch.setup( Gaffer.IntPlug() )
		self.assertEqual( switch["connectedInputs"].getValue(), IECore.IntVectorData() )

		inputA = Gaffer.IntPlug()
		switch["in"][0]["value"].setInput( inputA )
		self.assertEqual( switch["connectedInputs"].getValue(), IECore.IntVectorData( [ 0 ] ) )

		switch["in"][1]["value"].setInput( inputA )
		self.assertEqual( switch["connectedInputs"].getValue(), IECore.IntVectorData( [ 0, 1 ] ) )

		switch["in"][0]["value"].setInput( None )
		self.assertEqual( switch["connectedInputs"].getValue(), IECore.IntVectorData( [ 1 ] ) )

	def testConnectedInputsWithPromotedInPlug( self ) :

		box = Gaffer.Box()
		box["switch"] =  Gaffer.NameSwitch()
		self.assertEqual( box["switch"]["connectedInputs"].getValue(), IECore.IntVectorData() )

		box["switch"].setup( Gaffer.IntPlug() )
		self.assertEqual( box["switch"]["connectedInputs"].getValue(), IECore.IntVectorData() )

		Gaffer.PlugAlgo.promote( box["switch"]["in"] )
		self.assertEqual( box["switch"]["connectedInputs"].getValue(), IECore.IntVectorData() )

		inputA = Gaffer.IntPlug()
		box["in"][0]["value"].setInput( inputA )
		self.assertEqual( box["switch"]["connectedInputs"].getValue(), IECore.IntVectorData( [ 0 ] ) )

		box["in"][1]["value"].setInput( inputA )
		self.assertEqual( box["switch"]["connectedInputs"].getValue(), IECore.IntVectorData( [ 0, 1 ] ) )

		box["in"][0]["value"].setInput( None )
		self.assertEqual( box["switch"]["connectedInputs"].getValue(), IECore.IntVectorData( [ 1 ] ) )

	def testEnabledNames( self ) :

		switch = Gaffer.NameSwitch()
		self.assertEqual( switch["enabledNames"].getValue(), IECore.StringVectorData() )

		switch.setup( Gaffer.IntPlug() )
		self.assertEqual( switch["enabledNames"].getValue(), IECore.StringVectorData() )

		switch["in"][1]["name"].setValue( "A" )
		self.assertEqual( switch["enabledNames"].getValue(), IECore.StringVectorData( [ "A" ] ) )

		switch["in"].resize( 3 )
		switch["in"][2]["name"].setValue( "B" )
		self.assertEqual( switch["enabledNames"].getValue(), IECore.StringVectorData( [ "A", "B" ] ) )

		switch["in"][1]["enabled"].setValue( False )
		self.assertEqual( switch["enabledNames"].getValue(), IECore.StringVectorData( [ "B" ] ) )

		switch["in"][2]["enabled"].setValue( False )
		self.assertEqual( switch["enabledNames"].getValue(), IECore.StringVectorData() )

		switch["in"][1]["name"].setValue( "C" )
		switch["in"][1]["enabled"].setValue( True )
		self.assertEqual( switch["enabledNames"].getValue(), IECore.StringVectorData( [ "C" ] ) )
		switch["in"][2]["enabled"].setValue( True )
		self.assertEqual( switch["enabledNames"].getValue(), IECore.StringVectorData( [ "C", "B" ] ) )

if __name__ == "__main__":
	unittest.main()
