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
		
		s2["r"]["__mySpecialPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		s2["r"].load( "/tmp/test.grf" )
		
		self.assertTrue( "__mySpecialPlug" in s2["r"] )
	
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
	
	def testReferenceExportCustomPlugsFromBoxes( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		b["myCustomPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		b["__invisiblePlugThatShouldntGetExported"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		b.exportForReference( "/tmp/test.grf" )
		
		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		
		self.assertTrue( "myCustomPlug" in s2["r"] )
		self.assertTrue( "__invisiblePlugThatShouldntGetExported" not in s2["r"] )
	
	def testPlugMetadata( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		p = b.promotePlug( b["n1"]["op1"] )
		
		Gaffer.Metadata.registerPlugValue( p, "description", "ppp" )
		
		b.exportForReference( "/tmp/test.grf" )
		
		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		
		self.assertEqual( Gaffer.Metadata.plugValue( s2["r"].descendant( p.relativeName( b ) ), "description" ), "ppp" )
	
	def testMetadataIsntResaved( self ) :
	
		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()
		
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		p = b.promotePlug( b["n1"]["op1"] )
		
		Gaffer.Metadata.registerPlugValue( p, "description", "ppp" )
		
		b.exportForReference( "/tmp/test.grf" )
		
		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		
		self.assertTrue( "Metadata" not in s2.serialise() )
	
	def testSinglePlugWithMetadata( self ) :
	
		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["user"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		
		Gaffer.Metadata.registerPlugValue( s["b"]["user"]["p"], "description", "ddd" )
		
		s["b"].exportForReference( "/tmp/test.grf" )
		
		s["r"] = Gaffer.Reference()
		s["r"].load( "/tmp/test.grf" )
		
		self.assertEqual( Gaffer.Metadata.plugValue( s["r"]["user"]["p"], "description" ), "ddd" )
	
	def testReloadWithUnconnectedPlugs( self ) :
	
		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["user"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"].exportForReference( "/tmp/test.grf" )
		
		s["r"] = Gaffer.Reference()
		s["r"].load( "/tmp/test.grf" )
		
		self.assertEqual( s["r"]["user"].keys(), [ "p" ] )
		
		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		
		self.assertEqual( s2["r"]["user"].keys(), [ "p" ] )
	
	def testReloadRefreshesMetadata( self ) :
	
		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["user"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"].exportForReference( "/tmp/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( "/tmp/test.grf" )
		
		self.assertEqual( Gaffer.Metadata.plugValue( s["r"]["user"]["p"], "test" ), None )
		
		Gaffer.Metadata.registerPlugValue( s["b"]["user"]["p"], "test", 10 )
		s["b"].exportForReference( "/tmp/test.grf" )

		s["r"].load( "/tmp/test.grf" )

		self.assertEqual( Gaffer.Metadata.plugValue( s["r"]["user"]["p"], "test" ), 10 )		
	
	def testDefaultValueClashes( self ) :
	
		# export a reference where a promoted plug is not at
		# its default value.
	
		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()
		p = s["b"].promotePlug( s["b"]["n"]["op1"] )
		p.setValue( p.defaultValue() + 10 )
		
		s["b"].exportForReference( "/tmp/test.grf" )
		
		# reference it in to a new script, set the value back to
		# its default, and save the script.
		
		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( "/tmp/test.grf" )
		
		p2 = s2["r"].descendant( p.relativeName( s["b"] ) )
		self.assertEqual( p2.getValue(), p2.defaultValue() + 10 )
		p2.setToDefault()
		self.assertEqual( p2.getValue(), p2.defaultValue() )
		
		s2["fileName"].setValue( "/tmp/test.gfr" )
		s2.save()
		
		# load the script, and check that the value is at the default.
		
		s3 = Gaffer.ScriptNode()
		s3["fileName"].setValue( "/tmp/test.gfr" )
		s3.load()

		p3 = s3["r"].descendant( p.relativeName( s["b"] ) )
		self.assertEqual( p3.getValue(), p3.defaultValue() )
		
	def tearDown( self ) :
	
		for f in (
			"/tmp/test.grf",
			"/tmp/test.gfr",
		) :
			if os.path.exists( f ) :
				os.remove( f )
		
if __name__ == "__main__":
	unittest.main()
	
