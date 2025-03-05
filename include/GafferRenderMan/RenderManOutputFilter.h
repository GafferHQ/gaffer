//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferRenderMan/Export.h"
#include "GafferRenderMan/TypeIds.h"

#include "GafferScene/GlobalsProcessor.h"
#include "GafferScene/ShaderPlug.h"

namespace GafferRenderMan
{

/// Base class which contains all the shared implementation for RenderManDisplayFilter
/// and RenderManSampleFilter.
class GAFFERRENDERMAN_API RenderManOutputFilter : public GafferScene::GlobalsProcessor
{

	public :

		~RenderManOutputFilter() override;

		GAFFER_NODE_DECLARE_TYPE( GafferRenderMan::RenderManOutputFilter, RenderManOutputFilterTypeId, GafferScene::GlobalsProcessor );

		enum class Mode
		{
			Replace,
			InsertFirst,
			InsertLast
		};

		GafferScene::ShaderPlug *shaderPlug();
		const GafferScene::ShaderPlug *shaderPlug() const;

		Gaffer::IntPlug *modePlug();
		const Gaffer::IntPlug *modePlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		enum class FilterType
		{
			Display,
			Sample
		};

		RenderManOutputFilter( const std::string &name, FilterType filterType );

		bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const override;

		void hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const override;

	private :

		const FilterType m_filterType;
		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( RenderManOutputFilter )

} // namespace GafferRenderMan
