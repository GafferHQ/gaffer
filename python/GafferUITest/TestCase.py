##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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
import functools
import unittest
import inspect
import weakref

from Qt import QtCore
from Qt import QtCompat

import IECore

import Gaffer
import GafferTest
import GafferUI

## A useful base class for creating test cases for the ui.
class TestCase( GafferTest.TestCase ) :

	def setUp( self ) :

		GafferTest.TestCase.setUp( self )

		# Forward Qt messages to the IECore message handler.
		# This causes them to be reported as errors by our
		# base class.

		def messageHandler( type, context, message ) :

			IECore.msg(
				{
					QtCore.QtMsgType.QtInfoMsg : IECore.Msg.Level.Info,
					QtCore.QtMsgType.QtDebugMsg : IECore.Msg.Level.Debug,
				}.get( type, IECore.Msg.Level.Error ),
				"Qt",
				message
			)

		QtCompat.qInstallMessageHandler( messageHandler )
		self.addCleanup( functools.partial( QtCompat.qInstallMessageHandler, None ) )

	def tearDown( self ) :

		GafferTest.TestCase.tearDown( self )

		# Here we check that there are no Widget instances knocking
		# around after each test has run. this provides good coverage
		# for the Widget lifetime problems that are all too easy to
		# create. Our base class has already taken care of clearing
		# any exceptions which might be inadvertently holding
		# references to widget instances.

		widgetInstances = self.__widgetInstances()
		self.assertEqual( widgetInstances, [] )

	def waitForIdle( self, count = 1 ) :

		self.__idleCount = 0
		def f() :

			self.__idleCount += 1

			if self.__idleCount >= count :
				GafferUI.EventLoop.mainEventLoop().stop()
				return False

			return True

		GafferUI.EventLoop.addIdleCallback( f )
		GafferUI.EventLoop.mainEventLoop().start()

	def assertExampleFilesExist( self ) :

		examples = GafferUI.Examples.registeredExamples()
		for e in examples.values():
			self.assertIsNotNone( e['filePath'] )
			self.assertNotEqual( e['filePath'], "" )
			expanded = os.path.expandvars( e['filePath'] )
			self.assertTrue( os.path.exists( expanded ), "%s does not exist" % expanded )

	def assertExampleFilesDontReferenceUnstablePaths( self ) :

		forbidden = (
			"${script:name}",
			"/home/"
		)

		safePlugNames = (
			"title",
			"description"
		)

		examples = GafferUI.Examples.registeredExamples()
		for e in examples.values():
			path = os.path.expandvars( e['filePath'] )
			with open( path, 'r' ) as example :
				for line in example :
					# If the line contains a set for one of our safe plugs, don't check
					if any( '["%s"].setValue(' % plug in line for plug in safePlugNames ) :
						continue
					for phrase in forbidden :
						self.assertFalse( phrase in line, "Example %s references unstable '%s':\n%s" % ( e['filePath'], phrase, line ) )

	def assertNodeUIsHaveExpectedLifetime( self, module ) :

		for name in dir( module ) :

			cls = getattr( module, name )
			if not inspect.isclass( cls ) or not issubclass( cls, Gaffer.Node ) :
				continue

			script = Gaffer.ScriptNode()

			try :
				script["node"] = cls()
			except :
				continue

			with GafferUI.Window() as window :
				nodeUI = GafferUI.NodeUI.create( script["node"] )
			window.setVisible( True )
			self.waitForIdle( 10000 )

			weakNodeUI = weakref.ref( nodeUI )
			weakScript = weakref.ref( script )

			del window, nodeUI
			self.assertIsNone( weakNodeUI() )

			del script
			self.assertIsNone( weakScript() )

	@staticmethod
	def __widgetInstances() :

		result = []
		# yes, this is accessing Widget internals. we could add a public method
		# to the widget to expose this information, but i'd rather not add yet
		# more methods if we can avoid it.
		for w in GafferUI.Widget._Widget__qtWidgetOwners.values() :
			if w() is not None :
				result.append( w() )

		return result
