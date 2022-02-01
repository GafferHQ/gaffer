##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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
import glob

import IECore

import Gaffer
import GafferTest

class PathFilterTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		open( self.temporaryDirectory() + "/a", "w" )
		open( self.temporaryDirectory() + "/b.txt", "w" )

	def test( self ) :

		# First, check that we have a mix of extensions in
		# our test directory. Otherwise we can't test anything.

		self.assertTrue( len( glob.glob( self.temporaryDirectory() + "/*" ) ) != len( glob.glob( self.temporaryDirectory() + "/*.txt" ) ) )

		# Check that an unfiltered path can see all the files

		path = Gaffer.FileSystemPath( self.temporaryDirectory() )
		children = path.children()
		self.assertEqual( len( children ), len( glob.glob( self.temporaryDirectory() + "/*" ) ) )

		# Attach a filter, and check that the files are filtered
		txtFilter = Gaffer.FileNamePathFilter( [ "*.txt" ] )
		path.setFilter( txtFilter )

		children = path.children()
		self.assertEqual( len( children ), len( glob.glob( self.temporaryDirectory() + "/*.txt" ) ) )

		# Copy the path and check the filter is working on the copy
		pathCopy = path.copy()
		self.assertEqual( len( pathCopy.children() ), len( children ) )

		# Detach the filter and check that behaviour has reverted
		path.setFilter( None )
		children = path.children()
		self.assertEqual( len( children ), len( glob.glob( self.temporaryDirectory() + "/*" ) ) )

	def testEnabledState( self ) :

		path = Gaffer.FileSystemPath( self.temporaryDirectory() )

		f = Gaffer.FileNamePathFilter( [ "*.txt" ] )
		self.assertEqual( f.getEnabled(), True )

		path.setFilter( f )
		self.assertEqual( len( path.children() ), len( glob.glob( self.temporaryDirectory() + "/*.txt" ) ) )

		f.setEnabled( False )
		self.assertEqual( f.getEnabled(), False )
		self.assertEqual( len( path.children() ), len( glob.glob( self.temporaryDirectory() + "/*" ) ) )

		f.setEnabled( True )
		self.assertEqual( f.getEnabled(), True )
		self.assertEqual( len( path.children() ), len( glob.glob( self.temporaryDirectory() + "/*.txt" ) ) )

	def testChangedSignal( self ) :

		pathFilter = Gaffer.FileNamePathFilter( [ "*.gfr" ] )

		enabledStates = []

		def f( pf ) :

			self.assertTrue( pf.isSame( pathFilter ) )
			enabledStates.append( pf.getEnabled() )

		pathFilter.changedSignal().connect( f, scoped = False )

		pathFilter.setEnabled( False )
		pathFilter.setEnabled( False )
		pathFilter.setEnabled( True )
		pathFilter.setEnabled( True )
		pathFilter.setEnabled( False )

		self.assertEqual( enabledStates, [ False, True, False ] )

	def testUserData( self ) :

		pathFilter = Gaffer.FileNamePathFilter( [ "*.gfr" ] )
		self.assertEqual( pathFilter.userData(), IECore.CompoundData() )

		ud = IECore.CompoundData( { "a" : "a" } )
		pathFilter = Gaffer.FileNamePathFilter( [ "*.gfr" ], userData = ud )
		self.assertEqual( pathFilter.userData(), ud )
		self.assertFalse( pathFilter.userData() is ud )

if __name__ == "__main__":
	unittest.main()
