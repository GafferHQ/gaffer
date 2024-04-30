##########################################################################
#
#  Copyright (c) 2022 Hypothetical Inc. All rights reserved.
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
import pathlib
import subprocess
import unittest

import IECore

import Gaffer
import GafferTest

class HiddenFilePathFilterTest( GafferTest.TestCase ) :

	def test( self ) :

		hiddenFile = Gaffer.FileSystemPath( self.temporaryDirectory() / ".sneaky.txt" )
		with open( hiddenFile.nativeString(), "w", encoding = "utf-8" ) as f :
			f.write( "Can't see me" )
		if os.name == "nt" :
			subprocess.check_call( [ "attrib", "+H", hiddenFile.nativeString() ] )

		visibleFile = Gaffer.FileSystemPath( self.temporaryDirectory() / "frank.txt" )
		with open( visibleFile.nativeString(), "w", encoding = "utf-8" ) as f :
			f.write( "Can see me" )

		p = Gaffer.FileSystemPath( pathlib.Path( hiddenFile.nativeString() ).parent )

		self.assertEqual(
			sorted( [ str( i ) for i in p.children() ] ),
			sorted( [ str( hiddenFile ), str( visibleFile ) ] )
		)

		h = Gaffer.HiddenFilePathFilter()
		p.setFilter( h )

		self.assertEqual( p.children(), [ hiddenFile ] )

		h.setInverted( True )

		self.assertEqual( p.children(), [ visibleFile ] )

	def testSequence( self ) :

		hiddenSequence = IECore.FileSequence( ( self.temporaryDirectory() / ".hidden.#.txt 1-3" ).as_posix() )
		visibleSequence = IECore.FileSequence( ( self.temporaryDirectory() / "visible.#.txt 1-3" ).as_posix() )

		for frame in range( 3 ) :
			hiddenFile = Gaffer.FileSystemPath( hiddenSequence.fileNameForFrame( frame ) )
			with open( hiddenFile.nativeString(), "w", encoding = "utf-8" ) as f :
				f.write( "Hidden sequence")
			if os.name == "nt" :
				subprocess.check_call( [ "attrib", "+H", hiddenFile.nativeString() ] )

			visibleFile = Gaffer.FileSystemPath( visibleSequence.fileNameForFrame( frame ) )
			with open( visibleFile.nativeString(), "w", encoding = "utf-8" ) as f :
				f.write( "Visible sequence" )

		p = Gaffer.FileSystemPath( pathlib.Path( hiddenSequence.fileName ).parent, None, True )

		self.assertEqual(
			sorted( [ str( i ) for i in p.children() ] ),
			sorted(
				[ hiddenSequence.fileNameForFrame( i ) for i in range( 3 ) ] +
				[ visibleSequence.fileNameForFrame( i ) for i in range( 3 ) ] +
				[ hiddenSequence.fileName, visibleSequence.fileName ]
			)
		)

		h = Gaffer.HiddenFilePathFilter()
		p.setFilter( h )

		self.assertEqual(
			sorted( [ str( i ) for i in p.children() ] ),
			sorted(
				[ hiddenSequence.fileNameForFrame( i ) for i in range( 3 ) ] +
				[ hiddenSequence.fileName ]
			)
		)

		h.setInverted( True )

		self.assertEqual(
			sorted( [ str( i ) for i in p.children() ] ),
			sorted(
				[ visibleSequence.fileNameForFrame( i ) for i in range( 3 ) ] +
				[ visibleSequence.fileName ]
			)
		)



if __name__ == "__main__":
	unittest.main()
