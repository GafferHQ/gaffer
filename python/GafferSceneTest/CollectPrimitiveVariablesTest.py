##########################################################################
#
#  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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
import imath

import IECore
import IECoreScene

import Gaffer
import GafferScene
import GafferSceneTest

class CollectPrimitiveVariablesTest( GafferSceneTest.SceneTestCase ) :

	def test( self ) :

		# Make a few input scenes

		script = Gaffer.ScriptNode()

		script["Cube"] = GafferScene.Cube( "Cube" )
		script["PathFilter"] = GafferScene.PathFilter( "PathFilter" )
		script["PathFilter"]["paths"].setValue( IECore.StringVectorData( [ '/cube' ] ) )
		script["Transform"] = GafferScene.Transform( "Transform" )
		script["Transform"]["in"].setInput( script["Cube"]["out"] )
		script["Transform"]["filter"].setInput( script["PathFilter"]["out"] )
		script["FreezeTransform"] = GafferScene.FreezeTransform( "FreezeTransform" )
		script["FreezeTransform"]["in"].setInput( script["Transform"]["out"] )
		script["FreezeTransform"]["filter"].setInput( script["PathFilter"]["out"] )
		script["PrimitiveVariables"] = GafferScene.PrimitiveVariables( "PrimitiveVariables" )
		script["PrimitiveVariables"]["primitiveVariables"].addChild( Gaffer.CompoundDataPlug.MemberPlug( "member1" ) )
		script["PrimitiveVariables"]["primitiveVariables"]["member1"].addChild( Gaffer.StringPlug( "name" ) )
		script["PrimitiveVariables"]["primitiveVariables"]["member1"].addChild( Gaffer.Color3fPlug( "value" ) )
		script["PrimitiveVariables"]["primitiveVariables"]["member1"].addChild( Gaffer.BoolPlug( "enabled", defaultValue = True ) )
		script["PrimitiveVariables"]["in"].setInput( script["FreezeTransform"]["out"] )
		script["PrimitiveVariables"]["filter"].setInput( script["PathFilter"]["out"] )
		script["PrimitiveVariables"]["primitiveVariables"]["member1"]["name"].setValue( 'Cs' )
		script["CollectPrimitiveVariables"] = GafferScene.CollectPrimitiveVariables( "CollectPrimitiveVariables" )
		script["CollectPrimitiveVariables"]["in"].setInput( script["PrimitiveVariables"]["out"] )
		script["CollectPrimitiveVariables"]["filter"].setInput( script["PathFilter"]["out"] )
		script["Expression1"] = Gaffer.Expression( "Expression1" )
		script["Expression1"].setExpression( """
s =  context.get( "collect:primitiveVariableSuffix", "_suffix0" )
i = int( s[7] )
parent["Transform"]["transform"]["translate"] = imath.V3f( i )
parent["PrimitiveVariables"]["primitiveVariables"]["member1"]["value"] = imath.V3f( i )""", "python" )

		defaultCube = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( -0.5 ), imath.V3f( 0.5 ) ) )
		defaultCubeOff1 = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( 0.5 ), imath.V3f( 1.5 ) ) )
		defaultCubeOff2 = IECoreScene.MeshPrimitive.createBox( imath.Box3f( imath.V3f( 1.5 ), imath.V3f( 2.5 ) ) )


		self.assertEqual( set(script["CollectPrimitiveVariables"]["out"].object( "/cube" ).keys()), set([ "P", "N", "uv", "Cs" ]) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P"], defaultCube["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["N"], defaultCube["N"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["uv"], defaultCube["uv"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs"].data.value, imath.Color3f( 0 ) )

		script["CollectPrimitiveVariables"]["suffixes"].setValue( IECore.StringVectorData( [ '_suffix1', '_suffix2' ] ) )

		self.assertEqual( set(script["CollectPrimitiveVariables"]["out"].object( "/cube" ).keys()), set([ "P", "N", "uv", "P_suffix1", "P_suffix2", "Cs" ]) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P"], defaultCube["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P_suffix1"], defaultCubeOff1["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P_suffix2"], defaultCubeOff2["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs"].data.value, imath.Color3f( 0 ) )

		script["CollectPrimitiveVariables"]["primitiveVariables"].setValue( "P Cs" )

		self.assertEqual( set(script["CollectPrimitiveVariables"]["out"].object( "/cube" ).keys()), set([ "P", "N", "uv", "P_suffix1", "P_suffix2", "Cs", "Cs_suffix1", "Cs_suffix2" ]) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P"], defaultCube["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P_suffix1"], defaultCubeOff1["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P_suffix2"], defaultCubeOff2["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs"].data.value, imath.Color3f( 0 ) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs_suffix1"].data.value, imath.Color3f( 1 ) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs_suffix2"].data.value, imath.Color3f( 2 ) )

		script["CollectPrimitiveVariables"]["primitiveVariables"].setValue( "Cs" )

		self.assertEqual( set(script["CollectPrimitiveVariables"]["out"].object( "/cube" ).keys()), set([ "P", "N", "uv", "Cs", "Cs_suffix1", "Cs_suffix2" ]) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P"], defaultCube["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs"].data.value, imath.Color3f( 0 ) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs_suffix1"].data.value, imath.Color3f( 1 ) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs_suffix2"].data.value, imath.Color3f( 2 ) )

		script["CollectPrimitiveVariables"]["suffixContextVariable"].setValue( "collect:customVar" )

		self.assertEqual( set(script["CollectPrimitiveVariables"]["out"].object( "/cube" ).keys()), set([ "P", "N", "uv", "Cs", "Cs_suffix1", "Cs_suffix2" ]) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P"], defaultCube["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs"].data.value, imath.Color3f( 0 ) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs_suffix1"].data.value, imath.Color3f( 0 ) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs_suffix2"].data.value, imath.Color3f( 0 ) )

		script["CollectPrimitiveVariables"]["requireVariation"].setValue( True )

		self.assertEqual( set(script["CollectPrimitiveVariables"]["out"].object( "/cube" ).keys()), set([ "P", "N", "uv", "Cs" ]) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P"], defaultCube["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs"].data.value, imath.Color3f( 0 ) )

		self.assertEqual( script["CollectPrimitiveVariables"]["out"].objectHash( "/cube" ),
			script["PrimitiveVariables"]["out"].objectHash( "/cube" )
		)

		script["Expression1"].setExpression( """
s =  context.get( "collect:customVar", "_suffix0" )
i = int( s[7] )
parent["Transform"]["transform"]["translate"] = imath.V3f( i )
parent["PrimitiveVariables"]["primitiveVariables"]["member1"]["value"] = imath.V3f( i )""", "python" )

		self.assertEqual( set(script["CollectPrimitiveVariables"]["out"].object( "/cube" ).keys()), set([ "P", "N", "uv", "Cs", "Cs_suffix1", "Cs_suffix2" ]) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["P"], defaultCube["P"] )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs"].data.value, imath.Color3f( 0 ) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs_suffix1"].data.value, imath.Color3f( 1 ) )
		self.assertEqual( script["CollectPrimitiveVariables"]["out"].object( "/cube" )["Cs_suffix2"].data.value, imath.Color3f( 2 ) )

if __name__ == "__main__":
	unittest.main()
