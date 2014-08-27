##########################################################################
#
#  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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
import unittest

import IECore

import Gaffer
import GafferTest

class SystemCommandTest( GafferTest.TestCase ) :

	def test( self ) :

		n = Gaffer.SystemCommand()
		n["command"].setValue( "touch /tmp/systemCommandTest.txt" )

		n.execute()

		self.assertTrue( os.path.exists( "/tmp/systemCommandTest.txt" ) )

	def testEnvironmentVariables( self ) :

		n = Gaffer.SystemCommand()
		n["command"].setValue( "env > /tmp/systemCommandTest.txt" )
		n["environmentVariables"].addMember( "GAFFER_SYSTEMCOMMAND_TEST", IECore.StringData( "test" ) )

		n.execute()

		env = "".join( open( "/tmp/systemCommandTest.txt" ).readlines() )
		self.assertTrue( "GAFFER_SYSTEMCOMMAND_TEST=test" in env )

	def testSubstitutions( self ) :

		n = Gaffer.SystemCommand()
		n["command"].setValue( "echo {adjective} {noun} > /tmp/systemCommandTest.txt" )
		n["substitutions"].addMember( "adjective", IECore.StringData( "red" ) )
		n["substitutions"].addMember( "noun", IECore.StringData( "truck" ) )

		n.execute()
		self.assertEqual( "red truck\n", open( "/tmp/systemCommandTest.txt" ).readlines()[0] )

	def testHash( self ) :

		hashes = []

		n = Gaffer.SystemCommand()
		hashes.append( n.hash( Gaffer.Context.current() ) )

		n["command"].setValue( "env" )
		hashes.append( n.hash( Gaffer.Context.current() ) )

		n["command"].setValue( "echo abc" )
		hashes.append( n.hash( Gaffer.Context.current() ) )

		n["substitutions"].addMember( "test", IECore.StringData( "value" ) )
		hashes.append( n.hash( Gaffer.Context.current() ) )

		n["environmentVariables"].addMember( "test", IECore.StringData( "value" ) )
		hashes.append( n.hash( Gaffer.Context.current() ) )

		# check that all hashes are unique
		self.assertEqual( len( hashes ), len( set( hashes ) ) )

	def setUp( self ) :

		for f in [ "/tmp/systemCommandTest.txt" ] :
			if os.path.exists( f ) :
				os.remove( f )

	def tearDown( self ) :

		self.setUp()

if __name__ == "__main__":
	unittest.main()

