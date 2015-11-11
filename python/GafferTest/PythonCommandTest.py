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

class PythonCommandTest( GafferTest.TestCase ) :

	def testSelf( self ) :

		n = Gaffer.PythonCommand()
		n["command"].setValue( "self.executionCount += 1" )

		n.executionCount = 0

		n.execute()
		self.assertEqual( n.executionCount, 1 )

		n.execute()
		self.assertEqual( n.executionCount, 2 )

	def testVariables( self ) :

		n = Gaffer.PythonCommand()
		n["variables"].addMember( "testInt", 1 )
		n["variables"].addMember( "testFloat", 2.5 )
		n["variables"].addMember( "testColor", IECore.Color3f( 1, 2, 3 ) )
		n["command"].setValue( inspect.cleandoc(
			"""
			self.testInt = testInt
			self.testFloat = testFloat
			self.testColor = testColor
			"""
		) )

		n.execute()

		self.assertEqual( n.testInt, 1 )
		self.assertEqual( n.testFloat, 2.5 )
		self.assertEqual( n.testColor, IECore.Color3f( 1, 2, 3 ) )

	def testContextAccess( self ) :

		n = Gaffer.PythonCommand()
		n["command"].setValue( inspect.cleandoc(
			"""
			self.frame = context.getFrame()
			self.testInt = context['testInt']
			"""
		) )

		with Gaffer.Context() as c :
			c.setFrame( 10 )
			c["testInt"] = 2
			n.execute()

		self.assertEqual( n.frame, 10 )
		self.assertEqual( n.testInt, 2 )

	def testContextAffectsHash( self ) :

		# Hash should be constant if context not
		# accessed.
		n = Gaffer.PythonCommand()
		n["command"].setValue( "a = 10")

		with Gaffer.Context() as c :

			h = n.hash( c )

			c.setTime( 2 )
			self.assertEqual( n.hash( c ), h )
			c.setTime( 3 )
			self.assertEqual( n.hash( c ), h )

			c["testInt"] = 10
			self.assertEqual( n.hash( c ), h )
			c["testInt"] = 20
			self.assertEqual( n.hash( c ), h )

		# If we access the frame, then we should
		# be sensitive to the time, but not anything else

		n["command"].setValue( "a = context.getFrame()" )

		with Gaffer.Context() as c :

			c.setTime( 1 )
			h1 = n.hash( c )

			c.setTime( 2 )
			h2 = n.hash( c )

			c.setTime( 3 )
			h3 = n.hash( c )

			self.assertNotEqual( h1, h )
			self.assertNotEqual( h2, h1 )
			self.assertNotEqual( h3, h2 )
			self.assertNotEqual( h3, h1 )

			c["testInt"] = 10
			self.assertEqual( n.hash( c ), h3 )
			c["testInt"] = 20
			self.assertEqual( n.hash( c ), h3 )

		# The same should apply if we access the frame
		# via subscripting rather than the method.

		n["command"].setValue( "a = context['frame']" )

		with Gaffer.Context() as c :

			c.setTime( 1 )
			h1 = n.hash( c )

			c.setTime( 2 )
			h2 = n.hash( c )

			c.setTime( 3 )
			h3 = n.hash( c )

			self.assertNotEqual( h1, h )
			self.assertNotEqual( h2, h1 )
			self.assertNotEqual( h3, h2 )
			self.assertNotEqual( h3, h1 )

			c["testInt"] = 10
			self.assertEqual( n.hash( c ), h3 )
			c["testInt"] = 20
			self.assertEqual( n.hash( c ), h3 )

		# Likewise, accessing other variables should
		# affect the hash.

		n["command"].setValue( "a = context['testInt']" )

		with Gaffer.Context() as c :

			c["testInt"] = 1
			h1 = n.hash( c )

			c["testInt"] = 2
			h2 = n.hash( c )

			c["testInt"] = 3
			h3 = n.hash( c )

			self.assertNotEqual( h2, h1 )
			self.assertNotEqual( h3, h2 )
			self.assertNotEqual( h3, h1 )

			c.setFrame( 2 )
			self.assertEqual( n.hash( c ), h3 )
			c.setFrame( 3 )
			self.assertEqual( n.hash( c ), h3 )

if __name__ == "__main__":
	unittest.main()

