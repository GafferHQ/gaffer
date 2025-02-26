##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

import Gaffer
import GafferUI
import GafferUITest

class ExamplesTest( GafferUITest.TestCase ) :

	__testKeys = [
		"__test::one",
		"__test::two",
		"__test::three"
	]

	def setUp( self ) :

		# As startup scripts may register examples, we can't sensibly
		# test the 'default' state of examples without removing them
		# all, which then affects state for other tests and/or
		# creates test ordering challenges, so we choose some select
		# keys that we reserve for our test usage.
		examples = GafferUI.Examples.registeredExamples()
		for key in self.__testKeys :
			self.assertNotIn( key, examples )

	def tearDown( self ) :

		# Make sure we have de-registered test examples even in the
		# event of failure
		for key in self.__testKeys :
			GafferUI.Examples.deregisterExample( key )

	def testExampleRegistration( self ) :

		e1key = self.__testKeys[0]
		e1path = "/a/b/c"
		e1 = { "filePath" : e1path, "description" : "",  "notableNodes" : [] }

		e2key = self.__testKeys[1]
		e2path = "/a/d"
		e2desc = """Here is an example

		with a multiline string description.
		"""
		e2nodes = [ Gaffer.Box ]
		e2 = { "filePath" : e2path, "description" : e2desc,  "notableNodes" : e2nodes }

		GafferUI.Examples.registerExample( e1key, e1path )

		examples = GafferUI.Examples.registeredExamples()
		self.assertEqual( examples[ e1key ], e1 )
		self.assertNotIn( e2key, examples )

		GafferUI.Examples.registerExample( e2key, e2path, description = e2desc, notableNodes = e2nodes )

		examples = GafferUI.Examples.registeredExamples()
		self.assertEqual( examples[ e1key ], e1 )
		self.assertEqual( examples[ e2key ], e2 )

		GafferUI.Examples.deregisterExample( e1key )

		examples = GafferUI.Examples.registeredExamples()
		self.assertNotIn( e1key, examples )
		self.assertEqual( examples[ e2key ], e2 )

		GafferUI.Examples.deregisterExample( e2key )

		examples = GafferUI.Examples.registeredExamples()
		self.assertNotIn( e1key, examples )
		self.assertNotIn( e2key, examples )

	def testExampleFiltering( self ) :

		e1key = self.__testKeys[0]
		e1path = "/nodes/a"
		e1nodes = [ Gaffer.ContextQuery, Gaffer.ContextVariables ]

		e2key = self.__testKeys[1]
		e2path = "/nodes/b"
		e2nodes = [ Gaffer.Box ]

		examples = GafferUI.Examples.registeredExamples()
		self.assertNotIn( e1key, examples )
		self.assertNotIn( e2key, examples )

		GafferUI.Examples.registerExample( e1key, e1path, notableNodes = e1nodes )
		GafferUI.Examples.registerExample( e2key, e2path, notableNodes = e2nodes )

		examples = GafferUI.Examples.registeredExamples()
		self.assertIn( e1key, examples )
		self.assertIn( e2key, examples )

		examples = GafferUI.Examples.registeredExamples( node = Gaffer.Box )
		self.assertNotIn( e1key, examples )
		self.assertIn( e2key, examples )

		examples = GafferUI.Examples.registeredExamples( node = Gaffer.ContextQuery )
		self.assertIn( e1key, examples )
		self.assertNotIn( e2key, examples )

		examples = GafferUI.Examples.registeredExamples( node = Gaffer.ContextVariables )
		self.assertIn( e1key, examples )
		self.assertNotIn( e2key, examples )

	def testExampleOrdering( self ) :

		examples = GafferUI.Examples.registeredExamples()
		for k in self.__testKeys :
			self.assertNotIn( k, examples )

		# As we don't know what other examples may be already registered
		# as we assure order, we just work out where in the list anything
		# we register here will appear and ignore anything before that...

		lastExistingExampleIndex = len(examples)
		lastExistingBoxExampleIndex = len(GafferUI.Examples.registeredExamples( node = Gaffer.Box ))

		for k in self.__testKeys :
			GafferUI.Examples.registerExample( k, "", notableNodes = [ Gaffer.Box ] )

		examples = GafferUI.Examples.registeredExamples()
		newKeys = list( examples.keys() )[ lastExistingExampleIndex : ]
		self.assertEqual( newKeys, self.__testKeys )

		boxExamples = GafferUI.Examples.registeredExamples( node = Gaffer.Box )
		newBoxKeys = list( boxExamples.keys() )[ lastExistingBoxExampleIndex : ]
		self.assertEqual( newBoxKeys, self.__testKeys )

		for k in self.__testKeys :
			GafferUI.Examples.deregisterExample( k )

		examples = GafferUI.Examples.registeredExamples()
		for k in self.__testKeys :
			self.assertNotIn( k, examples )

		# Register in reverse order

		for k in self.__testKeys[ : : -1 ] :
			GafferUI.Examples.registerExample( k, "", notableNodes = [ Gaffer.Box ] )

		examples = GafferUI.Examples.registeredExamples()
		newKeys = list( examples.keys() )[ lastExistingExampleIndex : ]
		self.assertEqual( newKeys, self.__testKeys[ : : -1 ] )

		boxExamples = GafferUI.Examples.registeredExamples( node = Gaffer.Box )
		newBoxKeys = list( boxExamples.keys() )[ lastExistingBoxExampleIndex : ]
		self.assertEqual( newBoxKeys, self.__testKeys[ : : -1 ] )

	def testExampleFilesExist( self ) :

		self.assertExampleFilesExist()

	def testExampleFilesDontReferenceUnstablePaths( self ) :

		self.assertExampleFilesDontReferenceUnstablePaths()

if __name__ == "__main__":
	unittest.main()
