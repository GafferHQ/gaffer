##########################################################################
#
#  Copyright (c) 2012, John Haddon. All rights reserved.
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
import GafferUI
import GafferTest

class PlugValueWidgetTest( unittest.TestCase ) :

	def testContext( self ) :

		s = Gaffer.ScriptNode()
		s["m"] = GafferTest.MultiplyNode()
		s["e"] = Gaffer.Expression()
		s["e"]["engine"].setValue( "python" )
		s["e"]["expression"].setValue( "parent[\"m\"][\"op1\"] = int( context[\"frame\"] )" )

		w = GafferUI.NumericPlugValueWidget( s["m"]["op1"] )
		self.failUnless( w.getContext().isSame( s.context() ) )

		s.context().setFrame( 10 )
		self.assertEqual( w.numericWidget().getValue(), 10 )

		context = Gaffer.Context()
		context.setFrame( 20 )
		w.setContext( context )
		self.failUnless( w.getContext().isSame( context ) )
		self.assertEqual( w.numericWidget().getValue(), 20 )

	def testDisableCreationForSpecificTypes( self ) :

		class ValueWidgetTestPlug( Gaffer.CompoundPlug ) :

			def __init__( self, name="TestPlug", direction=Gaffer.Plug.Direction.In, flags=Gaffer.Plug.Flags.Default ) :

				Gaffer.CompoundPlug.__init__( self, name, direction, flags )

		IECore.registerRunTimeTyped( ValueWidgetTestPlug )

		n = Gaffer.Node()
		n["p"] = ValueWidgetTestPlug()

		w = GafferUI.PlugValueWidget.create( n["p"] )
		self.assertTrue( isinstance( w, GafferUI.CompoundPlugValueWidget ) )

		GafferUI.PlugValueWidget.registerType( ValueWidgetTestPlug, None )

		w = GafferUI.PlugValueWidget.create( n["p"] )
		self.assertEqual( w, None )

if __name__ == "__main__":
	unittest.main()

