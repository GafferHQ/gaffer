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

#include "GafferScene/ScenePlug.h"

#include "Gaffer/ContextProcessor.h"
#include "Gaffer/ShufflePlug.h"

namespace GafferScene
{

class GAFFERSCENE_API ShuffleRenderPasses : public Gaffer::ContextProcessor
{

	public :

		explicit ShuffleRenderPasses( const std::string &name=defaultName<ShuffleRenderPasses>() );
		~ShuffleRenderPasses() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::ShuffleRenderPasses, ShuffleRenderPassesTypeId, Gaffer::ContextProcessor );

		GafferScene::ScenePlug *inPlug();
		const GafferScene::ScenePlug *inPlug() const;

		GafferScene::ScenePlug *outPlug();
		const GafferScene::ScenePlug *outPlug() const;

		Gaffer::ShufflesPlug *shufflesPlug();
		const Gaffer::ShufflesPlug *shufflesPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		bool affectsContext( const Gaffer::Plug *input ) const override;
		void processContext( Gaffer::Context::EditableScope &context, IECore::ConstRefCountedPtr &storage ) const override;

	private :

		class ProcessedScope;

		Gaffer::StringPlug *sourceNamePlug();
		const Gaffer::StringPlug *sourceNamePlug() const;

		Gaffer::ObjectPlug *mappingPlug();
		const Gaffer::ObjectPlug *mappingPlug() const;

		void hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const;
		IECore::ConstCompoundObjectPtr computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ShuffleRenderPasses );

} // namespace GafferScene
