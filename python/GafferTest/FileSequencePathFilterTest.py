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

import pathlib
import unittest

import Gaffer
import GafferTest

class FileSequencePathFilterTest( GafferTest.TestCase ) :

	def test( self ) :

		p = Gaffer.FileSystemPath( self.__dir, includeSequences = True )
		self.assertTrue( p.getIncludeSequences() )

		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

		p.setFilter( Gaffer.FileSequencePathFilter( mode = Gaffer.FileSequencePathFilter.Keep.Files ) )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Files )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )


		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

		p = Gaffer.FileSystemPath( self.__dir, includeSequences = True )
		self.assertTrue( p.getIncludeSequences() )

		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

		p.setFilter( Gaffer.FileSequencePathFilter( mode = Gaffer.FileSequencePathFilter.Keep.Files ) )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Files )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )


		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

	def testNoSequences( self ) :

		# it doesn't really make sense to do this,
		# as we're using a sequence filter on a
		# path that by definition has no sequences,
		# but we may as well verify that it works.

		p = Gaffer.FileSystemPath( self.__dir, includeSequences = False )
		self.assertFalse( p.getIncludeSequences() )

		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.setFilter( Gaffer.FileSequencePathFilter( mode = Gaffer.FileSequencePathFilter.Keep.Files ) )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Files )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )


		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.SequentialFiles )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Sequences )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Concise )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Verbose )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setMode( Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.All )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

	def testEnabled( self ) :

		p = Gaffer.FileSystemPath( self.__dir, includeSequences = True )
		self.assertTrue( p.getIncludeSequences() )

		p.setFilter( Gaffer.FileSequencePathFilter( mode = Gaffer.FileSequencePathFilter.Keep.Files ) )
		self.assertEqual( p.getFilter().getMode(), Gaffer.FileSequencePathFilter.Keep.Files )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
		] ) )

		p.getFilter().setEnabled( False )
		self.assertEqual( set( [ str( c ) for c in p.children() ] ), set( [
			( self.__dir / "singleFile.txt" ).as_posix(),
			( self.__dir / "a.001.txt" ).as_posix(),
			( self.__dir / "a.002.txt" ).as_posix(),
			( self.__dir / "a.004.txt" ).as_posix(),
			( self.__dir / "b.003.txt" ).as_posix(),
			( self.__dir / "dir" ).as_posix(),
			( self.__dir / "a.###.txt" ).as_posix(),
			( self.__dir / "b.###.txt" ).as_posix()
		] ) )

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__dir = self.temporaryDirectory()

		( self.__dir / "dir" ).mkdir()
		for n in [ "singleFile.txt", "a.001.txt", "a.002.txt", "a.004.txt", "b.003.txt" ] :
			with open( self.__dir / n, "w", encoding = "utf-8" ) as f :
				f.write( "AAAA" )

if __name__ == "__main__":
	unittest.main()
