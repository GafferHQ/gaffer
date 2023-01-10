//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#ifndef GAFFEROSL_OSLSHADER_H
#define GAFFEROSL_OSLSHADER_H

#include "GafferOSL/Export.h"
#include "GafferOSL/TypeIds.h"

#include "GafferScene/Shader.h"

namespace GafferOSL
{

IE_CORE_FORWARDDECLARE( ShadingEngine )

class GAFFEROSL_API OSLShader : public GafferScene::Shader
{

	public :

		OSLShader( const std::string &name=defaultName<OSLShader>() );
		~OSLShader() override;

		GAFFER_NODE_DECLARE_TYPE( GafferOSL::OSLShader, OSLShaderTypeId, GafferScene::Shader );

		/// Returns a plug based on the "correspondingInput" metadata of each output plug
		Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) override;
		const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const override;

		/// \undoable.
		void loadShader( const std::string &shaderName, bool keepExistingValues=false ) override;

		void reloadShader() override;

		ConstShadingEnginePtr shadingEngine( const IECore::CompoundObject *substitutions = nullptr ) const;

		/// Returns an OSL metadata item from the shader.
		const IECore::Data *shaderMetadata( const IECore::InternedString &name ) const;
		/// Returns an OSL metadata item from the specified shader parameter.
		const IECore::Data *parameterMetadata( const Gaffer::Plug *plug, const IECore::InternedString &name ) const;

		/// Allows other renderer shaders to connect to OSL shaders by registering them.
		/// Returns true on success, false if already added.
		static bool registerCompatibleShader( const IECore::InternedString shaderType );


	protected :

		bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const override;

	private :

		// Shader metadata is stored in a "shader" member of the result and
		// parameter metadata is stored indexed by name inside a
		// "parameter" member of the result.
		const IECore::CompoundData *metadata() const;

		mutable IECore::ConstCompoundDataPtr m_metadata;

};

IE_CORE_DECLAREPTR( OSLShader )

} // namespace GafferOSL

#endif // GAFFEROSL_OSLSHADER_H
