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

import gc
import weakref
import unittest
import threading
import six

import IECore

import Gaffer
import GafferTest

class GraphComponentTest( GafferTest.TestCase ) :

	def testName( self ) :

		c = Gaffer.GraphComponent()
		self.assertEqual( c.getName(), "GraphComponent" )
		self.assertEqual( c.fullName(), "GraphComponent" )

		def f( c ) :
			GraphComponentTest.name = c.getName()

		con = c.nameChangedSignal().connect( f )
		GraphComponentTest.name = "xxx"
		c.setName( "newName" )
		self.assertEqual( GraphComponentTest.name, "newName" )
		# slot shouldn't be called this time, as the name
		# doesn't change (it's the same value)
		c.setName( "newName" )
		self.assertEqual( self.name, "newName" )

		self.assertEqual( c.getName(), "newName" )

		child1 = Gaffer.GraphComponent()
		child2 = Gaffer.GraphComponent()
		self.assertEqual( child1.getName(), "GraphComponent" )
		self.assertEqual( child2.getName(), "GraphComponent" )
		self.assertEqual( child1.fullName(), "GraphComponent" )
		self.assertEqual( child2.fullName(), "GraphComponent" )

		c.addChild( child1 )
		self.assertEqual( child1.getName(), "GraphComponent" )
		self.assertEqual( child1.fullName(), "newName.GraphComponent" )

		con = child2.nameChangedSignal().connect( f )
		GraphComponentTest.name = "xxx"
		c.addChild( child2 )
		self.assertEqual( child2.getName(), "GraphComponent1" )
		self.assertEqual( child2.fullName(), "newName.GraphComponent1" )
		self.assertEqual( child2.relativeName( None ), "newName.GraphComponent1" )
		self.assertEqual( child2.relativeName( c ), "GraphComponent1" )
		self.assertEqual( GraphComponentTest.name, "GraphComponent1" )

	def testParenting( self ) :

		parent1 = Gaffer.GraphComponent()
		self.assertIsNone( parent1.parent() )
		self.assertEqual( len( parent1.children() ), 0 )
		child1 = Gaffer.GraphComponent()
		self.assertIsNone( child1.parent() )
		self.assertEqual( len( child1.children() ), 0 )

		parent1.addChild( child1 )
		self.assertIsNone( parent1.parent() )
		self.assertTrue( parent1.getChild( "GraphComponent" ).isSame( child1 ) )
		self.assertTrue( parent1["GraphComponent"].isSame( child1 ) )
		self.assertTrue( child1.parent().isSame( parent1 ) )

		parent1.removeChild( child1 )
		self.assertEqual( parent1.children(), () )
		self.assertEqual( child1.parent(), None )

		self.assertRaises( RuntimeError, parent1.removeChild, child1 )

	def testParentingSignals( self ) :

		parent = Gaffer.GraphComponent()
		child = Gaffer.GraphComponent()

		def f( c, oldParent ) :

			GraphComponentTest.newParent = c.parent()
			GraphComponentTest.oldParent = oldParent

		def ff( p, c ) :

			GraphComponentTest.parenting = ( p, c )

		c1 = child.parentChangedSignal().connect( f )
		c2 = parent.childAddedSignal().connect( ff )

		GraphComponentTest.newParent = None
		GraphComponentTest.oldParent = None
		GraphComponentTest.parenting = None
		parent.addChild( child )
		self.assertTrue( GraphComponentTest.newParent.isSame( parent ) )
		self.assertIsNone( GraphComponentTest.oldParent )
		self.assertTrue( GraphComponentTest.parenting[0].isSame( parent ) )
		self.assertTrue( GraphComponentTest.parenting[1].isSame( child ) )

		GraphComponentTest.newParent = "xxx"
		GraphComponentTest.oldParent = None
		GraphComponentTest.parenting = None
		c2 = parent.childRemovedSignal().connect( ff )
		parent.removeChild( child )
		self.assertIsNone( GraphComponentTest.newParent )
		self.assertTrue( GraphComponentTest.oldParent.isSame( parent ) )
		self.assertTrue( GraphComponentTest.parenting[0].isSame( parent ) )
		self.assertTrue( GraphComponentTest.parenting[1].isSame( child ) )

	def testReparentingEmitsOnlyOneParentChangedSignal( self ) :

		p1 = Gaffer.GraphComponent()
		p2 = Gaffer.GraphComponent()

		c = Gaffer.GraphComponent()

		def f( child, previousParent ) :

			GraphComponentTest.newParent = child.parent()
			GraphComponentTest.oldParent = previousParent
			GraphComponentTest.child = child
			GraphComponentTest.numSignals += 1

		GraphComponentTest.newParent = None
		GraphComponentTest.oldParent = None
		GraphComponentTest.child = None
		GraphComponentTest.numSignals = 0

		p1["c"] = c

		connection = c.parentChangedSignal().connect( f )

		p2["c"] = c

		self.assertTrue( GraphComponentTest.newParent.isSame( p2 ) )
		self.assertTrue( GraphComponentTest.oldParent.isSame( p1 ) )
		self.assertTrue( GraphComponentTest.child.isSame( c ) )
		self.assertEqual( GraphComponentTest.numSignals, 1 )

	def testParentChangedBecauseParentDied( self ) :

		parent = Gaffer.GraphComponent()
		child = Gaffer.GraphComponent()
		parent["child"] = child

		def f( child, previousParent ) :

			GraphComponentTest.newParent = child.parent()
			GraphComponentTest.previousParent = previousParent

		c = child.parentChangedSignal().connect( f )

		GraphComponentTest.newParent = "XXX"
		GraphComponentTest.previousParent = "XXX"

		w = weakref.ref( parent )
		del parent
		while gc.collect() :
			pass
		IECore.RefCounted.collectGarbage()

		self.assertEqual( w(), None )

		self.assertIsNone( GraphComponentTest.newParent )
		self.assertIsNone( GraphComponentTest.previousParent )

	def testReparentingDoesntSignal( self ) :

		"""Adding a child to a parent who already owns that child should do nothing."""

		parent = Gaffer.GraphComponent()
		child = Gaffer.GraphComponent()

		parent.addChild( child )
		self.assertTrue( child.parent().isSame( parent ) )

		GraphComponentTest.numSignals = 0
		def f( a, b=None ) :
			GraphComponentTest.numSignals += 1

		c1 = child.parentChangedSignal().connect( f )
		c2 = parent.childAddedSignal().connect( f )

		parent.addChild( child )

		self.assertEqual( GraphComponentTest.numSignals, 0 )

	def testMany( self ) :

		l = []
		for i in range( 0, 100000 ) :
			l.append( Gaffer.GraphComponent() )

	def testDictionarySemantics( self ) :

		# check setitem and getitem
		p = Gaffer.GraphComponent()
		c = Gaffer.GraphComponent()
		p["c"] = c
		self.assertTrue( p.getChild( "c" ).isSame( c ) )
		self.assertTrue( p["c"].isSame( c ) )
		self.assertRaises( KeyError, p.__getitem__, "notAChild" )

		# check that setitem removes items with clashing names
		c2 = Gaffer.GraphComponent()
		p["c"] = c2
		self.assertTrue( p.getChild( "c" ).isSame( c2 ) )
		self.assertTrue( c2.parent().isSame( p ) )
		self.assertIsNone( c.parent() )

		# check delitem
		c3 = Gaffer.GraphComponent()
		p["c3"] = c3
		self.assertTrue( p.getChild( "c3" ).isSame( c3 ) )
		self.assertTrue( p["c3"].isSame( c3 ) )
		self.assertIn( "c3", p )

		del p["c3"]

		self.assertNotIn( "c3", p )

		self.assertRaises( KeyError, p.__delitem__, "xxxx" )

	def testUniqueNaming( self ) :

		p = Gaffer.GraphComponent()
		c1 = Gaffer.GraphComponent()
		c2 = Gaffer.GraphComponent()
		c3 = Gaffer.GraphComponent()

		c1.setName( "a" )
		c2.setName( "a" )
		c3.setName( "a" )

		p.addChild( c1 )
		self.assertEqual( c1.getName(), "a" )

		p.addChild( c2 )
		self.assertEqual( c2.getName(), "a1" )

		p.addChild( c3 )
		self.assertEqual( c3.getName(), "a2" )

		c4 = Gaffer.GraphComponent( "a1" )
		p.addChild( c4 )
		self.assertEqual( c4.getName(), "a3" )

		c1.setName( "b" )
		c2.setName( "b" )
		c3.setName( "b" )
		c4.setName( "b" )

		self.assertEqual( c1.getName(), "b" )
		self.assertEqual( c2.getName(), "b1" )
		self.assertEqual( c3.getName(), "b2" )
		self.assertEqual( c4.getName(), "b3" )

	def testParallelUniqueNaming( self ):
		# At one point setName was using a non-threadsafe static formatter which would throw
		# exceptions when used from multiple threads

		def f( q ) :
			try:
				g = Gaffer.GraphComponent()
				for i in range( 500 ):
					g.addChild( Gaffer.GraphComponent( "a" ) )

				self.assertEqual( set(g.keys()), set( [ "a" ] + [ "a%i" % i for i in range( 1, 500 ) ] ) )
			except Exception as e:
				q.put( e )

		threads = []
		q = six.moves.queue.Queue()
		for i in range( 0, 500 ) :

			t = threading.Thread( target = f, args = (q,) )
			t.start()
			threads.append( t )

		for t in threads :
			t.join()

		if not q.empty():
			raise q.get( False )

	def testAncestor( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["one"] = s

		n = GafferTest.AddNode()
		s["node"] = n

		self.assertTrue( n.ancestor( Gaffer.ScriptNode ).isSame( s ) )
		self.assertTrue( n.ancestor( Gaffer.ApplicationRoot ).isSame( a ) )

	def testCommonAncestor( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["one"] = s

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		self.assertTrue( s["n1"].commonAncestor( s["n2"], Gaffer.ScriptNode ).isSame( s ) )
		self.assertTrue( s["n2"].commonAncestor( s["n1"], Gaffer.ScriptNode ).isSame( s ) )

	def testCommonAncestorType( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = Gaffer.Node()
		s["n"]["user"]["p1"] = Gaffer.IntPlug()
		s["n"]["user"]["p2"] = Gaffer.Color3fPlug()

		self.assertEqual( s["n"]["user"]["p1"].commonAncestor( s["n"]["user"]["p2"]["r"] ), s["n"]["user"] )
		self.assertEqual( s["n"]["user"]["p1"].commonAncestor( s["n"]["user"]["p2"]["r"], Gaffer.Plug ), s["n"]["user"] )
		self.assertEqual( s["n"]["user"]["p1"].commonAncestor( s["n"]["user"]["p2"]["r"], Gaffer.Node ), s["n"] )

	def testRenameThenRemove( self ) :

		p = Gaffer.GraphComponent()
		c = Gaffer.GraphComponent()

		p.addChild( c )
		c.setName( "c" )
		p.removeChild( c )

	def testDescendant( self ) :

		p1 = Gaffer.GraphComponent()
		p2 = Gaffer.GraphComponent()
		p3 = Gaffer.GraphComponent()

		p1["p2"] = p2
		p2["p3"] = p3

		self.assertTrue( p1.descendant( "p2" ).isSame( p2 ) )
		self.assertTrue( p1.descendant( "p2.p3" ).isSame( p3 ) )

	def testNameConstraints( self ) :

		n = Gaffer.GraphComponent()

		for name in ( "0", "0a", "@A", "a.A", ".", "A:", "a|", "a(" ) :
			self.assertRaises( Exception, n.setName, name )
			self.assertRaises( Exception, Gaffer.GraphComponent, name )

		for name in ( "hello", "_1", "brdf_0_degree_refl" ) :
			n.setName( name )

	def testContains( self ) :

		n = Gaffer.GraphComponent()
		self.assertNotIn( "c", n )
		n["c"] = Gaffer.GraphComponent()
		self.assertIn( "c", n )

	def testIsAncestorOf( self ) :

		n = Gaffer.GraphComponent()
		n["c"] = Gaffer.GraphComponent()
		n["c"]["c"] = Gaffer.GraphComponent()
		n2 = Gaffer.GraphComponent()

		self.assertTrue( n.isAncestorOf( n["c"]["c"] ) )
		self.assertTrue( n.isAncestorOf( n["c"] ) )
		self.assertFalse( n.isAncestorOf( n ) )
		self.assertFalse( n2.isAncestorOf( n ) )
		self.assertFalse( n.isAncestorOf( n2 ) )

	def testDerivingInPython( self ) :

		class TestGraphComponent( Gaffer.GraphComponent ) :

			def __init__( self, name = "TestGraphComponent" ) :

				Gaffer.GraphComponent.__init__( self, name )

				self.acceptsChildCalled = False
				self.acceptsParentCalled = False

			def acceptsChild( self, potentialChild ) :

				self.acceptsChildCalled = True

				return isinstance( potentialChild, TestGraphComponent )

			def acceptsParent( self, potentialParent ) :

				self.acceptsParentCalled = True
				return isinstance( potentialParent, TestGraphComponent )

		IECore.registerRunTimeTyped( TestGraphComponent )

		# check names in constructors

		g1 = TestGraphComponent()
		self.assertEqual( g1.getName(), "TestGraphComponent" )

		g2 = TestGraphComponent( "g" )
		self.assertEqual( g2.getName(), "g" )

		# check calling virtual overrides directly

		self.assertEqual( g1.acceptsChildCalled, False )
		self.assertEqual( g1.acceptsParentCalled, False )
		self.assertEqual( g2.acceptsChildCalled, False )
		self.assertEqual( g2.acceptsParentCalled, False )

		self.assertTrue( g1.acceptsChild( g2 ) )
		self.assertTrue( g1.acceptsParent( g2 ) )
		self.assertFalse( g1.acceptsChild( Gaffer.Node() ) )
		self.assertFalse( g1.acceptsParent( Gaffer.Node() ) )

		self.assertEqual( g1.acceptsChildCalled, True )
		self.assertEqual( g1.acceptsParentCalled, True )
		self.assertEqual( g2.acceptsChildCalled, False )
		self.assertEqual( g2.acceptsParentCalled, False )

		# check calling virtual overrides indirectly through C++

		g1 = TestGraphComponent()
		g2 = TestGraphComponent( "g" )
		self.assertEqual( g1.acceptsChildCalled, False )
		self.assertEqual( g1.acceptsParentCalled, False )

		self.assertRaises( RuntimeError, g1.addChild, Gaffer.Node() )
		self.assertEqual( g1.acceptsChildCalled, True )
		self.assertEqual( g1.acceptsParentCalled, False )

		self.assertRaises( RuntimeError, Gaffer.GraphComponent().addChild, g1 )
		self.assertEqual( g1.acceptsChildCalled, True )
		self.assertEqual( g1.acceptsParentCalled, True )

	def testLen( self ) :

		g = Gaffer.GraphComponent()
		self.assertEqual( len( g ), 0 )

		g["a"] = Gaffer.GraphComponent()
		self.assertEqual( len( g ), 1 )

		g["b"] = Gaffer.GraphComponent()
		self.assertEqual( len( g ), 2 )

		del g["a"]
		self.assertEqual( len( g ), 1 )

	def testSetChild( self ) :

		p1 = Gaffer.GraphComponent()
		p2 = Gaffer.GraphComponent()

		c1 = Gaffer.GraphComponent()
		c2 = Gaffer.GraphComponent()

		self.assertEqual( len( p1 ), 0 )
		self.assertEqual( len( p2 ), 0 )

		self.assertEqual( c1.parent(), None )
		self.assertEqual( c2.parent(), None )

		p1.setChild( "a", c1 )
		self.assertEqual( c1.getName(), "a" )
		self.assertEqual( c1.parent(), p1 )
		self.assertEqual( len( p1 ), 1 )

		p1.setChild( "a", c2 )
		self.assertEqual( c1.getName(), "a" )
		self.assertEqual( c2.getName(), "a" )
		self.assertEqual( c1.parent(), None )
		self.assertEqual( c2.parent(), p1 )
		self.assertEqual( len( p1 ), 1 )

		p2.setChild( "b", c2 )
		self.assertEqual( c2.getName(), "b" )
		self.assertEqual( c2.parent(), p2 )
		self.assertEqual( len( p1 ), 0 )
		self.assertEqual( len( p2 ), 1 )

	def testSetChildAgain( self ) :

		# Setting a child to the same thing should
		# cause nothing to happen and no signals to
		# be triggered.

		parent = Gaffer.GraphComponent()
		child = Gaffer.GraphComponent()

		parent.setChild( "c", child )
		self.assertTrue( child.parent().isSame( parent ) )

		GraphComponentTest.numSignals = 0
		def f( *args ) :
			GraphComponentTest.numSignals += 1

		c1 = child.parentChangedSignal().connect( f )
		c2 = parent.childAddedSignal().connect( f )
		c3 = parent.childRemovedSignal().connect( f )
		c4 = child.nameChangedSignal().connect( f )

		parent.setChild( "c", child )

		self.assertEqual( GraphComponentTest.numSignals, 0 )

	def testEmptyName( self ) :

		g = Gaffer.GraphComponent()
		self.assertRaises( RuntimeError, g.setName, "" )

	def testGetChildWithEmptyName( self ) :

		g = Gaffer.GraphComponent()
		self.assertEqual( g.getChild( "" ), None )
		self.assertRaises( KeyError, g.__getitem__, "" )

	def testKeysAndValuesAndItems( self ) :

		g = Gaffer.GraphComponent()
		self.assertEqual( g.keys(), [] )
		self.assertEqual( g.values(), [] )

		g["a"] = Gaffer.GraphComponent()
		g["b"] = Gaffer.GraphComponent()
		g["c"] = Gaffer.GraphComponent()

		self.assertEqual( g.keys(), [ "a", "b", "c" ] )
		self.assertEqual( len( g.values() ), 3 )
		self.assertEqual( g.values()[0].getName(), "a" )
		self.assertEqual( g.values()[1].getName(), "b" )
		self.assertEqual( g.values()[2].getName(), "c" )

		items = g.items()
		self.assertEqual( len( items ), 3 )
		self.assertEqual( items[0][0], "a" )
		self.assertEqual( items[1][0], "b" )
		self.assertEqual( items[2][0], "c" )
		self.assertEqual( items[0][1].getName(), "a" )
		self.assertEqual( items[1][1].getName(), "b" )
		self.assertEqual( items[2][1].getName(), "c" )

	def testIndexByIndex( self ) :

		g = Gaffer.GraphComponent()

		g["a"] = Gaffer.GraphComponent()
		g["b"] = Gaffer.GraphComponent()
		g["c"] = Gaffer.GraphComponent()

		self.assertEqual( len( g ), 3 )

		self.assertRaises( IndexError, g.__getitem__, 3 )
		self.assertRaises( IndexError, g.__getitem__, -4 )

		self.assertEqual( g[0].getName(), "a" )
		self.assertEqual( g[1].getName(), "b" )
		self.assertEqual( g[2].getName(), "c" )
		self.assertEqual( g[-1].getName(), "c" )
		self.assertEqual( g[-2].getName(), "b" )
		self.assertEqual( g[-3].getName(), "a" )

	def testChildrenByType( self ) :

		g = Gaffer.Node()
		g["a"] = Gaffer.IntPlug()
		g["b"] = Gaffer.Plug()
		g["c"] = Gaffer.Node()

		self.assertEqual( len( g.children() ), 4 )
		self.assertEqual( len( g.children( Gaffer.GraphComponent ) ), 4 )
		self.assertEqual( len( g.children( Gaffer.Plug ) ), 3 )
		self.assertEqual( len( g.children( Gaffer.Node ) ), 1 )
		self.assertEqual( len( g.children( Gaffer.IntPlug ) ), 1 )

	def testRemoveMany( self ) :

		g = Gaffer.GraphComponent()
		l = []
		for i in range( 0, 10000 ) :
			c = Gaffer.GraphComponent()
			l.append( c )
			g["c%d"%i] = c

		for c in l :
			g.removeChild( c )

	def testManyChildrenWithSameInitialName( self ) :

		g = Gaffer.GraphComponent()
		for i in range( 0, 2000 ) :
			g.addChild( Gaffer.GraphComponent() )

		for index, child in enumerate( g ) :
			if index == 0 :
				self.assertEqual( child.getName(), "GraphComponent" )
			else :
				self.assertEqual( child.getName(), "GraphComponent%d" % index )

	def testNamesWithStrangeSuffixes( self ) :

		g = Gaffer.GraphComponent()
		g.addChild( Gaffer.GraphComponent( "a" ) )
		g.addChild( Gaffer.GraphComponent( "a1somethingElse" ) )
		self.assertEqual( g[0].getName(), "a" )
		self.assertEqual( g[1].getName(), "a1somethingElse" )

		g.addChild( Gaffer.GraphComponent( "a" ) )
		self.assertEqual( g[2].getName(), "a1" )

	def testAddChildWithExistingNumericSuffix( self ) :

		g = Gaffer.GraphComponent()
		g.addChild( Gaffer.GraphComponent( "a1" ) )
		g.addChild( Gaffer.GraphComponent( "a1" ) )

		self.assertEqual( g[0].getName(), "a1" )
		self.assertEqual( g[1].getName(), "a2" )

	def testSetChildDoesntRemoveChildIfNewChildIsntAccepted( self ) :

		class AddNodeAcceptor( Gaffer.Node ) :

			def __init__( self, name = "AddNodeAcceptor" ) :

				Gaffer.Node.__init__( self, name )

			def acceptsChild( self, potentialChild ) :

				return isinstance( potentialChild, GafferTest.AddNode )

		IECore.registerRunTimeTyped( AddNodeAcceptor )

		g = AddNodeAcceptor()
		a = GafferTest.AddNode()
		g["a"] = a

		self.assertRaises( RuntimeError, g.setChild, "a", GafferTest.MultiplyNode() )

		self.assertTrue( g["a"].isSame( a ) )

	def testCircularParentingThrows( self ) :

		a = Gaffer.GraphComponent()
		b = Gaffer.GraphComponent()

		a["b"] = b
		self.assertRaises( RuntimeError, b.addChild, a )

		a = Gaffer.GraphComponent()
		b = Gaffer.GraphComponent()
		c = Gaffer.GraphComponent()

		a["b"] = b
		b["c"] = c

		self.assertRaises( RuntimeError, c.addChild, a )

		a = Gaffer.GraphComponent()
		self.assertRaises( RuntimeError, a.addChild, a )

	def testTypeNamePrefixes( self ) :

		self.assertTypeNamesArePrefixed(
			Gaffer,
			# Ignore the names imported from GafferCortex and
			# GafferDispatch into the Gaffer namespace - they're
			# just for backwards compatibility.
			namesToIgnore = set( [
				"GafferCortex::ObjectReader",
				"GafferCortex::ObjectWriter",
				"GafferCortex::ExecutableOpHolder",
				"GafferCortex::OpHolder",
				"GafferCortex::ParameterisedHolderNode",
				"GafferCortex::ParameterisedHolderDependencyNode",
				"GafferCortex::ParameterisedHolderComputeNode",
				"GafferCortex::ParameterisedHolderTaskNode",
				"GafferCortex::AttributeCachePath",
				"GafferCortex::ClassLoaderPath",
				"GafferCortex::IndexedIOPath",
				"GafferCortex::ParameterPath",
				"GafferDispatch::Dispatcher",
				"GafferDispatch::LocalDispatcher",
				"GafferDispatch::TaskNode",
				"GafferDispatch::PythonCommand",
				"GafferDispatch::SystemCommand",
				"GafferDispatch::TaskContextProcessor",
				"GafferDispatch::TaskContextVariables",
				"GafferDispatch::TaskList",
				"GafferDispatch::TaskSwitch",
				"GafferDispatch::Wedge",
				"GafferDispatch::FrameMask",
			] )
		)
		self.assertTypeNamesArePrefixed( GafferTest )

	def testDefaultNames( self ) :

		self.assertDefaultNamesAreCorrect( Gaffer )
		self.assertDefaultNamesAreCorrect( GafferTest )

	def testClearChildren( self ) :

		p = Gaffer.GraphComponent()

		for i in range( 0, 10 ) :
			p.addChild( Gaffer.GraphComponent() )

		self.assertEqual( len( p ), 10 )

		p.clearChildren()

		self.assertEqual( len( p ), 0 )

	def testParentChanging( self ) :

		class Child( Gaffer.GraphComponent ) :

			def __init__( self, name = "Child" ) :

				Gaffer.GraphComponent.__init__( self, name )

				self.parentChanges = []

			def _parentChanging( self, newParent ) :

				self.parentChanges.append( ( self.parent(), newParent ) )

		p1 = Gaffer.GraphComponent()
		p2 = Gaffer.GraphComponent()

		c = Child()
		self.assertEqual( len( c.parentChanges ), 0 )

		p1.addChild( c )
		self.assertEqual( len( c.parentChanges ), 1 )
		self.assertEqual( c.parentChanges[-1], ( None, p1 ) )

		p1.removeChild( c )
		self.assertEqual( len( c.parentChanges ), 2 )
		self.assertEqual( c.parentChanges[-1], ( p1, None ) )

		p1.addChild( c )
		self.assertEqual( len( c.parentChanges ), 3 )
		self.assertEqual( c.parentChanges[-1], ( None, p1 ) )

		p2.addChild( c )
		self.assertEqual( len( c.parentChanges ), 4 )
		self.assertEqual( c.parentChanges[-1], ( p1, p2 ) )

		# cause a parent change by destroying the parent.
		# we need to remove all references to the parent to do
		# this, including those stored in the parentChanges list.
		del p2
		del c.parentChanges[:]

		self.assertEqual( len( c.parentChanges ), 1 )
		self.assertEqual( c.parentChanges[-1], ( None, None ) )

	def testDescriptiveKeyErrors( self ) :

		g = Gaffer.GraphComponent()
		six.assertRaisesRegex( self, KeyError, "'a' is not a child of 'GraphComponent'", g.__getitem__, "a" )
		six.assertRaisesRegex( self, KeyError, "'a' is not a child of 'GraphComponent'", g.__delitem__, "a" )

	def testNoneIsNotAString( self ) :

		g = Gaffer.GraphComponent()
		self.assertRaises( TypeError, g.getChild, None )
		self.assertRaises( TypeError, g.__getitem__, None )
		self.assertRaises( TypeError, g.__delitem__, None )
		self.assertRaises( TypeError, g.descendant, None )
		self.assertRaises( TypeError, g.__contains__, None )
		self.assertRaises( TypeError, g.setName, None )

	def testDelItemByIndex( self ) :

		g = Gaffer.GraphComponent()
		a = Gaffer.GraphComponent( "a" )
		b = Gaffer.GraphComponent( "b" )
		g["a"] = a
		g["b"] = b
		self.assertEqual( a.parent(), g )
		self.assertEqual( b.parent(), g )

		del g[0]
		self.assertEqual( a.parent(), None )
		self.assertEqual( b.parent(), g )

	def testRemoveChildUndoIndices( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = Gaffer.Node()

		a = Gaffer.Plug( "a" )
		b = Gaffer.Plug( "b" )
		c = Gaffer.Plug( "c" )

		s["n"]["user"].addChild( a )
		s["n"]["user"].addChild( b )
		s["n"]["user"].addChild( c )

		def assertPreconditions() :

			self.assertEqual( len( s["n"]["user"] ), 3 )
			self.assertEqual( s["n"]["user"][0], a )
			self.assertEqual( s["n"]["user"][1], b )
			self.assertEqual( s["n"]["user"][2], c )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :

			del s["n"]["user"]["b"]

		def assertPostConditions() :

			self.assertEqual( len( s["n"]["user"] ), 2 )
			self.assertEqual( s["n"]["user"][0], a )
			self.assertEqual( s["n"]["user"][1], c )

		assertPostConditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostConditions()

		s.undo()
		assertPreconditions()

	def testMoveChildUndoIndices( self ) :

		s = Gaffer.ScriptNode()
		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		a = Gaffer.Plug( "a" )
		b = Gaffer.Plug( "b" )
		c = Gaffer.Plug( "c" )

		s["n1"]["user"].addChild( a )
		s["n1"]["user"].addChild( b )
		s["n1"]["user"].addChild( c )

		def assertPreconditions() :

			self.assertEqual( len( s["n1"]["user"] ), 3 )
			self.assertEqual( s["n1"]["user"][0], a )
			self.assertEqual( s["n1"]["user"][1], b )
			self.assertEqual( s["n1"]["user"][2], c )
			self.assertEqual( len( s["n2"]["user"] ), 0 )

		assertPreconditions()

		with Gaffer.UndoScope( s ) :

			s["n2"]["user"].addChild( s["n1"]["user"]["b"] )

		def assertPostConditions() :

			self.assertEqual( len( s["n1"]["user"] ), 2 )
			self.assertEqual( s["n1"]["user"][0], a )
			self.assertEqual( s["n1"]["user"][1], c )
			self.assertEqual( len( s["n2"]["user"] ), 1 )
			self.assertEqual( s["n2"]["user"][0], b )

		assertPostConditions()

		s.undo()
		assertPreconditions()

		s.redo()
		assertPostConditions()

		s.undo()
		assertPreconditions()

	def testParentChangedOverride( self ) :

		class Child( Gaffer.GraphComponent ) :

			def __init__( self, name = "Child" ) :

				Gaffer.GraphComponent.__init__( self, name )

				self.parentChanges = []

			def _parentChanged( self, oldParent ) :

				self.parentChanges.append( ( oldParent, self.parent() ) )

		p1 = Gaffer.GraphComponent()
		p2 = Gaffer.GraphComponent()

		c = Child()
		self.assertEqual( len( c.parentChanges ), 0 )

		p1.addChild( c )
		self.assertEqual( len( c.parentChanges ), 1 )
		self.assertEqual( c.parentChanges[-1], ( None, p1 ) )

		p1.removeChild( c )
		self.assertEqual( len( c.parentChanges ), 2 )
		self.assertEqual( c.parentChanges[-1], ( p1, None ) )

		p1.addChild( c )
		self.assertEqual( len( c.parentChanges ), 3 )
		self.assertEqual( c.parentChanges[-1], ( None, p1 ) )

		p2.addChild( c )
		self.assertEqual( len( c.parentChanges ), 4 )
		self.assertEqual( c.parentChanges[-1], ( p1, p2 ) )

		# Cause a parent change by destroying the parent.
		# We need to remove all references to the parent to do
		# this, including those stored in the parentChanges list.
		del p2
		del c.parentChanges[:]

		self.assertEqual( len( c.parentChanges ), 1 )
		self.assertEqual( c.parentChanges[-1], ( None, None ) )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testMakeNamesUnique( self ) :

		s = Gaffer.ScriptNode()

		for i in range( 0, 1000 ) :
			n = GafferTest.AddNode()
			s.addChild( n )

	@GafferTest.TestRunner.PerformanceTestMethod()
	def testGetChild( self ) :

		s = Gaffer.ScriptNode()

		for i in range( 0, 1000 ) :
			# explicitly setting the name to something unique
			# avoids the overhead incurred by the example
			# in testMakeNamesUnique
			n = GafferTest.AddNode( "AddNode" + str( i ) )
			s.addChild( n )

		for i in range( 0, 1000 ) :
			n = "AddNode" + str( i )
			c = s[n]
			self.assertEqual( c.getName(), n )

	def testNoneIsNotAGraphComponent( self ) :

		g = Gaffer.GraphComponent()

		with six.assertRaisesRegex( self, Exception, r"did not match C\+\+ signature" ) :
			g.addChild( None )

		with six.assertRaisesRegex( self, Exception, r"did not match C\+\+ signature" ) :
			g.setChild( "x", None )

		with six.assertRaisesRegex( self, Exception, r"did not match C\+\+ signature" ) :
			g.removeChild( None )

	def testRanges( self ) :

		g = Gaffer.GraphComponent()
		g["c1"] = Gaffer.GraphComponent()
		g["c2"] = Gaffer.GraphComponent()
		g["c2"]["gc1"] = Gaffer.GraphComponent()
		g["c3"] = Gaffer.GraphComponent()
		g["c3"]["gc2"] = Gaffer.GraphComponent()
		g["c3"]["gc3"] = Gaffer.GraphComponent()

		self.assertEqual(
			list( Gaffer.GraphComponent.Range( g ) ),
			[ g["c1"], g["c2"], g["c3"] ],
		)

		self.assertEqual(
			list( Gaffer.GraphComponent.RecursiveRange( g ) ),
			[ g["c1"], g["c2"], g["c2"]["gc1"], g["c3"], g["c3"]["gc2"], g["c3"]["gc3"] ],
		)

if __name__ == "__main__":
	unittest.main()
