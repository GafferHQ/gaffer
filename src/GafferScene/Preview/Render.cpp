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

#include "boost/filesystem.hpp"

#include "IECore/ObjectPool.h"

#include "Gaffer/PerformanceMonitor.h"
#include "Gaffer/MonitorAlgo.h"

#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferScene/Preview/Render.h"
#include "GafferScene/Preview/RendererAlgo.h"
#include "GafferScene/ScenePlug.h"
#include "GafferScene/SceneNode.h"
#include "GafferScene/RendererAlgo.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferDispatch;
using namespace GafferScene;
using namespace GafferScene::Preview;

namespace
{

InternedString g_performanceMonitorOptionName( "option:render:performanceMonitor" );

} // namespace

size_t Render::g_firstPlugIndex = 0;

IE_CORE_DEFINERUNTIMETYPED( Render );

Render::Render( const std::string &name )
	:	TaskNode( name )
{
	construct();
}

Render::Render( const IECore::InternedString &rendererType, const std::string &name )
	:	TaskNode( name )
{
	construct( rendererType );
}

void Render::construct( const IECore::InternedString &rendererType )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "in" ) );
	addChild( new StringPlug( rendererType.string().empty() ? "renderer" : "__renderer", Plug::In, rendererType.string() ) );
	addChild( new IntPlug( "mode", Plug::In, RenderMode, RenderMode, SceneDescriptionMode ) );
	addChild( new StringPlug( "fileName" ) );
	addChild( new ScenePlug( "out", Plug::Out, Plug::Default & ~Plug::Serialisable ) );
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

IECore::MurmurHash Render::hash( const Gaffer::Context *context ) const
{
	if( !IECore::runTimeCast<const SceneNode>( inPlug()->source<Plug>()->node() ) )
	{
		return IECore::MurmurHash();
	}

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

	return h;
}

void Render::execute() const
{
	if( !IECore::runTimeCast<const SceneNode>( inPlug()->source<Plug>()->node() ) )
	{
		return;
	}

	const std::string rendererType = rendererPlug()->getValue();
	if( rendererType.empty() )
	{
		return;
	}

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
			if( !directoryPath.empty() )
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

	ConstCompoundObjectPtr globals = inPlug()->globalsPlug()->getValue();
	GafferScene::RendererAlgo::createDisplayDirectories( globals.get() );

	boost::shared_ptr<PerformanceMonitor> performanceMonitor;
	if( const BoolData *d = globals->member<const BoolData>( g_performanceMonitorOptionName ) )
	{
		if( d->readable() )
		{
			performanceMonitor.reset( new PerformanceMonitor );
		}
	}
	Monitor::Scope performanceMonitorScope( performanceMonitor.get() );

	RendererAlgo::outputOptions( globals.get(), renderer.get() );
	RendererAlgo::outputOutputs( globals.get(), renderer.get() );

	RendererAlgo::RenderSets renderSets( inPlug() );

	RendererAlgo::outputCameras( inPlug(), globals.get(), renderSets, renderer.get() );
	RendererAlgo::outputLights( inPlug(), globals.get(), renderSets, renderer.get() );
	RendererAlgo::outputObjects( inPlug(), globals.get(), renderSets, renderer.get() );

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
