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

#include "RenderBinding.h"

#include "GafferScene/InteractiveRender.h"
#include "GafferScene/OpenGLRender.h"
#include "GafferScene/Private/IECoreScenePreview/CapturingRenderer.h"
#include "GafferScene/Private/IECoreScenePreview/CompoundRenderer.h"
#include "GafferScene/Private/IECoreScenePreview/Geometry.h"
#include "GafferScene/Private/IECoreScenePreview/Placeholder.h"
#include "GafferScene/Private/IECoreScenePreview/Procedural.h"
#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/Private/RendererAlgo.h"
#include "GafferScene/Render.h"

#include "GafferDispatchBindings/TaskNodeBinding.h"

#include "GafferBindings/DataBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"

using namespace boost::python;

using namespace Imath;
using namespace IECoreScenePreview;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferDispatchBindings;
using namespace GafferScene;

namespace
{

/// \todo Move to IECore module
struct CompoundDataMapFromDict
{

	CompoundDataMapFromDict()
	{
		boost::python::converter::registry::push_back(
			&convertible,
			&construct,
			boost::python::type_id<IECore::CompoundDataMap>()
		);
	}

	static void *convertible( PyObject *obj )
	{
		if( PyDict_Check( obj ) )
		{
			return obj;
		}
		return nullptr;
	}

