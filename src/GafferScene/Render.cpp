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

#include "GafferScene/OptionQuery.h"
#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/Private/RendererAlgo.h"
#include "GafferScene/SceneAlgo.h"
#include "GafferScene/SceneNode.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/SceneProcessor.h"

#include "Gaffer/ApplicationRoot.h"
#include "Gaffer/MonitorAlgo.h"
#include "Gaffer/PerformanceMonitor.h"
#include "Gaffer/Switch.h"

#include "IECore/ObjectPool.h"

#include <filesystem>
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
		if( const bool *d = context->getIfExists<bool>( g_sceneTranslationOnlyContextName ) )
		{
			m_sceneTranslationOnly = *d;
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

GAFFER_NODE_DEFINE_TYPE( Render );

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
	addChild( new StringPlug( "resolvedRenderer", Plug::Out, "", Plug::Default & ~Plug::Serialisable ) );
	addChild( new ScenePlug( "__adaptedIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	SceneProcessorPtr adaptors = GafferScene::SceneAlgo::createRenderAdaptors();
	setChild( "__adaptors", adaptors );
	adaptors->inPlug()->setInput( inPlug() );
	adaptedInPlug()->setInput( adaptors->outPlug() );

	outPlug()->setInput( inPlug() );

	// Internal network for `resolvedRenderer`. We use a Switch so that we don't
	// even evaluate the scene globals if the renderer is overridden by `rendererPlug()`.

	OptionQueryPtr optionQuery = new OptionQuery();
	setChild( "__optionQuery", optionQuery );
	optionQuery->scenePlug()->setInput( inPlug() );
	NameValuePlug *rendererQuery = optionQuery->addQuery( rendererPlug() );
	rendererQuery->namePlug()->setValue( "render:defaultRenderer" );

	SwitchPtr querySwitch = new Switch();
	setChild( "__querySwitch", querySwitch );
	querySwitch->setup( rendererPlug() );
	/// \todo Cast shouldn't be necessary - OptionQuery should provide a non-const accessor.
	querySwitch->inPlugs()->getChild<Plug>( 0 )->setInput( const_cast<ValuePlug *>( optionQuery->valuePlugFromQuery( rendererQuery ) ) );
	querySwitch->inPlugs()->getChild<Plug>( 1 )->setInput( rendererPlug() );
	querySwitch->indexPlug()->setValue( 1 );
	querySwitch->enabledPlug()->setInput( rendererPlug() );

	resolvedRendererPlug()->setInput( querySwitch->outPlug() );
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

Gaffer::StringPlug *Render::resolvedRendererPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::StringPlug *Render::resolvedRendererPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 5 );
}

ScenePlug *Render::adaptedInPlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex + 6 );
}

const ScenePlug *Render::adaptedInPlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex + 6 );
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

	const std::string rendererType = resolvedRendererPlug()->getValue();
	const Mode mode = static_cast<Mode>( modePlug()->getValue() );
	const std::string fileName = fileNamePlug()->getValue();
	if( rendererType.empty() || ( mode == SceneDescriptionMode && fileName.empty() ) )
	{
		return IECore::MurmurHash();
	}

	/// \todo Since we're computing the globals now (via `resolvedRenderer`),
	/// maybe our hash should be the hash of the output definitions?
	/// Then we'd know which parts of the context we were sensitive to
	/// and wouldn't have such a pessimistic hash that includes all
	/// context variables.

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
	executeInternal( /* flushCaches = */ true );
}

void Render::executeSequence( const std::vector<float> &frames ) const
{
	Context::EditableScope frameScope( Context::current() );

	for( auto frame : frames )
	{
		frameScope.setFrame( frame );
		// We don't flush Gaffer's caches when rendering batches of frames,
		// because that would mean starting scene generation from scratch
		// each time. We assume that if renders have been batched, they are
		// lightweight in the first place (otherwise there is little benefit
		// in sharing the startup cost between several of them).
		executeInternal( /* flushCaches = */ frames.size() == 1 );
	}
}

void Render::executeInternal( bool flushCaches ) const
{
	if( inPlug()->source()->direction() != Plug::Out )
	{
		return;
	}

	RenderScope renderScope( Context::current() );
	const std::string rendererType = resolvedRendererPlug()->getValue();
	if( rendererType.empty() )
	{
		return;
	}
	renderScope.set( g_rendererContextName, &rendererType );

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
			const std::filesystem::path fileNamePath( fileName );
			const std::filesystem::path directoryPath = fileNamePath.parent_path();
			if( !directoryPath.empty() && !renderScope.sceneTranslationOnly() )
			{
				std::filesystem::create_directories( directoryPath );
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

	GafferScene::Private::RendererAlgo::RenderOptions renderOptions( adaptedInPlug() );
	if( !renderScope.sceneTranslationOnly() )
	{
		GafferScene::Private::RendererAlgo::createOutputDirectories( renderOptions.globals.get() );
	}

	PerformanceMonitorPtr performanceMonitor;
	if( const BoolData *d = renderOptions.globals->member<const BoolData>( g_performanceMonitorOptionName ) )
	{
		if( d->readable() )
		{
			performanceMonitor = new PerformanceMonitor;
		}
	}
	Monitor::Scope performanceMonitorScope( performanceMonitor );

	GafferScene::Private::RendererAlgo::outputOptions( renderOptions.globals.get(), renderer.get() );

	{
		// Using nested scope so that we free the memory used by `renderSets`
		// and `lightLinks` before we call `render()`.
		GafferScene::Private::RendererAlgo::RenderSets renderSets( adaptedInPlug() );
		GafferScene::Private::RendererAlgo::LightLinks lightLinks;

		GafferScene::Private::RendererAlgo::outputCameras( adaptedInPlug(), renderOptions, renderSets, renderer.get() );
		GafferScene::Private::RendererAlgo::outputLights( adaptedInPlug(), renderOptions, renderSets, &lightLinks, renderer.get() );
		GafferScene::Private::RendererAlgo::outputLightFilters( adaptedInPlug(), renderOptions, renderSets, &lightLinks, renderer.get() );
		lightLinks.outputLightFilterLinks( adaptedInPlug() );
		GafferScene::Private::RendererAlgo::outputObjects( adaptedInPlug(), renderOptions, renderSets, &lightLinks, renderer.get() );
	}

	GafferScene::Private::RendererAlgo::outputOutputs( inPlug(), renderOptions.globals.get(), renderer.get() );

	if( renderScope.sceneTranslationOnly() )
	{
		return;
	}

	if( flushCaches )
	{
		// Now we have generated the scene, flush Cortex and Gaffer caches to
		// provide more memory to the renderer. We limit this to the `execute`
		// and `dispatch` applications for two reasons :
		//
		// - In a GUI application, we don't want to clear the caches because
		//   we'll probably benefit from using them again later.
		// - In `execute` and `dispatch` we know we're not executing concurrently
		//   with anything else, and can therefore pass `now = true` to
		//   `clearHashCache()` safely.
		auto *application = ancestor<ApplicationRoot>();
		if( application && ( application->getName() == "execute" || application->getName() == "dispatch" ) )
		{
			ObjectPool::defaultObjectPool()->clear();
			ValuePlug::clearCache();
			ValuePlug::clearHashCache( /* now = */ true );
		}
	}

	renderer->render();
	renderer.reset();

	if( performanceMonitor )
	{
		std::cerr << "\nPerformance Monitor\n===================\n\n";
		std::cerr << MonitorAlgo::formatStatistics( *performanceMonitor );
	}
}
