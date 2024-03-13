##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
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

import GafferTest
import GafferScene

class RendererTest( GafferTest.TestCase ) :

	def testReentrantPythonFactory( self ) :

		# Check that we can register a renderer alias from Python, by forwarding to some
		# other creator that is registered dynamically by the first one. We can use this
		# to implement delayed loading of the true renderer modules.

		self.assertNotIn( "Test", GafferScene.Private.IECoreScenePreview.Renderer.types() )

		self.addCleanup(
			GafferScene.Private.IECoreScenePreview.Renderer.deregisterType, "Test"
		)

		def creator1( renderType, fileName, messageHandler ) :

			GafferScene.Private.IECoreScenePreview.Renderer.registerType( "Test", creator2 )
			return GafferScene.Private.IECoreScenePreview.Renderer.create( "Test", renderType, fileName, messageHandler )

		def creator2( renderType, fileName, messageHandler ) :

			return GafferScene.Private.IECoreScenePreview.Renderer.create( "Capturing", renderType, fileName, messageHandler  )

		GafferScene.Private.IECoreScenePreview.Renderer.registerType( "Test", creator1 )
		self.assertIn( "Test", GafferScene.Private.IECoreScenePreview.Renderer.types() )

		self.assertIsInstance(
			GafferScene.Private.IECoreScenePreview.Renderer.create( "Test", GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive ),
			GafferScene.Private.IECoreScenePreview.CapturingRenderer
		)

		self.assertIn( "Test", GafferScene.Private.IECoreScenePreview.Renderer.types() )

		self.assertIsInstance(
			GafferScene.Private.IECoreScenePreview.Renderer.create( "Test", GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive ),
			GafferScene.Private.IECoreScenePreview.CapturingRenderer
		)

if __name__ == "__main__":
	unittest.main()
