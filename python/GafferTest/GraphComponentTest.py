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
		self.assert_( parent1.parent() is None )
		self.assertEqual( len( parent1.children() ), 0 )
		child1 = Gaffer.GraphComponent()
		self.assert_( child1.parent() is None )
		self.assertEqual( len( child1.children() ), 0 )

		parent1.addChild( child1 )
		self.assert_( parent1.parent() is None )
		self.assert_( parent1.getChild( "GraphComponent" ).isSame( child1 ) )
		self.assert_( parent1["GraphComponent"].isSame( child1 ) )
		self.assert_( child1.parent().isSame( parent1 ) )

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
		self.assert_( GraphComponentTest.newParent.isSame( parent ) )
		self.assert_( GraphComponentTest.oldParent is None )
		self.assert_( GraphComponentTest.parenting[0].isSame( parent ) )
		self.assert_( GraphComponentTest.parenting[1].isSame( child ) )

		GraphComponentTest.newParent = "xxx"
		GraphComponentTest.oldParent = None
		GraphComponentTest.parenting = None
		c2 = parent.childRemovedSignal().connect( ff )
		parent.removeChild( child )
		self.assert_( GraphComponentTest.newParent is None )
		self.assert_( GraphComponentTest.oldParent.isSame( parent ) )
		self.assert_( GraphComponentTest.parenting[0].isSame( parent ) )
		self.assert_( GraphComponentTest.parenting[1].isSame( child ) )

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

		self.failUnless( GraphComponentTest.newParent.isSame( p2 ) )
		self.failUnless( GraphComponentTest.oldParent.isSame( p1 ) )
		self.failUnless( GraphComponentTest.child.isSame( c ) )
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

		self.failUnless( GraphComponentTest.newParent is None )
		self.failUnless( GraphComponentTest.previousParent is None )

	def testReparentingDoesntSignal( self ) :

		"""Adding a child to a parent who already owns that child should do nothing."""

		parent = Gaffer.GraphComponent()
		child = Gaffer.GraphComponent()

		parent.addChild( child )
		self.assert_( child.parent().isSame( parent ) )

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
		self.assert_( p.getChild( "c" ).isSame( c ) )
		self.assert_( p["c"].isSame( c ) )
		self.assertRaises( KeyError, p.__getitem__, "notAChild" )

		# check that setitem removes items with clashing names
		c2 = Gaffer.GraphComponent()
		p["c"] = c2
		self.assert_( p.getChild( "c" ).isSame( c2 ) )
		self.assert_( c2.parent().isSame( p ) )
		self.assert_( c.parent() is None )

		# check delitem
		c3 = Gaffer.GraphComponent()
		p["c3"] = c3
		self.assert_( p.getChild( "c3" ).isSame( c3 ) )
		self.assert_( p["c3"].isSame( c3 ) )
		self.assert_( "c3" in p )

		del p["c3"]

		self.assert_( not "c3" in p )

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

	def testAncestor( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["one"] = s

		n = GafferTest.AddNode()
		s["node"] = n

		self.assert_( n.ancestor( Gaffer.ScriptNode ).isSame( s ) )
		self.assert_( n.ancestor( Gaffer.ApplicationRoot ).isSame( a ) )

	def testCommonAncestor( self ) :

		a = Gaffer.ApplicationRoot()
		s = Gaffer.ScriptNode()
		a["scripts"]["one"] = s

		s["n1"] = Gaffer.Node()
		s["n2"] = Gaffer.Node()

		self.assert_( s["n1"].commonAncestor( s["n2"], Gaffer.ScriptNode ).isSame( s ) )
		self.assert_( s["n2"].commonAncestor( s["n1"], Gaffer.ScriptNode ).isSame( s ) )

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

		self.failUnless( p1.descendant( "p2" ).isSame( p2 ) )
		self.failUnless( p1.descendant( "p2.p3" ).isSame( p3 ) )

	def testNameConstraints( self ) :

		n = Gaffer.GraphComponent()

		for name in ( "0", "0a", "@A", "a.A", ".", "A:", "a|", "a(" ) :
			self.assertRaises( Exception, n.setName, "0" )

		for name in ( "hello", "_1", "brdf_0_degree_refl" ) :
			n.setName( name )

	def testContains( self ) :

		n = Gaffer.GraphComponent()
		self.failIf( "c" in n )
		n["c"] = Gaffer.GraphComponent()
		self.failUnless( "c" in n )

	def testIsAncestorOf( self ) :

		n = Gaffer.GraphComponent()
		n["c"] = Gaffer.GraphComponent()
		n["c"]["c"] = Gaffer.GraphComponent()
		n2 = Gaffer.GraphComponent()

		self.failUnless( n.isAncestorOf( n["c"]["c"] ) )
		self.failUnless( n.isAncestorOf( n["c"] ) )
		self.failIf( n.isAncestorOf( n ) )
		self.failIf( n2.isAncestorOf( n ) )
		self.failIf( n.isAncestorOf( n2 ) )

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

		self.failUnless( g1.acceptsChild( g2 ) )
		self.failUnless( g1.acceptsParent( g2 ) )
		self.failIf( g1.acceptsChild( Gaffer.Node() ) )
		self.failIf( g1.acceptsParent( Gaffer.Node() ) )

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
		self.assert_( child.parent().isSame( parent ) )

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

		self.assertTypeNamesArePrefixed( Gaffer )
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

if __name__ == "__main__":
	unittest.main()

