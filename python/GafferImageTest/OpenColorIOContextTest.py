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

import IECore

import Gaffer
import GafferImage
import GafferImageTest

class OpenColorIOContextTest( GafferImageTest.ImageTestCase ) :

	def test( self ) :

		metadata = GafferImage.ImageMetadata()
		metadata["metadata"].addChild(
			Gaffer.NameValuePlug(
				"capturedContext",
				"config=${ocio:config} "
				"testA=${ocio:stringVar:testA} "
				"testB=${ocio:stringVar:testB} "
				"testC=${ocio:stringVar:testC}"
			)
		)

		ocioContext = GafferImage.OpenColorIOContext()
		ocioContext.setup( metadata["out"] )
		ocioContext["in"].setInput( metadata["out"] )

		self.assertEqual(
			ocioContext["out"].metadata()["capturedContext"].value,
			"config= testA= testB= testC="
		)

		studioConfig = "ocio://studio-config-v1.0.0_aces-v1.3_ocio-v2.1"
		ocioContext["config"]["value"].setValue( studioConfig )
		self.assertEqual(
			ocioContext["out"].metadata()["capturedContext"].value,
			"config= testA= testB= testC="
		)

		ocioContext["config"]["enabled"].setValue( True )
		self.assertEqual(
			ocioContext["out"].metadata()["capturedContext"].value,
			f"config={studioConfig} testA= testB= testC="
		)

		ocioContext["extraVariables"].setValue(
			IECore.CompoundData( {
				"testB" : "extraB",
				"testC" : "extraC"
			} )
		)

		self.assertEqual(
			ocioContext["out"].metadata()["capturedContext"].value,
			f"config={studioConfig} testA= testB=extraB testC=extraC"
		)

		ocioContext["variables"].addChild( Gaffer.NameValuePlug( "testA", "a", defaultEnabled = True ) )
		ocioContext["variables"].addChild( Gaffer.NameValuePlug( "testB", "b", defaultEnabled = True ) )

		self.assertEqual(
			ocioContext["out"].metadata()["capturedContext"].value,
			f"config={studioConfig} testA=a testB=b testC=extraC"
		)

		ocioContext["variables"][0]["enabled"].setValue( False )

		self.assertEqual(
			ocioContext["out"].metadata()["capturedContext"].value,
			f"config={studioConfig} testA= testB=b testC=extraC"
		)

if __name__ == "__main__":
	unittest.main()
