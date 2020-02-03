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

#include "GafferScene/Render.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/RendererAlgo.h"
#include "GafferScene/SceneNode.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/SceneProcessor.h"

#include "Gaffer/MonitorAlgo.h"
#include "Gaffer/PerformanceMonitor.h"

#include "IECore/ObjectPool.h"

#include "boost/filesystem.hpp"

#include <memory>

using namespace IECore;
using namespace IECoreScene;
using namespace Gaffer;
using namespace GafferDispatch;
using namespace GafferScene;

namespace
{

const InternedString g_performanceMonitorOptionName( "option:render:performanceMonitor" );
const InternedString g_sceneTranslationOnlyContextName( "scene:render:sceneTranslationOnly" );

struct RenderScope : public Context::EditableScope
{

	RenderScope( const Context *context )
		:	EditableScope( context ), m_sceneTranslationOnly( false )
	{
		if( auto d = context->get<BoolData>( g_sceneTranslationOnlyContextName, nullptr ) )
		{
			m_sceneTranslationOnly = d->readable();
			// Don't leak variable upstream.
			remove( g_sceneTranslationOnlyContextName );
		}
	}

	bool sceneTranslationOnly() const
	{
		return m_sceneTranslationOnly;
	}

	private :

		bool m_sceneTranslationOnly;

};

} // namespace

size_t Render::g_firstPlugIndex = 0;

static IECore::InternedString g_rendererContextName( "scene:renderer" );

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Render );

Render::Render( const std::string &name )
	:	Render( /* rendererType = */ InternedString(), name )
{
}

Render::Render( const IECore::InternedString &rendererType, const std::string &name )
	:	TaskNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
	addChild( new StringPlug( rendererType.string().empty() ? "renderer" : "__renderer", Plug::In, rendererType.string() ) );
	addChild( new IntPlug( "mode", Plug::In, RenderMode, RenderMode, SceneDescriptionMode ) );
	addChild( new StringPlug( "fileName" ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "__adaptedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	SceneProcessorPtr adaptors = GafferScene::RendererAlgo::createAdaptors();
	setChild( "__adaptors", adaptors );
	adaptors->inPlug()->setInput( inPlug() );
	adaptedInPlug()->setInput( adaptors->outPlug() );

	outPlug()->setInput( inPlug() );
}

Render::~Render()
{
}

ScenePlug *Render::inPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const ScenePlug *Render::inPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Render::rendererPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Render::rendererPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::IntPlug *Render::modePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::IntPlug *Render::modePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *Render::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *Render::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

ScenePlug *Render::outPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 4 );
}

const ScenePlug *Render::outPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 4 );
}

ScenePlug *Render::adaptedInPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 5 );
}

const ScenePlug *Render::adaptedInPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 5 );
}

void Render::preTasks( const Gaffer::Context *context, Tasks &tasks ) const
{
	RenderScope scope( context );
	TaskNode::preTasks( Context::current(), tasks );
}

void Render::postTasks( const Gaffer::Context *context, Tasks &tasks ) const
{
	RenderScope scope( context );
	TaskNode::postTasks( Context::current(), tasks );
}

IECore::MurmurHash Render::hash( const Gaffer::Context *context ) const
{
	if( inPlug()->source()->direction() != Plug::Out )
	{
		return IECore::MurmurHash();
	}

	RenderScope renderScope( context );

	const std::string rendererType = rendererPlug()->getValue();
	if( rendererType.empty() )
	{
		return IECore::MurmurHash();
	}

	const Mode mode = static_cast<Mode>( modePlug()->getValue() );
	const std::string fileName = fileNamePlug()->getValue();
	if( mode == SceneDescriptionMode && fileName.empty() )
	{
		return IECore::MurmurHash();
	}

	IECore::MurmurHash h = TaskNode::hash( context );
	h.append( (uint64_t)inPlug()->source<Plug>() );
	h.append( context->hash() );
	h.append( rendererType );
	h.append( mode );
	h.append( fileName );
	h.append( renderScope.sceneTranslationOnly() );

	return h;
}

void Render::execute() const
{
	if( inPlug()->source()->direction() != Plug::Out )
	{
		return;
	}

	RenderScope renderScope( Context::current() );

	const std::string rendererType = rendererPlug()->getValue();
	if( rendererType.empty() )
	{
		return;
	}

	renderScope.set( g_rendererContextName, rendererType );

	const Mode mode = static_cast<Mode>( modePlug()->getValue() );
	const std::string fileName = fileNamePlug()->getValue();
	if( mode == SceneDescriptionMode  )
	{
		if( fileName.empty() )
		{
			return;
		}
		else
		{
			boost::filesystem::path fileNamePath( fileName );
			boost::filesystem::path directoryPath = fileNamePath.parent_path();
			if( !directoryPath.empty() && !renderScope.sceneTranslationOnly() )
			{
				boost::filesystem::create_directories( directoryPath );
			}
		}
	}

	IECoreScenePreview::RendererPtr renderer = IECoreScenePreview::Renderer::create(
		rendererType,
		mode == RenderMode ? IECoreScenePreview::Renderer::Batch : IECoreScenePreview::Renderer::SceneDescription,
		fileName
	);
	if( !renderer )
	{
		return;
	}

	ConstCompoundObjectPtr globals = adaptedInPlug()->globalsPlug()->getValue();
	if( !renderScope.sceneTranslationOnly() )
	{
		GafferScene::RendererAlgo::createOutputDirectories( globals.get() );
	}

	PerformanceMonitorPtr performanceMonitor;
	if( const BoolData *d = globals->member<const BoolData>( g_performanceMonitorOptionName ) )
	{
		if( d->readable() )
		{
			performanceMonitor = new PerformanceMonitor;
		}
	}
	Monitor::Scope performanceMonitorScope( performanceMonitor );

	RendererAlgo::outputOptions( globals.get(), renderer.get() );
	RendererAlgo::outputOutputs( inPlug(), globals.get(), renderer.get() );

	{
		// Using nested scope so that we free the memory used by `renderSets`
		// and `lightLinks` before we call `render()`.
		RendererAlgo::RenderSets renderSets( adaptedInPlug() );
		RendererAlgo::LightLinks lightLinks;

		RendererAlgo::outputCameras( adaptedInPlug(), globals.get(), renderSets, renderer.get() );
		RendererAlgo::outputLights( adaptedInPlug(), globals.get(), renderSets, &lightLinks, renderer.get() );
		RendererAlgo::outputLightFilters( adaptedInPlug(), globals.get(), renderSets, &lightLinks, renderer.get() );
		lightLinks.outputLightFilterLinks( adaptedInPlug() );
		RendererAlgo::outputObjects( adaptedInPlug(), globals.get(), renderSets, &lightLinks, renderer.get() );
	}

	if( renderScope.sceneTranslationOnly() )
	{
		return;
	}

	// Now we have generated the scene, flush Cortex and Gaffer caches to
	// provide more memory to the renderer.
	/// \todo This is not ideal. If dispatch is batched then multiple
	/// renders in the same process might actually benefit from sharing
	/// the cache. And if executing directly within the gui app
	/// flushing the caches is definitely not wanted. Since these
	/// scenarios are currently uncommon, we prioritise the common
	/// case of performing a single render from within `gaffer execute`,
	/// but it would be good to do better.
	ObjectPool::defaultObjectPool()->clear();
	ValuePlug::clearCache();

	renderer->render();
	renderer.reset();

	if( performanceMonitor )
	{
		std::cerr << "\nPerformance Monitor\n===================\n\n";
		std::cerr << MonitorAlgo::formatStatistics( *performanceMonitor );
	}
}
