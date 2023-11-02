##########################################################################
#
#  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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
import GafferTest
import GafferUI
import GafferUITest

class BoxIOUITest( GafferUITest.TestCase ) :

	def testNoRedundantMetadata( self ) :

		box = Gaffer.Box()

		box["add"] = GafferTest.AddNode()

		box["switch"] = Gaffer.Switch()
		box["switch"].setup( box["add"]["sum"] )
		box["switch"]["in"][0].setInput( box["add"]["sum"] )

		Gaffer.PlugAlgo.promote( box["switch"]["in"][1] )
		Gaffer.BoxIO.insert( box )
		self.assertEqual( Gaffer.Metadata.registeredValues( box["BoxIn"]["__in"], Gaffer.Metadata.RegistrationTypes.Instance ), [] )

		oldColor = GafferUI.Metadata.value( box["add"]["op1"], "nodule:color", Gaffer.Metadata.RegistrationTypes.TypeId )
		self.addCleanup( Gaffer.Metadata.registerValue, Gaffer.IntPlug, "nodule:color", oldColor )

		newColor = imath.Color3f( 1, 0, 0 )
		Gaffer.Metadata.registerValue( Gaffer.IntPlug, "nodule:color", newColor )
		self.assertEqual( Gaffer.Metadata.value( box["add"]["op1"], "nodule:color" ), newColor )

		promoted = Gaffer.BoxIO.promote( box["switch"]["out"] )
		self.assertEqual(
			set( Gaffer.Metadata.registeredValues( box["BoxOut"]["__out"], Gaffer.Metadata.RegistrationTypes.Instance ) ),
			# We allow `description` and `plugValueWidget:type` because we do want those to be transferred through to
			# the promoted plug, even though `description` doesn't always make sense in the new context. But we definitely
			# don't want `nodule:color` to be promoted to instance metadata, because it is inherited from the type anyway.
			{ "description", "plugValueWidget:type" }
		)
		self.assertEqual( Gaffer.Metadata.value( promoted, "nodule:color" ), newColor )
		self.assertEqual( Gaffer.Metadata.value( box["BoxOut"]["__out"], "nodule:color" ), newColor )

if __name__ == "__main__":
	unittest.main()
