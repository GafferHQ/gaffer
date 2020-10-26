//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERARNOLD_ARNOLDSHADER_H
#define GAFFERARNOLD_ARNOLDSHADER_H

#include "GafferArnold/Export.h"
#include "GafferArnold/TypeIds.h"

#include "GafferScene/Shader.h"

namespace GafferArnold
{

class GAFFERARNOLD_API ArnoldShader : public GafferScene::Shader
{

	public :

		ArnoldShader( const std::string &name=defaultName<ArnoldShader>() );
		~ArnoldShader() override;

		GAFFER_NODE_DECLARE_TYPE( GafferArnold::ArnoldShader, ArnoldShaderTypeId, GafferScene::Shader );

		/// Implemented for outPlug(), returning the parameter named in the "primaryInput"
		/// shader annotation if it has been specified.
		Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) override;
		const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const override;

		void loadShader( const std::string &shaderName, bool keepExistingValues=false ) override;

	private :

		// Shader metadata is stored in a "shader" member of the result and
		// parameter metadata is stored indexed by name inside a
		// "parameter" member of the result.
		const IECore::CompoundData *metadata() const;

		mutable IECore::ConstCompoundDataPtr m_metadata;
};

IE_CORE_DECLAREPTR( ArnoldShader )

} // namespace GafferArnold

#endif // GAFFERARNOLD_ARNOLDSHADER_H
