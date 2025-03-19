//////////////////////////////////////////////////////////////////////////
//
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

#include "RenderBinding.h"

#include "boost/python.hpp"

#include "GafferScene/InteractiveRender.h"
#include "GafferScene/Private/RendererAlgo.h"
#include "GafferScene/Render.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"

#include "IECorePython/ExceptionAlgo.h"

using namespace boost::python;

using namespace Imath;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferScene;

namespace
{

ContextPtr interactiveRenderGetContext( InteractiveRender &r )
{
	return r.getContext();
}

void interactiveRenderSetContext( InteractiveRender &r, Context &context )
{
	IECorePython::ScopedGILRelease gilRelease;
	r.setContext( &context );
}

IECore::DataPtr interactiveRenderCommandWrapper( InteractiveRender &r, const IECore::InternedString name, const IECore::CompoundDataMap &parameters )
{
	IECorePython::ScopedGILRelease gilRelease;
	return r.command( name, parameters );
}

object objectSamplesWrapper( const Gaffer::ObjectPlug &objectPlug, const std::vector<float> &sampleTimes, IECore::MurmurHash *hash, bool copy )
{
	bool result;
	std::vector<IECore::ConstObjectPtr> samples;
	{
		IECorePython::ScopedGILRelease gilRelease;
		result = GafferScene::Private::RendererAlgo::objectSamples( &objectPlug, sampleTimes, samples, hash );
	}

	if( !result )
	{
		return object();
	}

	list pythonSamples;
	for( auto &s : samples )
	{
		if( copy )
		{
			pythonSamples.append( s->copy() );
		}
		else
		{
			pythonSamples.append( boost::const_pointer_cast<IECore::Object>( s ) );
		}
	}

	return pythonSamples;
}

object transformSamplesWrapper( const Gaffer::M44fPlug &transformPlug, const std::vector<float> &sampleTimes, IECore::MurmurHash *hash )
{
	bool result;
	std::vector<M44f> samples;
	{
		IECorePython::ScopedGILRelease gilRelease;
		result = GafferScene::Private::RendererAlgo::transformSamples( &transformPlug, sampleTimes, samples, hash );
	}

	if( !result )
	{
		return object();
	}

	list pythonSamples;
	for( auto &s : samples )
	{
		pythonSamples.append( s );
	}

	return pythonSamples;
}

void outputCamerasWrapper( const ScenePlug &scene, const GafferScene::Private::RendererAlgo::RenderOptions &renderOptions, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, IECoreScenePreview::Renderer &renderer )
{
	IECorePython::ScopedGILRelease gilRelease;
	GafferScene::Private::RendererAlgo::outputCameras( &scene, renderOptions, renderSets, &renderer );
}

void outputLightsWrapper( const ScenePlug &scene, const GafferScene::Private::RendererAlgo::RenderOptions &renderOptions, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, GafferScene::Private::RendererAlgo::LightLinks &lightLinks, IECoreScenePreview::Renderer &renderer )
{
	IECorePython::ScopedGILRelease gilRelease;
	GafferScene::Private::RendererAlgo::outputLights( &scene, renderOptions, renderSets, &lightLinks, &renderer );
}

void outputObjectsWrapper( const ScenePlug &scene, const GafferScene::Private::RendererAlgo::RenderOptions &renderOptions, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, GafferScene::Private::RendererAlgo::LightLinks &lightLinks, IECoreScenePreview::Renderer &renderer, const ScenePlug::ScenePath &root )
{
	IECorePython::ScopedGILRelease gilRelease;
	GafferScene::Private::RendererAlgo::outputObjects( &scene, renderOptions, renderSets, &lightLinks, &renderer, root );
}

struct RenderSlotCaller
{
	bool operator()( boost::python::object slot, const Render *r )
	{
		try
		{
			RenderPtr render = const_cast<Render * >( r );
			return slot( render );
		}
		catch( const boost::python::error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
		return false;
	}
};

} // namespace

void GafferSceneModule::bindRender()
{

	{
		scope s = GafferBindings::NodeClass<InteractiveRender>()
			.def( "getContext", &interactiveRenderGetContext )
			.def( "setContext", &interactiveRenderSetContext )
			.def( "command", &interactiveRenderCommandWrapper, ( arg( "name" ), arg( "parameters" ) = dict() ) )
		;

		enum_<InteractiveRender::State>( "State" )
			.value( "Stopped", InteractiveRender::Stopped )
			.value( "Running", InteractiveRender::Running )
			.value( "Paused", InteractiveRender::Paused )
		;
	}

	{
		scope s = TaskNodeClass<GafferScene::Render>()
		.def( "preRenderSignal", &Render::preRenderSignal, return_value_policy<reference_existing_object>() )
		.def( "postRenderSignal", &Render::postRenderSignal, return_value_policy<reference_existing_object>() )
			.staticmethod( "postRenderSignal" )
		;

		enum_<GafferScene::Render::Mode>( "Mode" )
			.value( "RenderMode", GafferScene::Render::RenderMode )
			.value( "SceneDescriptionMode", GafferScene::Render::SceneDescriptionMode )
		;

		SignalClass<Render::RenderSignal, DefaultSignalCaller<Render::RenderSignal>, RenderSlotCaller>( "RenderSignal" );
	}

	{
		object privateModule( borrowed( PyImport_AddModule( "GafferScene.Private" ) ) );
		scope().attr( "Private" ) = privateModule;

		{
			object rendererAlgoModule( borrowed( PyImport_AddModule( "GafferScene.Private.RendererAlgo" ) ) );
			scope().attr( "Private" ).attr( "RendererAlgo" ) = rendererAlgoModule;

			scope rendererAlgomoduleScope( rendererAlgoModule );

			class_<GafferScene::Private::RendererAlgo::RenderOptions>( "RenderOptions" )
				.def( init<const ScenePlug *>() )
				.def_readwrite( "globals", &GafferScene::Private::RendererAlgo::RenderOptions::globals )
				.def_readwrite( "transformBlur", &GafferScene::Private::RendererAlgo::RenderOptions::transformBlur )
				.def_readwrite( "deformationBlur", &GafferScene::Private::RendererAlgo::RenderOptions::deformationBlur )
				.def_readwrite( "shutter", &GafferScene::Private::RendererAlgo::RenderOptions::shutter )
				.def_readwrite( "includedPurposes", &GafferScene::Private::RendererAlgo::RenderOptions::includedPurposes )
				.def( self == self )
			;

			def( "objectSamples", &objectSamplesWrapper, ( arg( "objectPlug" ), arg( "sampleTimes" ), arg( "hash" ) = object(), arg( "_copy" ) = true ) );
			def( "transformSamples", &transformSamplesWrapper, ( arg( "transformPlug" ), arg( "sampleTimes" ), arg( "hash" ) = object() ) );

			class_<GafferScene::Private::RendererAlgo::RenderSets, boost::noncopyable>( "RenderSets" )
				.def( init<const ScenePlug *>() )
			;
			class_<GafferScene::Private::RendererAlgo::LightLinks, boost::noncopyable>( "LightLinks" )
				.def( init<>() )
			;

			def( "outputCameras", &outputCamerasWrapper );
			def( "outputLights", &outputLightsWrapper );
			def( "outputObjects", &outputObjectsWrapper, ( arg( "scene" ), arg( "globals" ), arg( "renderSets" ), arg( "lightLinks" ), arg( "renderer" ), arg( "root" ) = "/" ) );
		}
	}

}
