##########################################################################
#
#  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

import IECoreScene

import GafferScene
import GafferSceneTest
import GafferRenderMan

class StylizedAOVAdaptorTest( GafferSceneTest.SceneTestCase ) :

	def testNoOp( self ) :

		scene = GafferScene.StandardOptions()
		scene["options"]["renderCamera"]["enabled"].setValue( True )

		adaptor = GafferRenderMan._StylizedAOVAdaptor()
		adaptor["in"].setInput( scene["out"] )

		self.assertEqual( adaptor["out"].globals(), adaptor["in"].globals() )

	def testAOVs( self ) :

		toonFilter = GafferRenderMan.RenderManShader()
		toonFilter.loadShader( "PxrStylizedToon" )

		displayFilter = GafferRenderMan.RenderManDisplayFilter()
		displayFilter["displayFilter"].setInput( toonFilter["out"] )

		adaptor = GafferRenderMan._StylizedAOVAdaptor()
		adaptor["in"].setInput( displayFilter["out"] )

		aovData = {
			output.getData()
			for name, output in
			adaptor["out"].globals().items()
			if name.startswith( "output:" )
		}

		self.assertEqual(
			aovData,
			{
				"lpe nothruput;noinfinitecheck;noclamp;unoccluded;overwrite;C<.S'passthru'>*((U2L)|O)",
				"color NPRlineOutAlpha", "color NPRlineOut", "color P", "color Nn", "color NPRlineWidth",
				"color NPRalbedo", "color NPRhatchOut", "color NPRlineNZ", "color NPRtextureCoords",
				"color NPRoutline", "color NPRtoonOut", "color NPRcurvature",
				"color NPRNtriplanar", "color NPRlineAlbedo", "color NPRlineCamdist", "color NPRPtriplanar",
				"color NPRmask", "color NPRdistort", "lpe shadows;C[DS]+<L.>", "color NPRsections",
				"float sampleCount", "lpe C(D[DS]*[LO])|[LO]", "lpe C<RS>[<L.>O]",
			}
		)

	def testKeepsExistingAOVs( self ) :

		toonFilter = GafferRenderMan.RenderManShader()
		toonFilter.loadShader( "PxrStylizedToon" )

		displayFilter = GafferRenderMan.RenderManDisplayFilter()
		displayFilter["displayFilter"].setInput( toonFilter["out"] )

		outputs = GafferScene.Outputs()
		outputs["in"].setInput( displayFilter["out"] )

		outputs.addOutput(
			"Test",
			IECoreScene.Output(
				"test.exr",
				"exr",
				"color NPRhatchOut"
			)
		)

		adaptor = GafferRenderMan._StylizedAOVAdaptor()
		adaptor["in"].setInput( outputs["out"] )

		# Check that our own AOV has been retained even though it
		# uses the same data as one the adaptor wants to create.
		self.assertEqual( adaptor["out"].globals()["output:Test"], adaptor["in"].globals()["output:Test"] )
