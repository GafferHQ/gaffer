##########################################################################
#  
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
#  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest

class ScriptNodeTest( unittest.TestCase ) :

	def setUp( self ) :
	
		ScriptNodeTest.lastNode = None
		ScriptNodeTest.lastScript = None
		ScriptNodeTest.lastResult = None

	def test( self ) :
	
		s = Gaffer.ScriptNode()
		self.assertEqual( s.getName(), "ScriptNode" )
		
		self.assertEqual( s["fileName"].typeName(), "StringPlug" )
		
	def testExecution( self ) :
	
		s = Gaffer.ScriptNode()
				
		def f( n, s ) :
			ScriptNodeTest.lastNode = n
			ScriptNodeTest.lastScript = s
			
		c = s.scriptExecutedSignal().connect( f )

		s.execute( "addChild( Gaffer.Node( 'child' ) )" )
		self.assertEqual( ScriptNodeTest.lastNode, s )
		self.assertEqual( ScriptNodeTest.lastScript, "addChild( Gaffer.Node( 'child' ) )" )
				
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
		self.assertEqual( p.typeName(), "IntPlug" )
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
		
		s["a1"] = GafferTest.AddNode( inputs = { "op1" : 5, "op2" : 6 } )
		s["a2"] = GafferTest.AddNode( inputs = { "op1" : s["a1"]["sum"], "op2" : 10 } )
		
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
		s1["n1"]["dynamicStringPlug"] = Gaffer.StringPlug( flags = Gaffer.Plug.Flags.Default | Gaffer.Plug.Flags.Dynamic, value="hiThere" )
				
		s2 = Gaffer.ScriptNode()
		s2.execute( s1.serialise() )
		
		self.assert_( s2["n1"]["dynamicPlug"].getInput().isSame( s2["n2"]["sum"] ) )
		self.assertEqual( s2["n1"]["dynamicPlug2"].getValue(), 100 )
		self.assertEqual( s2["n1"]["dynamicStringPlug"].getValue(), "hiThere" )
		
	def testLifetime( self ) :
	
		s = Gaffer.ScriptNode()
		w = weakref.ref( s )
		del s
		IECore.RefCounted.collectGarbage()
	
		self.assertEqual( w(), None )
	
	def testSaveAndLoad( self ) :
	
		s = Gaffer.ScriptNode()
		
		s["a1"] = GafferTest.AddNode( inputs = { "op1" : 5, "op2" : 6 } )
		s["a2"] = GafferTest.AddNode( inputs = { "op1" : s["a1"]["sum"], "op2" : 10 } )
		
		s["fileName"].setValue( "/tmp/test.gfr" )
		s.save()
		
		s2 = Gaffer.ScriptNode()
		s2["fileName"].setValue( "/tmp/test.gfr" )
		s2.load()
		
		self.assert_( s2["a2"]["op1"].getInput().isSame( s2["a1"]["sum"] ) )

	def testSaveFailureHandling( self ) :
	
		s = Gaffer.ScriptNode()
		s["a1"] = GafferTest.AddNode( inputs = { "op1" : 5, "op2" : 6 } )

		s["fileName"].setValue( "/this/directory/doesnt/exist" )
		self.assertRaises( Exception, s.save )
		
	def testLoadFailureHandling( self ) :
	
		s = Gaffer.ScriptNode()
		s["a1"] = GafferTest.AddNode( inputs = { "op1" : 5, "op2" : 6 } )

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
		
		self.assertEqual( s2["in"].typeName(), "Node" )
	
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
				
		n = MyScriptNode( "s" )
		
		c1 = GafferTest.AddNode()
		c2 = Gaffer.Node()
		
		n.addChild( c1 )
		self.failUnless( c1.parent() is n )
	
		self.assertRaises( RuntimeError, n.addChild, c2 )
		self.failUnless( c2.parent() is None )
	
	def testExecutionExceptions( self ) :
	
		n = Gaffer.ScriptNode()
		
		self.assertRaises( ValueError, n.execute, "raise ValueError" )

		self.assertRaises( KeyError, n.evaluate, "{}['a']" )
		
	def testVariableScope( self ) :
	
		# if a variable gets made in one execution, then it should be available in the next
	
		n = Gaffer.ScriptNode()
		
		n.execute( "a = 10" )
		
		self.assertEqual( n.evaluate( "a" ), 10 )
	
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
	
	def testApplicationRoot( self ) :
	
		s = Gaffer.ScriptNode()
		self.failUnless( s.applicationRoot() is None )
	
		a = Gaffer.ApplicationRoot()
		a["scripts"]["one"] = s
		
		self.failUnless( s.applicationRoot().isSame( a ) )
			
	def testLifeTimeAfterExecution( self ) :
	
		a = Gaffer.ApplicationRoot()
		a["scripts"]["s"] = Gaffer.ScriptNode()
		
		# because the script editor allows execution of arbitrary code,
		# there's nothing stopping a user from making variables that refer
		# to the ScriptNode itself, causing circular references.
		a["scripts"]["s"].execute( "addChild( Gaffer.Node( \"a\" ) )" )
		a["scripts"]["s"].execute( "circularRef = getChild( \"a\" ).parent()" )
		
		w = weakref.ref( a["scripts"]["s"] )
		
		# we use the removal of the script from its parent to trigger a cleanup
		# of the execution context, allowing the ScriptNode to die. it's still
		# possible to create circular references that never die if the ScriptNode
		# never has a parent, but that is unlikely to be the case in the real world.
		## \todo Should it instead be the ScriptEditor that owns the execution
		# context perhaps? Then this wouldn't be an issue.
		del a["scripts"]["s"]
		IECore.RefCounted.collectGarbage()
	
		self.assertEqual( w(), None )
	
if __name__ == "__main__":
	unittest.main()
	
