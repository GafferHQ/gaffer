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

import IECore

import Gaffer
import GafferTest
import GafferUI
import GafferUITest

class PresetsPlugValueWidgetTest( GafferUITest.TestCase ) :

	def testContextDependentPresets( self ) :

		s = Gaffer.ScriptNode()

		s["variables"].addChild(
			Gaffer.NameValuePlug( "testPresetName", IECore.StringData( "presetA" ), "testPresetName" )
		)

		s["s"] = GafferTest.StringInOutNode()
		s["e"] = Gaffer.Expression()
		s["e"].setExpression( 'parent["s"]["in"] = context.get( "testPresetName", "none" )' )

		s["m"] = GafferTest.MultiplyNode()

		values = { "presetA" : 3, "presetB" : 4 }

		def presetNames( plug ) :
			return IECore.StringVectorData( [ s["s"]["out"].getValue() ] )

		def presetValues( plug ) :
			return IECore.IntVectorData( [ values[ s["s"]["out"].getValue() ] ] )

		Gaffer.Metadata.registerValue( GafferTest.MultiplyNode, "op1", "presetNames", presetNames )
		Gaffer.Metadata.registerValue( GafferTest.MultiplyNode, "op1", "presetValues", presetValues )

		w = GafferUI.PresetsPlugValueWidget( s["m"]["op1"] )

		self.assertEqual( [ "/presetA" ], [ i[0] for i in w._PresetsPlugValueWidget__menuDefinition().items() ] )
		w._PresetsPlugValueWidget__applyPreset( None, "presetA" )
		self.assertEqual( s["m"]["op1"].getValue(), 3 )

		s["variables"]["testPresetName"]["value"].setValue( "presetB" )

		self.assertEqual( [ "/presetB" ], [ i[0] for i in w._PresetsPlugValueWidget__menuDefinition().items() ] )
		w._PresetsPlugValueWidget__applyPreset( None, "presetB" )
		self.assertEqual( s["m"]["op1"].getValue(), 4 )

	def tearDown( self ) :

		GafferUITest.TestCase.tearDown( self )

		Gaffer.Metadata.deregisterValue( GafferTest.MultiplyNode, "op1", "presetNames" )
		Gaffer.Metadata.deregisterValue( GafferTest.MultiplyNode, "op1", "presetValues" )

if __name__ == "__main__":
	unittest.main()
