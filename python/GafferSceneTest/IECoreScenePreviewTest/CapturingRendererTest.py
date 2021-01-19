##########################################################################
#
#  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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
import IECoreScene

import GafferTest
import GafferScene

class CapturingRendererTest( GafferTest.TestCase ) :

	def testFactory( self ) :

		self.assertTrue( "Capturing" in GafferScene.Private.IECoreScenePreview.Renderer.types() )

		r = GafferScene.Private.IECoreScenePreview.Renderer.create( "Capturing" )
		self.assertTrue( isinstance( r, GafferScene.Private.IECoreScenePreview.CapturingRenderer ) )
		self.assertEqual( r.name(), "Capturing" )

	def testCapturedAttributes( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()

		coreAttributes = IECore.CompoundObject( { "x" : IECore.IntData( 10 ) } )
		attributes = renderer.attributes( coreAttributes )
		self.assertIsInstance( attributes, renderer.CapturedAttributes )
		self.assertTrue( attributes.attributes().isSame( coreAttributes ) )

	def testCapturedObject( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()

		attributes1 = renderer.attributes( IECore.CompoundObject( { "x" : IECore.IntData( 10 ) } ) )
		attributes2 = renderer.attributes( IECore.CompoundObject( { "x" : IECore.IntData( 10 ) } ) )

		self.assertIsNone( renderer.capturedObject( "o" ) )

		o = renderer.object( "o", IECoreScene.SpherePrimitive(), attributes1 )
		self.assertIsInstance( o, renderer.CapturedObject )
		self.assertTrue( o.isSame( renderer.capturedObject( "o" ) ) )
		self.assertEqual( o.capturedSamples(), [ IECoreScene.SpherePrimitive() ] )
		self.assertEqual( o.capturedSampleTimes(), [] )
		self.assertEqual( o.capturedAttributes(), attributes1 )
		self.assertEqual( o.capturedLinks( "lights" ), None )
		self.assertEqual( o.numAttributeEdits(), 1 )
		self.assertEqual( o.numLinkEdits( "lights" ), 0 )

		o.attributes( attributes2 )
		self.assertEqual( o.capturedAttributes(), attributes2 )
		self.assertEqual( o.numAttributeEdits(), 2 )

		l1 = renderer.light( "l1", IECore.NullObject(), attributes1 )
		l2 = renderer.light( "l2", IECore.NullObject(), attributes1 )

		o.link( "lights", { l1 } )
		self.assertEqual( o.capturedLinks( "lights" ), { l1 } )
		self.assertEqual( o.numLinkEdits( "lights" ), 1 )
		o.link( "lights", { l1, l2 } )
		self.assertEqual( o.capturedLinks( "lights" ), { l1, l2 } )
		self.assertEqual( o.numLinkEdits( "lights" ), 2 )

		del o
		self.assertIsNone( renderer.capturedObject( "o" ) )

		del l1
		del l2
		self.assertIsNone( renderer.capturedObject( "l1" ) )
		self.assertIsNone( renderer.capturedObject( "l2" ) )

	def testDuplicateNames( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		attributes = renderer.attributes( IECore.CompoundObject() )

		o = renderer.object( "o", IECoreScene.SpherePrimitive(), attributes )
		with IECore.CapturingMessageHandler() as mh :
			o2 = renderer.object( "o", IECoreScene.SpherePrimitive(), attributes )
			self.assertEqual( o2, None )

		self.assertEqual( len( mh.messages ), 1 )
		self.assertEqual( mh.messages[0].level, IECore.Msg.Level.Warning )
		self.assertEqual( mh.messages[0].context, "CapturingRenderer::object" )
		self.assertEqual( mh.messages[0].message, "Object named \"o\" already exists" )
		del o

	def testObjects( self ) :

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()

		renderableAttr = renderer.attributes( IECore.CompoundObject( {} ) )
		unrenderableAttr = renderer.attributes( IECore.CompoundObject( { "cr:unrenderable" : IECore.BoolData( True ) } ) )

		self.assertIsNone( renderer.object( "o", IECoreScene.SpherePrimitive(), unrenderableAttr ) )
		self.assertIsNone( renderer.camera( "c", IECoreScene.Camera(), unrenderableAttr ) )
		self.assertIsNone( renderer.light( "l", IECore.NullObject(), unrenderableAttr ) )
		self.assertIsNone( renderer.lightFilter( "lf", IECore.NullObject(), unrenderableAttr ) )

		self.assertIsInstance(
			renderer.object( "ro", IECoreScene.SpherePrimitive(), renderableAttr ),
			GafferScene.Private.IECoreScenePreview.Renderer.ObjectInterface
		)
		self.assertIsInstance(
			renderer.camera( "rc", IECoreScene.Camera(), renderableAttr ),
			GafferScene.Private.IECoreScenePreview.Renderer.ObjectInterface
		)
		self.assertIsInstance(
			renderer.light( "rl", IECore.NullObject(), renderableAttr ),
			GafferScene.Private.IECoreScenePreview.Renderer.ObjectInterface
		)
		self.assertIsInstance(
			renderer.lightFilter( "rl", IECore.NullObject(), renderableAttr ),
			GafferScene.Private.IECoreScenePreview.Renderer.ObjectInterface
		)

	def testDeformingObject( self ) :

		sphere1 = IECoreScene.SpherePrimitive( 1 )
		sphere2 = IECoreScene.SpherePrimitive( 2 )

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		o = renderer.object(
			"o", [ sphere1, sphere2 ], [ 1, 2 ], renderer.attributes( IECore.CompoundObject() )
		)

		c = renderer.capturedObject( "o" )
		self.assertEqual( c.capturedSamples(), [ sphere1, sphere2 ] )
		self.assertEqual( c.capturedSampleTimes(), [ 1, 2 ] )

if __name__ == "__main__":
	unittest.main()
