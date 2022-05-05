##########################################################################
#
#  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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
import IECoreScene

import GafferTest
import GafferScene

class CompoundRendererTest( GafferTest.TestCase ) :

	def test( self ) :

		renderers = [
			GafferScene.Private.IECoreScenePreview.Renderer.create( "Capturing" ),
			GafferScene.Private.IECoreScenePreview.Renderer.create( "Capturing" )
		]
		compoundRenderer = GafferScene.Private.IECoreScenePreview.CompoundRenderer( renderers )

		# Object creation

		coreAttributes1 = IECore.CompoundObject( { "x" : IECore.IntData( 10 ) } )
		attributes1 = compoundRenderer.attributes( coreAttributes1 )

		for r in renderers :
			self.assertIsNone( r.capturedObject( "o" ) )

		compoundObject = compoundRenderer.object( "o", IECoreScene.SpherePrimitive(), attributes1 )

		for r in renderers :
			o = r.capturedObject( "o" )
			self.assertIsNotNone( o )
			self.assertEqual( o.capturedSamples(), [ IECoreScene.SpherePrimitive() ] )
			self.assertEqual( o.capturedSampleTimes(), [] )
			self.assertEqual( o.capturedAttributes().attributes(), coreAttributes1 )
			self.assertEqual( o.id(), 0 )

		compoundObject.assignID( 1 )
		for r in renderers :
			o = r.capturedObject( "o" )
			self.assertEqual( o.id(), 1 )

		# Attribute edits

		coreAttributes2 = IECore.CompoundObject( { "x" : IECore.IntData( 20 ) } )
		attributes2 = compoundRenderer.attributes( coreAttributes2 )
		compoundObject.attributes( attributes2 )

		for r in renderers :
			o = r.capturedObject( "o" )
			self.assertEqual( o.capturedAttributes().attributes(), coreAttributes2 )

		# Transform edits

		transform = imath.M44f().translate( imath.V3f( 1, 2, 3 ) )
		compoundObject.transform( transform )

		for r in renderers :
			o = r.capturedObject( "o" )
			self.assertEqual( o.capturedTransforms(), [ transform ] )
			self.assertEqual( o.capturedTransformTimes(), [] )

		# Light linking

		light1 = compoundRenderer.light( "l1", IECore.NullObject(), attributes1 )
		light2 = compoundRenderer.light( "l2", IECore.NullObject(), attributes1 )

		compoundObject.link( "lights", { light1 } )

		for r in renderers :
			o = r.capturedObject( "o" )
			self.assertEqual( o.capturedLinks( "lights" ), { r.capturedObject( "l1" ) } )
			self.assertEqual( o.numLinkEdits( "lights" ), 1 )

		compoundObject.link( "lights", { light1, light2 } )

		for r in renderers :
			o = r.capturedObject( "o" )
			self.assertEqual( o.capturedLinks( "lights" ), { r.capturedObject( "l1" ), r.capturedObject( "l2" ) } )
			self.assertEqual( o.numLinkEdits( "lights" ), 2 )

if __name__ == "__main__":
	unittest.main()
