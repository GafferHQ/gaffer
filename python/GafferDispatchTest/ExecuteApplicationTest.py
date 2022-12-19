##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
#  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
import inspect
import imath

import IECore

import Gaffer
import GafferDispatch

import GafferTest
import GafferDispatchTest

class ExecuteApplicationTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() / "executeScript.gfr"
		self.__scriptFileNameWithSpecialCharacters = self.temporaryDirectory() / "executeScript-10.tmp.gfr"
		self.__outputTextFile = self.temporaryDirectory() / "executeOutput.txt"
		self.__outputFileSeq = IECore.FileSequence( str( self.temporaryDirectory() / "output.####.cob" ) )

	def testErrorReturnStatusForMissingScript( self ) :

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", "thisScriptDoesNotExist" ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		self.assertIn( "thisScriptDoesNotExist", "".join( p.stderr.readlines() ) )
		self.assertTrue( p.returncode )

	def testExecuteTextWriter( self ) :

		s = Gaffer.ScriptNode()

		s["write"] = GafferDispatchTest.TextWriter()
		s["write"]["fileName"].setValue( pathlib.Path( self.__outputFileSeq.fileName ) )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		self.assertFalse( os.path.exists( pathlib.Path( self.__outputFileSeq.fileNameForFrame( 1 ) ) ) )
		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", str( self.__scriptFileName ) ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.assertTrue( pathlib.Path( self.__outputFileSeq.fileNameForFrame( 1 ) ).exists() )
		self.assertFalse( p.returncode )

	def testFramesParameter( self ) :

		s = Gaffer.ScriptNode()

		s["write"] = GafferDispatchTest.TextWriter()
		s["write"]["fileName"].setValue( pathlib.Path( self.__outputFileSeq.fileName ) )
		s["write"]["text"].setValue( "test" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		frames = IECore.FrameList.parse( "1-5" )
		for f in frames.asList() :
			self.assertFalse( pathlib.Path( self.__outputFileSeq.fileNameForFrame( f ) ).exists() )

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", str( self.__scriptFileName ), "-frames", str( frames ) ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.assertFalse( p.returncode )
		for f in frames.asList() :
			self.assertTrue( pathlib.Path( self.__outputFileSeq.fileNameForFrame( f ) ).exists() )

	def testContextParameter( self ) :

		s = Gaffer.ScriptNode()

		s["write"] = GafferDispatchTest.TextWriter()
		s["write"]["fileName"].setValue( pathlib.Path( self.__outputFileSeq.fileName ) )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( "parent['write']['text'] = '{} {}'.format( context.get( 'valueOne', 0 ), context.get( 'valueTwo', 0 ) )" )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		self.assertFalse( pathlib.Path( self.__outputFileSeq.fileNameForFrame( 1 ) ).exists() )
		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", str( self.__scriptFileName ), "-context", "-valueOne", "1", "-valueTwo", "2" ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.assertFalse( p.returncode )
		self.assertTrue( pathlib.Path( self.__outputFileSeq.fileNameForFrame( 1 ) ).exists() )

		with open( pathlib.Path( self.__outputFileSeq.fileNameForFrame( 1 ) ) ) as f :
			string = f.read()

		self.assertEqual( string, "1 2" )

	def testErrorReturnStatusForBadContext( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.__scriptFileName )
		s["write"] = GafferDispatchTest.TextWriter()
		s.save()

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", "-script", str( self.__scriptFileName ), "-context", "-myArg", "10", "-noValue" ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertIn( "ERROR", error )
		self.assertIn( "Context parameter", error )
		self.assertTrue( p.returncode )

	def testIgnoreScriptLoadErrors( self ) :

		s = Gaffer.ScriptNode()
		s["node"] = GafferDispatch.PythonCommand()
		s["node"]["command"].setValue( "import time; time.sleep(.1)" )

		# because this doesn't have the dynamic flag set,
		# it won't serialise/load properly.
		s["node"]["user"]["badPlug"] = Gaffer.IntPlug()
		s["node"]["user"]["badPlug"].setValue( 10 )

		s["fileName"].setValue( self.__scriptFileName )
		s.save()

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", "-script", str( self.__scriptFileName ) ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertTrue( self.__scriptFileName.as_posix() in error )
		self.assertTrue( "KeyError: \"'badPlug'" in error )
		self.assertFalse( "Traceback" in error )
		self.assertNotEqual( p.returncode, 0 )

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", "-ignoreScriptLoadErrors", "-script", str( self.__scriptFileName ) ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertTrue( "KeyError: \"'badPlug'" in error )
		self.assertFalse( "Traceback" in error )
		self.assertEqual( p.returncode, 0 )

	def testErrorReturnStatusForExceptionDuringExecution( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.__scriptFileName )
		s["t"] = GafferDispatchTest.TextWriter()
		s["t"]["fileName"].setValue( "" ) # will cause an error
		s.save()

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", "-script", str( self.__scriptFileName ) ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertIn( "ERROR", error )
		self.assertIn( "executing t", error )
		self.assertTrue( p.returncode )

	def testSpecialCharactersInScriptFileName( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.__scriptFileNameWithSpecialCharacters )
		s["t"] = GafferDispatchTest.TextWriter()
		s["t"]["fileName"].setValue( self.__outputTextFile )
		s.save()

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", "-script", str( self.__scriptFileNameWithSpecialCharacters ) ],
			stderr = subprocess.PIPE,
		)
		p.wait()

		self.assertEqual( p.returncode, 0 )
		self.assertTrue( self.__outputTextFile.exists() )

	def testErrorMessagesIncludeNodeName( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.__scriptFileName )

		s["MyTextWriter"] = GafferDispatchTest.TextWriter()
		s["MyTextWriter"]["fileName"].setValue( self.__outputTextFile )

		s["MyExpression"] = Gaffer.Expression()
		s["MyExpression"].setExpression(
			"""parent["MyTextWriter"]["text"] = thisVariableDoesntExist"""
		)

		s["MyErroringTaskNode"] = GafferDispatchTest.ErroringTaskNode()

		s.save()

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", "-script", str( self.__scriptFileName ), "-nodes", "MyTextWriter" ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertIn( "MyTextWriter", error )
		self.assertIn( "MyExpression", error )

		p = subprocess.Popen(
			[ str( Gaffer.executablePath() ), "execute", "-script", str( self.__scriptFileName ), "-nodes", "MyErroringTaskNode" ],
			stderr = subprocess.PIPE,
			universal_newlines = True,
		)
		p.wait()

		error = "".join( p.stderr.readlines() )
		self.assertIn( "MyErroringTaskNode", error )
		self.assertNotIn( "MyExpression", error )

	def testDefaultFrame( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = GafferDispatchTest.TextWriter()
		s["t"]["fileName"].setValue( self.temporaryDirectory() / "test.####.txt" )
		s["t"]["text"].setValue( "test" )

		s["fileName"].setValue( self.__scriptFileName )
		s.context().setFrame( 10 )
		s.save()

		subprocess.check_call( [ str( Gaffer.executablePath() ), "execute", str( self.__scriptFileName ) ] )

		self.assertEqual(
			list( self.temporaryDirectory().glob( "test.*.txt" ) ),
			[ self.temporaryDirectory() / "test.0010.txt" ]
		)

	def testImathContextVariable( self ) :

		s = Gaffer.ScriptNode()
		s["t"] = GafferDispatchTest.TextWriter()
		s["t"]["fileName"].setValue( self.temporaryDirectory() / "test.txt" )

		s["e"] = Gaffer.Expression()
		s["e"].setExpression( inspect.cleandoc(
			"""
			c = context["c"]
			parent["t"]["text"] = "{0} {1} {2}".format( *c )
			"""
		) )

		s["fileName"].setValue(  self.temporaryDirectory() / "test.gfr" )
		s.save()

		subprocess.check_call( [ str( Gaffer.executablePath() ), "execute", s["fileName"].getValue(), "-context", "c", "imath.Color3f( 0, 1, 2 )" ] )

		self.assertEqual(
			open( s["t"]["fileName"].getValue() ).read(),
			"0.0 1.0 2.0"
		)

	def testCanSerialiseFrameDependentPlugs( self ) :

		s = Gaffer.ScriptNode()
		s["PythonCommand"] = GafferDispatch.PythonCommand()
		s["PythonCommand"]["command"].setValue(
			inspect.cleandoc( """
				import os
				import GafferDispatchTest

				tmpDir = os.path.dirname( self.scriptNode()["fileName"].getValue() )
				s = Gaffer.ScriptNode()
				s["t"] = GafferDispatchTest.TextWriter()
				s["t"]["fileName"].setValue( tmpDir + "/test.####.txt" )
				s["t"]["text"].setValue( "test" )
				s["fileName"].setValue( tmpDir + "/canSerialiseFrameDependentPlug.gfr" )
				s.save()
			""" )
		)

		def validate( sequence ) :

			s["PythonCommand"]["sequence"].setValue( sequence )

			s["fileName"].setValue( self.__scriptFileName )
			s.context().setFrame( 10 )
			s.save()

			subprocess.check_call( [ str( Gaffer.executablePath() ), "execute", str( self.__scriptFileName ), "-frames", "5", "-nodes", "PythonCommand" ] )

			self.assertTrue( ( self.temporaryDirectory() / "canSerialiseFrameDependentPlug.gfr" ).exists() )

			ss = Gaffer.ScriptNode()
			ss["fileName"].setValue( self.temporaryDirectory() / "canSerialiseFrameDependentPlug.gfr" )
			ss.load()

			# we must retain the non-substituted value
			self.assertEqual( ss["t"]["fileName"].getValue(), "{}/test.####.txt".format( self.temporaryDirectory().as_posix() ) )

		validate( sequence = True )
		validate( sequence = False )

if __name__ == "__main__":
	unittest.main()
