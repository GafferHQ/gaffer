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

	def testFactory( self ) :

		sphere = GafferTest.SphereNode()
		view = GafferUI.View.create( sphere["out"] )

		self.assertTrue( isinstance( view, GafferUI.ObjectView ) )
		self.assertTrue( view["in"].getInput().isSame( sphere["out"] ) )

		# check that we can make our own view and register it for the node

		class MyView( GafferUI.ObjectView ) :

			def __init__( self, viewedPlug = None ) :

				GafferUI.ObjectView.__init__( self )

				self["in"].setInput( viewedPlug )

		GafferUI.View.registerView( GafferTest.SphereNode, "out", MyView )

		view = GafferUI.View.create( sphere["out"] )
		self.assertTrue( isinstance( view, MyView ) )
		self.assertTrue( view["in"].getInput().isSame( sphere["out"] ) )

		# and check that that registration leaves other nodes alone

		n = Gaffer.Node()
		n["out"] = Gaffer.ObjectPlug( direction = Gaffer.Plug.Direction.Out, defaultValue = IECore.NullObject.defaultNullObject() )

		view = GafferUI.View.create( n["out"] )

		self.assertTrue( isinstance( view, GafferUI.ObjectView ) )
		self.assertTrue( view["in"].getInput().isSame( n["out"] ) )

if __name__ == "__main__":
	unittest.main()

