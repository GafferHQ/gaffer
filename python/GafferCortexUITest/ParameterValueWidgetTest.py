##########################################################################
#
#  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

import unittest
import imath

import IECore

import Gaffer
import GafferUI
import GafferUITest
import GafferCortex
import GafferCortexUI

class ParameterValueWidgetTest( GafferUITest.TestCase ) :

	def testCreate( self ) :

		n = Gaffer.Node()
		p = IECore.StringParameter( "s", "", "" )

		h = GafferCortex.ParameterHandler.create( p )
		h.setupPlug( n )

		w = GafferCortexUI.ParameterValueWidget.create( h )
		self.assertIsInstance( w, GafferCortexUI.StringParameterValueWidget )

	def testCreateWithUIHint( self ) :

		class CustomParameterValueWidget( GafferCortexUI.ParameterValueWidget ) :

			def __init__( self, parameterHandler, **kw ) :

				GafferCortexUI.ParameterValueWidget.__init__( self, GafferUI.StringPlugValueWidget( parameterHandler.plug() ), parameterHandler )

		GafferCortexUI.ParameterValueWidget.registerType( IECore.StringParameter.staticTypeId(), CustomParameterValueWidget, "CustomUI" )

		n = Gaffer.Node()
		p = IECore.StringParameter( "s", "", "" )

		h = GafferCortex.ParameterHandler.create( p )
		h.setupPlug( n )

		w = GafferCortexUI.ParameterValueWidget.create( h )
		self.assertIsInstance( w, GafferCortexUI.StringParameterValueWidget )

		p.userData()["UI"] = IECore.CompoundObject( { "typeHint" : IECore.StringData( "CustomUI" ) } )
		w = GafferCortexUI.ParameterValueWidget.create( h )
		self.assertIsInstance( w, CustomParameterValueWidget )

	def testCreateAlwaysReturnsParameterValueWidgetInstance( self ) :

		n = Gaffer.Node()
		p = IECore.V2fParameter( "v", "", imath.V2f( 1 ) )

		h = GafferCortex.ParameterHandler.create( p )
		h.setupPlug( n )

		w = GafferCortexUI.ParameterValueWidget.create( h )
		self.assertIsInstance( w, GafferCortexUI.ParameterValueWidget )

if __name__ == "__main__":
	unittest.main()
