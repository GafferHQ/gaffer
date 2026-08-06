##########################################################################
#
#  Copyright (c) 2026, Cinesite VFX Ltd. All rights reserved.
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

import math
import unittest

import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class PointInstancerCoreTest( GafferSceneTest.SceneTestCase ) :

	def testConvertToPointInstancer( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 10 ) ] ) )
		mesh = IECoreScene.MeshPrimitive.createSphere( 1 )

		core = GafferScene.PointInstancerCore()

		for inputPrimitive in [ points, mesh ] :

			core["inPoints"].setValue( inputPrimitive )

			pointInstancer = core["outPoints"].getValue()
			self.assertIsInstance( pointInstancer, IECoreScene.PointInstancer )
			self.assertTrue( pointInstancer.arePrimitiveVariablesValid() )
			self.assertIn( "P", pointInstancer )
			for k in inputPrimitive.keys() :
				if inputPrimitive[k].interpolation not in (
					IECoreScene.PrimitiveVariable.Interpolation.Constant,
					IECoreScene.PrimitiveVariable.Interpolation.Vertex
				) :
					continue
				self.assertEqual( pointInstancer[k], inputPrimitive[k] )

	def testPrototypeNamesUnique( self ) :

		points = IECoreScene.MeshPrimitive.createSphere( 1.0 )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [
				"/path/to/cube",
				"/path/to/sphere",
				"/path/to/another/cube",
				"/sphere",
				"/plane",
			] )
		)
		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )

		self.assertEqual(
			list( core["prototypeNames"].getValue() ),
			[ "cube", "sphere", "cube1", "sphere1", "plane" ]
		)

	def testUsingRootAsPrototype( self ) :

		points = IECoreScene.MeshPrimitive.createSphere( 1.0 )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [ "/" ] )
		)
		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )

		self.assertEqual( list( core["prototypeNames"].getValue() ), [ "prototype" ] )

		core["prototypeSelector"].setValue( "prototype" )
		self.assertEqual( core["prototype"].getValue(), "/" )

	def testPrototypeOutput( self ) :

		points = IECoreScene.MeshPrimitive.createSphere( 1.0 )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [
				"/path/to/cube",
				"/path/to/sphere",
			] )
		)

		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )

		core["prototypeSelector"].setValue( "cube" )
		self.assertEqual( core["prototype"].getValue(), "/path/to/cube" )

		core["prototypeSelector"].setValue( "sphere" )
		self.assertEqual( core["prototype"].getValue(), "/path/to/sphere" )

	def testTimeOffsets( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 4 ) ] ) )
		points["timeOffset"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0.0, 1.5, 0.0, 1.5 ] )
		)
		points["prototypeIndex"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 0, 0, 1 ] )
		)
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [
				"/path/to/cube",
				"/path/to/sphere",
			] )
		)

		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )
		core["timeOffset"].setValue( "timeOffset" )

		self.assertEqual( list( core["prototypeNames"].getValue() ), [ "cube_0", "cube_1_5", "sphere_1_5" ] )

		core["prototypeSelector"].setValue( "cube_0" )
		self.assertEqual( core["prototype"].getValue(), "/path/to/cube" )
		self.assertEqual( core["prototypeTimeOffset"].getValue(), 0 )

		core["prototypeSelector"].setValue( "cube_1_5" )
		self.assertEqual( core["prototype"].getValue(), "/path/to/cube" )
		self.assertEqual( core["prototypeTimeOffset"].getValue(), 1.5 )

		core["prototypeSelector"].setValue( "sphere_1_5" )
		self.assertEqual( core["prototype"].getValue(), "/path/to/sphere" )
		self.assertEqual( core["prototypeTimeOffset"].getValue(), 1.5 )

	def testContextVariables( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 2 ) ] ) )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [ "/path/to/cube" ] )
		)
		points["varA"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 0.0, 1.5 ] )
		)
		points["varB"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 3, 4 ] )
		)
		points["varC"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.StringVectorData( [ "foo", "bar" ] )
		)

		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )
		core["contextVariables"].setValue( "var*" )

		self.assertEqual( list( core["prototypeNames"].getValue() ), [ "cube_varA_0_varB_3_varC_foo", "cube_varA_1_5_varB_4_varC_bar" ] )

		core["prototypeSelector"].setValue( "cube_varA_0_varB_3_varC_foo" )
		self.assertEqual(
			core["prototypeContext"].getValue(), IECore.CompoundData( {
				"varA" : IECore.FloatData( 0 ), "varB" : IECore.IntData( 3 ), "varC" : IECore.StringData( "foo" )
			} )
		)

		core["prototypeSelector"].setValue( "cube_varA_1_5_varB_4_varC_bar" )
		self.assertEqual(
			core["prototypeContext"].getValue(), IECore.CompoundData( {
				"varA" : IECore.FloatData( 1.5 ), "varB" : IECore.IntData( 4 ), "varC" : IECore.StringData( "bar" )
			} )
		)

		points = core["outPoints"].getValue()
		self.assertEqual( points["prototypeIndex"].data, IECore.IntVectorData( [ 0, 1 ] ) )

	def testPrototypeNamesUniqueWithContextVariables( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 2 ) ] ) )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [ "/path/to/cube" ] )
		)
		points["varA"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 0 ] )
		)

		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )
		core["contextVariables"].setValue( "varA" )

		self.assertEqual( list( core["prototypeNames"].getValue() ), [ "cube_varA_0" ] )

	def testFloatFormatting( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 7 ) ] ) )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [ "/path/to/cube" ] )
		)
		points["varA"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ -1.0, 0.0000, 1.5, 1000.654, 1e6, -1e6, math.inf ] )
		)

		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )
		core["contextVariables"].setValue( "varA" )

		self.assertEqual(
			list( core["prototypeNames"].getValue() ),
			[
				"cube_varA_n1", "cube_varA_0", "cube_varA_1_5", "cube_varA_1000_654",
				"cube_varA_1000000", "cube_varA_n1000000", "cube_varA_inf"
			]
		)

	def testPrototypeFormat( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( x ) for x in range( 0, 2 ) ] ) )
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [ "/path/to/cube" ] )
		)
		points["varA"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 0, 1 ] )
		)
		points["varB"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 3, 4 ] )
		)

		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )
		core["contextVariables"].setValue( "var*" )

		hash0 = "75ce4fb5bb7bde761e58ae729339376e"
		hash1 = "b5eee4915c21320b8974886032857915"

		for format, expectedNames in {
			"{name}:b{varB}:a{varA}" : [ "cube:b3:a0", "cube:b4:a1" ],
			"{name}_b{varB}_a{varA}_suffix" : [ "cube_b3_a0_suffix", "cube_b4_a1_suffix" ],
			"{hash}" : [ hash0, hash1 ],
			# Incomplete names get the hash appended automatically.
			"{name}" : [ f"cube_{hash0}", f"cube_{hash1}" ],
			"{name}_{varA}" : [ f"cube_0_{hash0}", f"cube_1_{hash1}" ],
			"prototype" : [ f"prototype_{hash0}", f"prototype_{hash1}" ],
		}.items() :

			with self.subTest( format = format ) :

				core["prototypeFormat"].setValue( format )
				self.assertEqual( list( core["prototypeNames"].getValue() ), expectedNames )

	def testInvalidPrototypeIndex( self ) :

		points = IECoreScene.PointsPrimitive( IECore.V3fVectorData( [ imath.V3f( 0 ) ] ) )
		points["prototypeIndex"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.IntVectorData( [ 1 ] )
		)
		points["prototypeRoots"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Constant,
			IECore.StringVectorData( [
				"/path/to/cube",
			] )
		)
		points["timeOffset"] = IECoreScene.PrimitiveVariable(
			IECoreScene.PrimitiveVariable.Interpolation.Vertex,
			IECore.FloatVectorData( [ 1.5 ] )
		)

		core = GafferScene.PointInstancerCore()
		core["inPoints"].setValue( points )

		# When there's no variation, we don't rely on the index, so
		# just pass it through, valid or not.

		self.assertEqual( core["outPoints"].getValue()["prototypeIndex"], points["prototypeIndex"] )

		# But when asked to do variation, we depend on the index, so
		# must throw.

		core["timeOffset"].setValue( "timeOffset" )
		with self.assertRaisesRegex( Gaffer.ProcessException, r".*Prototype index 1 out of range \(on point 0\)" ) :
			core["outPoints"].getValue()

if __name__ == "__main__":
	unittest.main()
