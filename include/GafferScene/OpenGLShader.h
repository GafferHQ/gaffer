//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

class GAFFERSCENE_API OpenGLShader : public GafferScene::Shader
{

	public :

		explicit OpenGLShader( const std::string &name=defaultName<OpenGLShader>() );
		~OpenGLShader() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::OpenGLShader, OpenGLShaderTypeId, GafferScene::Shader );

		void loadShader( const std::string &shaderName, bool keepExistingValues=false ) override;

	protected :

		/// Reimplemented to allow ImageNodes to be plugged in to texture parameters.
		void parameterHash( const Gaffer::Plug *parameterPlug, IECore::MurmurHash &h ) const override;
		IECore::DataPtr parameterValue( const Gaffer::Plug *parameterPlug ) const override;

		/// Reimplemented to allow glsl source specified by specifically named parameters.
		/// Use a StringPlug named "glVertexSource", "glGeometrySource", or "glFragmentSource"
		/// to specify the various types of glsl source code.
		IECore::ConstCompoundObjectPtr attributes( const Gaffer::Plug *output ) const override;

};

IE_CORE_DECLAREPTR( OpenGLShader )

} // namespace GafferScene
