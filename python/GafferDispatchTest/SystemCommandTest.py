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
import subprocess
import unittest

import IECore

import Gaffer
import GafferTest
import GafferDispatch

class SystemCommandTest( GafferTest.TestCase ) :

	def test( self ) :

		n = GafferDispatch.SystemCommand()
		n["command"].setValue( "echo 1 > {}".format( ( self.temporaryDirectory() / "systemCommandTest.txt" ).as_posix() ) )

		n["task"].execute()

		self.assertTrue( ( self.temporaryDirectory() / "systemCommandTest.txt" ).is_file() )

	def testEnvironmentVariables( self ) :

		n = GafferDispatch.SystemCommand()
		if os.name != "nt" :
			n["command"].setValue( "env > {}".format( self.temporaryDirectory() / "systemCommandTest.txt" ) )
		else :
			n["command"].setValue( " set > {}".format( ( self.temporaryDirectory() / "systemCommandTest.txt" ).as_posix() ) )
		n["environmentVariables"].addChild( Gaffer.NameValuePlug( "GAFFER_SYSTEMCOMMAND_TEST", IECore.StringData( "test" ) ) )

		n["task"].execute()

		env = "".join( open( self.temporaryDirectory() / "systemCommandTest.txt", encoding = "utf-8" ).readlines() )
		self.assertTrue( "GAFFER_SYSTEMCOMMAND_TEST=test" in env )

	def testSubstitutions( self ) :

		n = GafferDispatch.SystemCommand()
		n["command"].setValue( "echo {adjective} {noun}> " + ( self.temporaryDirectory() / "systemCommandTest.txt" ).as_posix() )
		n["substitutions"].addChild( Gaffer.NameValuePlug( "adjective", IECore.StringData( "red" ) ) )
		n["substitutions"].addChild( Gaffer.NameValuePlug( "noun", IECore.StringData( "truck" ) ) )

		n["task"].execute()
		self.assertEqual( "red truck\n", open( self.temporaryDirectory() / "systemCommandTest.txt", encoding = "utf-8" ).readlines()[0] )

	def testHash( self ) :

		hashes = []

		n = GafferDispatch.SystemCommand()
		hashes.append( n["task"].hash() )

		n["command"].setValue( "env" )
		hashes.append( n["task"].hash() )

		n["command"].setValue( "echo abc" )
		hashes.append( n["task"].hash() )

		n["substitutions"].addChild( Gaffer.NameValuePlug( "test", IECore.StringData( "value" ) ) )
		hashes.append( n["task"].hash() )

		n["environmentVariables"].addChild( Gaffer.NameValuePlug( "test", IECore.StringData( "value" ) ) )
		hashes.append( n["task"].hash() )

		# check that all hashes are unique
		self.assertEqual( len( hashes ), len( set( hashes ) ) )

	def testFrameRangeSubstitutions( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferDispatch.SystemCommand()
		s["n"]["command"].setValue( "echo 1 > {}".format( ( self.temporaryDirectory() / "systemCommandTest.####.txt" ).as_posix() ) )

		d = GafferDispatch.LocalDispatcher()
		d["jobsDirectory"].setValue( self.temporaryDirectory() / "jobs" )
		d["framesMode"].setValue( d.FramesMode.CustomRange )
		d["frameRange"].setValue( "1-10" )

		d.dispatch( [ s["n"] ] )

		sequences = IECore.ls( str( self.temporaryDirectory() ) )
		self.assertEqual( len( sequences ), 1 )
		self.assertEqual( str( sequences[0] ), "systemCommandTest.####.txt 1-10" )

	def testShell( self ) :

		s = Gaffer.ScriptNode()

		s["n"] = GafferDispatch.SystemCommand()

		self.assertEqual( s["n"]["shell"].getValue(), True )

		# The following command is only valid when interpreted as a shell command
		if os.name != "nt" :
			s["n"]["command"].setValue( "date | wc -l" )
		else :
			s["n"]["command"].setValue( "set" )

		s["n"].execute()

		s["n"]["shell"].setValue( False )

		if os.name != "nt" :
			with self.assertRaises( subprocess.CalledProcessError ) :
				s["n"].execute()
		else :
			with self.assertRaises( FileNotFoundError ) :
				s["n"].execute()

	def testEmptyCommand( self ) :

		c = GafferDispatch.SystemCommand()
		self.assertEqual( c["command"].getValue(), "" )
		self.assertEqual( c["task"].hash(), IECore.MurmurHash() )

if __name__ == "__main__":
	unittest.main()
