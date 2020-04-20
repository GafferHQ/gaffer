##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import sys
import unittest
import inspect
import subprocess
import types
import shutil
import tempfile
import functools

import IECore

import Gaffer

## A useful base class for creating test cases for nodes.
class TestCase( unittest.TestCase ) :

	def setUp( self ) :

		self.__temporaryDirectory = None

		# Set up a capturing message handler and a cleanup function so
		# we can assert that no warning or error messages are triggered by
		# the tests. If any such messages are actually expected during testing,
		# the relevant tests should use their own CapturingMessageHandler
		# to grab them and then assert that they are as expected.
		self.addCleanup( functools.partial( self.__messageHandlerCleanup, IECore.MessageHandler.getDefaultHandler() ) )
		IECore.MessageHandler.setDefaultHandler( IECore.CapturingMessageHandler() )

		# Clear the cache so that each test starts afresh. This is
		# important for tests which use monitors to assert that specific
		# processes are being invoked as expected.
		Gaffer.ValuePlug.clearCache()

	def tearDown( self ) :

		# Clear any previous exceptions, as they can be holding
		# references to resources we would like to die. This is
		# important for both the UI tests where we wish to check
		# that all widgets have been destroyed, and also for the
		# shutdown tests that are run when the test application
		# exits.

		if "_ExpectedFailure" in str( sys.exc_info()[0] ) :
			# the expected failure exception in the unittest module
			# unhelpfully also hangs on to exceptions, so we remove
			# that before calling exc_clear().
			sys.exc_info()[1].exc_info = ( None, None, None )

		sys.exc_clear()

		if self.__temporaryDirectory is not None :
			shutil.rmtree( self.__temporaryDirectory )

	@staticmethod
	def __messageHandlerCleanup( originalHandler ) :

		mh = IECore.MessageHandler.getDefaultHandler()
		IECore.MessageHandler.setDefaultHandler( originalHandler )

		for message in mh.messages :
			if message.level in  ( mh.Level.Warning, mh.Level.Error ) :
				raise RuntimeError( "Unexpected message : " + mh.levelAsString( message.level ) + " : " + message.context + " : " + message.message )

	## Returns a path to a directory the test may use for temporary
	# storage. This will be cleaned up automatically after the test
	# has been run.
	def temporaryDirectory( self ) :

		if self.__temporaryDirectory is None :
			 self.__temporaryDirectory = tempfile.mkdtemp( prefix = "gafferTest" )

		return self.__temporaryDirectory

	## Attempts to ensure that the hashes for a node
	# are reasonable by jiggling around input values
	# and checking that the hash changes when it should.
	def assertHashesValid( self, node, inputsToIgnore=[], outputsToIgnore=[] ) :

		# find all input ValuePlugs
		inputPlugs = []
		def __walkInputs( parent ) :
			for child in parent.children() :
				if len( child ) :
					__walkInputs( child )
				elif isinstance( child, Gaffer.ValuePlug ) :
					if child not in inputsToIgnore :
						inputPlugs.append( child )
		__walkInputs( node )

		self.assertGreater( len( inputPlugs ), 0 )

		numTests = 0
		for inputPlug in inputPlugs :
			for outputPlug in node.affects( inputPlug ) :

				if outputPlug in outputsToIgnore :
					continue

				hash = outputPlug.hash()

				value = inputPlug.getValue()
				if isinstance( value, float ) :
					increment = 0.1
				elif isinstance( value, int ) :
					increment = 1
				elif isinstance( value, basestring ) :
					increment = "a"
				else :
					# don't know how to deal with this
					# value type.
					continue

				inputPlug.setValue( value + increment )
				if inputPlug.getValue() == value :
					inputPlug.setValue( value - increment )
				if inputPlug.getValue() == value :
					continue

				self.assertNotEqual( outputPlug.hash(), hash, outputPlug.fullName() + " hash not affected by " + inputPlug.fullName() )

				# Set value back to the input value
				# ( The calling code may have set up plugs in a specific state, because some plugs may
				# have no affect in certain states )
				inputPlug.setValue( value )

				numTests += 1

		self.assertGreater( numTests, 0 )

	def assertTypeNamesArePrefixed( self, module, namesToIgnore = () ) :

		incorrectTypeNames = []
		for name in dir( module ) :

			cls = getattr( module, name )
			if not inspect.isclass( cls ) :
				continue

			if issubclass( cls, IECore.RunTimeTyped ) :
				if cls.staticTypeName() in namesToIgnore :
					continue
				if cls.staticTypeName() != module.__name__ + "::" + cls.__name__ :
					incorrectTypeNames.append( cls.staticTypeName() )

		self.assertEqual( incorrectTypeNames, [] )

	def assertDefaultNamesAreCorrect( self, module, namesToIgnore = () ) :

		for name in dir( module ) :

			cls = getattr( module, name )
			if not inspect.isclass( cls ) or not issubclass( cls, Gaffer.GraphComponent ) :
				continue

			try :
				instance = cls()
			except :
				continue

			if instance.getName() in namesToIgnore :
				continue

			self.assertEqual( instance.getName(), cls.staticTypeName().rpartition( ":" )[2] )

	def assertNodesAreDocumented( self, module, additionalTerminalPlugTypes = () ) :

		terminalPlugTypes = (
			Gaffer.ArrayPlug,
			Gaffer.V2fPlug, Gaffer.V3fPlug,
			Gaffer.V2iPlug, Gaffer.V3iPlug,
			Gaffer.Color3fPlug, Gaffer.Color4fPlug,
			Gaffer.SplineffPlug, Gaffer.SplinefColor3fPlug, Gaffer.SplinefColor4fPlug,
			Gaffer.Box2iPlug, Gaffer.Box3iPlug,
			Gaffer.Box2fPlug, Gaffer.Box3fPlug,
			Gaffer.TransformPlug, Gaffer.Transform2DPlug,
			Gaffer.CompoundDataPlug.MemberPlug,
			additionalTerminalPlugTypes
		)

		undocumentedNodes = []
		undocumentedPlugs = []
		for name in dir( module ) :

			cls = getattr( module, name )
			if not inspect.isclass( cls ) or not issubclass( cls, Gaffer.Node ) :
				continue

			if not cls.__module__.startswith( module.__name__ + "." ) :
				# Skip nodes which look like they've been injected from
				# another module by one of the compatibility config files.
				# We use this same test in `DocumentationAlgo.exportNodeReference()`.
				continue

			try :
				node = cls()
			except :
				continue

			description = Gaffer.Metadata.value( node, "description" )
			if (not description) or description.isspace() :
				# No description.
				undocumentedNodes.append( node.getName() )
			else :
				baseNode = None
				try :
					baseNode = cls.__bases__[0]()
				except :
					pass
				if baseNode is not None :
					if description == Gaffer.Metadata.value( baseNode, "description" ) :
						# Same description as base class
						undocumentedNodes.append( node.getName() )

			def checkPlugs( graphComponent ) :

				if isinstance( graphComponent, Gaffer.Plug ) and not graphComponent.getName().startswith( "__" ) :
					description = Gaffer.Metadata.value( graphComponent, "description" )
					if (not description) or description.isspace() :
						undocumentedPlugs.append( graphComponent.fullName() )

				if not isinstance( graphComponent, terminalPlugTypes ) :
					for plug in graphComponent.children( Gaffer.Plug ) :
						checkPlugs( plug )

			checkPlugs( node )

		self.assertEqual( undocumentedNodes, [] )
		self.assertEqual( undocumentedPlugs, [] )

	## We don't serialise plug values when they're at their default, so
	# newly constructed nodes _must_ have all their plugs be at the default value.
	# Use `nodesToIgnore` with caution : the only good reason for using it is to
	# ignore compatibility stubs used to load old nodes and convert them into new
	# ones.
	def assertNodesConstructWithDefaultValues( self, module, nodesToIgnore = None ) :

		for name in dir( module ) :

			cls = getattr( module, name )
			if not inspect.isclass( cls ) or not issubclass( cls, Gaffer.Node ) :
				continue

			if nodesToIgnore is not None and cls in nodesToIgnore :
				continue

			try :
				node = cls()
			except :
				continue

			for plug in node.children( Gaffer.Plug ) :

				if plug.source().direction() != plug.Direction.In or not isinstance( plug, Gaffer.ValuePlug ) :
					continue

				if not plug.getFlags( plug.Flags.Serialisable ) :
					continue

				self.assertTrue( plug.isSetToDefault(), plug.fullName() + " not at default value following construction" )

	def assertModuleDoesNotImportUI( self, moduleName ) :

		script = os.path.join( self.temporaryDirectory(), "test.py" )
		with open( script, "w" ) as f :
			f.write( "import {}\n".format( moduleName ) )
			f.write( "import sys\n" )
			f.write( "assert( 'GafferUI' not in sys.modules )\n" )

		subprocess.check_call( [ "gaffer", "python", script ] )
