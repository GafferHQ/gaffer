##########################################################################
#
#  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class ViewTest( GafferUITest.TestCase ) :

	def setUp( self ) :

		GafferUITest.TestCase.setUp( self )

		self.originalDisplayTransforms = GafferUI.View.DisplayTransform.registeredDisplayTransforms()

	def tearDown( self ) :

		GafferUITest.TestCase.tearDown( self )

		for name in GafferUI.View.DisplayTransform.registeredDisplayTransforms() :
			if name not in self.originalDisplayTransforms :
				GafferUI.View.DisplayTransform.deregisterDisplayTransform( name )

	class MyView( GafferUI.View ) :

		def __init__( self, viewedPlug = None ) :

			GafferUI.View.__init__( self, "MyView", Gaffer.IntPlug( "in" ) )

			self["in"].setInput( viewedPlug )

	IECore.registerRunTimeTyped( MyView, typeName = "GafferUITest::MyView" )

	def testFactory( self ) :

		node = GafferTest.AddNode()
		self.assertTrue( GafferUI.View.create( node["sum"] ) is None )

		# check that we can make our own view and register it for the node

		GafferUI.View.registerView( GafferTest.AddNode, "sum", self.MyView )

		view = GafferUI.View.create( node["sum"] )
		self.assertTrue( isinstance( view, self.MyView ) )
		self.assertTrue( view["in"].getInput().isSame( node["sum"] ) )

		# and check that that registration leaves other nodes alone

		n = Gaffer.Node()
		n["sum"] = Gaffer.IntPlug( direction = Gaffer.Plug.Direction.Out )

		self.assertTrue( GafferUI.View.create( n["sum"] ) is None )

	def testEditScope( self ) :

		view = self.MyView()

		addNode = GafferTest.AddNode()
		editScope = Gaffer.EditScope()
		editScope.setup( view["in"] )

		self.assertEqual( view.editScope(), None )
		view["editScope"].setInput( editScope["out"] )
		self.assertEqual( view.editScope(), editScope )

	def testDisplayTransformRegistrations( self ) :

		def dummyTransform() :
			# OK, because we're not expecting this to be called.
			raise NotImplementedError

		# Register some transforms, and check they are returned in the order
		# we registered them.

		newNames = [ "z", "a", "c", "b" ]
		for name in newNames :
			GafferUI.View.DisplayTransform.registerDisplayTransform( name, dummyTransform )

		self.assertEqual(
			GafferUI.View.DisplayTransform.registeredDisplayTransforms(),
			self.originalDisplayTransforms + newNames
		)

		# Deregister them, and check we're back where we started.

		for name in newNames :
			GafferUI.View.DisplayTransform.deregisterDisplayTransform( name )

		self.assertEqual(
			GafferUI.View.DisplayTransform.registeredDisplayTransforms(),
			self.originalDisplayTransforms
		)

		# Repeat, this time in reverse order, in case the original ordering matched by fluke.

		for name in reversed( newNames  ) :
			GafferUI.View.DisplayTransform.registerDisplayTransform( name, dummyTransform )

		self.assertEqual(
			GafferUI.View.DisplayTransform.registeredDisplayTransforms(),
			self.originalDisplayTransforms + list( reversed( newNames ) )
		)

		# No need to clean up - `tearDown()` will do that for us.

if __name__ == "__main__":
	unittest.main()
