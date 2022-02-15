//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFERARNOLD_ARNOLDCOLORMANAGER_H
#define GAFFERARNOLD_ARNOLDCOLORMANAGER_H

#include "GafferArnold/Export.h"
#include "GafferArnold/TypeIds.h"

#include "GafferScene/GlobalsProcessor.h"
#include "GafferScene/ShaderPlug.h"

#include "Gaffer/StringPlug.h"

namespace GafferArnold
{

class ArnoldShader;

class GAFFERARNOLD_API ArnoldColorManager : public GafferScene::GlobalsProcessor
{

	public :

		ArnoldColorManager( const std::string &name=defaultName<ArnoldColorManager>() );
		~ArnoldColorManager() override;

		GAFFER_NODE_DECLARE_TYPE( GafferArnold::ArnoldColorManager, ArnoldColorManagerTypeId, GafferScene::GlobalsProcessor );

		Gaffer::Plug *parametersPlug();
		const Gaffer::Plug *parametersPlug() const;

		void loadColorManager( const std::string &name, bool keepExistingValues=false );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const override;

	private :

		GafferScene::ShaderPlug *shaderInPlug();
		const GafferScene::ShaderPlug *shaderInPlug() const;

		ArnoldShader *shaderNode();
		const ArnoldShader *shaderNode() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ArnoldColorManager )

} // namespace GafferArnold

#endif // GAFFERARNOLD_ARNOLDCOLORMANAGER_H
