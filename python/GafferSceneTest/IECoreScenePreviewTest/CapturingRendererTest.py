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

import collections
import imath
import unittest
import re

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
		self.assertEqual( attributes.attributes(), coreAttributes )

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
		self.assertEqual( o.id(), 0 )

		o.attributes( attributes2 )
		self.assertEqual( o.capturedAttributes(), attributes2 )
		self.assertEqual( o.numAttributeEdits(), 2 )

		o.assignID( 10 )
		self.assertEqual( o.id(), 10 )

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

	class TestProcedural( GafferScene.Private.IECoreScenePreview.Procedural ) :

		def __init__( self ) :

			GafferScene.Private.IECoreScenePreview.Procedural.__init__( self )

		def render( self, renderer ) :

			attributes = renderer.attributes( IECore.CompoundObject( { "a" : IECore.FloatData( 12 ) } ) )
			o = renderer.object( "a", IECoreScene.SpherePrimitive( 42 ), attributes )
			o.transform( imath.M44f().translate( imath.V3f( 3, 0, 0 ) ) )

	class TestRecursiveProcedural( GafferScene.Private.IECoreScenePreview.Procedural ) :

		def __init__( self ) :

			GafferScene.Private.IECoreScenePreview.Procedural.__init__( self )

		def render( self, renderer ) :

			attributes = renderer.attributes( IECore.CompoundObject( { "b" : IECore.FloatData( 7 ) } ) )
			p = renderer.object( "b", CapturingRendererTest.TestProcedural(), attributes )
			p.transform( [
					imath.M44f( 0, 1, 0, 0,  -1, 0, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1 ),
					imath.M44f( 0, -1, 0, 0,  1, 0, 0, 0,  0, 0, 1, 0,  0, 0, 0, 1 )
				], [ 0, 1 ]
			)

			attributes = renderer.attributes( IECore.CompoundObject() )
			renderer.object( "x", IECoreScene.SpherePrimitive( 37 ), attributes )

	__ExpandedCapture = collections.namedtuple( 'ExpandedCapture',
		[ 'capturedSamples', 'capturedSampleTimes', 'capturedTransforms', 'capturedTransformSampleTimes',
		'capturedAttributes', 'capturedLinks' ]
	)

	@staticmethod
	def __expandCapturingRenderer( capturingRenderer, expandProcedurals = False ):
		result = {}
		for objectName in capturingRenderer.capturedObjectNames():
			co = capturingRenderer.capturedObject( objectName )
			linkDict = { str(t) : [ i.capturedName() for i in co.capturedLinks( t ) or [] ] for t in co.capturedLinkTypes() }
			capturedObject = CapturingRendererTest.__ExpandedCapture( co.capturedSamples(), co.capturedSampleTimes(), co.capturedTransforms(), co.capturedTransformTimes(), co.capturedAttributes().attributes(), linkDict )


			isProcedural = isinstance( capturedObject.capturedSamples[0], GafferScene.Private.IECoreScenePreview.Procedural )

			if not expandProcedurals or not isProcedural:
				result[objectName] = capturedObject
				continue

			procRenderer = GafferScene.Private.IECoreScenePreview.CapturingRenderer( GafferScene.Private.IECoreScenePreview.Renderer.RenderType.Batch )

			capturedObject.capturedSamples[0].render( procRenderer )
			procExpanded = CapturingRendererTest.__expandCapturingRenderer( procRenderer, expandProcedurals = True )

			for subName, subObject in procExpanded.items():

				if subName == "" or subName == "/":
					newName = objectName
				elif subName.startswith( "/" ):
					newName = objectName + subName
				else:
					newName = objectName + "/" + subName

				newAttrs = capturedObject.capturedAttributes.copy()
				for a, val in subObject.capturedAttributes.items():
					newAttrs[a] = val

				parentTransformSampleTimes = capturedObject.capturedTransformSampleTimes
				newTransformTimes = subObject.capturedTransformSampleTimes
				if newTransformTimes != parentTransformSampleTimes:
					if parentTransformSampleTimes == []:
						# Combining a static transform with an animated transform results in an animated transform
						pass
					elif newTransformTimes == []:
						newTransformTimes = parentTransformSampleTimes
					else:
						raise IECore.Exception( "Incompatible transform sample times when expanding procedural at location '%s' : %s != %s" % ( newName, parentTransformSampleTimes, newTransformTimes ) )

				parentTransforms = capturedObject.capturedTransforms
				newTransforms = subObject.capturedTransforms
				if parentTransforms == []:
					pass
				elif newTransforms == []:
					newTransforms = parentTransforms
				else:
					effectiveParentTransforms = parentTransforms
					if len( effectiveParentTransforms ) != len( newTransforms ):
						if len( effectiveParentTransforms ) == 1:
							effectiveParentTransforms = [ parentTransforms[0] ] * len( newTransforms )
						elif len( newTransforms ) == 1:
							newTransforms = [ newTransforms[0] ] * len( effectiveParentTransforms )
						else:
							raise IECore.Exception( "Incompatible transform sample lengths when expanding procedural at location '%s' : %s != %s" % ( newName, len( parentTransforms ), len( newTransforms ) ) )

					newTransforms = [
						newTransforms[i] * effectiveParentTransforms[i]
						for i in range( len( newTransforms ) )
					]

				# \todo - If we want to test links properly, that would need better support ... passing
				# object references from `procRenderer` doesn't feel reliable ... it's probably reasonable
				# to just pass object names for comparison purposes, but then we should probably prefix all
				# the names in the list, the same way we do the new object name?
				# I don't think we currently really support light linking inside procedurals much, so I haven't
				# worried about it yet.

				result[ newName ] = CapturingRendererTest.__ExpandedCapture(
					subObject.capturedSamples, subObject.capturedSampleTimes, newTransforms, newTransformTimes,
					newAttrs, subObject.capturedLinks
				)

		return result

	@staticmethod
	def assertRendersMatch( capturingA, capturingB, expandProcedurals = False, ignoreLinks = False ):
		expandA = CapturingRendererTest.__expandCapturingRenderer( capturingA, expandProcedurals )
		expandB = CapturingRendererTest.__expandCapturingRenderer( capturingB, expandProcedurals )

		if expandA.keys() != expandB.keys():
			raise AssertionError( "Objects do not match : %s != %s" % ( list( expandA.keys() ), list( expandB.keys() ) ) )

		for k in expandA.keys():

			aSampleTimes = expandA[k].capturedSampleTimes
			bSampleTimes = expandB[k].capturedSampleTimes

			if aSampleTimes != bSampleTimes:
				raise AssertionError(
					"Mismatched samples times at path '%s' : %s != %s " % ( k, aSampleTimes, bSampleTimes )
				)

			aObjects = expandA[k].capturedSamples
			bObjects = expandB[k].capturedSamples

			if len( aObjects ) != len( bObjects ):
				raise AssertionError(
					"Mismatched samples counts at path '%s' : %i != %i" % ( k, len( aObjects ), len( bObjects ) )
				)

			for i in range( len( aObjects ) ):
				if type( aObjects[i] ) != type( bObjects[i] ):
					raise AssertionError(
						"Mismatched object types at path '%s', sample %i : %s != %s" %
						( k, i, type( aObjects[i] ).__name__, type( bObjects[i] ).__name__ )
					)

				if aObjects[i] != bObjects[i]:
					raise AssertionError( "Mismatch for objects of type %s at path '%s', sample %i" % ( type( aObjects[i] ).__name__, k, i ) )

			aTransformTimes = expandA[k].capturedTransformSampleTimes
			bTransformTimes = expandB[k].capturedTransformSampleTimes

			if aTransformTimes != bTransformTimes:
				raise AssertionError(
					"Mismatched transform times at path '%s' : %s != %s" % ( k, aTransformTimes, bTransformTimes )
				)

			aTransforms = expandA[k].capturedTransforms
			bTransforms = expandB[k].capturedTransforms

			if aTransforms != bTransforms:
				raise AssertionError(
					"Mismatched transforms at path '%s' : %s != %s" % ( k, aTransforms, bTransforms )
				)

			aAttributes = expandA[k].capturedAttributes
			bAttributes = expandB[k].capturedAttributes

			if aAttributes != bAttributes:
				if aAttributes.keys() != bAttributes.keys():
					raise AssertionError(
						"Mismatched attributes at path '%s' : %s != %s" % ( k, sorted( list( aAttributes.keys() ) ), sorted( list( bAttributes.keys() ) ) )
					)

				for i in aAttributes.keys():
					if aAttributes[i] != bAttributes[i]:
						raise AssertionError(
							"Mismatched attribute '%s' at path '%s' : %s != %s" %
							( i, k, aAttributes[i], bAttributes[i] )
						)

			if not ignoreLinks:
				aLinks = expandA[k].capturedLinks
				bLinks = expandB[k].capturedLinks

				if aLinks.keys() != bLinks.keys():
					raise AssertionError(
						"Mismatched link types at path '%s' : %s != %s" % ( k, sorted( list( aLinks.keys() ) ), sorted( list( bLinks.keys() ) ) )
					)

				for i in aLinks.keys():
					if aLinks[i] != bLinks[i]:
						raise AssertionError(
							"Mismatched links for type %s at path '%s' : %s != %s" % ( i, k, sorted( aLinks[i] ), sorted( bLinks[i] ) )
						)

	def testAssertRendersMatch( self ):

		rendererA = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		rendererB = GafferScene.Private.IECoreScenePreview.CapturingRenderer()

		CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		sphere1 = IECoreScene.SpherePrimitive( 1 )
		attrs = IECore.CompoundObject( { "x" : IECore.IntData( 1 ) } )

		oA = rendererA.object( "/o", sphere1, rendererA.attributes( attrs ) )

		with self.assertRaisesRegex( AssertionError, r"Objects do not match : \['/o'\] != \[\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		oB = rendererB.object( "/o", sphere1, rendererB.attributes( attrs ) )

		CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		del oA
		oA = rendererA.object( "/o", [ sphere1, sphere1 ], [ 0, 1 ], rendererA.attributes( attrs ) )

		with self.assertRaisesRegex( AssertionError, r"Mismatched samples times at path '/o' : \[0.0, 1.0\] != \[\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		del oB
		oB = rendererB.object( "/o", [ sphere1 ], [ 0, 1 ], rendererB.attributes( attrs ) )

		with self.assertRaisesRegex( AssertionError, r"Mismatched samples counts at path '/o' : 2 != 1" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		mesh = IECoreScene.MeshPrimitive.createSphere( 1 )

		del oB
		oB = rendererB.object( "/o", [ sphere1, mesh ], [ 0, 1 ], rendererB.attributes( attrs ) )

		with self.assertRaisesRegex( AssertionError, r"Mismatched object types at path '/o', sample 1 : SpherePrimitive != MeshPrimitive" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		sphere2 = IECoreScene.SpherePrimitive( 2 )
		del oB
		oB = rendererB.object( "/o", [ sphere1, sphere2 ], [ 0, 1 ], rendererB.attributes( attrs ) )

		with self.assertRaisesRegex( AssertionError, r"Mismatch for objects of type SpherePrimitive at path '/o', sample 1" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		proc1 = self.TestProcedural()
		del oA
		oA = rendererA.object( "/o", [ sphere1, proc1 ], [ 0, 1 ], rendererA.attributes( attrs ) )

		with self.assertRaisesRegex( AssertionError, r"Mismatched object types at path '/o', sample 1 : TestProcedural != SpherePrimitive" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		proc2 = self.TestRecursiveProcedural()
		del oB
		oB = rendererB.object( "/o", [ sphere1, proc2 ], [ 0, 1 ], rendererB.attributes( attrs ) )

		with self.assertRaisesRegex( AssertionError, r"Mismatched object types at path '/o', sample 1 : TestProcedural != TestRecursiveProcedural" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		del oB
		oB = rendererB.object( "/o", [ sphere1, proc1 ], [ 0, 1 ], rendererB.attributes( attrs ) )

		CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		oA.transform( imath.M44f( 1 ) )

		with self.assertRaisesRegex( AssertionError, re.escape( r"Mismatched transforms at path '/o' : [M44f((1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1))] != []" ) ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		oB.transform( imath.M44f( 1 ) )
		CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		oA.transform( [ imath.M44f( 1 ), imath.M44f( 2 ) ], [ 0, 1 ] )

		with self.assertRaisesRegex( AssertionError, r"Mismatched transform times at path '/o' : \[0.0, 1.0\] != \[\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		oB.transform( [ imath.M44f( 1 ), imath.M44f( 2 ) ], [ 0, 1 ] )

		CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		attrsB = IECore.CompoundObject( { "x" : IECore.IntData( 1 ), "y" : IECore.BoolData( False ) } )

		del oA
		oA = rendererA.object( "/o", sphere1, rendererA.attributes( attrs ) )

		del oB
		oB = rendererB.object( "/o", sphere1, rendererB.attributes( attrsB ) )

		with self.assertRaisesRegex( AssertionError, r"Mismatched attributes at path '/o' : \['x'\] != \['x', 'y'\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		attrsB = IECore.CompoundObject( { "x" : IECore.BoolData( False ) } )

		del oB
		oB = rendererB.object( "/o", sphere1, rendererB.attributes( attrsB ) )

		with self.assertRaisesRegex( AssertionError, r"Mismatched attribute 'x' at path '/o' : 1 != 0" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		del oB
		oB = rendererB.object( "/o", sphere1, rendererB.attributes( attrs ) )

		CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		lA = rendererA.object( "/l", sphere1, rendererA.attributes( attrs ) )

		with self.assertRaisesRegex( AssertionError, r"Objects do not match : \['/o', '/l'\] != \['/o'\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		lB = rendererB.object( "/l", sphere1, rendererB.attributes( attrs ) )

		CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		lA.link( "test", [ oA ] )

		with self.assertRaisesRegex( AssertionError, r"Mismatched link types at path '/l' : \['test'\] != \[\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		lB.link( "test", [ oB, lB ] )

		with self.assertRaisesRegex( AssertionError, r"Mismatched links for type test at path '/l' : \['/o'\] != \['/l', '/o'\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		lB.link( "test", [ oB ] )

		CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

	def testAssertRendersMatchExpand( self ):

		rendererA = GafferScene.Private.IECoreScenePreview.CapturingRenderer()
		rendererB = GafferScene.Private.IECoreScenePreview.CapturingRenderer()

		attrs = IECore.CompoundObject( { "c" : IECore.IntData( 1 ), "a" : IECore.FloatData( 67 ) } )
		oA = rendererA.object( "/c", self.TestRecursiveProcedural(), rendererA.attributes( attrs ) )
		oA.transform( imath.M44f().translate( imath.V3f( 2, 0, 0 ) ) )

		with self.assertRaisesRegex( AssertionError, r"Objects do not match : \['/c'\] != \[\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB )

		with self.assertRaisesRegex( AssertionError, r"Objects do not match : \['/c/b/a', '/c/x'\] != \[\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB, expandProcedurals = True )

		attrsCx = IECore.CompoundObject( { "c" : IECore.IntData( 1 ), "a" : IECore.FloatData( 67 ) } )

		cx = rendererB.object( "/c/x", IECoreScene.SpherePrimitive( 37 ), rendererB.attributes( attrsCx ) )
		cx.transform( imath.M44f(
			(1, 0, 0, 0),
			(0, 1, 0, 0),
			(0, 0, 1, 0),
			(2, 0, 0, 1)
		) )

		attrsCba = IECore.CompoundObject(
			{ "a" : IECore.FloatData( 12 ), "b" : IECore.FloatData( 7 ), "c" : IECore.IntData( 1 ) }
		)
		cba = rendererB.object( "/c/b/a", IECoreScene.SpherePrimitive( 42 ), rendererB.attributes( attrsCba ) )
		cba.transform( [
				imath.M44f(
					(0, 1, 0, 0),
					(-1,0, 0, 0),
					(0, 0, 1, 0),
					(2, 3, 0, 1)
				),
				imath.M44f(
					(0,-1, 0, 0),
					(1, 0, 0, 0),
					(0, 0, 1, 0),
					(2,-3, 0, 1)
				)
			], [ 0, 1 ]
		)

		CapturingRendererTest.assertRendersMatch( rendererA, rendererB, expandProcedurals = True )

		# Test transform mismatch errors
		oA.transform( [ imath.M44f(), imath.M44f(), imath.M44f() ], [] )

		with self.assertRaisesRegex( RuntimeError, r"Incompatible transform sample lengths when expanding procedural at location '/c/b/a' : 3 != 2" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB, expandProcedurals = True )

		oA.transform( [ imath.M44f() ], [1,2,3] )

		with self.assertRaisesRegex( RuntimeError, r"Incompatible transform sample times when expanding procedural at location '/c/b/a' : \[1.0, 2.0, 3.0\] != \[0.0, 1.0\]" ):
			CapturingRendererTest.assertRendersMatch( rendererA, rendererB, expandProcedurals = True )

if __name__ == "__main__":
	unittest.main()
