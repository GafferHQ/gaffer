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

import os
import unittest

import IECore

import Gaffer
import GafferTest

class ReferenceTest( unittest.TestCase ) :
			
	def testLoad( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		
		b.exportForReference( "/tmp/test.grf" )
		
		s["r"] = Gaffer.Reference()
		s["r"].load( "/tmp/test.grf" )
		
		self.assertTrue( "n1" in s["r"] )
		self.assertTrue( s["r"]["out"].getInput().isSame( s["r"]["n1"]["sum"] ) )
	
	def testSerialisation( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		b.promotePlug( b["n1"]["op1"] )
		
		b.exportForReference( "/tmp/test.grf" )
		
		s = Gaffer.ScriptNode()
		s["r"] = Gaffer.Reference()
		s["r"].load( "/tmp/test.grf" )
		
		self.assertTrue( "n1" in s["r"] )
		self.assertTrue( s["r"]["n1"]["op1"].getInput().isSame( s["r"]["user"]["n1_op1"] ) )
		self.assertTrue( s["r"]["out"].getInput().isSame( s["r"]["n1"]["sum"] ) )
		
		s["r"]["user"]["n1_op1"].setValue( 25 )
		self.assertEqual( s["r"]["out"].getValue(), 25 )
	
		ss = s.serialise()
				
		# referenced nodes should be referenced only, and not
		# explicitly mentioned in the serialisation at all.
		self.assertTrue( "AddNode" not in ss )
		# but the values of user plugs should be stored, so
		# they can override the values from the reference.
		self.assertTrue( "\"n1_op1\"" in ss )
		
		s2 = Gaffer.ScriptNode()
		s2.execute( ss )
		
		self.assertTrue( "n1" in s2["r"] )
		self.assertTrue( s2["r"]["out"].getInput().isSame( s2["r"]["n1"]["sum"] ) )
		self.assertEqual( s2["r"]["out"].getValue(), 25 )
		
	def testReload( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"] ] ) )
		b.promotePlug( b["n2"]["op2"] )
		
		b.exportForReference( "/tmp/test.grf" )
		
		s2 = Gaffer.ScriptNode()
		s2["n1"] = GafferTest.AddNode()
		s2["n3"] = GafferTest.AddNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		
		s2["r"]["in"].setInput( s2["n1"]["sum"] )
		s2["r"]["user"]["n2_op2"].setValue( 1001 )
		s2["n3"]["op1"].setInput( s2["r"]["out"] )
		
		self.assertTrue( "n2" in s2["r"] )
		self.assertTrue( s2["r"]["n2"]["op1"].getInput().isSame( s2["r"]["in"] ) )
		self.assertTrue( s2["r"]["n2"]["op2"].getInput().isSame( s2["r"]["user"]["n2_op2"] ) )
		self.assertEqual( s2["r"]["user"]["n2_op2"].getValue(), 1001 )
		self.assertTrue( s2["r"]["out"].getInput().isSame( s2["r"]["n2"]["sum"] ) )
		self.assertTrue( s2["r"]["in"].getInput().isSame( s2["n1"]["sum"] ) )
		self.assertTrue( s2["n3"]["op1"].getInput().isSame( s2["r"]["out"] ) )
		originalReferencedNames = s2["r"].keys()
		
		b["anotherNode"] = GafferTest.AddNode()
		b.promotePlug( b["anotherNode"]["op2"] )
		s.serialiseToFile( "/tmp/test.grf", b )
		
		s2["r"].load( "/tmp/test.grf" )
				
		self.assertTrue( "n2" in s2["r"] )
		self.assertEqual( set( s2["r"].keys() ), set( originalReferencedNames + [ "anotherNode" ] ) )
		self.assertTrue( s2["r"]["n2"]["op1"].getInput().isSame( s2["r"]["in"] ) )
		self.assertTrue( s2["r"]["n2"]["op2"].getInput().isSame( s2["r"]["user"]["n2_op2"] ) )
		self.assertEqual( s2["r"]["user"]["n2_op2"].getValue(), 1001 )
		self.assertTrue( s2["r"]["anotherNode"]["op2"].getInput().isSame( s2["r"]["user"]["anotherNode_op2"] ) )
		self.assertTrue( s2["r"]["out"].getInput().isSame( s2["r"]["n2"]["sum"] ) )
		self.assertTrue( s2["r"]["in"].getInput().isSame( s2["n1"]["sum"] ) )
		self.assertTrue( s2["n3"]["op1"].getInput().isSame( s2["r"]["out"] ) )

	def testReloadPreservesPlugIdentities( self ) :
	
		# when reloading a reference, we'd prefer to reuse the old external output plugs rather than
		# replace them with new ones - this makes life much easier for observers of those plugs.
		
		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"] ] ) )
		
		b.exportForReference( "/tmp/test.grf" )

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		
		inPlug = s2["r"]["in"]
		outPlug = s2["r"]["out"]
		
		s2["r"].load( "/tmp/test.grf" )
		
		self.assertTrue( inPlug.isSame( s2["r"]["in"] ) )
		self.assertTrue( outPlug.isSame( s2["r"]["out"] ) )

	def testReloadDoesntRemoveCustomPlugs( self ) :
	
		# plugs unrelated to referencing shouldn't disappear when a reference is
		# reloaded. various parts of the ui might be using them for other purposes.
		
		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		b.exportForReference( "/tmp/test.grf" )
		
		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		
		s2["r"]["mySpecialPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		s2["r"].load( "/tmp/test.grf" )
		
		self.assertTrue( "mySpecialPlug" in s2["r"] )
	
	def testLoadScriptWithReference( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"] ] ) )
		b.promotePlug( b["n2"]["op2"] )
		b.exportForReference( "/tmp/test.grf" )
		
		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		s2["a"] = GafferTest.AddNode()
		
		s2["r"]["user"]["n2_op2"].setValue( 123 )
		s2["r"]["in"].setInput( s2["a"]["sum"] )
		
		self.assertTrue( "n2_op2" in s2["r"]["user"] )
		self.assertTrue( "n2" in s2["r"] )
		self.assertTrue( "out" in s2["r"] )
		self.assertEqual( s2["r"]["user"]["n2_op2"].getValue(), 123 )
		self.assertTrue( s2["r"]["in"].getInput().isSame( s2["a"]["sum"] ) )
		
		s2["fileName"].setValue( "/tmp/test.gfr" )
		s2.save()
				
		s3 = Gaffer.ScriptNode()
		s3["fileName"].setValue( "/tmp/test.gfr" )
		s3.load()
		
		self.assertEqual( s3["r"].keys(), s2["r"].keys() )
		self.assertEqual( s3["r"]["user"].keys(), s2["r"]["user"].keys() )
		self.assertEqual( s3["r"]["user"]["n2_op2"].getValue(), 123 )
		self.assertTrue( s3["r"]["in"].getInput().isSame( s3["a"]["sum"] ) )
	
	def testReferencesDontGetCustomPlugsFromBoxes( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		b["myCustomPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		b.exportForReference( "/tmp/test.grf" )
		
		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		
		self.assertTrue( "myCustomPlug" not in s2["r"] )
		
	def tearDown( self ) :
	
		for f in (
			"/tmp/test.grf",
			"/tmp/test.gfr",
		) :
			if os.path.exists( f ) :
				os.remove( f )
		
if __name__ == "__main__":
	unittest.main()
	
