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

import unittest

import arnold

import IECoreArnold

import Gaffer
import GafferUSD
import GafferSceneTest

class USDLightTest( GafferSceneTest.SceneTestCase ) :

	def __assertArnoldParameters( self, name, expectedParameters ) :

		light = GafferUSD.USDLight()
		light.loadShader( name )

		expectedParameters += [
			# Parameters common to all lights.
			( "arnold:aov", Gaffer.StringPlug, "default" ),
			( "arnold:samples", Gaffer.IntPlug, 1 ),
			( "arnold:volume_samples", Gaffer.IntPlug, 2 ),
			( "arnold:sss", Gaffer.FloatPlug, 1.0 ),
			( "arnold:indirect", Gaffer.FloatPlug, 1.0 ),
			( "arnold:volume", Gaffer.FloatPlug, 1.0 ),
			( "arnold:cast_volumetric_shadows", Gaffer.BoolPlug, True ),
			( "arnold:max_bounces", Gaffer.IntPlug, 999 ),
		]

		allNames = set()
		for name, plugType, defaultValue in expectedParameters :
			with self.subTest( name = name ) :
				allNames.add( name )
				self.assertIn( name, light["parameters"] )
				plug = light["parameters"][name]
				self.assertIsInstance( plug, Gaffer.OptionalValuePlug )
				self.assertEqual( plug.direction(), Gaffer.Plug.Direction.In )
				self.assertEqual( plug.getFlags(), Gaffer.Plug.Flags.Default )
				self.assertEqual( plug["enabled"].defaultValue(), False )
				self.assertIs( type( plug["value"] ), plugType )
				self.assertEqual( plug["value"].defaultValue(), defaultValue )
				self.assertTrue( plug.isSetToDefault() )

		self.assertEqual(
			allNames, { k for k in light["parameters"].keys() if k.startswith( "arnold:" ) }
		)

	def testRectLightParameters( self ) :

		self.__assertArnoldParameters(
			"RectLight",
			[
				( "arnold:roundness", Gaffer.FloatPlug, 0.0 ),
				( "arnold:soft_edge", Gaffer.FloatPlug, 0.0 ),
				( "arnold:spread", Gaffer.FloatPlug, 1.0 ),
				( "arnold:resolution", Gaffer.IntPlug, 512 ),
				( "arnold:camera", Gaffer.FloatPlug, 0.0 ),
				( "arnold:transmission", Gaffer.FloatPlug, 0.0 ),
			]
		)

	def testPointLightParameters( self ) :

		self.__assertArnoldParameters(
			"SphereLight",
			[
				( "arnold:camera", Gaffer.FloatPlug, 0.0 ),
				( "arnold:transmission", Gaffer.FloatPlug, 0.0 ),
			]
		)

	def testRectLightParameters( self ) :

		self.__assertArnoldParameters(
			"RectLight",
			[
				( "arnold:roundness", Gaffer.FloatPlug, 0.0 ),
				( "arnold:soft_edge", Gaffer.FloatPlug, 0.0 ),
				( "arnold:spread", Gaffer.FloatPlug, 1.0 ),
				( "arnold:resolution", Gaffer.IntPlug, 512 ),
				( "arnold:camera", Gaffer.FloatPlug, 0.0 ),
				( "arnold:transmission", Gaffer.FloatPlug, 0.0 ),
			]
		)

	def testDefaultParameterValues( self ) :

		light = GafferUSD.USDLight()

		for usdLight, arnoldLight in [
			( "SphereLight", "point_light" ),
			( "RectLight", "quad_light" ),
			( "DiskLight", "disk_light" ),
			( "DomeLight", "skydome_light" ),
			( "CylinderLight", "cylinder_light" ),
			( "DistantLight", "distant_light" ),
		] :

			with self.subTest( usdLight = usdLight ) :

				light.loadShader( usdLight )

				with IECoreArnold.UniverseBlock( writable = False ) :

					arnoldNode = arnold.AiNodeEntryLookUp( arnoldLight )

					for plug in light["parameters"].values() :

						if not plug.getName().startswith( "arnold:" ) :
							continue

						param = arnold.AiNodeEntryLookUpParameter( arnoldNode, plug.getName().replace( "arnold:", "" ) )
						self.assertIsNotNone( param )

						match arnold.AiParamGetType( param ) :
							case arnold.AI_TYPE_BOOLEAN :
								paramDefault = arnold.AiParamGetDefault( param ).contents.BOOL
							case arnold.AI_TYPE_INT :
								paramDefault = arnold.AiParamGetDefault( param ).contents.INT
							case arnold.AI_TYPE_FLOAT :
								paramDefault = arnold.AiParamGetDefault( param ).contents.FLT
							case arnold.AI_TYPE_STRING :
								paramDefault = arnold.AtStringToStr( arnold.AiParamGetDefault( param ).contents.STR )
							case arnold.AI_TYPE_ENUM :
								enum = arnold.AiParamGetEnum( param )
								paramDefault = arnold.AiEnumGetString(
									arnold.AiParamGetEnum( param ),
									arnold.AiParamGetDefault( param ).contents.INT
								)
							case _ :
								self.fail( "Unhandled parameter type for {}".format( plug.getName() ) )

						self.assertEqual( plug["value"].defaultValue(), paramDefault, plug.getName() )

if __name__ == "__main__":
	unittest.main()
