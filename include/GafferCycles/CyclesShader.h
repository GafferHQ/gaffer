//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Alex Fuller. All rights reserved.
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

#include "GafferCycles/Export.h"
#include "GafferCycles/TypeIds.h"

#include "GafferScene/Shader.h"

namespace GafferCycles
{

class GAFFERCYCLES_API CyclesShader : public GafferScene::Shader
{

	public :

		CyclesShader( const std::string &name=defaultName<CyclesShader>() );
		~CyclesShader() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferCycles::CyclesShader, CyclesShaderTypeId, GafferScene::Shader );

		void loadShader( const std::string &shaderName, bool keepExistingValues=false ) override;

	protected :

		/// Overrides attributes for when an AOV is assigned and we need to set the name of
		/// the AOV name eg. cycles:aov:customName
		IECore::ConstCompoundObjectPtr attributes( const Gaffer::Plug *output ) const override;

	private :

		// Shader metadata is stored in a "shader" member of the result and
		// parameter metadata is stored indexed by name inside a
		// "parameter" member of the result.
		const IECore::CompoundData *metadata() const;

		mutable IECore::ConstCompoundDataPtr m_metadata;
};

IE_CORE_DECLAREPTR( CyclesShader )

} // namespace GafferCycles