	static void construct( PyObject *obj, boost::python::converter::rvalue_from_python_stage1_data *data )
	{
		void *storage = ( (converter::rvalue_from_python_storage<IECore::CompoundDataMap>*) data )->storage.bytes;
		IECore::CompoundDataMap *map = new( storage ) IECore::CompoundDataMap();
		data->convertible = storage;

		dict d( borrowed( obj ) );
		list items = d.items();
		for( unsigned i = 0, e = boost::python::len( items ); i < e; ++i )
		{
			IECore::InternedString k = extract<IECore::InternedString>( items[i][0] );
			(*map)[k] = extract<IECore::DataPtr>( items[i][1] );
		}
	}

};

ContextPtr interactiveRenderGetContext( InteractiveRender &r )
{
	return r.getContext();
}

void interactiveRenderSetContext( InteractiveRender &r, Context &context )
{
	IECorePython::ScopedGILRelease gilRelease;
	r.setContext( &context );
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

const char *rendererName( Renderer &renderer )
{
	return renderer.name().c_str();
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


IECoreScenePreview::Renderer::ObjectInterfacePtr rendererCamera1( Renderer &renderer, const std::string &name, const IECoreScene::Camera *camera, const Renderer::AttributesInterface *attributes )
{
	return renderer.camera( name, camera, attributes );
}

IECoreScenePreview::Renderer::ObjectInterfacePtr rendererCamera2( Renderer &renderer, const std::string &name, object pythonSamples, object pythonTimes, const Renderer::AttributesInterface *attributes )
{
	std::vector<const IECoreScene::Camera *> samples;
	container_utils::extend_container( samples, pythonSamples );

	std::vector<float> times;
	container_utils::extend_container( times, pythonTimes );

	return renderer.camera( name, samples, times, attributes );
}

object rendererCommand( Renderer &renderer, const IECore::InternedString name, const IECore::CompoundDataMap &parameters = IECore::CompoundDataMap() )
{
	return dataToPython(
		renderer.command( name, parameters ).get()
	);
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

void objectInterfaceLink( Renderer::ObjectInterface &objectInterface, const IECore::InternedString &type, object pythonObjectSet )
{
	std::vector<Renderer::ObjectInterfacePtr> objectVector;
	container_utils::extend_container( objectVector, pythonObjectSet );
	auto objectSet = std::make_shared<Renderer::ObjectSet>( objectVector.begin(), objectVector.end() );
	objectInterface.link( type, objectSet );
}

void render( Renderer &renderer )
{
	IECorePython::ScopedGILRelease gilRelease;
	renderer.render();
}

RendererPtr compoundRendererConstructor( object pythonRenderers )
{
	std::vector<RendererPtr> renderers;
	container_utils::extend_container( renderers, pythonRenderers );
	return new CompoundRenderer( renderers );
}

class ProceduralWrapper : public IECorePython::RunTimeTypedWrapper<IECoreScenePreview::Procedural>
{

	public :

		ProceduralWrapper( PyObject *self )
			:	IECorePython::RunTimeTypedWrapper<IECoreScenePreview::Procedural>( self )
		{
		}

		Imath::Box3f bound() const final
		{
			IECorePython::ScopedGILLock gilLock;
			try
			{
				boost::python::object f = this->methodOverride( "bound" );
				if( f )
				{
					return extract<Imath::Box3f>( f() );
				}
			}
			catch( const boost::python::error_already_set & )
			{
				IECorePython::ExceptionAlgo::translatePythonException();
			}

			throw IECore::Exception( "No bound method defined" );
		}

		void render( IECoreScenePreview::Renderer *renderer ) const final
		{
			IECorePython::ScopedGILLock gilLock;
			try
			{
				boost::python::object f = this->methodOverride( "render" );
				if( f )
				{
					f( IECoreScenePreview::RendererPtr( renderer ) );
					return;
				}
			}
			catch( const boost::python::error_already_set & )
			{
				IECorePython::ExceptionAlgo::translatePythonException();
			}

			throw IECore::Exception( "No render method defined" );
		}

};

IECore::CompoundObjectPtr capturedAttributesAttributes( const CapturingRenderer::CapturedAttributes &a )
{
	return const_cast<IECore::CompoundObject *>( a.attributes() );
}

CapturingRenderer::CapturedObjectPtr capturingRendererCapturedObject( const CapturingRenderer &r, const std::string &name )
{
	return const_cast<CapturingRenderer::CapturedObject *>( r.capturedObject( name ) );
}

list capturedObjectCapturedSamples( const CapturingRenderer::CapturedObject &o )
{
	list result;
	for( auto s : o.capturedSamples() )
	{
		result.append( boost::const_pointer_cast<IECore::Object>( s ) );
	}
	return result;
}

list capturedObjectCapturedSampleTimes( const CapturingRenderer::CapturedObject &o )
{
	list result;
	for( auto t : o.capturedSampleTimes() )
	{
		result.append( t );
	}
	return result;
}

list capturedObjectCapturedTransforms( const CapturingRenderer::CapturedObject &o )
{
	list result;
	for( auto s : o.capturedTransforms() )
	{
		result.append( s );
	}
	return result;
}

list capturedObjectCapturedTransformTimes( const CapturingRenderer::CapturedObject &o )
{
	list result;
	for( auto t : o.capturedTransformTimes() )
	{
		result.append( t );
	}
	return result;
}

CapturingRenderer::CapturedAttributesPtr capturedObjectCapturedAttributes( const CapturingRenderer::CapturedObject &o )
{
	return const_cast<CapturingRenderer::CapturedAttributes *>( o.capturedAttributes() );
}

object capturedObjectCapturedLinks( const CapturingRenderer::CapturedObject &o, const IECore::InternedString &type )
{
	if( o.capturedLinks( type ) )
	{
		list l;
		for( auto &s : *o.capturedLinks( type ) )
		{
			l.append( s );
		}
		PyObject *set = PySet_New( l.ptr() );
		return object( handle<>( set ) );
	}
	else
	{
		// Null pointer used to say "no linking" - return None
		return object();
	}
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

void outputCamerasWrapper( const ScenePlug &scene, const IECore::CompoundObject &globals, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, IECoreScenePreview::Renderer &renderer )
{
	IECorePython::ScopedGILRelease gilRelease;
	GafferScene::Private::RendererAlgo::outputCameras( &scene, &globals, renderSets, &renderer );
}

void outputLightsWrapper( const ScenePlug &scene, const IECore::CompoundObject &globals, const GafferScene::Private::RendererAlgo::RenderSets &renderSets, GafferScene::Private::RendererAlgo::LightLinks &lightLinks, IECoreScenePreview::Renderer &renderer )
{
	IECorePython::ScopedGILRelease gilRelease;
	GafferScene::Private::RendererAlgo::outputLights( &scene, &globals, renderSets, &lightLinks, &renderer );
}


} // namespace

void GafferSceneModule::bindRender()
{

	{
		scope s = GafferBindings::NodeClass<InteractiveRender>()
			.def( "getContext", &interactiveRenderGetContext )
			.def( "setContext", &interactiveRenderSetContext )
		;

		enum_<InteractiveRender::State>( "State" )
			.value( "Stopped", InteractiveRender::Stopped )
			.value( "Running", InteractiveRender::Running )
			.value( "Paused", InteractiveRender::Paused )
		;
	}

	{
		scope s = TaskNodeClass<GafferScene::Render>();

		enum_<GafferScene::Render::Mode>( "Mode" )
			.value( "RenderMode", GafferScene::Render::RenderMode )
			.value( "SceneDescriptionMode", GafferScene::Render::SceneDescriptionMode )
		;
	}

	{
		object privateModule( borrowed( PyImport_AddModule( "GafferScene.Private" ) ) );
		scope().attr( "Private" ) = privateModule;

		{
			object rendererAlgoModule( borrowed( PyImport_AddModule( "GafferScene.Private.RendererAlgo" ) ) );
			scope().attr( "Private" ).attr( "RendererAlgo" ) = rendererAlgoModule;

			scope rendererAlgomoduleScope( rendererAlgoModule );

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
		}

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
				.def( "link", &objectInterfaceLink )
				.def( "assignID", &Renderer::ObjectInterface::assignID )
			;
		}

		renderer

			.def( "types", &rendererTypes )
			.staticmethod( "types" )
			.def( "create", &Renderer::create, ( arg( "type" ), arg( "renderType" ) = Renderer::Batch, arg( "fileName" ) = "", arg( "messageHandler" ) = IECore::MessageHandlerPtr() ) )
			.staticmethod( "create" )

			.def( "name", &rendererName )

			.def( "option", &Renderer::option )
			.def( "output", &Renderer::output )

			.def( "attributes", &Renderer::attributes )

			.def( "camera", &rendererCamera1 )
			.def( "camera", &rendererCamera2 )
			.def( "light", &Renderer::light )
			.def( "lightFilter", &Renderer::lightFilter )

			.def( "object", &rendererObject1 )
			.def( "object", &rendererObject2 )

			.def( "render", render )
			.def( "pause", &Renderer::pause )
			.def( "command", &rendererCommand )

		;

		CompoundDataMapFromDict();

		IECorePython::RefCountedClass<CompoundRenderer, Renderer>( "CompoundRenderer" )
			.def( "__init__", make_constructor( compoundRendererConstructor, default_call_policies(), arg( "renderers" ) ) )
		;

		IECorePython::RunTimeTypedClass<IECoreScenePreview::Procedural, ProceduralWrapper>()
			.def( init<>() )
			.def( "render", (void (Procedural::*)( IECoreScenePreview::Renderer *)const)&Procedural::render )
		;

		IECorePython::RunTimeTypedClass<Geometry>()
			.def(
				init<const std::string &, const Box3f &, const IECore::CompoundDataPtr &>(
					(
						arg( "type" ) = "",
						arg( "bound" ) = Box3f(),
						arg( "parameters" ) = object()
					)
				)
			)
			.def( "setType", &Geometry::setType )
			.def( "getType", &Geometry::getType, return_value_policy<copy_const_reference>() )
			.def( "setBound", &Geometry::setBound )
			.def( "getBound", &Geometry::getBound, return_value_policy<copy_const_reference>() )
			.def( "parameters", (IECore::CompoundData *(Geometry::*)())&Geometry::parameters, return_value_policy<IECorePython::CastToIntrusivePtr>() )
		;

		IECorePython::RunTimeTypedClass<Placeholder>()
			.def( init<const Box3f &>( arg( "bound" ) = Box3f() ) )
			.def( "setBound", &Placeholder::setBound )
			.def( "getBound", &Placeholder::getBound, return_value_policy<copy_const_reference>() )
		;

		scope capturingRendererScope = IECorePython::RefCountedClass<CapturingRenderer, Renderer>( "CapturingRenderer" )
			.def( init<Renderer::RenderType, const std::string &, const IECore::MessageHandlerPtr &>( ( arg( "renderType" ) = Renderer::RenderType::Interactive, arg( "fileName" ) = "", arg( "messageHandler") = IECore::MessageHandlerPtr() ) ) )
			.def( "capturedObject", &capturingRendererCapturedObject )
		;

		IECorePython::RefCountedClass<CapturingRenderer::CapturedAttributes, Renderer::AttributesInterface>( "CapturedAttributes" )
			.def( "attributes", &capturedAttributesAttributes )
		;

		IECorePython::RefCountedClass<CapturingRenderer::CapturedObject, Renderer::ObjectInterface>( "CapturedObject" )
			.def( "capturedSamples", &capturedObjectCapturedSamples )
			.def( "capturedSampleTimes", &capturedObjectCapturedSampleTimes )
			.def( "capturedTransforms", &capturedObjectCapturedTransforms )
			.def( "capturedTransformTimes", &capturedObjectCapturedTransformTimes )
			.def( "capturedAttributes", &capturedObjectCapturedAttributes )
			.def( "capturedLinks", &capturedObjectCapturedLinks )
			.def( "numAttributeEdits", &CapturingRenderer::CapturedObject::numAttributeEdits )
			.def( "numLinkEdits", &CapturingRenderer::CapturedObject::numLinkEdits )
			.def( "id", &CapturingRenderer::CapturedObject::id )
		;
	}

	TaskNodeClass<OpenGLRender>();

}
