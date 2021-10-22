##########################################################################
#
#  Copyright (c) 2021, Image Engine Design Inc. All rights reserved.
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
#      * Neither the name of Image Engine Design Inc nor the names of
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

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene

import GafferSceneTest

class MotionPathTest( GafferSceneTest.SceneTestCase ) :

	def makeScene( self ) :

		script = Gaffer.ScriptNode()
		script["cube"] = GafferScene.Cube()
		script["cube"]["sets"].setValue( "geometry" )

		animY = Gaffer.Animation.acquire( script["cube"]["transform"]["translate"]["y"] )
		animY.addKey( Gaffer.Animation.Key( 0 / 24.0, 0, Gaffer.Animation.Interpolation.Constant ) )
		animY.addKey( Gaffer.Animation.Key( 1 / 24.0, 1, Gaffer.Animation.Interpolation.Constant ) )
		animY.addKey( Gaffer.Animation.Key( 2 / 24.0, 2, Gaffer.Animation.Interpolation.Constant ) )

		animX = Gaffer.Animation.acquire( script["cube"]["transform"]["translate"]["x"] )
		animX.addKey( Gaffer.Animation.Key( 2 / 24.0, 0, Gaffer.Animation.Interpolation.Constant ) )
		animX.addKey( Gaffer.Animation.Key( 3 / 24.0, 1, Gaffer.Animation.Interpolation.Constant ) )
		animX.addKey( Gaffer.Animation.Key( 4 / 24.0, 2, Gaffer.Animation.Interpolation.Constant ) )

		script["sphere"] = GafferScene.Sphere()
		script["sphere"]["sets"].setValue( "geometry" )
		script["parent"] = GafferScene.Parent()
		script["parent"]["in"].setInput( script["cube"]["out"] )
		script["parent"]["child"][0].setInput( script["sphere"]["out"] )
		script["cubeFilter"] = GafferScene.PathFilter()
		script["cubeFilter"]["paths"].setValue( IECore.StringVectorData( [ "/cube" ] ) )
		script["parent"]["filter"].setInput( script["cubeFilter"]["out"] )

		script["camera"] = GafferScene.Camera()
		script["camera"]["sets"].setValue( "cameras" )
		script["camera"]["transform"]["translate"]["y"].setValue( 0.5 )
		camAnimZ = Gaffer.Animation.acquire( script["camera"]["transform"]["translate"]["z"] )
		camAnimZ.addKey( Gaffer.Animation.Key( 0 / 24.0, 5, Gaffer.Animation.Interpolation.Linear ) )
		camAnimZ.addKey( Gaffer.Animation.Key( 4 / 24.0, 10, Gaffer.Animation.Interpolation.Linear ) )

		script["light"] = GafferSceneTest.TestLight()
		script["light"]["sets"].setValue( "lights" )

		script["group"] = GafferScene.Group()
		script["group"]["in"][0].setInput( script["parent"]["out"] )
		script["group"]["in"][1].setInput( script["camera"]["out"] )
		script["group"]["in"][2].setInput( script["light"]["out"] )

		script["motion"] = GafferScene.MotionPath()
		script["motion"]["in"].setInput( script["group"]["out"] )
		script["motionFilter"] = GafferScene.PathFilter()
		script["motionFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )
		script["motion"]["filter"].setInput( script["motionFilter"]["out"] )
		script["motion"]["start"]["frame"].setValue( 0 )
		script["motion"]["end"]["frame"].setValue( 4 )

		script.context().setFrame( 0 )

		cubeMotionP = IECore.V3fVectorData( [
			imath.V3f( 0, 0, 0 ), imath.V3f( 0, 1, 0 ), imath.V3f( 0, 2, 0 ),
			imath.V3f( 1, 2, 0 ), imath.V3f( 2, 2, 0 ),
		], IECore.GeometricData.Interpretation.Point )

		return script, cubeMotionP

	def testRelativeRange( self ) :

		script, expectedP = self.makeScene()
		script["motion"]["start"]["mode"].setValue( GafferScene.MotionPath.FrameMode.Relative )
		script["motion"]["end"]["mode"].setValue( GafferScene.MotionPath.FrameMode.Relative )

		# leading
		script["motion"]["start"]["frame"].setValue( 0 )
		script["motion"]["end"]["frame"].setValue( 4 )
		script.context().setFrame( 0 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( curve["P"].data, expectedP )
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 0, 1, 2, 3, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

		# centered
		script["motion"]["start"]["frame"].setValue( -2 )
		script["motion"]["end"]["frame"].setValue( 2 )
		script.context().setFrame( 2 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( curve["P"].data, expectedP )
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 0, 1, 2, 3, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

		# trailing
		script["motion"]["start"]["frame"].setValue( -4 )
		script["motion"]["end"]["frame"].setValue( 0 )
		script.context().setFrame( 4 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( curve["P"].data, expectedP )
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 0, 1, 2, 3, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

		# partial
		script["motion"]["start"]["frame"].setValue( 0 )
		script["motion"]["end"]["frame"].setValue( 2 )
		script.context().setFrame( 2 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 3 ] ) )
		self.assertEqual( curve["P"].data, expectedP[2:] )
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 2, 3, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

		# overshoot
		script["motion"]["start"]["frame"].setValue( 0 )
		script["motion"]["end"]["frame"].setValue( 4 )
		script.context().setFrame( 2 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		overshootP = expectedP[2:]
		overshootP.append( expectedP[-1] )
		overshootP.append( expectedP[-1] )
		self.assertEqual( curve["P"].data, overshootP )
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 2, 3, 4, 5, 6 ] ) )
		self.assertEqual( bound, curve.bound() )

	def testAbsoluteRange( self ) :

		script, expectedP = self.makeScene()
		script["motion"]["start"]["mode"].setValue( GafferScene.MotionPath.FrameMode.Absolute )
		script["motion"]["end"]["mode"].setValue( GafferScene.MotionPath.FrameMode.Absolute )

		script["motion"]["start"]["frame"].setValue( 0 )
		script["motion"]["end"]["frame"].setValue( 4 )

		for f in range( -5, 5 ) :
			script.context().setFrame( f )
			with script.context() :
				curve = script["motion"]["out"].object( "/group/cube" )
				bound = script["motion"]["out"].bound( "/group/cube" )
			self.assertTrue( curve.arePrimitiveVariablesValid() )
			self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
			self.assertEqual( curve["P"].data, expectedP )
			self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 0, 1, 2, 3, 4 ] ) )
			self.assertEqual( bound, curve.bound() )

		# mixed modes
		script["motion"]["start"]["mode"].setValue( GafferScene.MotionPath.FrameMode.Relative )
		script.context().setFrame( 3 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 2 ] ) )
		self.assertEqual( curve["P"].data, expectedP[-2:] )
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 3, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

	def testVariableSampling( self ) :

		script, _ = self.makeScene()
		script["motion"]["samplingMode"].setValue( GafferScene.MotionPath.SamplingMode.Variable )
		script["motion"]["step"].setValue( 0.5 )
		script.context().setFrame( 0 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 9 ] ) )
		# note intermediate samples aren't interpolated only because the anim keys use Constant interpolation
		self.assertEqual( curve["P"].data, IECore.V3fVectorData( [
				imath.V3f( 0, 0, 0 ), imath.V3f( 0, 0, 0 ), imath.V3f( 0, 1, 0 ),
				imath.V3f( 0, 1, 0 ), imath.V3f( 0, 2, 0 ), imath.V3f( 0, 2, 0 ),
				imath.V3f( 1, 2, 0 ), imath.V3f( 1, 2, 0 ), imath.V3f( 2, 2, 0 )
			], IECore.GeometricData.Interpretation.Point )
		)
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

		# step overshoot still contains the end point
		script["motion"]["step"].setValue( 5 )
		script.context().setFrame( 0 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 2 ] ) )
		self.assertEqual( curve["P"].data, IECore.V3fVectorData( [
				imath.V3f( 0, 0, 0 ), imath.V3f( 2, 2, 0 ),
			], IECore.GeometricData.Interpretation.Point )
		)
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 0, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

		# step overshoot still contains the end point
		script["motion"]["step"].setValue( 3 )
		script.context().setFrame( 0 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 3 ] ) )
		self.assertEqual( curve["P"].data, IECore.V3fVectorData( [
				imath.V3f( 0, 0, 0 ), imath.V3f( 1, 2, 0 ), imath.V3f( 2, 2, 0 ),
			], IECore.GeometricData.Interpretation.Point )
		)
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 0, 3, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

	def testFixedSampling( self ) :

		script, expectedP = self.makeScene()
		script["motion"]["samplingMode"].setValue( GafferScene.MotionPath.SamplingMode.Fixed )

		script["motion"]["samples"].setValue( 5 )
		script.context().setFrame( 0 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( curve["P"].data, expectedP )
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( range( 0, 5 ) ) )
		self.assertEqual( bound, curve.bound() )

		script["motion"]["samples"].setValue( 9 )
		script.context().setFrame( 0 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 9 ] ) )
		# note intermediate samples aren't interpolated only because the anim keys use Constant interpolation
		self.assertEqual( curve["P"].data, IECore.V3fVectorData( [
				imath.V3f( 0, 0, 0 ), imath.V3f( 0, 0, 0 ), imath.V3f( 0, 1, 0 ),
				imath.V3f( 0, 1, 0 ), imath.V3f( 0, 2, 0 ), imath.V3f( 0, 2, 0 ),
				imath.V3f( 1, 2, 0 ), imath.V3f( 1, 2, 0 ), imath.V3f( 2, 2, 0 )
			], IECore.GeometricData.Interpretation.Point )
		)
		self.assertEqual( curve["frame"].data, IECore.FloatVectorData( [ 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4 ] ) )
		self.assertEqual( bound, curve.bound() )

		for i in range( 2, 20 ) :
			script["motion"]["samples"].setValue( i )
			with script.context() :
				curve = script["motion"]["out"].object( "/group/cube" )
			self.assertTrue( curve.arePrimitiveVariablesValid() )
			self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ i ] ) )
			expectedFrames = IECore.FloatVectorData( [ x * 4. / (i-1) for x in range( 0, i ) ] )
			for f in range( 0, len(curve["frame"].data) ) :
				self.assertAlmostEqual( curve["frame"].data[f], expectedFrames[f], 5 )

	def testBadRange( self ) :

		script, _ = self.makeScene()
		script["motion"]["start"]["frame"].setValue( 4 )
		script["motion"]["end"]["frame"].setValue( 0 )
		script.context().setFrame( 0 )
		with script.context() :
			self.assertEqual( script["motion"]["out"].object( "/group/cube" ), IECore.NullObject() )

		script["motion"]["start"]["mode"].setValue( GafferScene.MotionPath.FrameMode.Absolute )
		script["motion"]["end"]["mode"].setValue( GafferScene.MotionPath.FrameMode.Absolute )
		with script.context() :
			self.assertEqual( script["motion"]["out"].object( "/group/cube" ), IECore.NullObject() )

	def testDontAdjustBounds( self ) :

		script, expectedP = self.makeScene()
		script["motion"]["adjustBounds"].setValue( False )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			self.assertEqual( script["motion"]["out"].bound( "/group/cube" ), script["motion"]["in"].bound( "/group/cube" ) )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( curve["P"].data, expectedP )

	def testFilter( self ) :

		script, _ = self.makeScene()
		with script.context() :

			script["motionFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube" ] ) )
			self.assertEqual( script["motion"]["in"].childNames( "/group" ), IECore.InternedStringVectorData( [ "cube", "camera", "light" ] ) )
			self.assertEqual( script["motion"]["out"].childNames( "/group" ), IECore.InternedStringVectorData( [ "cube" ] ) )
			self.assertEqual( script["motion"]["out"].object( "/group/cube/sphere" ), IECore.NullObject() )
			curve = script["motion"]["out"].object( "/group/cube" )
			self.assertIsInstance( curve, IECoreScene.CurvesPrimitive )
			self.assertEqual( script["motion"]["out"].object( "/group" ), IECore.NullObject() )
			self.assertEqual( script["motion"]["out"].object( "/" ), IECore.NullObject() )
			self.assertEqual( script["motion"]["out"].bound( "/group/cube/sphere" ), imath.Box3f() )
			self.assertEqual( script["motion"]["out"].bound( "/group/cube" ), curve.bound() )
			self.assertEqual( script["motion"]["out"].bound( "/group" ), curve.bound() )
			self.assertEqual( script["motion"]["out"].bound( "/" ), curve.bound() )

			# unmatched path
			script["motionFilter"]["paths"].setValue( IECore.StringVectorData( [ "/fake" ] ) )
			self.assertEqual( script["motion"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [] ) )

			# no filter
			script["motion"]["filter"].setInput( None )
			self.assertEqual( script["motion"]["out"].childNames( "/" ), IECore.InternedStringVectorData( [] ) )

	def testMultipleMatches( self ) :

		script, cubeMotionP = self.makeScene()
		script["motionFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube", "/group/camera" ] ) )
		with script.context() :
			cubeCurve = script["motion"]["out"].object( "/group/cube" )
			cubeBound = script["motion"]["out"].bound( "/group/cube" )
			cameraCurve = script["motion"]["out"].object( "/group/camera" )
			cameraBound = script["motion"]["out"].bound( "/group/camera" )
			groupBound = script["motion"]["out"].bound( "/group" )

		self.assertTrue( cubeCurve.arePrimitiveVariablesValid() )
		self.assertEqual( cubeCurve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( cubeCurve["P"].data, cubeMotionP )
		self.assertEqual( cubeBound, cubeCurve.bound() )

		self.assertTrue( cameraCurve.arePrimitiveVariablesValid() )
		self.assertEqual( cameraCurve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( cameraCurve["P"].data, IECore.V3fVectorData( [
				imath.V3f( 0, 0.5, 5 ), imath.V3f( 0, 0.5, 6.25 ), imath.V3f( 0, 0.5, 7.5 ),
				imath.V3f( 0, 0.5, 8.75 ), imath.V3f( 0, 0.5, 10 )
			], IECore.GeometricData.Interpretation.Point )
		)
		self.assertEqual( cameraBound, cameraCurve.bound() )

		combinedBound = imath.Box3f()
		combinedBound.extendBy( cubeBound )
		combinedBound.extendBy( cameraBound )
		self.assertEqual( groupBound, combinedBound )

	def testComplexTransforms( self ) :

		script, expectedP = self.makeScene()
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( curve["P"].data, expectedP )
		self.assertEqual( bound, curve.bound() )

		# new motion gives a new curve
		script["cube"]["transform"]["translate"]["z"].setValue( 1 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( curve["P"].data, expectedP + IECore.V3fVectorData( [ imath.V3f( 0, 0, 1 ) ] * 5 ) )
		self.assertEqual( bound, curve.bound() )

		# parent motion gives a new curve
		script["group"]["transform"]["translate"]["y"].setValue( 2 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
			bound = script["motion"]["out"].bound( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 5 ] ) )
		self.assertEqual( curve["P"].data, expectedP + IECore.V3fVectorData( [ imath.V3f( 0, 2, 1 ) ] * 5 ) )
		self.assertEqual( bound, curve.bound() )

	def testSets( self ) :

		script, _ = self.makeScene()
		with script.context() :

			script["motionFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/cube", "/group/camera", "/group/light" ] ) )
			self.assertEqual( set( [ str(x) for x in script["motion"]["in"].setNames() ] ), { "geometry", "cameras", "lights", "__cameras", "__lights", "defaultLights" } )
			self.assertEqual( set( [ str(x) for x in script["motion"]["out"].setNames() ] ), { "geometry", "cameras", "lights" } )
			self.assertEqual( script["motion"]["out"].set( "geometry" ).value.paths(), [ "/group/cube", '/group/cube/sphere' ] )
			self.assertEqual( script["motion"]["out"].set( "cameras" ).value.paths(), [ "/group/camera" ] )
			self.assertEqual( script["motion"]["out"].set( "lights" ).value.paths(), [ "/group/light" ] )
			self.assertEqual( script["motion"]["out"].set( "__cameras" ).value.paths(), [] )
			self.assertEqual( script["motion"]["out"].set( "__lights" ).value.paths(), [] )
			self.assertEqual( script["motion"]["out"].set( "defaultLights" ).value.paths(), [] )

			script["camera"]["sets"].setValue( "cameras foo" )
			self.assertEqual( set( [ str(x) for x in script["motion"]["out"].setNames() ] ), { "geometry", "cameras", "lights", "foo" } )
			self.assertEqual( script["motion"]["out"].set( "cameras" ).value.paths(), [ "/group/camera" ] )
			self.assertEqual( script["motion"]["out"].set( "foo" ).value.paths(), [ "/group/camera" ] )

			script["camera"]["sets"].setValue( "bar" )
			self.assertEqual( set( [ str(x) for x in script["motion"]["out"].setNames() ] ), { "geometry", "lights", "bar" } )
			self.assertEqual( script["motion"]["out"].set( "cameras" ).value.paths(), [] )
			self.assertEqual( script["motion"]["out"].set( "bar" ).value.paths(), [ "/group/camera" ] )

			script["motionFilter"]["paths"].setValue( IECore.StringVectorData( [ "/group/light" ] ) )
			self.assertEqual( set( [ str(x) for x in script["motion"]["out"].setNames() ] ), { "geometry", "lights", "bar" } )
			self.assertEqual( script["motion"]["out"].set( "geometry" ).value.paths(), [] )
			self.assertEqual( script["motion"]["out"].set( "lights" ).value.paths(), [ "/group/light" ] )
			self.assertEqual( script["motion"]["out"].set( "bar" ).value.paths(), [] )

	def testShutterWithVariableSamples( self ) :

		script, expectedP = self.makeScene()
		script["motion"]["start"]["frame"].setValue( -0.25 )
		script["motion"]["end"]["frame"].setValue( 0.25 )
		script["motion"]["samplingMode"].setValue( GafferScene.MotionPath.SamplingMode.Variable )
		script["motion"]["step"].setValue( 0.1 )

		# on frame
		script.context().setFrame( 2 )
		onFrameSamples = IECore.FloatVectorData( [ 1.75, 1.85, 1.95, 2.05, 2.15, 2.25 ] )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 6 ] ) )
		for i in range( 0, len(curve["frame"].data) ) :
			self.assertAlmostEqual( curve["frame"].data[i], onFrameSamples[i], 5 )

		# shutter open
		script.context().setFrame( 1.75 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 6 ] ) )
		for i in range( 0, len(curve["frame"].data) ) :
			self.assertAlmostEqual( curve["frame"].data[i], onFrameSamples[i] - 0.25, 5 )

		# shutter close
		script.context().setFrame( 2.25 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 6 ] ) )
		for i in range( 0, len(curve["frame"].data) ) :
			self.assertAlmostEqual( curve["frame"].data[i], onFrameSamples[i] + 0.25, 5 )

	def testShutterWithFixedSamples( self ) :

		script, expectedP = self.makeScene()
		script["motion"]["start"]["frame"].setValue( -0.25 )
		script["motion"]["end"]["frame"].setValue( 0.25 )
		script["motion"]["samplingMode"].setValue( GafferScene.MotionPath.SamplingMode.Fixed )
		script["motion"]["samples"].setValue( 6 )

		# on frame
		script.context().setFrame( 2 )
		onFrameSamples = IECore.FloatVectorData( [ 1.75, 1.85, 1.95, 2.05, 2.15, 2.25 ] )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 6 ] ) )
		for i in range( 0, len(curve["frame"].data) ) :
			self.assertAlmostEqual( curve["frame"].data[i], onFrameSamples[i], 5 )

		# shutter open
		script.context().setFrame( 1.75 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 6 ] ) )
		for i in range( 0, len(curve["frame"].data) ) :
			self.assertAlmostEqual( curve["frame"].data[i], onFrameSamples[i] - 0.25, 5 )

		# shutter close
		script.context().setFrame( 2.25 )
		with script.context() :
			curve = script["motion"]["out"].object( "/group/cube" )
		self.assertTrue( curve.arePrimitiveVariablesValid() )
		self.assertEqual( curve.verticesPerCurve(), IECore.IntVectorData( [ 6 ] ) )
		for i in range( 0, len(curve["frame"].data) ) :
			self.assertAlmostEqual( curve["frame"].data[i], onFrameSamples[i] + 0.25, 5 )
