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
import imath

import IECore
import Gaffer
import GafferTest

class SwitchTest( GafferTest.TestCase ) :

	def intSwitch( self ) :

		result = Gaffer.Switch()
		result.setup( Gaffer.IntPlug() )

		return result

	def colorSwitch( self ) :

		result = Gaffer.Switch()
		result.setup( Gaffer.Color3fPlug() )

		return result

	def intPlug( self, value ) :

		result = Gaffer.IntPlug()
		result.setValue( value )

		# we need to keep it alive for the duration of the
		# test - it'll be cleaned up in tearDown().
		self.__inputPlugs.append( result )

		return result

	def colorPlug( self, value ) :

		result = Gaffer.Color3fPlug()
		result.setValue( value )

		# we need to keep it alive for the duration of the
		# test - it'll be cleaned up in tearDown().
		self.__inputPlugs.append( result )

		return result

	def test( self ) :

		n = self.intSwitch()
		n["in"][0].setInput( self.intPlug( 0 ) )
		n["in"][1].setInput( self.intPlug( 1 ) )
		n["in"][2].setInput( self.intPlug( 2 ) )

		n["index"].setValue( 0 )
		self.assertEqual( n["out"].hash(), n["in"][0].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][0].getValue() )

		n["index"].setValue( 1 )
		self.assertEqual( n["out"].hash(), n["in"][1].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][1].getValue() )

		n["index"].setValue( 2 )
		self.assertEqual( n["out"].hash(), n["in"][2].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][2].getValue() )

	def testCorrespondingInput( self ) :

		n = self.intSwitch()
		self.assertTrue( n.correspondingInput( n["out"] ).isSame( n["in"][0] ) )

	def testDisabling( self ) :

		n = self.intSwitch()
		n["in"][0].setInput( self.intPlug( 0 ) )
		n["in"][1].setInput( self.intPlug( 1 ) )

		n["index"].setValue( 1 )
		self.assertEqual( n["out"].hash(), n["in"][1].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][1].getValue() )

		n["enabled"].setValue( False )

		self.assertEqual( n["out"].hash(), n["in"][0].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][0].getValue() )

		n["enabled"].setValue( True )

		self.assertEqual( n["out"].hash(), n["in"][1].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][1].getValue() )

		self.assertTrue( n["enabled"].isSame( n.enabledPlug() ) )

	def testAffects( self ) :

		n = self.intSwitch()
		n["in"][0].setInput( self.intPlug( 0 ) )
		n["in"][1].setInput( self.intPlug( 0 ) )

		for plug in [ n["enabled"], n["index"] ] :
			a = n.affects( plug )
			self.assertEqual( len( a ), 1 )
			self.assertTrue( a[0].isSame( n["out"] ) )

		# Because the constant-index case is optimised
		# via a pass-through connection, the inputs should
		# not affect the output (dependency is carried by
		# the connection instead).
		for plug in [ n["in"][0], n["in"][1] ] :
			self.assertEqual( n.affects( plug ), [] )

		# Now the index is computed, the dependencies
		# must be declared.
		a = GafferTest.AddNode()
		n["index"].setInput( a["sum"] )
		for plug in [ n["in"][0], n["in"][1] ] :
			self.assertEqual( n.affects( plug ), [ n["out"] ] )

		self.assertEqual( n.affects( n["out"] ), [] )

	def testOutOfRangeIndex( self ) :

		n = self.intSwitch()
		n["in"][0].setInput( self.intPlug( 0 ) )
		n["in"][1].setInput( self.intPlug( 1 ) )
		n["in"][2].setInput( self.intPlug( 2 ) )

		n["index"].setValue( 2 )
		self.assertEqual( n["out"].hash(), n["in"][2].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][2].getValue() )

		# wrap around if the index is out of range

		n["index"].setValue( 3 )
		self.assertEqual( n["out"].hash(), n["in"][0].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][0].getValue() )

		n["index"].setValue( 4 )
		self.assertEqual( n["out"].hash(), n["in"][1].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][1].getValue() )

		n["index"].setValue( 5 )
		self.assertEqual( n["out"].hash(), n["in"][2].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][2].getValue() )

	def testAffectsIgnoresAdditionalPlugs( self ) :

		n = self.intSwitch()
		n["myPlug"] = Gaffer.IntPlug()
		n["indubitablyNotAnInputBranch"] = Gaffer.IntPlug()
		n["in2dubitablyNotAnInputBranch"] = Gaffer.IntPlug()
		self.assertEqual( n.affects( n["myPlug"] ), [] )
		self.assertEqual( n.affects( n["indubitablyNotAnInputBranch"] ), [] )
		self.assertEqual( n.affects( n["in2dubitablyNotAnInputBranch"] ), [] )

	def testCompoundPlugs( self ) :

		n = self.colorSwitch()
		n["in"][0].setInput( self.colorPlug( imath.Color3f( 0, 0.1, 0.2 ) ) )
		n["in"][1].setInput( self.colorPlug( imath.Color3f( 1, 1.1, 1.2 ) ) )
		n["in"][2].setInput( self.colorPlug( imath.Color3f( 2, 2.1, 2.2 ) ) )

		n["index"].setValue( 0 )
		self.assertEqual( n["out"].hash(), n["in"][0].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][0].getValue() )

		n["index"].setValue( 1 )
		self.assertEqual( n["out"].hash(), n["in"][1].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][1].getValue() )

		n["index"].setValue( 2 )
		self.assertEqual( n["out"].hash(), n["in"][2].hash() )
		self.assertEqual( n["out"].getValue(), n["in"][2].getValue() )

	def testSerialisation( self ) :

		script = Gaffer.ScriptNode()
		script["s"] = self.intSwitch()
		script["a1"] = GafferTest.AddNode()
		script["a2"] = GafferTest.AddNode()
		script["a1"]["op1"].setValue( 1 )
		script["a2"]["op2"].setValue( 2 )
		script["s"]["in"][0].setInput( script["a1"]["sum"] )
		script["s"]["in"][1].setInput( script["a2"]["sum"] )

		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )

		self.assertEqual( len( script2["s"]["in"] ), 3 )

		self.assertEqual( script2["s"]["out"].getValue(), 1 )
		script2["s"]["index"].setValue( 1 )
		self.assertEqual( script2["s"]["out"].getValue(), 2 )

	def testIndexExpression( self ) :

		script = Gaffer.ScriptNode()
		script["s"] = self.intSwitch()
		script["a1"] = GafferTest.AddNode()
		script["a2"] = GafferTest.AddNode()
		script["a1"]["op1"].setValue( 1 )
		script["a2"]["op2"].setValue( 2 )
		script["s"]["in"][0].setInput( script["a1"]["sum"] )
		script["s"]["in"][1].setInput( script["a2"]["sum"] )

		# Should be using an internal connection for speed
		self.assertTrue( script["s"]["out"].getInput() is not None )

		script["expression"] = Gaffer.Expression()
		script["expression"].setExpression( 'parent["s"]["index"] = int( context.getFrame() )' )

		# Should not be using an internal connection, because the result
		# varies with context.
		self.assertTrue( script["s"]["out"].getInput() is None )

		with script.context() :
			script.context().setFrame( 0 )
			self.assertEqual( script["s"]["out"].getValue(), 1 )
			script.context().setFrame( 1 )
			self.assertEqual( script["s"]["out"].getValue(), 2 )

		del script["expression"]

		# Should be using an internal connection for speed now the expression has
		# been removed.
		self.assertTrue( script["s"]["out"].getInput() is not None )

	def testPassThroughWhenIndexConstant( self ) :

		n = Gaffer.Switch()
		n["in"] = Gaffer.ArrayPlug( element = Gaffer.Plug(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic  )

		self.assertTrue( n["out"].source().isSame( n["in"][0] ) )

		input0 = Gaffer.Plug()
		input1 = Gaffer.Plug()
		input2 = Gaffer.Plug()

		n["in"][0].setInput( input0 )
		self.assertTrue( n["out"].source().isSame( input0 ) )

		n["in"][1].setInput( input1 )
		self.assertTrue( n["out"].source().isSame( input0 ) )

		n["index"].setValue( 1 )
		self.assertTrue( n["out"].source().isSame( input1 ) )

		n["enabled"].setValue( False )
		self.assertTrue( n["out"].source().isSame( input0 ) )

		n["in"][2].setInput( input2 )
		self.assertTrue( n["out"].source().isSame( input0 ) )

		n["enabled"].setValue( True )
		self.assertTrue( n["out"].source().isSame( input1 ) )

		n["index"].setValue( 2 )
		self.assertTrue( n["out"].source().isSame( input2 ) )

	def testIndexInputAcceptance( self ) :

		cs = Gaffer.Switch()

		a = GafferTest.AddNode()
		a["boolInput"] = Gaffer.BoolPlug()
		a["boolOutput"] = Gaffer.BoolPlug( direction=Gaffer.Plug.Direction.Out )

		self.assertTrue( cs["index"].acceptsInput( a["op1"] ) )
		self.assertTrue( cs["index"].acceptsInput( a["sum"] ) )

		self.assertTrue( cs["enabled"].acceptsInput( a["boolInput"] ) )
		self.assertTrue( cs["enabled"].acceptsInput( a["boolOutput"] ) )

	def testConnectedIndex( self ) :

		n = Gaffer.Switch()
		n["in"] = Gaffer.ArrayPlug( element = Gaffer.Plug(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic  )

		input0 = Gaffer.Plug()
		input1 = Gaffer.Plug()
		input2 = Gaffer.Plug()

		n["in"][0].setInput( input0 )
		n["in"][1].setInput( input1 )
		n["in"][2].setInput( input2 )

		self.assertTrue( n["out"].source().isSame( input0 ) )

		indexInput = Gaffer.IntPlug()
		n["index"].setInput( indexInput )
		self.assertTrue( n["out"].source().isSame( input0 ) )

		indexInput.setValue( 1 )
		self.assertTrue( n["out"].source().isSame( input1 ) )

		indexInput.setValue( 2 )
		self.assertTrue( n["out"].source().isSame( input2 ) )

		indexInput.setValue( 3 )
		self.assertTrue( n["out"].source().isSame( input0 ) )

	def testAcceptsNoneInputs( self ) :

		n = Gaffer.Switch()
		self.assertTrue( n["enabled"].acceptsInput( None ) )
		self.assertTrue( n["index"].acceptsInput( None ) )

	def testIndirectInputsToIndex( self ) :

		n = Gaffer.Switch()
		n["in"] = Gaffer.ArrayPlug( element = Gaffer.Plug(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic  )

		input0 = Gaffer.Plug()
		input1 = Gaffer.Plug()
		input2 = Gaffer.Plug()

		n["in"][0].setInput( input0 )
		n["in"][1].setInput( input1 )
		n["in"][2].setInput( input2 )

		self.assertTrue( n["out"].source().isSame( input0 ) )

		indexInput = Gaffer.IntPlug()
		n["index"].setInput( indexInput )
		self.assertTrue( n["out"].source().isSame( input0 ) )

		indirectIndexInput1 = Gaffer.IntPlug( defaultValue = 1 )
		indirectIndexInput2 = Gaffer.IntPlug( defaultValue = 2 )

		indexInput.setInput( indirectIndexInput1 )
		self.assertTrue( n["out"].source().isSame( input1 ) )

		indexInput.setInput( indirectIndexInput2 )
		self.assertTrue( n["out"].source().isSame( input2 ) )

	def testAcceptsInputPerformance( self ) :

		s1 = GafferTest.AddNode()
		lastPlug = s1["sum"]

		switches = []
		for i in range( 0, 8 ) :
			switch = self.intSwitch()
			for i in range( 0, 9 ) :
				switch["in"][i].setInput( lastPlug )
			switches.append( switch )
			lastPlug = switch["out"]

		s2 = GafferTest.AddNode()
		self.assertTrue( switches[0]["in"][0].acceptsInput( s2["sum"] ) )

	def testActiveInPlug( self ) :

		s = Gaffer.ScriptNode()

		s["a1"] = GafferTest.AddNode()
		s["a2"] = GafferTest.AddNode()

		s["switch"] = self.intSwitch()
		s["switch"]["in"][0].setInput( s["a1"]["sum"] )
		s["switch"]["in"][1].setInput( s["a2"]["sum"] )

		self.assertTrue( s["switch"].activeInPlug().isSame( s["switch"]["in"][0] ) )

		s["switch"]["index"].setValue( 1 )
		self.assertTrue( s["switch"].activeInPlug().isSame( s["switch"]["in"][1] ) )

		s["switch"]["enabled"].setValue( False )
		self.assertTrue( s["switch"].activeInPlug().isSame( s["switch"]["in"][0] ) )

		s["switch"]["enabled"].setValue( True )
		self.assertTrue( s["switch"].activeInPlug().isSame( s["switch"]["in"][1] ) )

		s["expression"] = Gaffer.Expression()
		s["expression"].setExpression( 'parent["switch"]["index"] = context.getFrame()' )

		with Gaffer.Context() as c :

			c.setFrame( 0 )
			self.assertTrue( s["switch"].activeInPlug().isSame( s["switch"]["in"][0] ) )

			c.setFrame( 1 )
			self.assertTrue( s["switch"].activeInPlug().isSame( s["switch"]["in"][1] ) )

			c.setFrame( 2 )
			self.assertTrue( s["switch"].activeInPlug().isSame( s["switch"]["in"][0] ) )

	def testSetupFromNonSerialisablePlug( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["n1"]["sum"].setFlags( Gaffer.Plug.Flags.Serialisable, False )

		s["switch"] = Gaffer.Switch()
		s["switch"].setup( s["n1"]["sum"] )

		s["switch"]["in"][0].setInput( s["n1"]["sum"] )
		s["n2"]["op1"].setInput( s["switch"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["n2"]["op1"].getInput().isSame( s2["switch"]["out"] ) )
		self.assertTrue( s2["switch"]["in"][0].getInput().isSame( s2["n1"]["sum"] ) )

	def testInactiveInputsDontPropagateDirtiness( self ) :

		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()

		s = Gaffer.Switch()
		s.setup( n1["sum"] )
		s["in"][0].setInput( n1["sum"] )
		s["in"][1].setInput( n2["sum"] )

		# Because the index is constant, the switch should
		# have a direct pass-through connection.
		self.assertEqual( s["out"].source(), n1["sum"] )

		# Which means that the inactive inputs should not
		# affect the output of the switch at all.
		cs = GafferTest.CapturingSlot( s.plugDirtiedSignal() )
		n2["op1"].setValue( 10 )
		self.assertNotIn( s["out"], { x[0] for x in cs } )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__inputPlugs = []

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		self.__inputPlugs = []

if __name__ == "__main__":
	unittest.main()
