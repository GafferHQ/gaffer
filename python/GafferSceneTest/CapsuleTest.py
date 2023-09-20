##########################################################################
#
#  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

import inspect
import unittest

import IECore

import Gaffer
import GafferScene
import GafferSceneTest

class CapsuleTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		sphere = GafferScene.Sphere()

		h = IECore.MurmurHash()
		for path in ( "/", "/sphere" ) :
			for method in ( "boundHash", "transformHash", "objectHash", "attributesHash" ) :
				h.append( getattr( sphere["out"], method )( path ) )

		capsule = GafferScene.Capsule(
			sphere["out"],
			"/",
			Gaffer.Context(),
			h,
			sphere["out"].bound( "/" )
		)

		self.assertEqual( capsule.scene(), sphere["out"] )
		self.assertEqual( capsule.root(), "/" )
		self.assertEqual( capsule.bound(), sphere["out"].bound( "/" ) )

		capsuleCopy = capsule.copy()
		self.assertEqual( capsuleCopy.scene(), sphere["out"] )
		self.assertEqual( capsuleCopy.root(), "/" )
		self.assertEqual( capsuleCopy.bound(), sphere["out"].bound( "/" ) )
		self.assertEqual( capsuleCopy.hash(), capsule.hash() )

	def testInheritedAttributesAreNotBakedIntoCapsuleContents( self ) :

		# Make a Capsule which inherits attributes from its parent
		# and from the scene globals.

		sphere = GafferScene.Sphere()
		group = GafferScene.Group()
		group["in"][0].setInput( sphere["out"] )

		groupFilter = GafferScene.PathFilter()
		groupFilter["paths"].setValue( IECore.StringVectorData( [ "/group" ] ) )

		groupAttributes = GafferScene.CustomAttributes()
		groupAttributes["in"].setInput( group["out"] )
		groupAttributes["filter"].setInput( groupFilter["out"] )
		groupAttributes["attributes"].addChild( Gaffer.NameValuePlug( "groupAttribute", 10 ) )

		globalAttributes = GafferScene.CustomAttributes()
		globalAttributes["in"].setInput( groupAttributes["out"] )
		globalAttributes["global"].setValue( True )
		globalAttributes["attributes"].addChild( Gaffer.NameValuePlug( "globalAttribute", 20 ) )

		encapsulate = GafferScene.Encapsulate()
		encapsulate["in"].setInput( globalAttributes["out"] )
		encapsulate["filter"].setInput( groupFilter["out"] )

		# Render it, and check that the capsule object had the inherited attributes applied to it.

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)
		GafferScene.Private.RendererAlgo.outputObjects(
			encapsulate["out"], encapsulate["out"].globals(), GafferScene.Private.RendererAlgo.RenderSets( encapsulate["out"] ), GafferScene.Private.RendererAlgo.LightLinks(),
			renderer
		)

		capturedGroup = renderer.capturedObject( "/group" )
		self.assertIsInstance( capturedGroup.capturedSamples()[0], GafferScene.Capsule )
		self.assertEqual(
			capturedGroup.capturedAttributes().attributes(),
			IECore.CompoundObject( {
				"groupAttribute" : IECore.IntData( 10 ),
				"globalAttribute" : IECore.IntData( 20 ),
				"sets" : IECore.InternedStringVectorData(),
			} )
		)

		# Expand the capsule, and check that it didn't bake the inherited attributes onto
		# its contents. It is the responsibity of the Renderer itself to take care of attribute
		# inheritance, ideally doing it "live", so that changes to inherited attributes don't
		# require re-expansion of the capsule.

		renderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer(
			GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch
		)
		capturedGroup.capturedSamples()[0].render( renderer )
		capturedSphere = renderer.capturedObject( "/sphere" )
		self.assertEqual(
			capturedSphere.capturedAttributes().attributes(),
			IECore.CompoundObject( {
				"sets" : IECore.InternedStringVectorData(),
			} )
		)

if __name__ == "__main__":
	unittest.main()
