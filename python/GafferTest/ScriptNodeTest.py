##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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
import sys
import weakref
import gc
import os
import shutil
import inspect
import functools

import IECore

import Gaffer
import GafferTest

class ScriptNodeTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		ScriptNodeTest.lastNode = None
		ScriptNodeTest.lastScript = None
		ScriptNodeTest.lastResult = None

	def test( self ) :

		s = Gaffer.ScriptNode()
		self.assertEqual( s.getName(), "ScriptNode" )

		self.assertEqual( s["fileName"].typeName(), "Gaffer::StringPlug" )

	def testExecution( self ) :

		s = Gaffer.ScriptNode()

		def f( n, s ) :
			ScriptNodeTest.lastNode = n
			ScriptNodeTest.lastScript = s

		c = s.scriptExecutedSignal().connect( f )

		s.execute( "script.addChild( Gaffer.Node( 'child' ) )" )
		self.assertEqual( ScriptNodeTest.lastNode, s )
		self.assertEqual( ScriptNodeTest.lastScript, "script.addChild( Gaffer.Node( 'child' ) )" )

		self.assert_( s["child"].typeName(), "Node" )

	def testEvaluation( self ) :

		s = Gaffer.ScriptNode()

		def f( n, s, r ) :
			ScriptNodeTest.lastNode = n
			ScriptNodeTest.lastScript = s
			ScriptNodeTest.lastResult = r

		c = s.scriptEvaluatedSignal().connect( f )

		n = s.evaluate( "10 * 10" )
		self.assertEqual( n, 100 )
		self.assertEqual( ScriptNodeTest.lastNode, s )
		self.assertEqual( ScriptNodeTest.lastScript, "10 * 10" )
		self.assertEqual( ScriptNodeTest.lastResult, 100 )

		p = s.evaluate( "Gaffer.IntPlug()" )
		self.assertEqual( p.typeName(), "Gaffer::IntPlug" )
		self.assertEqual( ScriptNodeTest.lastNode, s )
		self.assertEqual( ScriptNodeTest.lastScript, "Gaffer.IntPlug()" )
		self.assert_( p.isSame( ScriptNodeTest.lastResult ) )
		del p
		del ScriptNodeTest.lastResult

	def testSelection( self ) :

		s = Gaffer.ScriptNode()
		self.assert_( isinstance( s.selection(), Gaffer.Set ) )

		n = Gaffer.Node()

		self.assertRaises( Exception, s.selection().add, n )

		s.addChild( n )

		s.selection().add( n )

		self.failUnless( n in s.selection() )

		s.removeChild( n )

		self.failIf( n in s.selection() )

	def testSerialisation( self ) :

		s = Gaffer.ScriptNode()

		s["a1"] = GafferTest.AddNode()
		s["a1"]["op1"].setValue( 5 )
		s["a1"]["op2"].setValue( 6 )

		s["a2"] = GafferTest.AddNode()
		s["a2"]["op1"].setInput( s["a1"]["sum"] )
		s["a2"]["op2"].setValue( 10 )

		s2 = Gaffer.ScriptNode()
		se = s.serialise()

		s2.execute( se )

		self.assert_( s2["a2"]["op1"].getInput().isSame( s2["a1"]["sum"] ) )

	def testDynamicPlugSerialisation( self ) :

		s1 = Gaffer.ScriptNode()

		s1["n1"] = GafferTest.AddNode()
		s1["n2"] = GafferTest.AddNode()
		s1["n1"]["dynamicPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s1["n1"]["dynamicPlug"].setInput( s1["n2"]["sum"] )
		s1["n1"]["dynamicPlug2"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s1["n1"]["dynamicPlug2"].setValue( 100 )
		s1["n1"]["dynamicStringPlug"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s1["n1"]["dynamicStringPlug"].setValue( "hiThere" )
		s1["n1"]["dynamicOutPlug"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, direction=Gaffer.Plug.Direction.Out )
		s1["n1"]["dynamicColorOutPlug"] = Gaffer.Color3fPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, direction=Gaffer.Plug.Direction.Out )

		s2 = Gaffer.ScriptNode()
		s2.execute( s1.serialise() )

		self.assert_( s2["n1"]["dynamicPlug"].getInput().isSame( s2["n2"]["sum"] ) )
		self.assertEqual( s2["n1"]["dynamicPlug2"].getValue(), 100 )
		self.assertEqual( s2["n1"]["dynamicStringPlug"].getValue(), "hiThere" )
		self.failUnless( isinstance( s2["n1"]["dynamicOutPlug"], Gaffer.IntPlug ) )
		self.failUnless( isinstance( s2["n1"]["dynamicColorOutPlug"], Gaffer.Color3fPlug ) )

	def testLifetime( self ) :

		s = Gaffer.ScriptNode()
		w = weakref.ref( s )
		del s
		IECore.RefCounted.collectGarbage()

		self.assertEqual( w(), None )

	def testSaveAndLoad( self ) :

		s = Gaffer.ScriptNode()

		s["a1"] = GafferTest.AddNode()
		s["a2"] = GafferTest.AddNode()

		s["a1"]["op1"].setValue( 5 )
		s["a1"]["op2"].setValue( 6 )

		s["a2"] = GafferTest.AddNode()
		s["a2"]["op1"].setInput( s["a1"]["sum"] )
		s["a2"]["op2"].setValue( 10 )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.load()

		self.assert_( s2["a2"]["op1"].getInput().isSame( s2["a1"]["sum"] ) )

	def testLoadClearsFirst( self ) :

		s = Gaffer.ScriptNode()
		s["a1"] = GafferTest.AddNode()

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s.load()
		self.failIf( "a2" in s )

	def testSaveFailureHandling( self ) :

		s = Gaffer.ScriptNode()
		s["a1"] = GafferTest.AddNode()

		s["fileName"].setValue( "/this/directory/doesnt/exist" )
		self.assertRaises( Exception, s.save )

	def testLoadFailureHandling( self ) :

		s = Gaffer.ScriptNode()

		s["fileName"].setValue( "/this/file/doesnt/exist" )
		self.assertRaises( Exception, s.load )

	def testCopyPaste( self ) :

		app = Gaffer.ApplicationRoot()

		s1 = Gaffer.ScriptNode()
		s2 = Gaffer.ScriptNode()

		app["scripts"]["s1"] = s1
		app["scripts"]["s2"] = s2

		n1 = GafferTest.AddNode()
		s1["n1"] = n1

		s1.copy()

		s2.paste()

		self.assert_( s1["n1"].isInstanceOf( GafferTest.AddNode.staticTypeId() ) )
		self.assert_( s2["n1"].isInstanceOf( GafferTest.AddNode.staticTypeId() ) )

	def testSerialisationWithKeywords( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = GafferTest.KeywordPlugNode()

		se = s.serialise()
		s2 = Gaffer.ScriptNode()
		s2.execute( se )

	def testSerialisationWithNodeKeywords( self ) :

		s = Gaffer.ScriptNode()
		s["in"] = Gaffer.Node()

		se = s.serialise()

		s2 = Gaffer.ScriptNode()
		s2.execute( se )

		self.assertEqual( s2["in"].typeName(), "Gaffer::Node" )

	# Executing the result of serialise() shouldn't leave behind any residue.
	def testSerialisationPollution( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n"]["op1"].setInput( s["n2"]["sum"] )

		s.execute( "import Gaffer" ) # we don't want to complain that this would be added by the serialisation and execution
		s.execute( "import GafferTest" ) # same here as our test module contains the AddNode

		se = s.serialise()

		l = s.evaluate( "set( locals().keys() )" )
		g = s.evaluate( "set( globals().keys() )" )

		s.execute( se )

		self.failUnless( s.evaluate( "set( locals().keys() )" )==l )
		self.failUnless( s.evaluate( "set( globals().keys() )" )==g )

	def testDeriveAndOverrideAcceptsChild( self ) :

		class MyScriptNode( Gaffer.ScriptNode ) :

			def __init__( self, name ) :

				Gaffer.ScriptNode.__init__( self, name )

			def acceptsChild( self, child ) :

				return isinstance( child, GafferTest.AddNode )

		IECore.registerRunTimeTyped( MyScriptNode )

		n = MyScriptNode( "s" )

		c1 = GafferTest.AddNode()
		c2 = Gaffer.Node()

		n.addChild( c1 )
		self.failUnless( c1.parent() is n )
		self.failUnless( c1.scriptNode() is n )

		self.assertRaises( RuntimeError, n.addChild, c2 )
		self.failUnless( c2.parent() is None )

	def testExecutionExceptions( self ) :

		n = Gaffer.ScriptNode()

		self.assertRaises( RuntimeError, n.execute, "raise ValueError" )

		self.assertRaises( KeyError, n.evaluate, "{}['a']" )

	def testVariableScope( self ) :

		# if a variable gets made in one execution, it shouldn't persist in the next.

		n = Gaffer.ScriptNode()

		n.execute( "a = 10" )

		self.assertRaises( NameError, n.evaluate, "a" )

	def testClassScope( self ) :

		# this works in a normal python console, so it damn well better work
		# in a script editor.

		s = """
class A() :

	def __init__( self ) :

		print A

a = A()"""

		n = Gaffer.ScriptNode()
		n.execute( s )

	def testDeselectionOnDelete( self ) :

		s = Gaffer.ScriptNode()

		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()

		s["n1"] = n1
		s["n2"] = n2

		s.selection().add( n1 )
		self.failUnless( n1 in s.selection() )

		del s["n1"]

		self.failUnless( n1 not in s.selection() )

	def testContext( self ) :

		s = Gaffer.ScriptNode()

		c = s.context()
		c.setFrame( 10.0 )

		self.assertEqual( s.context().getFrame(), 10.0 )
		self.failUnless( s.context().isSame( c ) )

	def testFrameRange( self ) :

		s = Gaffer.ScriptNode()

		self.failUnless( isinstance( s["frameRange"]["start"], Gaffer.IntPlug ) )
		self.failUnless( isinstance( s["frameRange"]["end"], Gaffer.IntPlug ) )

		self.assertEqual( s["frameRange"]["start"].getValue(), 1 )
		self.assertEqual( s["frameRange"]["end"].getValue(), 100 )

		s["frameRange"]["start"].setValue( 110 )
		self.assertEqual( s["frameRange"]["start"].getValue(), 110 )
		self.assertEqual( s["frameRange"]["end"].getValue(), 110 )

		s["frameRange"]["end"].setValue( 200 )
		self.assertEqual( s["frameRange"]["start"].getValue(), 110 )
		self.assertEqual( s["frameRange"]["end"].getValue(), 200 )

		s["frameRange"]["end"].setValue( 100 )
		self.assertEqual( s["frameRange"]["start"].getValue(), 100 )
		self.assertEqual( s["frameRange"]["end"].getValue(), 100 )

	def testFrameRangeLoadAndSave( self ) :

		s = Gaffer.ScriptNode()

		s["frameRange"]["start"].setValue( 110 )
		s["frameRange"]["end"].setValue( 200 )
		self.assertEqual( s["frameRange"]["start"].getValue(), 110 )
		self.assertEqual( s["frameRange"]["end"].getValue(), 200 )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.load()

		self.assertEqual( s2["frameRange"]["start"].getValue(), 110 )
		self.assertEqual( s2["frameRange"]["end"].getValue(), 200 )

	def testApplicationRoot( self ) :

		s = Gaffer.ScriptNode()
		self.failUnless( s.applicationRoot() is None )

		a = Gaffer.ApplicationRoot()
		a["scripts"]["one"] = s

		self.failUnless( s.applicationRoot().isSame( a ) )

	def testLifeTimeAfterExecution( self ) :

		# the ScriptNode used to keep an internal dictionary
		# as the context for all script execution. this created the
		# danger of circular references keeping it alive forever.
		# that is no longer the case, but this test remains to ensure
		# that the same problem doesn't crop up in the future.

		a = Gaffer.ApplicationRoot()
		a["scripts"]["s"] = Gaffer.ScriptNode()

		a["scripts"]["s"].execute( "script.addChild( Gaffer.Node( \"a\" ) )" )
		a["scripts"]["s"].execute( "circularRef = script.getChild( \"a\" ).parent()" )

		w = weakref.ref( a["scripts"]["s"] )

		del a["scripts"]["s"]
		IECore.RefCounted.collectGarbage()

		self.assertEqual( w(), None )

	def testDeleteNodes( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()
		self.assertEqual( len( s.children( Gaffer.Node ) ), 3 )

		s.deleteNodes()
		self.assertEqual( len( s.children( Gaffer.Node ) ), 0 )

	def testDeleteManyNodes( self ) :

		s = Gaffer.ScriptNode()
		for i in range( 0, 10000 ) :
			s["c%d"%i] = Gaffer.Node()

		s.deleteNodes()

		self.assertEqual( len( s.children( Gaffer.Node ) ), 0 )

	def testDeleteNodesDoesntRemovePlugs( self ) :

		s = Gaffer.ScriptNode()
		s.deleteNodes()

		self.failUnless( "fileName" in s )

	def testDeleteNodesWithFilter( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()
		self.assertEqual( len( s.children( Gaffer.Node ) ), 3 )

		s.deleteNodes( filter = Gaffer.StandardSet( [ s["n1"] ] ) )
		self.assertEqual( len( s.children( Gaffer.Node ) ), 2 )
		self.failUnless( "n" in s )
		self.failUnless( "n1" not in s )
		self.failUnless( "n2" in s )

	def testDeleteNodesMaintainsConnections( self ) :

		s = Gaffer.ScriptNode()
		n1 = GafferTest.AddNode()
		n2 = GafferTest.MultiplyNode()
		n3 = GafferTest.AddNode()
		n4 = GafferTest.AddNode()

		s.addChild( n1 )
		s.addChild( n2 )
		s.addChild( n3 )
		s.addChild( n4 )

		n2["op1"].setInput( n1["sum"] )
		n2["op2"].setInput( n1["sum"] )
		n3["op1"].setInput( n1["sum"] )
		n3["op2"].setInput( n1["sum"] )
		n4["op1"].setInput( n2["product"] )
		n4["op2"].setInput( n3["sum"] )
		self.assert_( n2["op1"].getInput().isSame( n1["sum"] ) )
		self.assert_( n2["op2"].getInput().isSame( n1["sum"] ) )
		self.assert_( n3["op1"].getInput().isSame( n1["sum"] ) )
		self.assert_( n3["op2"].getInput().isSame( n1["sum"] ) )
		self.assert_( n4["op1"].getInput().isSame( n2["product"] ) )
		self.assert_( n4["op2"].getInput().isSame( n3["sum"] ) )

		s.deleteNodes( filter = Gaffer.StandardSet( [ n2, n3 ] ) )

		self.assertEqual( n2["op1"].getInput(), None )
		self.assertEqual( n2["op2"].getInput(), None )
		self.assertEqual( n3["op1"].getInput(), None )
		self.assertEqual( n3["op2"].getInput(), None )
		# None because MultiplyOp does not define enabledPlug()
		self.assertEqual( n4["op1"].getInput(), None )
		self.assert_( n4["op2"].getInput().isSame( n1["sum"] ) )

		n2["op1"].setInput( n1["sum"] )
		n2["op2"].setInput( n1["sum"] )
		n3["op1"].setInput( n1["sum"] )
		n3["op2"].setInput( n1["sum"] )
		n4["op1"].setInput( n2["product"] )
		n4["op2"].setInput( n3["sum"] )
		s.addChild( n2 )
		s.addChild( n3 )

		s.deleteNodes( filter = Gaffer.StandardSet( [ n2, n3 ] ), reconnect = False )

		self.assertEqual( n2["op1"].getInput(), None )
		self.assertEqual( n2["op2"].getInput(), None )
		self.assertEqual( n3["op1"].getInput(), None )
		self.assertEqual( n3["op2"].getInput(), None )
		self.assertEqual( n4["op1"].getInput(), None )
		self.assertEqual( n4["op2"].getInput(), None )

	def testDeleteNodesWithEnabledPlugsWithoutCorrespondingInput( self ) :

		class MyAddNode( GafferTest.AddNode ) :

			def correspondingInput( self, output ) :

				return None

		s = Gaffer.ScriptNode()
		n1 = GafferTest.AddNode()
		n2 = MyAddNode()
		n3 = GafferTest.AddNode()

		s.addChild( n1 )
		s.addChild( n2 )
		s.addChild( n3 )

		n2["op1"].setInput( n1["sum"] )
		n2["op2"].setInput( n1["sum"] )
		n3["op1"].setInput( n2["sum"] )
		n3["op2"].setInput( n2["sum"] )
		self.assert_( n2["op1"].getInput().isSame( n1["sum"] ) )
		self.assert_( n2["op2"].getInput().isSame( n1["sum"] ) )
		self.assert_( n3["op1"].getInput().isSame( n2["sum"] ) )
		self.assert_( n3["op2"].getInput().isSame( n2["sum"] ) )

		s.deleteNodes( filter = Gaffer.StandardSet( [ n2 ] ) )

		self.assertEqual( n2["op1"].getInput(), None )
		self.assertEqual( n2["op2"].getInput(), None )
		self.assertEqual( n3["op1"].getInput(), None )
		self.assertEqual( n3["op2"].getInput(), None )

	def testReconnectionToFloatingNodes( self ) :

		s = Gaffer.ScriptNode()
		n1 = GafferTest.AddNode()
		n2 = GafferTest.AddNode()
		n3 = GafferTest.AddNode()

		s.addChild( n1 )
		s.addChild( n2 )

		n2["op1"].setInput( n1["sum"] )
		n2["op2"].setInput( n1["sum"] )

		n3["op1"].setInput( n2["sum"] )
		n3["op2"].setInput( n2["sum"] )

		self.assert_( n2["op1"].getInput().isSame( n1["sum"] ) )
		self.assert_( n2["op2"].getInput().isSame( n1["sum"] ) )

		self.assert_( n3["op1"].getInput().isSame( n2["sum"] ) )
		self.assert_( n3["op2"].getInput().isSame( n2["sum"] ) )

		s.deleteNodes( filter = Gaffer.StandardSet( [ n2 ] ) )

		# the inputs to n3 shouldn't have been reconnected, as it's not a descendant of the script:
		self.assertEqual( n3["op1"].getInput(), None )
		self.assertEqual( n3["op2"].getInput(), None )

	def testScriptAccessor( self ) :

		s = Gaffer.ScriptNode()
		self.failUnless( s.evaluate( "script" ).isSame( s ) )

	def testParentAccessor( self ) :

		s = Gaffer.ScriptNode()
		self.failUnless( s.evaluate( "parent" ).isSame( s ) )

		s["b"] = Gaffer.Box()
		self.failUnless( s.evaluate( "parent", parent = s["b"] ).isSame( s["b"] ) )

	def testDynamicPlugSaveAndLoad( self ) :

		s = Gaffer.ScriptNode()

		s["customSetting"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["customSetting"].setValue( 100 )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.load()

		self.assertEqual( s2["customSetting"].getValue(), 100 )

	def testSerialiseCircularConnections( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		s["n1"]["in"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n1"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out,  flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n2"]["in"] = Gaffer.Plug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
		s["n2"]["out"] = Gaffer.Plug( direction = Gaffer.Plug.Direction.Out, flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )

		s["n1"]["in"].setInput( s["n2"]["out"] )
		s["n2"]["in"].setInput( s["n1"]["out"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )

		self.assertTrue( s2["n1"]["in"].getInput().isSame( s2["n2"]["out"] ) )
		self.assertTrue( s2["n2"]["in"].getInput().isSame( s2["n1"]["out"] ) )

	def testSerialiseWithFilter( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise( filter = Gaffer.StandardSet( [ s["n2"] ] ) ) )

		self.assertTrue( "n2" in s2 )
		self.assertTrue( "n1" not in s2 )

		self.assertEqual( s2["n2"]["op1"].getInput(), None )

	def testCopyIgnoresNestedSelections( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"].addChild( s )

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["b"] = Gaffer.Box()
		s["b"]["n1"] = GafferTest.AddNode()

		s.selection().add( s["n1"] )
		s.selection().add( s["b"]["n1"] )
		s.copy( filter = s.selection() )

		s2 = Gaffer.ScriptNode()
		a["scripts"].addChild( s2 )
		s2.paste()

		self.assertTrue( "n1" in s2 )
		self.assertTrue( "b" not in s2 )

		s.selection().clear()
		s.selection().add( s["b"]["n1"] )
		s.copy( filter = s.selection() )

		s2 = Gaffer.ScriptNode()
		a["scripts"].addChild( s2 )
		s2.paste()

		self.assertTrue( "b" not in s2 )
		self.assertTrue( "n1" not in s2 )

	def testCopyPasteWithSpecificSourceParent( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"].addChild( s )

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["b"] = Gaffer.Box()
		s["b"]["n3"] = GafferTest.AddNode()
		s["b"]["n4"] = GafferTest.AddNode()

		s.selection().add( s["n1"] )
		s.selection().add( s["b"]["n3"] )

		s.copy( parent=s["b"], filter = s.selection() )

		s2 = Gaffer.ScriptNode()
		a["scripts"].addChild( s2 )
		s2.paste()

		self.assertTrue( "n1" not in s2 )
		self.assertTrue( "n2" not in s2 )
		self.assertTrue( "b" not in s2 )
		self.assertTrue( "n3" in s2 )
		self.assertTrue( "n4" not in s2 )

	def testCopyPasteWithSpecificDestinationParent( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"].addChild( s )

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()

		s.selection().add( s["n1"] )
		s.copy( filter = s.selection() )

		s2 = Gaffer.ScriptNode()
		a["scripts"].addChild( s2 )
		s2["b"] = Gaffer.Box()
		s2.paste( parent = s2["b"] )

		self.assertTrue( "n1" not in s2 )
		self.assertTrue( "n2" not in s2 )
		self.assertTrue( "n1" in s2["b"] )
		self.assertTrue( "n2" not in s2["b"] )

		self.assertEqual( len( s2.selection() ), 1 )
		self.assertTrue( s2["b"]["n1"] in s2.selection() )

	def testCutWithSpecificSourceParent( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"].addChild( s )

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["b"] = Gaffer.Box()
		s["b"]["n3"] = GafferTest.AddNode()
		s["b"]["n4"] = GafferTest.AddNode()

		s.selection().add( s["n1"] )
		s.selection().add( s["b"]["n3"] )

		s.cut( parent=s["b"], filter = s.selection() )
		self.assertTrue( "n1" in s )
		self.assertTrue( "n2" in s )
		self.assertTrue( "b" in s )
		self.assertTrue( "n3" not in s["b"] )
		self.assertTrue( "n4" in s["b"] )

		s2 = Gaffer.ScriptNode()
		a["scripts"].addChild( s2 )
		s2.paste()

		self.assertTrue( "n1" not in s2 )
		self.assertTrue( "n2" not in s2 )
		self.assertTrue( "b" not in s2 )
		self.assertTrue( "n3" in s2 )
		self.assertTrue( "n4" not in s2 )

	def testActionSignal( self ) :

		s = Gaffer.ScriptNode()

		cs = GafferTest.CapturingSlot( s.actionSignal() )

		# shouldn't trigger anything, because it's not in an undo context
		s.addChild( Gaffer.Node() )
		self.assertEqual( len( cs ), 0 )

		# should trigger something, because it's in an undo context
		with Gaffer.UndoContext( s ) :
			s.addChild( Gaffer.Node( "a" ) )

		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( s ) )
		self.assertTrue( isinstance( cs[0][1], Gaffer.Action ) )
		self.assertEqual( cs[0][2], Gaffer.Action.Stage.Do )

		# undo should trigger as well
		s.undo()

		self.assertEqual( len( cs ), 2 )
		self.assertTrue( cs[1][0].isSame( s ) )
		self.assertTrue( cs[1][1].isSame( cs[0][1] ) )
		self.assertEqual( cs[1][2], Gaffer.Action.Stage.Undo )

		# as should redo
		s.redo()

		self.assertEqual( len( cs ), 3 )
		self.assertTrue( cs[2][0].isSame( s ) )
		self.assertTrue( cs[2][1].isSame( cs[0][1] ) )
		self.assertEqual( cs[2][2], Gaffer.Action.Stage.Redo )

	def testLoadingMovedScriptDoesntKeepOldFileName( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		shutil.move( self.temporaryDirectory() + "/test.gfr", self.temporaryDirectory() + "/test2.gfr" )

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.temporaryDirectory() + "/test2.gfr" )
		s.load()

		self.assertEqual( s["fileName"].getValue(), self.temporaryDirectory() + "/test2.gfr" )

	def testUnsavedChanges( self ) :

		s = Gaffer.ScriptNode()

		self.assertEqual( s["unsavedChanges"].getValue(), False )

		# the unsaved changes flag only reacts to undoable changes
		# so this shouldn't set the flag
		s["nonUndoableNode"] = GafferTest.AddNode()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

		# but this should.
		with Gaffer.UndoContext( s ) :
			s["node"] = GafferTest.AddNode()
		self.assertEqual( s["unsavedChanges"].getValue(), True )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

		with Gaffer.UndoContext( s ) :
			s["node"]["op1"].setValue( 10 )
		self.assertEqual( s["unsavedChanges"].getValue(), True )

		s.save()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

		with Gaffer.UndoContext( s ) :
			s["node"]["op1"].setValue( 20 )
		self.assertEqual( s["unsavedChanges"].getValue(), True )

		s.save()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

		s.undo()
		self.assertEqual( s["unsavedChanges"].getValue(), True )

		s.save()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

		s.redo()
		self.assertEqual( s["unsavedChanges"].getValue(), True )

		s.save()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

		with Gaffer.UndoContext( s ) :
			s["node2"] = GafferTest.AddNode()
		self.assertEqual( s["unsavedChanges"].getValue(), True )

		s.save()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

		with Gaffer.UndoContext( s ) :
			s["node2"]["op1"].setInput( s["node"]["sum"] )
		self.assertEqual( s["unsavedChanges"].getValue(), True )

		s.save()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

		s.load()
		self.assertEqual( s["unsavedChanges"].getValue(), False )

	def testSerialiseToFile( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		s.serialiseToFile( self.temporaryDirectory() + "/test.gfr" )

		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.load()

		self.assertTrue( "n1" in s2 )
		self.assertTrue( "n2" in s2 )
		self.assertTrue( s2["n2"]["op1"].getInput().isSame( s2["n1"]["sum"] ) )

		s.serialiseToFile( self.temporaryDirectory() + "/test.gfr", filter = Gaffer.StandardSet( [ s["n2"] ] ) )

		s3 = Gaffer.ScriptNode()
		s3["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s3.load()

		self.assertTrue( "n1" not in s3 )
		self.assertTrue( "n2" in s3 )

	def testExecuteFile( self ) :

		s = Gaffer.ScriptNode()

		s["n1"] = GafferTest.AddNode()
		s["n2"] = GafferTest.AddNode()
		s["n2"]["op1"].setInput( s["n1"]["sum"] )

		s.serialiseToFile( self.temporaryDirectory() + "/test.gfr" )

		s2 = Gaffer.ScriptNode()

		self.assertRaises( RuntimeError, s2.executeFile, "thisFileDoesntExist.gfr" )

		s2.executeFile( self.temporaryDirectory() + "/test.gfr" )

		self.assertTrue( s2["n2"]["op1"].getInput().isSame( s2["n1"]["sum"] ) )

	def testUndoAndRedoOrder( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.IntPlug()

		values = []
		def f( plug ) :
			values.append( plug.getValue() )

		c = s["n"].plugSetSignal().connect( f )

		with Gaffer.UndoContext( s ) :
			s["n"]["p"].setValue( 10 )
			s["n"]["p"].setValue( 20 )

		self.assertEqual( values, [ 10, 20 ] )

		s.undo()
		self.assertEqual( values, [ 10, 20, 10, 0 ] )

		s.redo()
		self.assertEqual( values, [ 10, 20, 10, 0, 10, 20 ] )

	def testUndoAddedSignal( self ) :

		s = Gaffer.ScriptNode()

		cs = GafferTest.CapturingSlot( s.undoAddedSignal() )

		s["n"] = Gaffer.Node()
		self.assertEqual( cs, [] )

		with Gaffer.UndoContext( s ) :
			s["n"]["p"] = Gaffer.IntPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic )
			s["n"]["p"].setValue( 100 )

		self.assertEqual( len( cs ), 1 )
		self.assertTrue( cs[0][0].isSame( s ) )

		with Gaffer.UndoContext( s, mergeGroup = "test" ) :
			s["n"]["p"].setValue( 200 )

		self.assertEqual( len( cs ), 2 )
		self.assertTrue( cs[1][0].isSame( s ) )

		with Gaffer.UndoContext( s, mergeGroup = "test" ) :
			s["n"]["p"].setValue( 300 )

		# undo was merged, so a new one wasn't added
		self.assertEqual( len( cs ), 2 )
		self.assertTrue( cs[1][0].isSame( s ) )

	def testCustomVariables( self ) :

		s = Gaffer.ScriptNode()

		p = s["variables"].addMember( "test", IECore.IntData( 10 ) )
		self.assertEqual( s.context().get( "test" ), 10 )
		p["value"].setValue( 20 )
		self.assertEqual( s.context().get( "test" ), 20 )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.load()

		self.assertEqual( s2["variables"][p.getName()]["value"].getValue(), 20 )
		self.assertEqual( s2.context().get( "test" ), 20 )

	def testFileNameVariables( self ) :

		s = Gaffer.ScriptNode()
		self.assertEqual( s.context().get( "script:name" ), "" )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		self.assertEqual( s.context().get( "script:name" ), "test" )

	def testReloadWithCustomVariables( self ) :

		s = Gaffer.ScriptNode()
		s["variables"].addMember( "test", IECore.IntData( 10 ) )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s["variables"][0]["value"].setValue( 100 )
		s.load()

		self.assertEqual( len( s["variables"] ), 1 )
		self.assertEqual( s["variables"][0]["value"].getValue(), 10 )

	def testLoadCustomVariablesWithDefaultValues( self ) :

		s = Gaffer.ScriptNode()

		p = s["variables"].addMember( "test", IECore.IntData( 10 ) )
		self.assertEqual( s.context().get( "test" ), 10 )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.load()

		self.assertEqual( s2["variables"][p.getName()]["value"].getValue(), 10 )
		self.assertEqual( s2.context().get( "test" ), 10 )

	def testCurrentActionStage( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		actionStages = []
		def f( plug ) :

			actionStages.append( s.currentActionStage() )

			if s.currentActionStage() != Gaffer.Action.Stage.Invalid :
				self.assertFalse( s.undoAvailable() )
				self.assertFalse( s.redoAvailable() )

		c = s["n"].plugSetSignal().connect( f )

		self.assertEqual( s.currentActionStage(), Gaffer.Action.Stage.Invalid )
		self.assertEqual( len( actionStages ), 0 )

		s["n"]["op1"].setValue( 10 )

		self.assertEqual( len( actionStages ), 1 )
		self.assertEqual( actionStages[-1], Gaffer.Action.Stage.Invalid )

		with Gaffer.UndoContext( s ) :
			s["n"]["op1"].setValue( 11 )

		self.assertEqual( len( actionStages ), 2 )
		self.assertEqual( actionStages[-1], Gaffer.Action.Stage.Do )

		s.undo()

		self.assertEqual( len( actionStages ), 3 )
		self.assertEqual( actionStages[-1], Gaffer.Action.Stage.Undo )

		s.redo()

		self.assertEqual( len( actionStages ), 4 )
		self.assertEqual( actionStages[-1], Gaffer.Action.Stage.Redo )

		s.undo()

		self.assertEqual( len( actionStages ), 5 )
		self.assertEqual( actionStages[-1], Gaffer.Action.Stage.Undo )

		self.assertEqual( s.currentActionStage(), Gaffer.Action.Stage.Invalid )

	def testUndoListDoesntCreateReferenceCycles( self ) :

		s = Gaffer.ScriptNode()
		c = s.refCount()

		s["n"] = Gaffer.Node()
		s["n"]["p"] = Gaffer.IntPlug()

		with Gaffer.UndoContext( s ) :
			s.setName( "somethingElse" )
			self.assertEqual( s.getName(), "somethingElse" )
		self.assertEqual( s.refCount(), c )

		with Gaffer.UndoContext( s ) :
			s["n"].setName( "n2" )
			self.assertEqual( s["n2"].getName(), "n2" )
		self.assertEqual( s.refCount(), c )

		with Gaffer.UndoContext( s ) :
			Gaffer.Metadata.registerValue( s, "test", 10 )
			Gaffer.Metadata.registerValue( s["n2"], "test", 10 )
			Gaffer.Metadata.registerValue( s["n2"]["p"], "test", 10 )
		self.assertEqual( s.refCount(), c )

		with Gaffer.UndoContext( s ) :
			s["n3"] = Gaffer.Node()
			n4 = Gaffer.Node( "n4" )
			s.addChild( n4 )
		self.assertEqual( s.refCount(), c )

		with Gaffer.UndoContext( s ) :
			s["n3"].addChild( s["n2"]["p"] )
		self.assertEqual( s.refCount(), c )

		with Gaffer.UndoContext( s ) :
			s.addChild( s["n3"]["p"] )
		self.assertEqual( s.refCount(), c )

		with Gaffer.UndoContext( s ) :
			s["n3"].addChild( s["p"] )
		self.assertEqual( s.refCount(), c )

		with Gaffer.UndoContext( s ) :
			s.removeChild( s["n2"] )
		self.assertEqual( s.refCount(), c )

	def testErrorTolerantExecution( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferTest.AddNode()

		with IECore.CapturingMessageHandler() as c :
			s.execute( 'parent["n"]["op1"].setValue( 101 )\niWillFail(); parent["n"]["op2"].setValue( 102 )', continueOnError=True )

		self.assertEqual( s["n"]["op1"].getValue(), 101 )
		self.assertEqual( s["n"]["op2"].getValue(), 102 )

		self.assertEqual( len( c.messages ), 1 )
		self.assertEqual( c.messages[0].level, IECore.Msg.Level.Error )
		self.assertTrue( "Line 2" in c.messages[0].context )
		self.assertTrue( "name 'iWillFail' is not defined" in c.messages[0].message )

	def testExecuteReturnValue( self ) :

		s = Gaffer.ScriptNode()

		self.assertEqual( s.execute( "a = 10" ), False )
		self.assertEqual( s.execute( "a = 10", continueOnError=True ), False )

		with IECore.CapturingMessageHandler() : # suppress error reporting, to avoid confusing test output
			self.assertEqual( s.execute( "a = iDontExist", continueOnError=True ), True )

	def testExecuteExceptionsIncludeLineNumber( self ) :

		s = Gaffer.ScriptNode()
		self.assertRaisesRegexp( RuntimeError, "Line 2 .* name 'iDontExist' is not defined", s.execute, "a = 10\na=iDontExist" )

	def testFileVersioning( self ) :

		s = Gaffer.ScriptNode()

		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:milestoneVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:majorVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:minorVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:patchVersion" ), None )

		s.serialiseToFile( self.temporaryDirectory() + "/test.gfr" )

		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:milestoneVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:majorVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:minorVersion" ), None )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:patchVersion" ), None )

		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.load()

		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:milestoneVersion" ), Gaffer.About.milestoneVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:majorVersion" ), Gaffer.About.majorVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:minorVersion" ), Gaffer.About.minorVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:patchVersion" ), Gaffer.About.patchVersion() )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s2.load()

		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:milestoneVersion" ), Gaffer.About.milestoneVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:majorVersion" ), Gaffer.About.majorVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:minorVersion" ), Gaffer.About.minorVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:patchVersion" ), Gaffer.About.patchVersion() )

	def testFileVersioningUpdatesOnSave( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( os.path.dirname( __file__ ) + "/scripts/previousSerialisationVersion.gfr" )
		s.load()

		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:milestoneVersion" ), 0 )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:majorVersion" ), 14 )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:minorVersion" ), 0 )
		self.assertEqual( Gaffer.Metadata.value( s, "serialiser:patchVersion" ), 0 )

		s["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s.save()

		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( self.temporaryDirectory() + "/test.gfr" )
		s2.load()

		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:milestoneVersion" ), Gaffer.About.milestoneVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:majorVersion" ), Gaffer.About.majorVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:minorVersion" ), Gaffer.About.minorVersion() )
		self.assertEqual( Gaffer.Metadata.value( s2, "serialiser:patchVersion" ), Gaffer.About.patchVersion() )

	def testFramesPerSecond( self ) :

		s = Gaffer.ScriptNode()
		self.assertEqual( s["framesPerSecond"].getValue(), 24.0 )
		self.assertEqual( s.context().getFramesPerSecond(), 24.0 )

		s["framesPerSecond"].setValue( 48.0 )
		self.assertEqual( s.context().getFramesPerSecond(), 48.0 )

		s2 = Gaffer.ScriptNode()
		s2.execute( s.serialise() )
		self.assertEqual( s2["framesPerSecond"].getValue(), 48.0 )
		self.assertEqual( s2.context().getFramesPerSecond(), 48.0 )

	def testLineNumberForExecutionSyntaxError( self ) :

		s = Gaffer.ScriptNode()
		self.assertRaisesRegexp(
			Exception,
			"^Exception : Line 2",
			s.execute,
			inspect.cleandoc(
				"""
				a = 10
				i am a syntax error
				b = 20
				"""
			)
		)

	def testFileNameInExecutionError( self ) :

		fileName = self.temporaryDirectory() + "/test.gfr"
		with open( fileName, "w" ) as f :
			f.write( "a = 10\n" )
			f.write( "a = iDontExist\n" )

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( fileName )

		for method in ( s.load, functools.partial( s.executeFile, fileName ) ) :

			self.assertRaisesRegexp(
				RuntimeError,
				"Line 2 of " + fileName + " : NameError: name 'iDontExist' is not defined",
				method
			)

			with IECore.CapturingMessageHandler() as mh :
				method( continueOnError = True )

			self.assertEqual( len( mh.messages ), 1 )
			self.assertEqual( mh.messages[0].context, "Line 2 of " + fileName )
			self.assertTrue( "NameError: name 'iDontExist' is not defined" in mh.messages[0].message )

if __name__ == "__main__":
	unittest.main()
