##########################################################################
#
#  Copyright (c) 2011, John Haddon. All rights reserved.
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

import Gaffer
import GafferUI
import GafferUITest

class SplinePlugGadgetTest( GafferUITest.TestCase ) :

	def testSelection( self ) :

		g = GafferUI.SplinePlugGadget()

		n = Gaffer.Node()
		p = Gaffer.SplineffPlug()
		n.addChild( p )

		p1 = p.pointPlug( p.addPoint() )
		p2 = p.pointPlug( p.addPoint() )

		self.failIf( p1 in g.selection() )
		self.failIf( p2 in g.selection() )

		# shouldn't be able to add a point to the selection if
		# the spline isn't being edited
		self.assertRaises( Exception, g.selection().add, p1 )

		g.splines().add( p )

		g.selection().add( p1 )
		self.failUnless( p1 in g.selection() )

		g.selection().add( p2 )
		self.failUnless( p2 in g.selection() )

		p.removePoint( 1 )
		self.failIf( p2 in g.selection() )

		g.splines().remove( p )

		self.failIf( p1 in g.selection() )

if __name__ == "__main__" :
	unittest.main()
