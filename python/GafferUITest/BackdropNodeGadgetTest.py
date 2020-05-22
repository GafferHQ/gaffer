##########################################################################
#
#  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

import imath

import Gaffer
import GafferUI
import GafferUITest

class BackdropNodeGadgetTest( GafferUITest.TestCase ) :

	def testNoExtraPlugsAfterCopyPaste( self ) :

		script = Gaffer.ScriptNode()
		script["b"] = Gaffer.Backdrop()
		script["n"] = Gaffer.Node()

		graphGadget = GafferUI.GraphGadget( script )
		backdropGadget = graphGadget.nodeGadget( script["b"] )
		self.assertIsInstance( backdropGadget, GafferUI.BackdropNodeGadget )
		backdropGadget.frame( [ script["n"] ] )

		script.execute( script.serialise( filter = Gaffer.StandardSet( [ script["b"] ] ) ) )
		self.assertEqual( script["b1"].keys(), script["b"].keys() )

	def testBoundAccessors( self ) :

		b = Gaffer.Backdrop()
		g = GafferUI.BackdropNodeGadget( b )
		self.assertEqual( g.getBound(), imath.Box2f( imath.V2f( -10 ), imath.V2f( 10 ) ) )

		g.setBound( imath.Box2f( imath.V2f( -1, -2 ), imath.V2f( 3, 4 ) ) )
		self.assertEqual(
			g.getBound(),
			imath.Box2f( imath.V2f( -1, -2 ), imath.V2f( 3, 4 ) )
		)

if __name__ == "__main__":
	unittest.main()
