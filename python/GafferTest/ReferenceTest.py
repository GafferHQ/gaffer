##########################################################################
#
#  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
import shutil
import collections
import imath
import six

import IECore

import Gaffer
import GafferTest

class ReferenceTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		# stash the StringInOutNode so we can restore it in
		# tearDown() - we're going to mischievously delete
		# it from the GafferTest module to induce errors
		# during testing.
		self.__StringInOutNode = GafferTest.StringInOutNode

	def testLoad( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )

		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( "n1" in s["r"] )
		self.assertTrue( s["r"]["sum"].getInput().isSame( s["r"]["n1"]["sum"] ) )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		Gaffer.PlugAlgo.promote( b["n1"]["op1"] )

		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		s = Gaffer.ScriptNode()
		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( "n1" in s["r"] )
		self.assertTrue( s["r"]["n1"]["op1"].getInput().isSame( s["r"]["op1"] ) )
		self.assertTrue( s["r"]["sum"].getInput().isSame( s["r"]["n1"]["sum"] ) )

		s["r"]["op1"].setValue( 25 )
		self.assertEqual( s["r"]["sum"].getValue(), 25 )

		ss = s.serialise()

		# referenced nodes should be referenced only, and not
		# explicitly mentioned in the serialisation at all.
		self.assertTrue( "AddNode" not in ss )
		# but the values of user plugs should be stored, so
		# they can override the values from the reference.
		self.assertTrue( "\"op1\"" in ss )

		s2 = Gaffer.ScriptNode()
		s2.execute( ss )

		self.assertTrue( "n1" in s2["r"] )
		self.assertTrue( s2["r"]["sum"].getInput().isSame( s2["r"]["n1"]["sum"] ) )
		self.assertEqual( s2["r"]["sum"].getValue(), 25 )

	def testReload( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n3"]["op1"].setInput( s["n2"]["sum"] )
		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"] ] ) )
		Gaffer.PlugAlgo.promote( b["n2"]["op2"] )

		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		s2 = Gaffer.ScriptNode()
		s2["n1"] = GafferTest.AddNode()
		s2["n3"] = GafferTest.AddNode()
		s2["n4"] = GafferTest.AddNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		s2["r"]["op1"].setInput( s2["n1"]["sum"] )
		s2["r"]["op2"].setValue( 1001 )
		s2["n3"]["op1"].setInput( s2["r"]["sum"] )
		s2["n4"]["op1"].setInput( s2["r"]["op2"] )

		self.assertTrue( "n2" in s2["r"] )
		self.assertTrue( s2["r"]["n2"]["op1"].getInput().isSame( s2["r"]["op1"] ) )
		self.assertTrue( s2["r"]["n2"]["op2"].getInput().isSame( s2["r"]["op2"] ) )
		self.assertEqual( s2["r"]["op2"].getValue(), 1001 )
		self.assertTrue( s2["r"]["sum"].getInput().isSame( s2["r"]["n2"]["sum"] ) )
		self.assertTrue( s2["r"]["op1"].getInput().isSame( s2["n1"]["sum"] ) )
		self.assertTrue( s2["n3"]["op1"].getInput().isSame( s2["r"]["sum"] ) )
		self.assertTrue( s2["n4"]["op1"].getInput() and s2["n4"]["op1"].getInput().isSame( s2["r"]["op2"] ) )
		originalReferencedNames = s2["r"].keys()

		b["anotherNode"] = GafferTest.AddNode()
		Gaffer.PlugAlgo.promote( b["anotherNode"]["op2"] )
		s.serialiseToFile( self.temporaryDirectory() + "/test.grf", b )

		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( "n2" in s2["r"] )
		self.assertEqual( set( s2["r"].keys() ), set( originalReferencedNames + [ "anotherNode", "op3" ] ) )
		self.assertTrue( s2["r"]["n2"]["op1"].getInput().isSame( s2["r"]["op1"] ) )
		self.assertTrue( s2["r"]["n2"]["op2"].getInput().isSame( s2["r"]["op2"] ) )
		self.assertEqual( s2["r"]["op2"].getValue(), 1001 )
		self.assertTrue( s2["r"]["anotherNode"]["op2"].getInput().isSame( s2["r"]["op3"] ) )
		self.assertTrue( s2["r"]["sum"].getInput().isSame( s2["r"]["n2"]["sum"] ) )
		self.assertTrue( s2["r"]["op1"].getInput().isSame( s2["n1"]["sum"] ) )
		self.assertTrue( s2["n3"]["op1"].getInput().isSame( s2["r"]["sum"] ) )
		self.assertTrue( s2["n4"]["op1"].getInput() and s2["n4"]["op1"].getInput().isSame( s2["r"]["op2"] ) )

	def testReloadDoesntRemoveCustomPlugs( self ) :

		# plugs unrelated to referencing shouldn't disappear when a reference is
		# reloaded. various parts of the ui might be using them for other purposes.

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		s2["r"]["__mySpecialPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( "__mySpecialPlug" in s2["r"] )

	def testLoadScriptWithReference( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n3"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )
		s["n3"]["op1"].setInput( s["n2"]["sum"] )

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n2"] ] ) )
		Gaffer.PlugAlgo.promote( b["n2"]["op2"] )
		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )
		s2["a"] = GafferTest.AddNode()

		s2["r"]["op2"].setValue( 123 )
		s2["r"]["op1"].setInput( s2["a"]["sum"] )

		self.assertTrue( "n2" in s2["r"] )
		self.assertTrue( "sum" in s2["r"] )
		self.assertTrue( s2["r"]["op1"].getInput().isSame( s2["a"]["sum"] ) )

		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.save()

		s3 = Gaffer.ScriptNode()
		s3["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s3.load()

		self.assertEqual( s3["r"].keys(), s2["r"].keys() )
		self.assertEqual( s3["r"]["user"].keys(), s2["r"]["user"].keys() )
		self.assertEqual( s3["r"]["op2"].getValue(), 123 )
		self.assertTrue( s3["r"]["op1"].getInput().isSame( s3["a"]["sum"] ) )

	def testReferenceExportCustomPlugsFromBoxes( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		b["myCustomPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		b["__invisiblePlugThatShouldntGetExported"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( "myCustomPlug" in s2["r"] )
		self.assertTrue( "__invisiblePlugThatShouldntGetExported" not in s2["r"] )

	def testPlugMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		p = Gaffer.PlugAlgo.promote( b["n1"]["op1"] )

		Gaffer.Metadata.registerValue( p, "description", "ppp" )

		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( Gaffer.Metadata.value( s2["r"].descendant( p.relativeName( b ) ), "description" ), "ppp" )

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertEqual( Gaffer.Metadata.value( s3["r"].descendant( p.relativeName( b ) ), "description" ), "ppp" )

	def testMetadataIsntResaved( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		p = Gaffer.PlugAlgo.promote( b["n1"]["op1"] )

		Gaffer.Metadata.registerValue( p, "description", "ppp" )

		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( "description" not in s2.serialise() )

	def testSinglePlugWithMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( s["b"]["p"], "description", "ddd" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "description" ), "ddd" )

	def testEditPlugMetadata( self ) :

		# Export a box with some metadata

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		p = Gaffer.PlugAlgo.promote( b["n1"]["op1"] )
		p.setName( "p" )

		Gaffer.Metadata.registerValue( p, "test", "referenced" )

		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		# Reference it, and check it loaded.

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( Gaffer.Metadata.value( s2["r"]["p"], "test" ), "referenced" )

		# Edit it, and check it overwrote the original.

		Gaffer.Metadata.registerValue( s2["r"]["p"], "test", "edited" )
		self.assertEqual( Gaffer.Metadata.value( s2["r"]["p"], "test" ), "edited" )

		# Save and load the script, and check the edit stays in place.

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertEqual( Gaffer.Metadata.value( s3["r"]["p"], "test" ), "edited" )

		# Reload the reference, and check the edit stays in place.

		s3["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertEqual( Gaffer.Metadata.value( s3["r"]["p"], "test" ), "edited" )

	def testAddPlugMetadata( self ) :

		# Export a box with no metadata

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.AddNode()

		b = Gaffer.Box.create( s, Gaffer.StandardSet( [ s["n1"] ] ) )
		p = Gaffer.PlugAlgo.promote( b["n1"]["op1"] )
		p.setName( "p" )

		b.exportForReference( self.temporaryDirectory() + "/test.grf" )

		# Reference it, and check it loaded.

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		# Add some metadata to the Reference node (not the reference file)

		Gaffer.Metadata.registerValue( s2["r"]["p"], "test", "added" )
		self.assertEqual( Gaffer.Metadata.value( s2["r"]["p"], "test" ), "added" )

		# Save and load the script, and check the added metadata stays in place.

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )
		self.assertEqual( Gaffer.Metadata.value( s3["r"]["p"], "test" ), "added" )

		# Reload the reference, and check the edit stays in place.

		s3["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertEqual( Gaffer.Metadata.value( s3["r"]["p"], "test" ), "added" )

	def testReloadWithUnconnectedPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( s["r"].keys(), [ "user", "p" ] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( s2["r"].keys(), [ "user", "p" ] )

	def testReloadRefreshesMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "test" ), None )

		Gaffer.Metadata.registerValue( s["b"]["p"], "test", 10 )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "test" ), 10 )

	def testDefaultValueClashes( self ) :

		# export a reference where a promoted plug is not at
		# its default value.

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()
		p = Gaffer.PlugAlgo.promote( s["b"]["n"]["op1"] )
		p.setValue( 10 )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		# reference it in to a new script, set the value back to
		# its default, and save the script.

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		p2 = s2["r"].descendant( p.relativeName( s["b"] ) )
		self.assertEqual( p2.getValue(), 10 )
		p2.setToDefault()
		self.assertEqual( p2.getValue(), p2.defaultValue() )

		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.save()

		# load the script, and check that the value is at the default.

		s3 = Gaffer.ScriptNode()
		s3["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s3.load()

		p3 = s3["r"].descendant( p.relativeName( s["b"] ) )
		self.assertEqual( p3.getValue(), p3.defaultValue() )

	def testLoadThrowsExceptionsOnError( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.StringInOutNode()

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		del GafferTest.StringInOutNode # induce a failure during loading

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()

		with IECore.CapturingMessageHandler() as mh :
			self.assertRaises( Exception, s2["r"].load, self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( len( mh.messages ), 2 )
		self.assertTrue( "has no attribute 'StringInOutNode'" in mh.messages[0].message )
		self.assertTrue( "KeyError: 'n'" in mh.messages[1].message )

	def testErrorTolerantLoading( self ) :

		# make a box containing 2 nodes, and export it.

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["s"] = GafferTest.StringInOutNode()
		s["b"]["a"] = GafferTest.AddNode()

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		# import it into a script.

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( "a" in s2["r"] )
		self.assertTrue( isinstance( s2["r"]["a"], GafferTest.AddNode ) )

		# save that script, and then mysteriously
		# disable GafferTest.StringInOutNode.

		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.save()

		del GafferTest.StringInOutNode

		# load the script, and check that we could at least
		# load in the other referenced node.

		s3 = Gaffer.ScriptNode()
		s3["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		with IECore.CapturingMessageHandler() as mh :
			s3.load( continueOnError=True )

		self.assertTrue( len( mh.messages ) )

		self.assertTrue( "a" in s3["r"] )
		self.assertTrue( isinstance( s3["r"]["a"], GafferTest.AddNode ) )

	def testDependencyNode( self ) :

		s = Gaffer.ScriptNode()

		# Make a reference, and check it's a DependencyNode

		s["r"] = Gaffer.Reference()
		self.assertTrue( isinstance( s["r"], Gaffer.DependencyNode ) )
		self.assertTrue( s["r"].isInstanceOf( Gaffer.DependencyNode.staticTypeId() ) )
		self.assertTrue( isinstance( s["r"], Gaffer.SubGraph ) )
		self.assertTrue( s["r"].isInstanceOf( Gaffer.SubGraph.staticTypeId() ) )

		# create a box with a promoted output:
		s["b"] = Gaffer.Box()
		s["b"]["n"] = GafferTest.AddNode()
		Gaffer.PlugAlgo.promote( s["b"]["n"]["sum"] )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		# load onto reference:
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertEqual( s["r"].correspondingInput( s["r"]["sum"] ), None )
		self.assertEqual( s["r"].enabledPlug(), None )

		# Wire it up to support enabledPlug() and correspondingInput()
		Gaffer.PlugAlgo.promote( s["b"]["n"]["op1"] )
		s["b"]["n"]["op2"].setValue( 10 )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		# reload reference and test:
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertEqual( s["r"].correspondingInput( s["r"]["sum"] ), None )
		self.assertEqual( s["r"].enabledPlug(), None )

		# add an enabled plug:
		s["b"]["enabled"] = Gaffer.BoolPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		# reload reference and test that's now visible via enabledPlug():
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertEqual( s["r"].correspondingInput( s["r"]["sum"] ), None )
		self.assertTrue( s["r"].enabledPlug().isSame( s["r"]["enabled"] ) )

		# hook up the enabled plug inside the box:
		s["b"]["n"]["enabled"].setInput( s["b"]["enabled"] )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		# reload reference and test that's now visible via enabledPlug():
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertTrue( s["r"].enabledPlug().isSame( s["r"]["enabled"] ) )
		self.assertTrue( s["r"].correspondingInput( s["r"]["sum"] ).isSame( s["r"]["op1"] ) )

		# Connect it into a network, delete it, and check that we get nice auto-reconnect behaviour
		s["a"] = GafferTest.AddNode()
		s["r"]["op1"].setInput( s["a"]["sum"] )

		s["c"] = GafferTest.AddNode()
		s["c"]["op1"].setInput( s["r"]["sum"] )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["r"] ] ) )

		self.assertTrue( s["c"]["op1"].getInput().isSame( s["a"]["sum"] ) )

	def testPlugFlagsOnReload( self ):

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["s"] = GafferTest.StringInOutNode()
		s["b"]["a"] = GafferTest.AddNode()

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		# import it into a script.

		s2 = Gaffer.ScriptNode()
		s2["r"] = Gaffer.Reference()
		s2["r"].load( self.temporaryDirectory() + "/test.grf" )
		s2["r"]["__pluggy"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		s2["r"]["__pluggy"]["int"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		s2["r"]["__pluggy"]["compound"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		s2["r"]["__pluggy"]["compound"]["int"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )

		self.assertEqual( s2["r"]["__pluggy"].getFlags(), Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		self.assertEqual( s2["r"]["__pluggy"]["int"].getFlags(), Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		self.assertEqual( s2["r"]["__pluggy"]["compound"].getFlags(), Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		self.assertEqual( s2["r"]["__pluggy"]["compound"]["int"].getFlags(), Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )

		s2["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( s2["r"]["__pluggy"].getFlags(), Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		self.assertEqual( s2["r"]["__pluggy"]["int"].getFlags(), Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		self.assertEqual( s2["r"]["__pluggy"]["compound"].getFlags(), Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )
		self.assertEqual( s2["r"]["__pluggy"]["compound"]["int"].getFlags(), Gaffer.Plug.Flags.Dynamic | Gaffer.Plug.Flags.Default )

	def testDefaultValues( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.IntPlug( defaultValue = 1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["p"].setValue( 2 )
		s["b"]["c"] = Gaffer.Color3fPlug( defaultValue = imath.Color3f( 1 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["c"].setValue( imath.Color3f( 0.5 ) )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		# The value at the time of box export should become
		# the default value on the reference node. But the
		# default value on the box itself should remain the
		# same.

		self.assertEqual( s["r"]["p"].getValue(), 2 )
		self.assertEqual( s["r"]["p"].defaultValue(), 2 )
		self.assertEqual( s["b"]["p"].defaultValue(), 1 )

		self.assertEqual( s["r"]["c"].getValue(), imath.Color3f( 0.5 ) )
		self.assertEqual( s["r"]["c"].defaultValue(), imath.Color3f( 0.5 ) )
		self.assertEqual( s["b"]["c"].defaultValue(), imath.Color3f( 1 ) )

		# And we should be able to save and reload the script
		# and have that still be the case.

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()
		s.load()

		self.assertEqual( s["r"]["p"].getValue(), 2 )
		self.assertEqual( s["r"]["p"].defaultValue(), 2 )
		self.assertEqual( s["b"]["p"].getValue(), 2 )
		self.assertEqual( s["b"]["p"].defaultValue(), 1 )

		self.assertEqual( s["r"]["c"].getValue(), imath.Color3f( 0.5 ) )
		self.assertEqual( s["r"]["c"].defaultValue(), imath.Color3f( 0.5 ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Color3f( 0.5 ) )
		self.assertEqual( s["b"]["c"].defaultValue(), imath.Color3f( 1 ) )

		# If we change the value on the box and reexport,
		# then the reference should pick up both the new value
		# and the new default.

		s["b"]["p"].setValue( 3 )
		s["b"]["c"].setValue( imath.Color3f( 0.25 ) )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( s["r"]["p"].getValue(), 3 )
		self.assertEqual( s["r"]["p"].defaultValue(), 3 )
		self.assertEqual( s["b"]["p"].getValue(), 3 )
		self.assertEqual( s["b"]["p"].defaultValue(), 1 )

		self.assertEqual( s["r"]["c"].getValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["r"]["c"].defaultValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["b"]["c"].defaultValue(), imath.Color3f( 1 ) )

		# And that should still hold after saving and reloading the script.

		s.save()
		s.load()
		self.assertEqual( s["r"]["p"].getValue(), 3 )
		self.assertEqual( s["r"]["p"].defaultValue(), 3 )
		self.assertEqual( s["b"]["p"].getValue(), 3 )
		self.assertEqual( s["b"]["p"].defaultValue(), 1 )

		self.assertEqual( s["r"]["c"].getValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["r"]["c"].defaultValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["b"]["c"].defaultValue(), imath.Color3f( 1 ) )

		# But if the user changes the value on the reference node,
		# it should be kept.

		s["r"]["p"].setValue( 100 )
		s["r"]["c"].setValue( imath.Color3f( 100 ) )

		self.assertEqual( s["r"]["p"].getValue(), 100 )
		self.assertEqual( s["r"]["p"].defaultValue(), 3 )
		self.assertEqual( s["b"]["p"].getValue(), 3 )
		self.assertEqual( s["b"]["p"].defaultValue(), 1 )

		self.assertEqual( s["r"]["c"].getValue(), imath.Color3f( 100 ) )
		self.assertEqual( s["r"]["c"].defaultValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["b"]["c"].defaultValue(), imath.Color3f( 1 ) )

		# And a save and load shouldn't change that.

		s.save()
		s.load()

		self.assertEqual( s["r"]["p"].getValue(), 100 )
		self.assertEqual( s["r"]["p"].defaultValue(), 3 )
		self.assertEqual( s["b"]["p"].getValue(), 3 )
		self.assertEqual( s["b"]["p"].defaultValue(), 1 )

		self.assertEqual( s["r"]["c"].getValue(), imath.Color3f( 100 ) )
		self.assertEqual( s["r"]["c"].defaultValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Color3f( 0.25 ) )
		self.assertEqual( s["b"]["c"].defaultValue(), imath.Color3f( 1 ) )

		# And now the user has changed a value, only the
		# default value should be updated if we load a new
		# reference.

		s["b"]["p"].setValue( 4 )
		s["b"]["c"].setValue( imath.Color3f( 4 ) )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( s["r"]["p"].getValue(), 100 )
		self.assertEqual( s["r"]["p"].defaultValue(), 4 )
		self.assertEqual( s["b"]["p"].getValue(), 4 )
		self.assertEqual( s["b"]["p"].defaultValue(), 1 )

		self.assertEqual( s["r"]["c"].getValue(), imath.Color3f( 100 ) )
		self.assertEqual( s["r"]["c"].defaultValue(), imath.Color3f( 4 ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Color3f( 4 ) )
		self.assertEqual( s["b"]["c"].defaultValue(), imath.Color3f( 1 ) )

		# And a save and load shouldn't change anything.

		s.save()
		s.load()

		self.assertEqual( s["r"]["p"].getValue(), 100 )
		self.assertEqual( s["r"]["p"].defaultValue(), 4 )
		self.assertEqual( s["b"]["p"].getValue(), 4 )
		self.assertEqual( s["b"]["p"].defaultValue(), 1 )

		self.assertEqual( s["r"]["c"].getValue(), imath.Color3f( 100 ) )
		self.assertEqual( s["r"]["c"].defaultValue(), imath.Color3f( 4 ) )
		self.assertEqual( s["b"]["c"].getValue(), imath.Color3f( 4 ) )
		self.assertEqual( s["b"]["c"].defaultValue(), imath.Color3f( 1 ) )

		# And since we know that all plugs in box exports
		# have had their default values set to the current
		# value, there shouldn't be any need for a single
		# setValue() call in the exported file.

		e = "".join( open( self.temporaryDirectory() + "/test.grf" ).readlines() )
		self.assertTrue( "setValue" not in e )

	def testInternalNodeDefaultValues( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["n"] = Gaffer.Node()
		s["b"]["n"]["p"] = Gaffer.IntPlug( defaultValue = 1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["n"]["p"].setValue( 2 )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		# Nothing at all should have changed about the
		# values and defaults on the internal nodes.

		self.assertEqual( s["r"]["n"]["p"].getValue(), 2 )
		self.assertEqual( s["r"]["n"]["p"].defaultValue(), 1 )

		# And we should be able to save and reload the script
		# and have that still be the case.

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()
		s.load()

		self.assertEqual( s["r"]["n"]["p"].getValue(), 2 )
		self.assertEqual( s["r"]["n"]["p"].defaultValue(), 1 )

	def testNodeMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()

		Gaffer.Metadata.registerValue( s["b"], "description", "Test description" )
		Gaffer.Metadata.registerValue( s["b"], "nodeGadget:color", imath.Color3f( 1, 0, 0 ) )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( Gaffer.Metadata.value( s["r"], "description" ), "Test description" )
		self.assertEqual( Gaffer.Metadata.value( s["r"], "nodeGadget:color" ), imath.Color3f( 1, 0, 0 ) )

	def testVersionMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( Gaffer.Metadata.value( s["r"], "serialiser:milestoneVersion" ), Gaffer.About.milestoneVersion() )
		self.assertEqual( Gaffer.Metadata.value( s["r"], "serialiser:majorVersion" ), Gaffer.About.majorVersion() )
		self.assertEqual( Gaffer.Metadata.value( s["r"], "serialiser:minorVersion" ), Gaffer.About.minorVersion() )
		self.assertEqual( Gaffer.Metadata.value( s["r"], "serialiser:patchVersion" ), Gaffer.About.patchVersion() )

		self.assertTrue( "serialiser:milestoneVersion" not in Gaffer.Metadata.registeredValues( s["r"], persistentOnly = True ) )
		self.assertTrue( "serialiser:majorVersion" not in Gaffer.Metadata.registeredValues( s["r"], persistentOnly = True ) )
		self.assertTrue( "serialiser:minorVersion" not in Gaffer.Metadata.registeredValues( s["r"], persistentOnly = True ) )
		self.assertTrue( "serialiser:patchVersion" not in Gaffer.Metadata.registeredValues( s["r"], persistentOnly = True ) )

	def testSerialiseWithoutLoading( self ) :

		s = Gaffer.ScriptNode()
		s["r"] = Gaffer.Reference()

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

	def testUserPlugMetadata( self ) :

		# People should be able to do what they want with the user plug,
		# and anything they do should be serialised appropriately.

		s = Gaffer.ScriptNode()
		s["r"] = Gaffer.Reference()
		s["r"]["user"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( s["r"]["user"], "testPersistent", 1, persistent = True )
		Gaffer.Metadata.registerValue( s["r"]["user"], "testNonPersistent", 2, persistent = False )

		Gaffer.Metadata.registerValue( s["r"]["user"]["p"], "testPersistent", 3, persistent = True )
		Gaffer.Metadata.registerValue( s["r"]["user"]["p"], "testNonPersistent", 4, persistent = False )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["user"], "testPersistent" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["user"], "testNonPersistent" ), 2 )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["user"]["p"], "testPersistent" ), 3 )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["user"]["p"], "testNonPersistent" ), 4 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertEqual( Gaffer.Metadata.value( s2["r"]["user"], "testPersistent" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( s2["r"]["user"], "testNonPersistent" ), None )

		self.assertEqual( Gaffer.Metadata.value( s2["r"]["user"]["p"], "testPersistent" ), 3 )
		self.assertEqual( Gaffer.Metadata.value( s2["r"]["user"]["p"], "testNonPersistent" ), None )

	def testNamespaceIsClear( self ) :

		# We need the namespace of the node to be empty, so
		# that people can call plugs anything they want when
		# authoring references.

		r = Gaffer.Reference()
		n = Gaffer.Node()
		self.assertEqual( r.keys(), n.keys() )

	def testPlugCalledFileName( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["fileName"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["fileName"].setValue( "iAmUsingThisForMyOwnPurposes" )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( s["r"]["fileName"].getValue(), "iAmUsingThisForMyOwnPurposes" )

	def testLoadScriptWithReferenceFromVersion0_14( self ) :

		shutil.copyfile(
			os.path.dirname( __file__ ) + "/references/version-0.14.0.0.grf",
			"/tmp/test.grf"
		)

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/referenceVersion-0.14.0.0.gfr" )

		with IECore.CapturingMessageHandler() as mh :
			s.load( continueOnError = True )

		# Although we expect it to load OK, we do also expect to receive a
		# warning message because we removed the fileName plug after version 0.14.
		self.assertEqual( len( mh.messages ), 1 )
		self.assertTrue( "KeyError: \"'fileName'" in mh.messages[0].message )

		self.assertEqual( s["Reference"]["testPlug"].getValue(), 2 )

	def testFileNameAccessor( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		self.assertEqual( s["r"].fileName(), "" )

		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertEqual( s["r"].fileName(), self.temporaryDirectory() + "/test.grf" )

	def testUndo( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		self.assertEqual( s["r"].fileName(), "" )
		self.assertTrue( "p" not in s["r"] )

		State = collections.namedtuple( "State", [ "keys", "fileName" ] )
		states = []
		def referenceLoaded( node ) :
			states.append( State( keys = node.keys(), fileName = node.fileName() ) )

		c = s["r"].referenceLoadedSignal().connect( referenceLoaded )

		with Gaffer.UndoScope( s ) :
			s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( "p" in s["r"] )
		self.assertEqual( s["r"].fileName(), self.temporaryDirectory() + "/test.grf" )
		self.assertTrue( len( states ), 1 )
		self.assertEqual( states[0], State( [ "user", "p" ], self.temporaryDirectory() + "/test.grf" ) )

		s.undo()
		self.assertEqual( s["r"].fileName(), "" )
		self.assertTrue( "p" not in s["r"] )
		self.assertTrue( len( states ), 2 )
		self.assertEqual( states[1], State( [ "user" ], "" ) )

		s.redo()
		self.assertTrue( "p" in s["r"] )
		self.assertEqual( s["r"].fileName(), self.temporaryDirectory() + "/test.grf" )
		self.assertTrue( len( states ), 3 )
		self.assertEqual( states[2], State( [ "user", "p" ], self.temporaryDirectory() + "/test.grf" ) )

	def testUserPlugsNotReferenced( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["user"]["a"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		self.assertTrue( "a" in s["b"]["user"] )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertTrue( "a" not in s["r"]["user"] )

		a = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		b = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["r"]["user"]["a"] = a
		s["r"]["user"]["b"] = b
		self.assertTrue( s["r"]["user"]["a"].isSame( a ) )
		self.assertTrue( s["r"]["user"]["b"].isSame( b ) )

		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertTrue( s["r"]["user"]["a"].isSame( a ) )
		self.assertTrue( s["r"]["user"]["b"].isSame( b ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( "a" in s2["r"]["user"] )
		self.assertTrue( "b" in s2["r"]["user"] )

	def testCopyPaste( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["a1"] = GafferTest.AddNode()
		s["b"]["a2"] = GafferTest.AddNode()
		s["b"]["a2"]["op1"].setInput( s["b"]["a1"]["sum"] )
		Gaffer.PlugAlgo.promote( s["b"]["a1"]["op1"] )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s.execute( s.serialise( parent = s["r"], filter = Gaffer.StandardSet( [ s["r"]["a1"], s["r"]["a2"] ] ) ) )

		self.assertTrue( "a1" in s )
		self.assertTrue( "a2" in s )
		self.assertTrue( s["a2"]["op1"].getInput().isSame( s["a1"]["sum"] ) )

	def testReloadWithNestedInputConnections( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["array"] = Gaffer.ArrayPlug( element = Gaffer.IntPlug(), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["color"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["a"] = GafferTest.AddNode()

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["r"]["array"][0].setInput( s["a"]["sum"] )
		s["r"]["array"][1].setInput( s["a"]["sum"] )
		s["r"]["color"]["g"].setInput( s["a"]["sum"] )

		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( s["r"]["array"][0].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["r"]["array"][1].getInput().isSame( s["a"]["sum"] ) )
		self.assertTrue( s["r"]["color"]["g"].getInput().isSame( s["a"]["sum"] ) )

	def testReloadWithNestedOutputConnections( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["color"] = Gaffer.Color3fPlug(
			direction = Gaffer.Plug.Direction.Out,
			flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic
		)
		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["a"] = GafferTest.AddNode()

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		s["a"]["op1"].setInput( s["r"]["color"]["g"] )

		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertTrue( s["a"]["op1"].getInput().isSame( s["r"]["color"]["g"] ) )

	def testReloadWithBoxIO( self ) :

		s = Gaffer.ScriptNode()

		s["b"] = Gaffer.Box()
		s["b"]["a"] = GafferTest.AddNode()

		s["b"]["i"] = Gaffer.BoxIn()
		s["b"]["i"]["name"].setValue( "in" )
		s["b"]["i"].setup( s["b"]["a"]["op1"] )
		s["b"]["a"]["op1"].setInput( s["b"]["i"]["out"] )

		s["b"]["o"] = Gaffer.BoxOut()
		s["b"]["o"]["name"].setValue( "out" )
		s["b"]["o"].setup( s["b"]["a"]["sum"] )
		s["b"]["o"]["in"].setInput( s["b"]["a"]["sum"] )

		referenceFileName = self.temporaryDirectory() + "/test.grf"
		s["b"].exportForReference( referenceFileName )

		s["a1"] = GafferTest.AddNode()

		s["r"] = Gaffer.Reference()
		s["r"].load( referenceFileName )
		s["r"]["in"].setInput( s["a1"]["sum"] )

		s["a2"] = GafferTest.AddNode()
		s["a2"]["op1"].setInput( s["r"]["out"] )

		def assertReferenceConnections() :

			self.assertTrue( s["a2"]["op1"].source().isSame( s["r"]["a"]["sum"] ) )
			self.assertTrue( s["r"]["a"]["op1"].source().isSame( s["a1"]["sum"] ) )

			self.assertEqual(
				set( s["r"].keys() ),
				set( [ "in", "out", "user", "a", "i", "o" ] ),
			)

		assertReferenceConnections()

		s["r"].load( referenceFileName )

		assertReferenceConnections()

	def testSearchPaths( self ) :

		s = Gaffer.ScriptNode()

		referenceFile = "test.grf"

		boxA = Gaffer.Box( "BoxA" )
		boxA["p"] = Gaffer.StringPlug( defaultValue = "a", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s.addChild( boxA )
		boxPathA = os.path.join( self.temporaryDirectory(), "a" )
		os.makedirs( boxPathA )
		fileA = os.path.join( boxPathA, referenceFile )
		boxA.exportForReference( fileA )

		boxB = Gaffer.Box( "BoxB" )
		boxB["p"] = Gaffer.StringPlug( defaultValue = "b", flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s.addChild( boxB )
		boxPathB = os.path.join(self.temporaryDirectory(), "b")
		os.makedirs( boxPathB )
		fileB = os.path.join( boxPathB, referenceFile )
		boxB.exportForReference( fileB )

		searchPathA = ":".join( [boxPathA, boxPathB] )
		searchPathB = ":".join( [boxPathB, boxPathA] )

		os.environ["GAFFER_REFERENCE_PATHS"] = searchPathA
		s["r"] = Gaffer.Reference()

		s["r"].load(referenceFile)
		self.assertEqual( s["r"].fileName(), referenceFile )
		self.assertEqual( s["r"]["p"].getValue(), "a" )

		os.environ["GAFFER_REFERENCE_PATHS"] = searchPathB
		s["r"].load( referenceFile )
		self.assertEqual( s["r"].fileName(), referenceFile )
		self.assertEqual( s["r"]["p"].getValue(), "b" )

	def testLoadThrowsOnMissingFile( self ) :

		s = Gaffer.ScriptNode()
		s["r"] = Gaffer.Reference()

		with six.assertRaisesRegex( self, Exception, "Could not find file 'thisFileDoesntExist.grf'" ) :
			s["r"].load( "thisFileDoesntExist.grf" )

	def testHasMetadataEdit( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p1"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["b"]["p2"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		Gaffer.Metadata.registerValue( s["b"]["p1"], "referenced", "original" )
		Gaffer.Metadata.registerValue( s["b"]["p2"], "referenced", "original" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p1"], "referenced" ) )
		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p2"], "referenced" ) )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p1"], "referenced" ), "original" )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p2"], "referenced" ), "original" )

		with Gaffer.UndoScope( s ) :
			Gaffer.Metadata.registerValue( s["r"]["p1"], "referenced", "override" )

		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p1"], "referenced" ) )
		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p2"], "referenced" ) )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p1"], "referenced" ), "override" )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p2"], "referenced" ), "original" )

		with Gaffer.UndoScope( s ) :
			Gaffer.Metadata.registerValue( s["r"]["p1"], "referenced", "foo" )
			Gaffer.Metadata.registerValue( s["r"]["p2"], "referenced", "bar" )

		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p1"], "referenced" ) )
		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p2"], "referenced" ) )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p1"], "referenced" ), "foo" )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p2"], "referenced" ), "bar" )

		s.undo()

		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p1"], "referenced" ) )
		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p2"], "referenced" ) )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p1"], "referenced" ), "override" )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p2"], "referenced" ), "original" )

		s.undo()

		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p1"], "referenced" ) )
		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p2"], "referenced" ) )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p1"], "referenced"), "original" )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p2"], "referenced"), "original" )

		s.redo()

		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p1"], "referenced" ) )
		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p2"], "referenced" ) )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p1"], "referenced" ), "override" )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p2"], "referenced" ), "original" )

		s.redo()

		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p1"], "referenced" ) )
		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p2"], "referenced" ) )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p1"], "referenced" ), "foo" )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p2"], "referenced" ), "bar" )

	def testHasMetadataEditAfterReload( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.IntPlug( defaultValue = 1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.Metadata.registerValue( s["b"]["p"], "referenced", "original" )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p"], "referenced" ) )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "referenced" ), "original" )

		Gaffer.Metadata.registerValue( s["r"]["p"], "referenced", "override" )
		p = s["r"]["p"]
		self.assertTrue( s["r"].hasMetadataEdit( p, "referenced" ) )
		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p"], "referenced" ) )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "referenced" ), "override" )

		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		# The old plug doesn't have an edit any more, because
		# it doesn't even belong to the reference any more.
		self.assertFalse( s["r"].isAncestorOf( p ) )
		self.assertFalse( s["r"].hasMetadataEdit( p, "referenced" ) )

		# But the new plug does have one.
		self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p"], "referenced" ) )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "referenced"), "override" )

	def testPlugMetadataOverrides( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.IntPlug( defaultValue = 1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.Metadata.registerValue( s["b"]["p"], "preset:Red", 0 )
		Gaffer.Metadata.registerValue( s["b"]["p"], "preset:Green", 1 )
		Gaffer.Metadata.registerValue( s["b"]["p"], "preset:Blue", 2 )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		# Make sure the metadata exported on the plug was loaded by the Reference
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "preset:Red" ), 0 )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "preset:Green" ), 1 )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "preset:Blue" ), 2 )

		# Overriding one of the existing entries
		Gaffer.Metadata.registerValue( s["r"]["p"], "preset:Green", 100 )
		# Add an entirely new metadata entry
		Gaffer.Metadata.registerValue( s["r"]["p"], "preset:Alpha", 3 )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "preset:Alpha" ), 3 )

		# Change exported metadata and reload.
		# When reloading, the existing data on the Reference is preserved.
		# When creating new Reference, the data on the new instance is as per the referenced box.
		Gaffer.Metadata.registerValue( s["b"]["p"], "preset:Blue", 42 )

		s["b"].exportForReference( self.temporaryDirectory() + "/test2.grf" )
		s["r"].load( self.temporaryDirectory() + "/test2.grf" )

		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "preset:Red" ), 0 )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "preset:Green" ), 100 )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "preset:Blue" ), 42 )  # Reverted to referenced value
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"], "preset:Alpha" ), 3 )

		def assertMetadata( script ) :

			# Red hasn't been touched at all, expect value from the referenced box.
			self.assertEqual( Gaffer.Metadata.value( script["r"]["p"], "preset:Red" ), 0 )
			self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p"], "preset:Red" ) )

			# Green has been overridden on the Reference node which needs to be preserved.
			self.assertEqual( Gaffer.Metadata.value( script["r"]["p"], "preset:Green" ), 100 )
			self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p"], "preset:Green" ) )

			# Blue has been changed in the referenced box and the new value needs
			# to come through as the old one hasn't been overridden.
			self.assertEqual( Gaffer.Metadata.value( script["r"]["p"], "preset:Blue" ), 42 )
			self.assertFalse( s["r"].hasMetadataEdit( s["r"]["p"], "preset:Blue" ) )

			# Alpha has been added, which needs to be preserved.
			self.assertEqual( Gaffer.Metadata.value( script["r"]["p"], "preset:Alpha" ), 3 )
			self.assertTrue( s["r"].hasMetadataEdit( s["r"]["p"], "preset:Alpha" ) )

		assertMetadata( s )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		assertMetadata( s2 )

		# Make sure serialising several times doesn't change the serialised
		# data. This could happen if serialised edits wouldn't lead to recorded
		# edits on the new reference.

		s3 = Gaffer.ScriptNode()
		s3.execute( s2.serialise() )

		assertMetadata( s3 )

	def testChildPlugMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()
		s["b"]["p"] = Gaffer.Color3fPlug( defaultValue = imath.Color3f( 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["r"] = Gaffer.Reference()
		s["r"].load( self.temporaryDirectory() + "/test.grf" )

		Gaffer.Metadata.registerValue( s["r"]["p"]["r"], "isRed", True )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		# The metadata needs to be serialised.
		self.assertEqual( Gaffer.Metadata.value( s2["r"]["p"]["r"], "isRed" ), True )

		# It also needs to be transferred on reload
		s["r"].load( self.temporaryDirectory() + "/test.grf" )
		self.assertEqual( Gaffer.Metadata.value( s["r"]["p"]["r"], "isRed" ), True )

	def testUserPlugMetadataSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["r"] = Gaffer.Reference()
		Gaffer.Metadata.registerValue( s["r"]["user"], "hasChild", True )

		s["r"]["user"]["child"] = Gaffer.IntPlug( defaultValue = 1, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.Metadata.registerValue( s["r"]["user"]["child"], "hasChild", False )

		# We don't register edits on user plugs.
		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["user"], "hasChild" ) )
		self.assertFalse( s["r"].hasMetadataEdit( s["r"]["user"]["child"], "hasChild" ) )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		# We do, however, expect changes to be serialised.
		self.assertEqual( Gaffer.Metadata.value( s2["r"]["user"], "hasChild" ), True )
		self.assertEqual( Gaffer.Metadata.value( s2["r"]["user"]["child"], "hasChild" ), False )

	def testPlugPromotionPreservesMetadata( self ) :

		s = Gaffer.ScriptNode()
		s["b"] = Gaffer.Box()

		s["b"]["p"] = Gaffer.Color3fPlug( defaultValue = imath.Color3f( 0 ), flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		Gaffer.Metadata.registerValue( s["b"]["p"], "isColor", True )

		s["b"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		s["b2"] = Gaffer.Box()

		s["b2"]["r"] = Gaffer.Reference()
		s["b2"]["r"].load( self.temporaryDirectory() + "/test.grf" )

		Gaffer.PlugAlgo.promote( s["b2"]["r"]["p"] )

		self.assertEqual( Gaffer.Metadata.value( s["b2"]["p"], "isColor" ), True )

	def testPromotedSpreadsheetDefaultValues( self ) :

		script = Gaffer.ScriptNode()
		script["box"] = Gaffer.Box()

		script["box"]["spreadsheet"] = Gaffer.Spreadsheet()
		script["box"]["spreadsheet"]["rows"].addColumn( Gaffer.StringPlug( "string" ) )
		script["box"]["spreadsheet"]["rows"].addColumn( Gaffer.IntPlug( "int" ) )
		script["box"]["spreadsheet"]["rows"].addRows( 2 )

		script["box"]["spreadsheet"]["rows"][0]["cells"]["string"]["value"].setValue( "default" )
		script["box"]["spreadsheet"]["rows"][0]["cells"]["int"]["value"].setValue( -1 )
		script["box"]["spreadsheet"]["rows"][1]["cells"]["string"]["value"].setValue( "one" )
		script["box"]["spreadsheet"]["rows"][1]["cells"]["int"]["value"].setValue( 1 )
		script["box"]["spreadsheet"]["rows"][2]["cells"]["string"]["value"].setValue( "two" )
		script["box"]["spreadsheet"]["rows"][2]["cells"]["int"]["value"].setValue( 2 )

		script["box"]["spreadsheet"]["rows"][1]["name"].setValue( "row1" )
		script["box"]["spreadsheet"]["rows"][1]["enabled"].setValue( False )

		Gaffer.PlugAlgo.promote( script["box"]["spreadsheet"]["rows"] )

		script["box"].exportForReference( self.temporaryDirectory() + "/test.grf" )

		script["reference"] = Gaffer.Reference()
		script["reference"].load( self.temporaryDirectory() + "/test.grf" )

		self.assertEqual( len( script["reference"]["rows"] ), len( script["box"]["rows"] ) )
		self.assertEqual( script["reference"]["rows"][0].keys(), script["box"]["rows"][0].keys() )

		for row in range( 0, len( script["box"]["rows"] ) ) :

			self.assertEqual(
				script["reference"]["rows"][row]["name"].getValue(),
				script["box"]["rows"][row]["name"].getValue()
			)
			self.assertEqual(
				script["reference"]["rows"][row]["enabled"].getValue(),
				script["box"]["rows"][row]["enabled"].getValue()
			)

			for column in range( 0, len( script["box"]["rows"][0]["cells"].keys() ) ) :
				self.assertEqual(
					script["reference"]["rows"][row]["cells"][column]["value"].getValue(),
					script["box"]["rows"][row]["cells"][column]["value"].getValue(),
				)
				self.assertEqual(
					script["reference"]["rows"][row]["cells"][column]["enabled"].getValue(),
					script["box"]["rows"][row]["cells"][column]["enabled"].getValue(),
				)

		self.assertTrue( script["reference"]["rows"].isSetToDefault() )

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		GafferTest.StringInOutNode = self.__StringInOutNode

		for f in (
			"/tmp/test.grf",
		) :
			if os.path.exists( f ) :
				os.remove( f )

if __name__ == "__main__":
	unittest.main()
