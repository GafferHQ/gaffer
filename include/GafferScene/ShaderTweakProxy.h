//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#pragma once

#include "GafferScene/Shader.h"

namespace GafferScene
{

class GAFFERSCENE_API ShaderTweakProxy : public Shader
{

	public :

		ShaderTweakProxy( const std::string &name = defaultName<ShaderTweakProxy>() );

		~ShaderTweakProxy() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::ShaderTweakProxy, ShaderTweakProxyTypeId, Shader );

		// Use this to set up a proxy for a specific type of shader - for auto proxies, call setupAutoProxy
		// instead. The shader name passed in should start with a type prefix followed by a colon, to
		// indicate how we need to load a shader in order to find its outputs to create a proxy. For example
		// "osl:Conversion/ColorToFloat" means we will look for an OSL shader named "Conversion/ColorToFloat",
		// and set up a proxy with matching output plugs. keepExistingValues is ignored, because proxies have
		// only outputs.
		void loadShader( const std::string &shaderName, bool keepExistingValues=false ) override;

		// Auto-proxies connect to the original input of whatever parameter you are tweaking on a ShaderTweaks.
		// They use dynamic plugs to store the type of their output - the reference plug provides the type
		// of plug to create.
		void setupAutoProxy( const Gaffer::Plug* referencePlug );

		// Parse the current shader name for the type prefix and source shader name
		void typePrefixAndSourceShaderName( std::string &typePrefix, std::string &sourceShaderName ) const;

		// Identify if a shader is a proxy, created by ShaderTweakProxy
		static bool isProxy( const IECoreScene::Shader *shader );

		template<class T>
		struct ShaderLoaderDescription
		{
			ShaderLoaderDescription( const std::string &typePrefix )
			{
				registerShaderLoader( typePrefix, []() -> GafferScene::ShaderPtr{ return new T(); } );
			}
		};

	private :

		using ShaderLoaderCreator = std::function< ShaderPtr() >;
		using ShaderLoaderCreatorMap = std::map< std::string, ShaderTweakProxy::ShaderLoaderCreator >;
		static ShaderLoaderCreatorMap &shaderLoaderCreators();

		static void registerShaderLoader( const std::string &typePrefix, ShaderLoaderCreator creator );

		static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( ShaderTweakProxy )

} // namespace GafferScene
