##########################################################################
#
#  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

import unittest
import fnmatch

import IECore

import Gaffer
import GafferUI
import GafferTest
import GafferUITest

class NoduleTest( GafferUITest.TestCase ) :

	def test( self ) :

		class NoduleTestNode( Gaffer.Node ) :

			def __init__( self ) :

				Gaffer.Node.__init__( self )

				self.addChild(

					Gaffer.IntPlug( "i" )

				)

				self.addChild(

					Gaffer.Plug( "c" )

				)

		IECore.registerRunTimeTyped( NoduleTestNode )

		n = NoduleTestNode()

		ni = GafferUI.Nodule.create( n["i"] )
		nc = GafferUI.Nodule.create( n["c"] )

		self.assertIsInstance( ni, GafferUI.StandardNodule )
		self.assertIsInstance( nc, GafferUI.StandardNodule )

		Gaffer.Metadata.registerValue( NoduleTestNode, "c", "nodule:type", "GafferUI::CompoundNodule" )

		nc = GafferUI.Nodule.create( n["c"] )
		self.assertIsInstance( nc, GafferUI.CompoundNodule )

		class NoduleTestNodeSubclass( NoduleTestNode ) :

			def __init__( self ) :

				NoduleTestNode.__init__( self )

		n2 = NoduleTestNode()
		nc2 = GafferUI.Nodule.create( n2["c"] )
		self.assertIsInstance( nc2, GafferUI.CompoundNodule )

if __name__ == "__main__":
	unittest.main()
