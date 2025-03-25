//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "GafferDispatch/TaskNode.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

class GAFFERSCENE_API Render : public GafferDispatch::TaskNode
{

	public :

		explicit Render( const std::string &name=defaultName<Render>() );
		~Render() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Render, GafferScene::RenderTypeId, GafferDispatch::TaskNode );

		enum Mode
		{
			RenderMode = 0,
			SceneDescriptionMode = 1
		};

		ScenePlug *inPlug();
		const ScenePlug *inPlug() const;

		Gaffer::StringPlug *rendererPlug();
		const Gaffer::StringPlug *rendererPlug() const;

		Gaffer::IntPlug *modePlug();
		const Gaffer::IntPlug *modePlug() const;

		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		ScenePlug *outPlug();
		const ScenePlug *outPlug() const;

		Gaffer::StringPlug *resolvedRendererPlug();
		const Gaffer::StringPlug *resolvedRendererPlug() const;

		using RenderSignal = Gaffer::Signals::Signal<void ( const Render * ), Gaffer::Signals::CatchingCombiner<void>>;
		// Signal emitted prior to rendering. When executing a sequence, this is
		// emitted once per frame.
		static RenderSignal &preRenderSignal();
		// Signal emitted after a render has been completed. When executing a
		// sequence, this is emitted once per frame.
		static RenderSignal &postRenderSignal();

	protected :

		void preTasks( const Gaffer::Context *context, Tasks &tasks ) const override;
		void postTasks( const Gaffer::Context *context, Tasks &tasks ) const override;
		IECore::MurmurHash hash( const Gaffer::Context *context ) const override;
		void execute() const override;
		void executeSequence( const std::vector<float> &frames ) const override;

	private :

		void executeInternal( bool flushCaches ) const;

		ScenePlug *adaptedInPlug();
		const ScenePlug *adaptedInPlug() const;

		static size_t g_firstPlugIndex;

		// Friendship for the bindings
		friend struct GafferDispatchBindings::Detail::TaskNodeAccessor;

};

IE_CORE_DECLAREPTR( Render );

} // namespace GafferScene
