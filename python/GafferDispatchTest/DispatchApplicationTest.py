##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import subprocess32 as subprocess
import unittest

import Gaffer
import GafferDispatch

import GafferTest
import GafferDispatchTest

class DispatchApplicationTest( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		self.__scriptFileName = self.temporaryDirectory() + "/script.gfr"
		self.__outputTextFile = self.temporaryDirectory() + "/output.txt"

	def writeSimpleScript( self ) :

		s = Gaffer.ScriptNode()
		s["fileName"].setValue( self.__scriptFileName )
		s["test"] = GafferDispatchTest.TextWriter( "test" )
		s["test"]["fileName"].setValue( self.__outputTextFile )
		s["test"]["text"].setValue( "its a test" )
		s.save()

		self.failUnless( os.path.exists( self.__scriptFileName ) )
		self.failIf( os.path.exists( self.__outputTextFile ) )

		return s

	def waitForCommand( self, command ) :

		# we force a custom jobsDirectory to ensure the tmp files go somewhere sensible
		if "-settings" not in command :
			command += " -settings"
		if "-dispatcher.jobsDirectory" not in command :
			command += " -dispatcher.jobsDirectory '\"{tmpDir}/dispatcher/local\"'".format( tmpDir = self.temporaryDirectory() )

		p = subprocess.Popen( command, shell=True, stderr = subprocess.PIPE )
		p.wait()

		return p

	def testErrorReturnStatus( self ) :

		# no nodes
		p = self.waitForCommand( "gaffer dispatch" )
		self.failUnless( "No nodes were specified" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		# bad nodes
		p = self.waitForCommand( "gaffer dispatch -nodes Gaffer.NotANode" )
		self.failUnless( "NotANode" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		# no namespace
		p = self.waitForCommand( "gaffer dispatch -nodes TextWriter" )
		self.failUnless( "TextWriter" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		# bad dispatcher
		p = self.waitForCommand( "gaffer dispatch -nodes GafferDispatchTest.TextWriter -dispatcher NotADispatcher" )
		self.failUnless( "NotADispatcher" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		# invalid script
		p = self.waitForCommand( "gaffer dispatch -script thisScriptDoesNotExist -nodes GafferDispatch.SystemCommand" )
		self.failUnless( "thisScriptDoesNotExist" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		self.writeSimpleScript()

		# nodes not in script
		p = self.waitForCommand( "gaffer dispatch -script {script} -nodes notANode".format( script = self.__scriptFileName ) )
		self.failUnless( "notANode" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		# bad plugs
		p = self.waitForCommand( "gaffer dispatch -script {script} -nodes test -settings -test.notAPlug 1".format( script = self.__scriptFileName ) )
		self.failUnless( "notAPlug" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		# bad values (text is a string so needs quotations)
		p = self.waitForCommand( "gaffer dispatch -script {script} -nodes test -settings -test.text 1".format( script = self.__scriptFileName ) )
		self.failUnless( "test.text" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		# bad dispatcher plugs
		p = self.waitForCommand( "gaffer dispatch -script {script} -nodes test -settings -LocalDispatcher.notAPlug 1".format( script = self.__scriptFileName ) )
		self.failUnless( "notAPlug" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

		# bad dispatcher values
		p = self.waitForCommand( "gaffer dispatch -script {script} -nodes test -settings -LocalDispatcher.executeInBackground '\"its a bool\"'".format( script = self.__scriptFileName ) )
		self.failUnless( "executeInBackground" in "".join( p.stderr.readlines() ) )
		self.failUnless( p.returncode )

	def testScript( self ) :

		self.writeSimpleScript()

		p = self.waitForCommand(
			"gaffer dispatch -script {script} -nodes {node}".format(
				script = self.__scriptFileName,
				node = "test",
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.failIf( p.returncode )
		with file( self.__outputTextFile, "r" ) as f :
			self.assertEqual( f.readlines(), [ "its a test" ] )

	def testScriptLoadErrors( self ) :

		s = self.writeSimpleScript()
		# because this doesn't have the dynamic flag set,
		# it won't serialise/load properly.
		s["test"]["user"]["badPlug"] = Gaffer.IntPlug()
		s["test"]["user"]["badPlug"].setValue( 10 )
		s.save()

		p = self.waitForCommand(
			"gaffer dispatch -script {script} -nodes {node}".format(
				script = self.__scriptFileName,
				node = "test",
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertTrue( self.__scriptFileName in error )
		self.assertTrue( "KeyError: \"'badPlug'" in error )
		self.assertFalse( "Traceback" in error )
		self.assertNotEqual( p.returncode, 0 )
		self.failIf( os.path.exists( self.__outputTextFile ) )

		p = self.waitForCommand(
			"gaffer dispatch -ignoreScriptLoadErrors -script {script} -nodes {node}".format(
				script = self.__scriptFileName,
				node = "test",
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertTrue( "KeyError: \"'badPlug'" in error )
		self.assertFalse( "Traceback" in error )
		self.assertEqual( p.returncode, 0 )
		with file( self.__outputTextFile, "r" ) as f :
			self.assertEqual( f.readlines(), [ "its a test" ] )

	def testNodesWithoutScript( self ) :

		p = self.waitForCommand(
			"gaffer dispatch -nodes {node} -settings -TextWriter.fileName '\"{output}\"' -TextWriter.text '\"{text}\"'".format(
				node = "GafferDispatchTest.TextWriter",
				output = self.__outputTextFile,
				text = "command line test",
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.failIf( p.returncode )
		with file( self.__outputTextFile, "r" ) as f :
			self.assertEqual( f.readlines(), [ "command line test" ] )

	def testApplyUserDefaults( self ) :

		p = self.waitForCommand(
			"gaffer dispatch -nodes {node} -applyUserDefaults -settings -TextWriter.fileName '\"{output}\"' -TextWriter.text '\"{text}\"'".format(
				node = "GafferDispatchTest.TextWriter",
				output = self.__outputTextFile,
				text = "userDefault test ${dispatcher:jobDirectory}",
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.failIf( p.returncode )
		jobDir = self.temporaryDirectory() + "/dispatcher/local/000000"
		with file( self.__outputTextFile, "r" ) as f :
			self.assertEqual( f.readlines(), [ "userDefault test {jobDir}".format( jobDir = jobDir ) ] )

	def testDispatcherOverrides( self ) :

		s = self.writeSimpleScript()
		s["test"]["text"].setValue( "${frame}\n" )
		s["test"]["mode"].setValue( "a" )
		s.save()

		# really we're using the same dispatcher, but setting it by name to show
		# this can be done as there aren't other dispatchers available to test with.

		p = self.waitForCommand(
			"gaffer dispatch -script {script} -nodes {node} -dispatcher Local -settings -dispatcher.framesMode {mode}".format(
				script = self.__scriptFileName,
				node = "test",
				mode = int(GafferDispatch.Dispatcher.FramesMode.FullRange),
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.failIf( p.returncode )
		with file( self.__outputTextFile, "r" ) as f :
			self.assertEqual( f.readlines(), [ str(x)+"\n" for x in range( 1, 101 ) ] )

	def testContextVariables( self ) :

		p = self.waitForCommand(
			"gaffer dispatch -nodes {node} -settings -TextWriter.fileName '\"{output}\"' -TextWriter.text '\"{text}\"' -context.myVar 1.25".format(
				node = "GafferDispatchTest.TextWriter",
				output = self.__outputTextFile,
				text = "context ${myVar} test",
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.failIf( p.returncode )
		with file( self.__outputTextFile, "r" ) as f :
			self.assertEqual( f.readlines(), [ "context 1.25 test" ] )

	def testBox( self ) :

		s = self.writeSimpleScript()
		s["box"] = Gaffer.Box()
		s["box"].addChild( s["test"] )
		Gaffer.PlugAlgo.promote( s["box"]["test"]["task"] )
		s.save()

		p = self.waitForCommand(
			"gaffer dispatch -script {script} -nodes {node} -settings -box.test.text '\"{text}\"'".format(
				script = self.__scriptFileName,
				node = "box",
				text = "test inside a box",
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.failIf( p.returncode )
		with file( self.__outputTextFile, "r" ) as f :
			self.assertEqual( f.readlines(), [ "test inside a box" ] )

	def testMultipleNodes( self ) :

		s = self.writeSimpleScript()
		s["test2"] = GafferDispatchTest.TextWriter()
		s["test2"]["fileName"].setValue( self.__outputTextFile + ".2" )
		s["test2"]["text"].setValue( "its a 2nd test" )
		s.save()

		p = self.waitForCommand(
			"gaffer dispatch -script {script} -nodes {nodeA} {nodeB}".format(
				script = self.__scriptFileName,
				nodeA = "test",
				nodeB = "test2",
			)
		)
		error = "".join( p.stderr.readlines() )
		self.assertEqual( error, "" )
		self.failIf( p.returncode )
		with file( self.__outputTextFile, "r" ) as f :
			self.assertEqual( f.readlines(), [ "its a test" ] )
		with file( self.__outputTextFile + ".2", "r" ) as f :
			self.assertEqual( f.readlines(), [ "its a 2nd test" ] )

if __name__ == "__main__":
	unittest.main()
