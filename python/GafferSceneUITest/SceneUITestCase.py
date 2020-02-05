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
#      * Neither the name of Cinesite VFX Ltd. nor the names of
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

import math
import unittest

import imath

import IECore
import IECoreGL

import Gaffer
import GafferUI
import GafferScene
import GafferTest

import GafferUITest

class SceneUITestCase( GafferUITest.TestCase ) :

	# Sets up a grid of instances on the XY plane of the supplied source
	# prototype scene. Each instance will have a random rotation applied. The
	# supplied ScenePlug's node needs to be parented to a Gaffer.ScriptNode.
	@staticmethod
	def setupInstancer( prototypeScenePlug, copies = 2500, spacing = 5 ) :

		divisions = math.ceil( math.sqrt( copies ) )
		dimension = divisions * spacing
		assert( divisions > 0 )

		script = prototypeScenePlug.node().ancestor( Gaffer.ScriptNode )
		script["_Plane"] = GafferScene.Plane()
		script["_Instancer"] = GafferScene.Instancer()
		script["_PathFilter"] = GafferScene.PathFilter()
		script["_Instancer"]["in"].setInput( script["_Plane"]["out"] )
		script["_Instancer"]["prototypes"].setInput( prototypeScenePlug )
		script["_Instancer"]["filter"].setInput( script["_PathFilter"]["out"] )
		script["_Plane"]["dimensions"].setValue( imath.V2f( dimension ) )
		script["_Plane"]["divisions"].setValue( imath.V2i( divisions ) )
		script["_PathFilter"]["paths"].setValue( IECore.StringVectorData( [ "/plane" ] ) )
		script["_Transform"] = GafferScene.Transform( "Transform" )
		script["_Transform"]["in"].setInput( script["_Instancer"]["out"] )
		script["_Random"] = Gaffer.Random( "Random" )
		script["_Expression"] = Gaffer.Expression( "Expression" )
		script["_PathFilter1"] = GafferScene.PathFilter( "PathFilter1" )
		script["_Transform"]["filter"].setInput( script["_PathFilter1"]["out"] )
		script["_Random"]["contextEntry"].setValue( 'scene:path' )
		script["_Random"]["baseColor"].setValue( imath.Color3f( 0.5, 0, 0 ) )
		script["_Random"]["hue"].setValue( 1.0 )
		script["_Random"]["saturation"].setValue( 1.0 )
		script["_Random"]["value"].setValue( 1.0 )
		script["_PathFilter1"]["paths"].setValue( IECore.StringVectorData( [ '/*/instances/*/*' ] ) )
		script["_Expression"].setExpression( 'import imath\n\nr = parent["_Random"]["outColor"]\nr *= 360\n\nparent["_Transform"]["transform"]["rotate"] = r', "python" )

		return script["_Transform" ]["out"]

	# Renders the supplied scene a fixed number of times using the
	# GafferTest.TestRunner.PerformanceScipe to record timings.
	def benchmarkRender( self, scenePlug, frames = 100, renderer = "OpenGL" ) :

		w = GafferUI.Window()
		g = GafferUI.GLWidget()
		w.setChild( g )

		w.setVisible( True )

		self.waitForIdle( 1000 )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create(
			renderer,
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Interactive
		)

		controller = GafferScene.RenderController( scenePlug,  Gaffer.Context(), r )
		controller.setMinimumExpansionDepth( 999 )
		controller.update()

		self.waitForIdle( 10000 )

		with GafferTest.TestRunner.PerformanceScope() :
			for i in range( frames )  :
				r.render()

if __name__ == "__main__":
	unittest.main()
