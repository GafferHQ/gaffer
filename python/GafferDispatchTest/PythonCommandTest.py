##########################################################################
#
#  Copyright (c) 2015, John Haddon. All rights reserved.
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
import inspect

import IECore

import Gaffer
import GafferTest
import GafferDispatch
import GafferDispatchTest

class PythonCommandTest( GafferTest.TestCase ) :

	## \todo Something like his exists in several test cases now. Move it
	# to a new DispatchTestCase base class? If we do that, then
	# also use it in DispatcherTest instead of abusing the registry
	# in setUp().
	def __dispatcher( self, frameRange = None ) :

		result = GafferDispatchTest.DispatcherTest.TestDispatcher()
		result["jobsDirectory"].setValue( self.temporaryDirectory() + "/jobs" )

		if frameRange is not None :
			result["framesMode"].setValue( result.FramesMode.CustomRange )
			result["frameRange"].setValue( frameRange )

		return result

	def testSelf( self ) :

		n = GafferDispatch.PythonCommand()
		n["command"].setValue( "self.executionCount += 1" )

		n.executionCount = 0

		n["task"].execute()
		self.assertEqual( n.executionCount, 1 )

		n["task"].execute()
		self.assertEqual( n.executionCount, 2 )

	def testVariables( self ) :

		n = GafferDispatch.PythonCommand()
		n["variables"].addMember( "testInt", 1 )
		n["variables"].addMember( "testFloat", 2.5 )
		n["variables"].addMember( "testColor", IECore.Color3f( 1, 2, 3 ) )
		n["command"].setValue( inspect.cleandoc(
			"""
			self.testInt = variables["testInt"]
			self.testFloat = variables["testFloat"]
			self.testColor = variables["testColor"]
			"""
		) )

		n["task"].execute()

		self.assertEqual( n.testInt, 1 )
		self.assertEqual( n.testFloat, 2.5 )
		self.assertEqual( n.testColor, IECore.Color3f( 1, 2, 3 ) )

	def testContextAccess( self ) :

		n = GafferDispatch.PythonCommand()
		n["command"].setValue( inspect.cleandoc(
			"""
			self.frame = context.getFrame()
			self.testInt = context['testInt']
			"""
		) )

		with Gaffer.Context() as c :
			c.setFrame( 10 )
			c["testInt"] = 2
			n["task"].execute()

		self.assertEqual( n.frame, 10 )
		self.assertEqual( n.testInt, 2 )

	def testContextAffectsHash( self ) :

		# Hash should be constant if context not
		# accessed.
		n = GafferDispatch.PythonCommand()
		n["command"].setValue( "a = 10")

		with Gaffer.Context() as c :

			h = n["task"].hash()

			c.setTime( 2 )
			self.assertEqual( n["task"].hash(), h )
			c.setTime( 3 )
			self.assertEqual( n["task"].hash(), h )

			c["testInt"] = 10
			self.assertEqual( n["task"].hash(), h )
			c["testInt"] = 20
			self.assertEqual( n["task"].hash(), h )

		# If we access the frame, then we should
		# be sensitive to the time, but not anything else

		n["command"].setValue( "a = context.getFrame()" )

		with Gaffer.Context() as c :

			c.setTime( 1 )
			h1 = n["task"].hash()

			c.setTime( 2 )
			h2 = n["task"].hash()

			c.setTime( 3 )
			h3 = n["task"].hash()

			self.assertNotEqual( h1, h )
			self.assertNotEqual( h2, h1 )
			self.assertNotEqual( h3, h2 )
			self.assertNotEqual( h3, h1 )

			c["testInt"] = 10
			self.assertEqual( n["task"].hash(), h3 )
			c["testInt"] = 20
			self.assertEqual( n["task"].hash(), h3 )

		# The same should apply if we access the frame
		# via subscripting rather than the method.

		n["command"].setValue( "a = context['frame']" )

		with Gaffer.Context() as c :

			c.setTime( 1 )
			h1 = n["task"].hash()

			c.setTime( 2 )
			h2 = n["task"].hash()

			c.setTime( 3 )
			h3 = n["task"].hash()

			self.assertNotEqual( h1, h )
			self.assertNotEqual( h2, h1 )
			self.assertNotEqual( h3, h2 )
			self.assertNotEqual( h3, h1 )

			c["testInt"] = 10
			self.assertEqual( n["task"].hash(), h3 )
			c["testInt"] = 20
			self.assertEqual( n["task"].hash(), h3 )

		# Likewise, accessing other variables should
		# affect the hash.

		n["command"].setValue( "a = context['testInt']" )

		with Gaffer.Context() as c :

			c["testInt"] = 1
			h1 = n["task"].hash()

			c["testInt"] = 2
			h2 = n["task"].hash()

			c["testInt"] = 3
			h3 = n["task"].hash()

			self.assertNotEqual( h2, h1 )
			self.assertNotEqual( h3, h2 )
			self.assertNotEqual( h3, h1 )

			c.setFrame( 2 )
			self.assertEqual( n["task"].hash(), h3 )
			c.setFrame( 3 )
			self.assertEqual( n["task"].hash(), h3 )

	def testRequiresSequenceExecution( self ) :

		n = GafferDispatch.PythonCommand()
		self.assertFalse( n.requiresSequenceExecution() )

		n["sequence"].setValue( True )
		self.assertTrue( n.requiresSequenceExecution() )

	def testFramesNotAvailableInNonSequenceMode( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatch.PythonCommand()
		s["n"]["command"].setValue( "self.frames = frames" )

		d = self.__dispatcher( frameRange = "1-5" )
		self.assertRaisesRegexp( RuntimeError, "NameError: name 'frames' is not defined", d.dispatch, [ s["n"] ] )

		s["n"]["dispatcher"]["batchSize"].setValue( 5 )
		self.assertRaisesRegexp( RuntimeError, "NameError: name 'frames' is not defined", d.dispatch, [ s["n"] ] )

	def testSequenceMode( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatch.PythonCommand()
		s["n"]["sequence"].setValue( True )

		s["n"]["command"].setValue( inspect.cleandoc(
			"""
			self.frames = frames
			try :
				self.numCalls += 1
			except AttributeError :
				self.numCalls = 1
			"""
		) )

		d = self.__dispatcher( frameRange = "1-5" )
		d.dispatch( [ s[ "n" ] ] )

		self.assertEqual( s["n"].frames, [ 1, 2, 3, 4, 5 ] )
		self.assertEqual( s["n"].numCalls, 1 )

	def testCannotAccessVariablesOutsideFrameRange( self ) :

		# We don't want to allow access to variables outside the frame range,
		# because that would mean that PythonCommand.hash() was no longer accurate.

		n = GafferDispatch.PythonCommand()
		n["variables"].addMember( "testInt", 1 )
		n["command"].setValue( inspect.cleandoc(
			"""
			context.setFrame( context.getFrame() + 1 )
			self.testInt = variables["testInt"]
			"""
		) )

		self.assertRaisesRegexp( Exception, "Invalid frame", n.execute )

	def testNonSequenceDispatch( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatch.PythonCommand()
		s["n"]["command"].setValue( inspect.cleandoc(
			"""
			try :
				self.numCalls += 1
			except AttributeError :
				self.numCalls = 1
			"""
		) )

		d = self.__dispatcher()
		d.dispatch( [ s["n"] ] )

		self.assertEqual( s["n"].numCalls, 1 )

	def testStringSubstitutions( self ) :

		s = Gaffer.ScriptNode()
		s["n"] = GafferDispatch.PythonCommand()
		s["n"]["variables"].addMember( "frameString", "###" )
		s["n"]["command"].setValue( 'self.frameString = variables["frameString"]' )

		with Gaffer.Context() as c :
			c.setFrame( 10 )
			s["n"]["task"].execute()

		self.assertEqual( s["n"].frameString, "010" )

	def testComments( self ) :

		c = Gaffer.PythonCommand()
		c["command"].setValue( "self.test = 10 # this is a comment" )

		c["task"].execute()
		self.assertEqual( c.test, 10 )

if __name__ == "__main__":
	unittest.main()
