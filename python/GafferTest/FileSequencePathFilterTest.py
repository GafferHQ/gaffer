##########################################################################
#
#  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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
import shutil
import unittest
import ctypes
import tempfile

import Gaffer
import GafferTest

class FileSequencePathFilterTest( GafferTest.TestCase ) :

	def test( self ) :

		p = Gaffer.FileSystemPath( self.__dir, includeSequences = True )
		self.assertTrue( p.getIncludeSequences() )

		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

		p.setFilter( Gaffer.FileSequencePathFilter( mode = Gaffer.FileSequencePathFilter.Keep.Files ) )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Files )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/dir",
		] ) )


		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

		p = Gaffer.FileSystemPath( self.__dir, includeSequences = True )
		self.assertTrue( p.getIncludeSequences() )

		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

		p.setFilter( Gaffer.FileSequencePathFilter( mode = Gaffer.FileSequencePathFilter.Keep.Files ) )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Files )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/dir",
		] ) )


		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

	def testNoSequences( self ) :

		# it doesn't really make sense to do this,
		# as we're using a sequence filter on a
		# path that by definition has no sequences,
		# but we may as well verify that it works.

		p = Gaffer.FileSystemPath( self.__dir, includeSequences = False )
		self.assertFalse( p.getIncludeSequences() )

		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
		] ) )

		p.setFilter( Gaffer.FileSequencePathFilter( mode = Gaffer.FileSequencePathFilter.Keep.Files ) )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Files )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/dir",
		] ) )


		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/dir",
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/dir",
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
		] ) )

	def testEnabled( self ) :

		p = Gaffer.FileSystemPath( self.__dir, includeSequences = True )
		self.assertTrue( p.getIncludeSequences() )

		p.setFilter( Gaffer.FileSequencePathFilter( mode = Gaffer.FileSequencePathFilter.Keep.Files ) )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Files )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/dir",
		] ) )

		p.getFilter().setEnabled( False )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			self.__dir + "/singleFile.txt",
			self.__dir + "/a.001.txt",
			self.__dir + "/a.002.txt",
			self.__dir + "/a.004.txt",
			self.__dir + "/b.003.txt",
			self.__dir + "/dir",
			self.__dir + "/a.###.txt",
			self.__dir + "/b.###.txt"
		] ) )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__dir = str( Gaffer.FileSystemPath( os.path.join( tempfile.gettempdir(), "gafferFileSequencePathFilterTest" ) ) )

		# clear out old files and make empty directory
		# to work in
		if os.path.exists( self.__dir ) :
			shutil.rmtree( self.__dir )
		os.mkdir( self.__dir )

		# On Windows, Python returns a temporary directory in Windows 8.3 file
		# naming format, which is a shortened version of the full filename.
		# This name contains numbers, which causes the test to fail when
		# IECore::findSequences thinks it finds a sequence due to the number
		# in the directory name.
		# The only way to expand the shortened name is either the Win32 Python
		# extensions, or calling the needed function through ctypes. We choose
		# ctypes to eliminate the need for additional modules.
		if os.name == "nt" :
			buffer = ctypes.create_unicode_buffer( 4096 )
			ctypes.windll.kernel32.GetLongPathNameW( self.__dir, buffer, 4096 )
			self.__dir = buffer.value

		os.mkdir( self.__dir + "/dir" )
		for n in [ "singleFile.txt", "a.001.txt", "a.002.txt", "a.004.txt", "b.003.txt" ] :
			with open( self.__dir + "/" + n, "w" ) as f :
				f.write( "AAAA" )

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		if os.path.exists( self.__dir ) :
			shutil.rmtree( self.__dir )

if __name__ == "__main__":
	unittest.main()
