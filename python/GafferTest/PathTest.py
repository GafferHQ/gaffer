##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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
import six

import IECore

import Gaffer
import GafferTest

class PathTest( GafferTest.TestCase ) :

	class TestPath( Gaffer.Path ) :

		def __init__( self, path=None, root="/", filter=None ) :

			Gaffer.Path.__init__( self, path, root, filter )

			self.pathChangedSignalCreatedCalled = False

		def _pathChangedSignalCreated( self ) :

			Gaffer.Path._pathChangedSignalCreated( self )
			self.pathChangedSignalCreatedCalled = True

	def test( self ) :

		p = Gaffer.Path( "/" )
		self.assertEqual( len( p ), 0 )
		self.assertEqual( str( p ), "/" )

		p = Gaffer.Path( "/a" )
		self.assertEqual( len( p ), 1 )
		self.assertEqual( p[0], "a" )
		self.assertEqual( str( p ), "/a" )

		p = Gaffer.Path( "/a//b/" )
		self.assertEqual( len( p ), 2 )
		self.assertEqual( p[0], "a" )
		self.assertEqual( p[1], "b" )
		self.assertEqual( str( p ), "/a/b" )

		p = Gaffer.Path( [ "a", "b" ] )
		self.assertEqual( len( p ), 2 )
		self.assertEqual( p[0], "a" )
		self.assertEqual( p[1], "b" )
		self.assertEqual( str( p ), "/a/b" )

	def testChangedSignal( self ) :

		changedPaths = []
		def f( path ) :
			changedPaths.append( str( path ) )

		p = Gaffer.Path( "/" )
		c = p.pathChangedSignal().connect( f )

		p.append( "hello" )
		p.append( "goodbye" )
		p[0] = "hello"
		p[1] = "bob"

		self.assertEqual( changedPaths, [ "/hello", "/hello/goodbye", "/hello/bob" ] )

	def testFilters( self ) :

		p = Gaffer.Path( "/" )
		self.assertEqual( p.getFilter(), None )

		changedPaths = []
		def f( path ) :
			changedPaths.append( str( path ) )

		c = p.pathChangedSignal().connect( f )
		self.assertEqual( len( changedPaths ), 0 )

		filter = Gaffer.FileNamePathFilter( [ "*.gfr" ] )

		p.setFilter( filter )
		self.assertTrue( p.getFilter().isSame( filter ) )
		self.assertEqual( len( changedPaths ), 1 )

		p.setFilter( filter )
		self.assertTrue( p.getFilter().isSame( filter ) )
		self.assertEqual( len( changedPaths ), 1 )

		p.setFilter( None )
		self.assertIsNone( p.getFilter() )
		self.assertEqual( len( changedPaths ), 2 )

		p.setFilter( filter )
		self.assertTrue( p.getFilter().isSame( filter ) )
		self.assertEqual( len( changedPaths ), 3 )

		filter.setEnabled( False )
		self.assertEqual( len( changedPaths ), 4 )

		filter.setEnabled( True )
		self.assertEqual( len( changedPaths ), 5 )

	def testConstructWithFilter( self ) :

		p = Gaffer.Path( "/test/path" )
		self.assertIsNone( p.getFilter() )

		f = Gaffer.FileNamePathFilter( [ "*.exr" ] )
		p = Gaffer.Path( "/test/path", filter = f )
		self.assertTrue( p.getFilter().isSame( f ) )

	def testInfo( self ) :

		p = self.TestPath( "/a/b/c" )
		self.assertEqual( p.info()["name"], "c" )
		self.assertEqual( p.info()["fullName"], "/a/b/c" )

		p = self.TestPath( "/" )
		self.assertEqual( p.info()["name"], "" )
		self.assertEqual( p.info()["fullName"], "/" )

	def testRepr( self ) :

		p = Gaffer.Path( "/test/path" )
		self.assertEqual( repr( p ), "Path( '/test/path' )" )

	def testReturnSelf( self ) :

		p = self.TestPath( "/test/path" )

		self.assertTrue( p.setFromString( "/test" ) is p )
		self.assertTrue( p.append( "a" ) is p )
		self.assertTrue( p.truncateUntilValid() is p )

	def testEmptyPath( self ) :

		p = self.TestPath()
		self.assertEqual( str( p ), "" )
		self.assertTrue( p.isEmpty() )
		self.assertFalse( p.isValid() )

		p2 = p.copy()
		self.assertEqual( str( p ), "" )
		self.assertTrue( p.isEmpty() )
		self.assertFalse( p.isValid() )

		p = self.TestPath( "/" )
		self.assertFalse( p.isEmpty() )
		p.setFromString( "" )
		self.assertTrue( p.isEmpty() )

	def testRootPath( self ) :

		p = self.TestPath( "/" )
		self.assertEqual( str( p ), "/" )

	def testRelativePath( self ) :

		p = self.TestPath( "a/b" )
		self.assertTrue( p.isValid() )
		self.assertFalse( p.isEmpty() )
		self.assertEqual( str( p ), "a/b" )

		p2 = p.copy()
		self.assertTrue( p2.isValid() )
		self.assertFalse( p2.isEmpty() )
		self.assertEqual( str( p2 ), "a/b" )

	def testRelativePathEquality( self ) :

		self.assertEqual( self.TestPath( "a/b" ), self.TestPath( "a/b" ) )
		self.assertNotEqual( self.TestPath( "/a/b" ), self.TestPath( "a/b" ) )

	def testFilterSignals( self ) :

		p = Gaffer.Path( "/" )

		f1 = Gaffer.FileNamePathFilter( [ "*.gfr" ] )
		f2 = Gaffer.FileNamePathFilter( [ "*.grf" ] )
		self.assertEqual( f1.changedSignal().num_slots(), 0 )
		self.assertEqual( f2.changedSignal().num_slots(), 0 )

		# The Path shouldn't connect to the filter changed signal
		# until it really needs to - when something is connected
		# to the path's own changed signal.
		p.setFilter( f1 )
		self.assertEqual( f1.changedSignal().num_slots(), 0 )
		self.assertEqual( f2.changedSignal().num_slots(), 0 )

		cs = GafferTest.CapturingSlot( p.pathChangedSignal() )
		self.assertEqual( f1.changedSignal().num_slots(), 1 )
		self.assertEqual( f2.changedSignal().num_slots(), 0 )
		self.assertEqual( len( cs ), 0 )

		f1.setEnabled( False )
		self.assertEqual( len( cs ), 1 )

		p.setFilter( f2 )
		self.assertEqual( f1.changedSignal().num_slots(), 0 )
		self.assertEqual( f2.changedSignal().num_slots(), 1 )
		self.assertEqual( len( cs ), 2 )

		f1.setEnabled( True )
		self.assertEqual( len( cs ), 2 )

		f2.setEnabled( False )
		self.assertEqual( len( cs ), 3 )

	def testSlicing( self ) :

		p = Gaffer.Path()
		self.assertEqual( p[:], [] )

		p[:] = [ "a", "b" ]
		self.assertEqual( p[:], [ "a", "b" ] )

		p[:1] = [ "c" ]
		self.assertEqual( p[:], [ "c", "b" ] )

		p[1:] = [ "d" ]
		self.assertEqual( p[:], [ "c", "d" ] )

		p[:] = [ "a", "b", "c", "d" ]
		self.assertEqual( p[:], [ "a", "b", "c", "d" ] )

		p[1:3] = [ "e", "f", "g" ]
		self.assertEqual( p[:], [ "a", "e", "f", "g", "d" ] )

		p[1:3] = [ "j" ]
		self.assertEqual( p[:], [ "a", "j", "g", "d" ] )

		del p[3:]
		self.assertEqual( p[:], [ "a", "j", "g" ] )

		del p[:2]
		self.assertEqual( p[:], [ "g" ] )

		del p[:]
		self.assertEqual( p[:], [] )

	def testSubclassWithoutCopy( self ) :

		class PathWithoutCopy( Gaffer.Path ) :

			def __init__( self, path=None, root="/", filter=None ) :

				Gaffer.Path.__init__( self, path, root, filter )

		p = PathWithoutCopy( "/a" )
		six.assertRaisesRegex( self, Exception, ".*Path.copy\(\) not implemented.*", p.parent )

	def testProperties( self ) :

		p = Gaffer.Path( "/a/b/c")

		n = p.propertyNames()
		self.assertTrue( isinstance( n, list ) )
		self.assertTrue( "name" in n )
		self.assertTrue( "fullName" in n )

		self.assertEqual( p.property( "name"), "c" )
		self.assertEqual( p.property( "fullName"), "/a/b/c" )

	def testDisconnectFromFilterChangedOnDestruct( self ) :

		# make a path with a filter
		f = Gaffer.FileNamePathFilter( [ "*.gfr" ] )
		p = Gaffer.FileSystemPath( "/a/b/c", filter = f )

		# force the path to connect to the
		# filter's changed signal.
		c = p.pathChangedSignal()

		# delete the path
		del p
		del c

		# edit the filter
		f.setEnabled( False )

		# we should not crash

	def testChangedSignalCreation( self ) :

		p = self.TestPath( "/" )
		self.assertFalse( p.pathChangedSignalCreatedCalled )
		self.assertFalse( p._havePathChangedSignal() )

		p.pathChangedSignal()
		self.assertTrue( p.pathChangedSignalCreatedCalled )
		self.assertTrue( p._havePathChangedSignal() )

if __name__ == "__main__":
	unittest.main()
