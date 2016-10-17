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

#include "boost/python.hpp"

#include "Gaffer/Context.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferScene/OpenGLRender.h"
#include "GafferScene/InteractiveRender.h"
#include "GafferScene/Preview/Render.h"
#include "GafferScene/Preview/InteractiveRender.h"
#include "GafferScene/Private/IECoreScenePreview/Renderer.h"

#include "GafferSceneBindings/RenderBinding.h"

using namespace boost::python;

using namespace IECoreScenePreview;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferScene;

namespace
{

class ExecutableRenderWrapper : public TaskNodeWrapper<ExecutableRender>
{

	public :

		ExecutableRenderWrapper( PyObject *self, const std::string &name )
			:	TaskNodeWrapper<ExecutableRender>( self, name )
		{
		}

		virtual IECore::RendererPtr createRenderer() const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "_createRenderer" );
				if( f )
				{
					return extract<IECore::RendererPtr>( f() );
				}
			}
			throw IECore::Exception( "No _createRenderer method defined in Python." );
		}

		virtual void outputWorldProcedural( const ScenePlug *scene, IECore::Renderer *renderer ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "_outputWorldProcedural" );
				if( f )
				{
					f( ScenePlugPtr( const_cast<ScenePlug *>( scene ) ), IECore::RendererPtr( renderer ) );
					return;
				}
			}
			return ExecutableRender::outputWorldProcedural( scene, renderer );
		}

};

ContextPtr interactiveRenderGetContext( InteractiveRender &r )
{
	return r.getContext();
}

ContextPtr previewInteractiveRenderGetContext( Preview::InteractiveRender &r )
{
	return r.getContext();
}

list rendererTypes()
{
	std::vector<IECore::InternedString> t = Renderer::types();
	list result;
	for( std::vector<IECore::InternedString>::const_iterator it = t.begin(), eIt = t.end(); it != eIt; ++it )
	{
		result.append( it->c_str() );
	}
	return result;
}

IECoreScenePreview::Renderer::ObjectInterfacePtr rendererObject1( Renderer &renderer, const std::string &name, const IECore::Object *object, const Renderer::AttributesInterface *attributes )
{
	return renderer.object( name, object, attributes );
}

IECoreScenePreview::Renderer::ObjectInterfacePtr rendererObject2( Renderer &renderer, const std::string &name, object pythonSamples, object pythonTimes, const Renderer::AttributesInterface *attributes )
{
	std::vector<const IECore::Object *> samples;
	container_utils::extend_container( samples, pythonSamples );

	std::vector<float> times;
	container_utils::extend_container( times, pythonTimes );

	return renderer.object( name, samples, times, attributes );
}

void objectInterfaceTransform1( Renderer::ObjectInterface &objectInterface, const Imath::M44f &transform )
{
	objectInterface.transform( transform );
}

void objectInterfaceTransform2( Renderer::ObjectInterface &objectInterface, object pythonSamples, object pythonTimes )
{
	std::vector<Imath::M44f> samples;
	container_utils::extend_container( samples, pythonSamples );

	std::vector<float> times;
	container_utils::extend_container( times, pythonTimes );

	return objectInterface.transform( samples, times );
}

} // namespace

void GafferSceneBindings::bindRender()
{

	TaskNodeClass<ExecutableRender, ExecutableRenderWrapper>();

	TaskNodeClass<OpenGLRender>();

	{
		scope s = GafferBindings::NodeClass<InteractiveRender>()
			.def( "getContext", &interactiveRenderGetContext )
			.def( "setContext", &InteractiveRender::setContext );

		enum_<InteractiveRender::State>( "State" )
			.value( "Stopped", InteractiveRender::Stopped )
			.value( "Running", InteractiveRender::Running )
			.value( "Paused", InteractiveRender::Paused )
		;
	}

	{
		object previewModule( borrowed( PyImport_AddModule( "GafferScene.Preview" ) ) );
		scope().attr( "Preview" ) = previewModule;

		scope previewScope( previewModule );

		{
			scope s = GafferBindings::NodeClass<GafferScene::Preview::InteractiveRender>()
				.def( "getContext", &previewInteractiveRenderGetContext )
				.def( "setContext", &GafferScene::Preview::InteractiveRender::setContext )
			;

			enum_<GafferScene::Preview::InteractiveRender::State>( "State" )
				.value( "Stopped", GafferScene::Preview::InteractiveRender::Stopped )
				.value( "Running", GafferScene::Preview::InteractiveRender::Running )
				.value( "Paused", GafferScene::Preview::InteractiveRender::Paused )
			;
		}

		{
			scope s = TaskNodeClass<GafferScene::Preview::Render>();

			enum_<GafferScene::Preview::Render::Mode>( "Mode" )
				.value( "RenderMode", GafferScene::Preview::Render::RenderMode )
				.value( "SceneDescriptionMode", GafferScene::Preview::Render::SceneDescriptionMode )
			;
		}

	}

	{
		object privateModule( borrowed( PyImport_AddModule( "GafferScene.Private" ) ) );
		scope().attr( "Private" ) = privateModule;

		object ieCoreScenePreviewModule( borrowed( PyImport_AddModule( "GafferScene.Private.IECoreScenePreview" ) ) );
		scope().attr( "Private" ).attr( "IECoreScenePreview" ) = ieCoreScenePreviewModule;

		scope previewScope( ieCoreScenePreviewModule );

		IECorePython::RefCountedClass<Renderer, IECore::RefCounted> renderer( "Renderer" );

		{
			scope rendererScope( renderer );

			enum_<Renderer::RenderType>( "RenderType" )
				.value( "Batch", Renderer::Batch )
				.value( "SceneDescription", Renderer::SceneDescription )
				.value( "Interactive", Renderer::Interactive )
			;

			IECorePython::RefCountedClass<Renderer::AttributesInterface, IECore::RefCounted>( "AttributesInterface" );

			IECorePython::RefCountedClass<Renderer::ObjectInterface, IECore::RefCounted>( "ObjectInterface" )
				.def( "transform", objectInterfaceTransform1 )
				.def( "transform", objectInterfaceTransform2 )
				.def( "attributes", &Renderer::ObjectInterface::attributes )
			;
		}

		renderer

			.def( "types", &rendererTypes )
			.staticmethod( "types" )
			.def( "create", &Renderer::create, ( arg( "type" ), arg( "renderType" ) = Renderer::Batch, arg( "fileName" ) = "" ) )
			.staticmethod( "create" )

			.def( "option", &Renderer::option )
			.def( "output", &Renderer::output )

			.def( "attributes", &Renderer::attributes )

			.def( "camera", &Renderer::camera )
			.def( "light", &Renderer::light )

			.def( "object", &rendererObject1 )
			.def( "object", &rendererObject2 )

			.def( "render", &Renderer::render )
			.def( "pause", &Renderer::pause )

		;

	}

}
