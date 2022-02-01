##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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
import weakref
import gc

import IECore

import Gaffer
import GafferTest

class StandardSetTest( GafferTest.TestCase ) :

	def testRunTimeTyped( self ) :

		s = Gaffer.StandardSet()
		self.assertEqual( s.typeName(), "Gaffer::StandardSet" )
		self.assertEqual( s.staticTypeName(), "Gaffer::StandardSet" )
		self.assertTrue( s.isInstanceOf( IECore.TypeId.RunTimeTyped ) )

	def testBasicMethods( self ) :

		s = Gaffer.StandardSet()
		self.assertEqual( len( s ), 0 )
		self.assertEqual( s.size(), 0 )

		n1 = Gaffer.Node()
		n2 = Gaffer.Node()

		self.assertNotIn( n1, s )
		self.assertNotIn( n2, s )

		a = s.add( n1 )
		self.assertEqual( a, True )
		self.assertIn( n1, s )
		self.assertTrue( not n1 not in s )
		self.assertNotIn( n2, s )
		self.assertEqual( len( s ), 1 )
		self.assertEqual( s.size(), 1 )

		a = s.add( n1 )
		self.assertEqual( a, False )
		self.assertIn( n1, s )
		self.assertTrue( not n1 not in s )
		self.assertNotIn( n2, s )
		self.assertEqual( len( s ), 1 )
		self.assertEqual( s.size(), 1 )

		a = s.add( n2 )
		self.assertEqual( a, True )
		self.assertIn( n1, s )
		self.assertIn( n2, s )
		self.assertEqual( len( s ), 2 )
		self.assertEqual( s.size(), 2 )

		a = s.remove( n1 )
		self.assertEqual( a, True )
		self.assertNotIn( n1, s )
		self.assertIn( n2, s )
		self.assertEqual( len( s ), 1 )
		self.assertEqual( s.size(), 1 )

		a = s.remove( n1 )
		self.assertEqual( a, False )
		self.assertNotIn( n1, s )
		self.assertIn( n2, s )
		self.assertEqual( len( s ), 1 )
		self.assertEqual( s.size(), 1 )

		s.clear()
		self.assertNotIn( n1, s )
		self.assertNotIn( n2, s )
		self.assertEqual( len( s ), 0 )
		self.assertEqual( s.size(), 0 )

	def testGetItem( self ) :

		s = Gaffer.StandardSet()

		n1 = Gaffer.Node()
		n2 = Gaffer.Node()

		s.add( n1 )
		s.add( n2 )

		self.assertTrue( s[0].isSame( n1 ) )
		self.assertTrue( s[1].isSame( n2 ) )
		self.assertTrue( s[-1].isSame( n2 ) )
		self.assertTrue( s[-2].isSame( n1 ) )

		self.assertRaises( IndexError, s.__getitem__, 2 )
		self.assertRaises( IndexError, s.__getitem__, -3 )

	def testMemberOrdering( self ) :

		s = Gaffer.StandardSet()

		for i in range( 0, 1000 ) :
			n = Gaffer.Node()
			n.setName( "s" + str( i ) )
			s.add( n )

		self.assertEqual( len( s ), 1000 )
		for i in range( 0, len( s ) ) :
			self.assertEqual( s[i].getName(), "s" + str( i ) )

	def testLastAdded( self ) :

		s = Gaffer.StandardSet()

		for i in range( 0, 1000 ) :

			n = Gaffer.Node()
			s.add( n )

			self.assertTrue( s[-1].isSame( n ) )

	def testSignals( self ) :

		ps = set()
		def added( set, member ) :

			ps.add( member )

		def removed( set, member ) :

			ps.remove( member )

		s = Gaffer.StandardSet()

		s.memberAddedSignal().connect( added, scoped = False )
		s.memberRemovedSignal().connect( removed, scoped = False )

		n1 = Gaffer.Node()
		n2 = Gaffer.Node()
		n3 = Gaffer.Node()

		s.add( n1 )
		s.add( n2 )
		s.add( n3 )

		self.assertEqual( ps, set( s ) )

		s.remove( n1 )
		s.remove( n2 )

		self.assertEqual( ps, set( s ) )

		s.add( n1 )
		s.add( n2 )
		s.clear()

		self.assertEqual( ps, set( s ) )

	def testConstructFromSequence( self ) :

		n1 = Gaffer.Node()
		n2 = Gaffer.Node()
		n3 = Gaffer.Node()

		s = Gaffer.StandardSet( ( n1, n2 ) )
		self.assertIn( n1, s )
		self.assertIn( n2, s )
		self.assertNotIn( n3, s )

	def testAddAndRemoveFromSequence( self ) :

		n = ( Gaffer.Node(), Gaffer.Node(), Gaffer.Node() )

		s = Gaffer.StandardSet()
		s.add( n )

		self.assertEqual( set( n ), set( s ) )

		s.remove( n )

		self.assertEqual( len( s ), 0 )
		self.assertEqual( set(), set( s ) )

	def testMemberAcceptanceSignals( self ) :

		s = Gaffer.StandardSet()

		def f( s, m ) :

			return m.isInstanceOf( Gaffer.Plug.staticTypeId() )

		s.memberAcceptanceSignal().connect(	f, scoped = False )

		n = Gaffer.Node()
		p = Gaffer.Plug()

		self.assertRaises( Exception, s.add, n )

		self.assertNotIn( n, s )

		s.add( p )

		self.assertIn( p, s )

	def testMembershipQueries( self ) :

		members = [ Gaffer.Node(), Gaffer.Node(), Gaffer.Node() ]
		notMembers = [ Gaffer.Node(), Gaffer.Node(), Gaffer.Node() ]

		s = Gaffer.StandardSet( members )

		for m in members :
			self.assertIn( m, s )
			self.assertTrue( s.contains( m ) )

		for m in notMembers :
			self.assertNotIn( m, s )
			self.assertFalse( s.contains( m ) )

	def testIteration( self ) :

		members = [ Gaffer.Node(), Gaffer.Node(), Gaffer.Node() ]
		s = Gaffer.StandardSet( members )

		i = 0
		for m in s :
			self.assertTrue( m.isSame( members[i] ) )
			i += 1

	def testRemoveReferenceCounting( self ) :

		s = Gaffer.StandardSet()
		for i in range( 0, 100 ) :
			s.add( IECore.StringData( "hello there!" ) )

		def f( s, m ) :

			pass

		s.memberRemovedSignal().connect( f, scoped = False )

		s.clear()

	def testAddAndRemoveFromSet( self ) :

		ints = [ IECore.IntData( i ) for i in range( 0, 10 ) ]

		all = Gaffer.StandardSet( ints )
		evens = Gaffer.StandardSet( [ x for x in ints if x.value % 2 == 0 ] )
		odds = Gaffer.StandardSet( [ x for x in ints if x.value % 2 == 1 ] )

		s = Gaffer.StandardSet()
		self.assertEqual( s.add( evens ), len( evens ) )
		self.assertEqual( len( s ), len( evens ) )
		for e in evens :
			self.assertTrue( e in s )

		self.assertEqual( s.add( odds ), len( odds ) )
		self.assertEqual( len( s ), len( all ) )
		for e in all :
			self.assertTrue( e in s )

		self.assertEqual( s.remove( evens ), len( evens ) )
		self.assertEqual( len( s ), len( odds ) )
		for e in odds :
			self.assertTrue( e in s )

	def testSlicing( self ) :

		l = [ IECore.IntData( i ) for i in range( 0, 10 ) ]
		s = Gaffer.StandardSet( l )

		self.assertEqual( l[:], s[:] )
		self.assertEqual( l[1:4], s[1:4] )
		self.assertEqual( l[:4], s[:4] )
		self.assertEqual( l[2:], s[2:] )
		self.assertEqual( l[2:-2], s[2:-2] )
		self.assertEqual( l[:40], s[:40] )
		self.assertEqual( l[1:-20], s[1:-20] )

	def testOrphanRemoval( self ) :

		p = Gaffer.GraphComponent()
		c1 = Gaffer.GraphComponent()
		c2 = Gaffer.GraphComponent()
		p["c1"] = c1
		p["c2"] = c2

		s = Gaffer.StandardSet( p.children(), removeOrphans = True )
		self.assertTrue( s.getRemoveOrphans() )

		self.assertEqual( len( s ), 2 )
		self.assertTrue( c1 in s )
		self.assertTrue( c2 in s )

		p.removeChild( c1 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertTrue( c2 in s )

		p["c1"] = c1

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertTrue( c2 in s )

		s.add( c1 )

		self.assertEqual( len( s ), 2 )
		self.assertTrue( c1 in s )
		self.assertTrue( c2 in s )

		p.removeChild( c1 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertTrue( c2 in s )

		p.removeChild( c2 )

		self.assertEqual( len( s ), 0 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )

		c3 = Gaffer.GraphComponent()
		s.add( c3 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertTrue( c3 in s )

		p["c3"] = c3

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertTrue( c3 in s )

		p.removeChild( c3 )

		self.assertEqual( len( s ), 0 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertFalse( c3 in s )

		p["c3"] = c3
		s.add( c3 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertTrue( c3 in s )

		s.setRemoveOrphans( False )
		self.assertFalse( s.getRemoveOrphans() )
		p.removeChild( c3 )

		self.assertEqual( len( s ), 1 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertTrue( c3 in s )

		s.setRemoveOrphans( True )
		self.assertTrue( s.getRemoveOrphans() )
		p.addChild( c3 )
		p.removeChild( c3 )

		self.assertEqual( len( s ), 0 )
		self.assertFalse( c1 in s )
		self.assertFalse( c2 in s )
		self.assertFalse( c3 in s )

	def testNoOrphanRemoval( self ) :

		p = Gaffer.GraphComponent()
		c1 = Gaffer.GraphComponent()
		c2 = Gaffer.GraphComponent()
		p["c1"] = c1
		p["c2"] = c2

		s1 = Gaffer.StandardSet( p.children() )
		s2 = Gaffer.StandardSet( p.children(), removeOrphans = False )

		self.assertFalse( s1.getRemoveOrphans() )
		self.assertFalse( s2.getRemoveOrphans() )

		p.removeChild( c1 )
		p.removeChild( c2 )

		self.assertTrue( c1 in s1 )
		self.assertTrue( c2 in s1 )
		self.assertTrue( c1 in s2 )
		self.assertTrue( c2 in s2 )

if __name__ == "__main__":
	unittest.main()
