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

class SwitchTest( GafferTest.TestCase ) :
	
	def intSwitch( self ) :
	
		result = Gaffer.SwitchComputeNode()
		result["in"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		result["out"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic  )
	
		return result
	
	def colorSwitch( self ) :
	
		result = Gaffer.SwitchComputeNode()
		result["in"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		result["out"] = Gaffer.Color3fPlug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
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
		n["in"].setInput( self.intPlug( 0 ) )
		n["in1"].setInput( self.intPlug( 1 ) )
		n["in2"].setInput( self.intPlug( 2 ) )
		
		n["index"].setValue( 0 )
		self.assertEqual( n["out"].hash(), n["in"].hash() )
		self.assertEqual( n["out"].getValue(), n["in"].getValue() )
		
		n["index"].setValue( 1 )
		self.assertEqual( n["out"].hash(), n["in1"].hash() )
		self.assertEqual( n["out"].getValue(), n["in1"].getValue() )
		
		n["index"].setValue( 2 )
		self.assertEqual( n["out"].hash(), n["in2"].hash() )
		self.assertEqual( n["out"].getValue(), n["in2"].getValue() )		
	
	def testCorrespondingInput( self ) :
	
		n = self.intSwitch()
		self.assertTrue( n.correspondingInput( n["out"] ).isSame( n["in"] ) )		
	
	def testDisabling( self ) :
	
		n = self.intSwitch()
		n["in"].setInput( self.intPlug( 0 ) )
		n["in1"].setInput( self.intPlug( 1 ) )
		
		n["index"].setValue( 1 )
		self.assertEqual( n["out"].hash(), n["in1"].hash() )
		self.assertEqual( n["out"].getValue(), n["in1"].getValue() )
		
		n["enabled"].setValue( False )
		
		self.assertEqual( n["out"].hash(), n["in"].hash() )
		self.assertEqual( n["out"].getValue(), n["in"].getValue() )
		
		n["enabled"].setValue( True )

		self.assertEqual( n["out"].hash(), n["in1"].hash() )
		self.assertEqual( n["out"].getValue(), n["in1"].getValue() )
		
		self.assertTrue( n["enabled"].isSame( n.enabledPlug() ) )
		
	def testAffects( self ) :
	
		n = self.intSwitch()
		n["in"].setInput( self.intPlug( 0 ) )
		n["in1"].setInput( self.intPlug( 0 ) )
		
		for name in [ "enabled", "index", "in", "in1" ] :
			a = n.affects( n[name] )
			self.assertEqual( len( a ), 1 )
			self.assertTrue( a[0].isSame( n["out"] ) )
		
		self.assertEqual( n.affects( n["out"] ), [] )
	
	def testOutOfRangeIndex( self ) :
	
		n = self.intSwitch()
		n["in"].setInput( self.intPlug( 0 ) )
		n["in1"].setInput( self.intPlug( 1 ) )
		n["in2"].setInput( self.intPlug( 2 ) )
		
		n["index"].setValue( 2 )
		self.assertEqual( n["out"].hash(), n["in2"].hash() )
		self.assertEqual( n["out"].getValue(), n["in2"].getValue() )

		# wrap around if the index is out of range
		
		n["index"].setValue( 3 )
		self.assertEqual( n["out"].hash(), n["in"].hash() )
		self.assertEqual( n["out"].getValue(), n["in"].getValue() )
		
		n["index"].setValue( 4 )
		self.assertEqual( n["out"].hash(), n["in1"].hash() )
		self.assertEqual( n["out"].getValue(), n["in1"].getValue() )
		
		n["index"].setValue( 5 )
		self.assertEqual( n["out"].hash(), n["in2"].hash() )
		self.assertEqual( n["out"].getValue(), n["in2"].getValue() )
	
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
		n["in"].setInput( self.colorPlug( IECore.Color3f( 0, 0.1, 0.2 ) ) )
		n["in1"].setInput( self.colorPlug( IECore.Color3f( 1, 1.1, 1.2 ) ) )
		n["in2"].setInput( self.colorPlug( IECore.Color3f( 2, 2.1, 2.2 ) ) )
		
		n["index"].setValue( 0 )
		self.assertEqual( n["out"].hash(), n["in"].hash() )
		self.assertEqual( n["out"].getValue(), n["in"].getValue() )
		
		n["index"].setValue( 1 )
		self.assertEqual( n["out"].hash(), n["in1"].hash() )
		self.assertEqual( n["out"].getValue(), n["in1"].getValue() )
		
		n["index"].setValue( 2 )
		self.assertEqual( n["out"].hash(), n["in2"].hash() )
		self.assertEqual( n["out"].getValue(), n["in2"].getValue() )		

	def testSerialisation( self ) :
	
		script = Gaffer.ScriptNode()
		script["s"] = self.intSwitch()
		script["a1"] = GafferTest.AddNode()
		script["a2"] = GafferTest.AddNode()
		script["a1"]["op1"].setValue( 1 )
		script["a2"]["op2"].setValue( 2 )
		script["s"]["in"].setInput( script["a1"]["sum"] )
		script["s"]["in1"].setInput( script["a2"]["sum"] )
		
		script2 = Gaffer.ScriptNode()
		script2.execute( script.serialise() )
		
		self.assertTrue( "in" in script2["s"] )
		self.assertTrue( "in1" in script2["s"] )
		self.assertTrue( "in2" in script2["s"] )
		self.assertFalse( "in3" in script2["s"] )
	
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
		script["s"]["in"].setInput( script["a1"]["sum"] )
		script["s"]["in1"].setInput( script["a2"]["sum"] )
		
		script["expression"] = Gaffer.Expression()
		script["expression"]["engine"].setValue( "python" )
		script["expression"]["expression"].setValue( 'parent["s"]["index"] = int( context.getFrame() )' )
		
		with script.context() :
			script.context().setFrame( 0 )
			self.assertEqual( script["s"]["out"].getValue(), 1 )
			script.context().setFrame( 1 )
			self.assertEqual( script["s"]["out"].getValue(), 2 )
	
	def testDependencyNodeSwitch( self ) :
	
		n = Gaffer.SwitchDependencyNode()
		n["in"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic  )
	
		self.assertTrue( n["out"].source().isSame( n["in"] ) )
		
		input0 = Gaffer.Plug()
		input1 = Gaffer.Plug()
		input2 = Gaffer.Plug()
		
		n["in"].setInput( input0 )
		self.assertTrue( n["out"].source().isSame( input0 ) )
	
		n["in1"].setInput( input1 )
		self.assertTrue( n["out"].source().isSame( input0 ) )
	
		n["index"].setValue( 1 )
		self.assertTrue( n["out"].source().isSame( input1 ) )
	
		n["enabled"].setValue( False )
		self.assertTrue( n["out"].source().isSame( input0 ) )
	
		n["in2"].setInput( input2 )
		self.assertTrue( n["out"].source().isSame( input0 ) )
	
		n["enabled"].setValue( True )
		self.assertTrue( n["out"].source().isSame( input1 ) )
	
		n["index"].setValue( 2 )
		self.assertTrue( n["out"].source().isSame( input2 ) )
	
	def testIndexInputAcceptance( self ) :
	
		cs = Gaffer.SwitchComputeNode()
		ds = Gaffer.SwitchDependencyNode()
		
		a = GafferTest.AddNode()
		a["boolInput"] = Gaffer.BoolPlug()
		a["boolOutput"] = Gaffer.BoolPlug( direction=Gaffer.Plug.Direction.Out )
		
		self.assertTrue( cs["index"].acceptsInput( a["op1"] ) )
		self.assertTrue( cs["index"].acceptsInput( a["sum"] ) )

		self.assertTrue( ds["index"].acceptsInput( a["op1"] ) )
		self.assertFalse( ds["index"].acceptsInput( a["sum"] ) )
		
		self.assertTrue( cs["enabled"].acceptsInput( a["boolInput"] ) )
		self.assertTrue( cs["enabled"].acceptsInput( a["boolOutput"] ) )

		self.assertTrue( ds["enabled"].acceptsInput( a["boolInput"] ) )
		self.assertFalse( ds["enabled"].acceptsInput( a["boolOutput"] ) )
	
	def testDependencyNodeConnectedIndex( self ) :
	
		n = Gaffer.SwitchDependencyNode()
		n["in"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		n["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic  )
		
		input0 = Gaffer.Plug()
		input1 = Gaffer.Plug()
		input2 = Gaffer.Plug()

		n["in"].setInput( input0 )
		n["in1"].setInput( input1 )
		n["in2"].setInput( input2 )
		
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

	def testDependencyNodeAcceptsNoneInputs( self ) :
	
		n = Gaffer.SwitchDependencyNode()
		self.assertTrue( n["enabled"].acceptsInput( None ) )
		self.assertTrue( n["index"].acceptsInput( None ) )

	def setUp( self ) :
	
		GafferTest.TestCase.setUp( self )

		self.__inputPlugs = []
	
	def tearDown( self ) :
	
		GafferTest.TestCase.tearDown( self )
		
		self.__inputPlugs = []

if __name__ == "__main__":
	unittest.main()
