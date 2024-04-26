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

import Gaffer
import GafferScene
import GafferSceneTest

import GafferScene.RenderPassTypeAdaptor

class RenderPassTypeAdaptorTest( GafferSceneTest.SceneTestCase ) :

	@staticmethod
	def __typeAProcessor() :

		result = GafferScene.CustomOptions()
		result["options"].addChild( Gaffer.NameValuePlug( "typeA", True ) )
		return result

	@staticmethod
	def __typeBProcessor() :

		result = GafferScene.CustomOptions()
		result["options"].addChild( Gaffer.NameValuePlug( "typeB", True ) )
		return result

	def testTypeProcessorRegistration( self ) :

		self.assertNotIn( "Test", GafferScene.RenderPassTypeAdaptor.registeredTypeNames() )

		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "Test", "Main", self.__typeAProcessor )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "Test", "Main" )

		self.assertIn( "Test", GafferScene.RenderPassTypeAdaptor.registeredTypeNames() )
		self.assertIn( "Main", GafferScene.RenderPassTypeAdaptor.registeredTypeProcessors( "Test" ) )

		GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor( "Test", "Main" )

		self.assertNotIn( "Test", GafferScene.RenderPassTypeAdaptor.registeredTypeNames() )

	def testTypeProcessorScope( self ) :

		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "TestA", "Test", self.__typeAProcessor )
		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "TestB", "Test", self.__typeBProcessor )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "TestA", "Test" )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "TestB", "Test" )

		renderPassType = GafferScene.CustomOptions()
		renderPassType["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "" ) )

		typeAdaptor = GafferScene.RenderPassTypeAdaptor()
		typeAdaptor["in"].setInput( renderPassType["out"] )

		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "TestA" )
		self.assertIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "TestB" )
		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "TestC" )
		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

	def testChainedTypeProcessors( self ) :

		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "Test", "TypeA", self.__typeAProcessor )
		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "Test", "TypeB", self.__typeBProcessor )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "Test", "TypeA" )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "Test", "TypeB" )

		renderPassType = GafferScene.CustomOptions()
		renderPassType["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "" ) )

		typeAdaptor = GafferScene.RenderPassTypeAdaptor()
		typeAdaptor["in"].setInput( renderPassType["out"] )

		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "NotAType" )

		self.assertNotIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

		renderPassType["options"][0]["value"].setValue( "Test" )

		self.assertIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertIn( "option:typeB", typeAdaptor["out"].globals() )

		GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor( "Test", "TypeB" )

		typeAdaptor = GafferScene.RenderPassTypeAdaptor()
		typeAdaptor["in"].setInput( renderPassType["out"] )

		self.assertIn( "option:typeA", typeAdaptor["out"].globals() )
		self.assertNotIn( "option:typeB", typeAdaptor["out"].globals() )

	def testAutoTypeFunction( self ) :

		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "shadow", "Test", self.__typeAProcessor )
		GafferScene.RenderPassTypeAdaptor.registerTypeProcessor( "reflection", "Test", self.__typeBProcessor )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "shadow", "Test" )
		self.addCleanup( GafferScene.RenderPassTypeAdaptor.deregisterTypeProcessor, "shadow", "Test" )

		def f( name ) :

			return name.split("_")[-1] if "_" in name else ""

		GafferScene.RenderPassTypeAdaptor.registerAutoTypeFunction( f )

		self.assertEqual( GafferScene.RenderPassTypeAdaptor.resolvedType( "auto", "test_shadow" ), "shadow" )

		renderPassTypeOption = GafferScene.CustomOptions()
		renderPassTypeOption["options"].addChild( Gaffer.NameValuePlug( "renderPass:type", "" ) )

		typeAdaptor = GafferScene.RenderPassTypeAdaptor()
		typeAdaptor["in"].setInput( renderPassTypeOption["out"] )

		for renderPassName, renderPassType, expected, notExpected in (
			( "test_shadow", "auto", "option:typeA", "option:typeB" ),
			( "test_reflection", "auto", "option:typeB", "option:typeA" )
		) :
			renderPassTypeOption["options"][0]["value"].setValue( renderPassType )
			with Gaffer.Context() as context :
				context["renderPass"] = renderPassName
				self.assertIn( expected, typeAdaptor["out"].globals() )
				self.assertNotIn( notExpected, typeAdaptor["out"].globals() )

if __name__ == "__main__":
	unittest.main()
