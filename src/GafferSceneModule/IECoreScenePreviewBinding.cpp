//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2024, Image Engine Design Inc. All rights reserved.
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

#include "IECoreScenePreviewBinding.h"

#include "boost/python.hpp"
#include "boost/python/suite/indexing/container_utils.hpp"

#include "IECorePython/ScopedGILRelease.h"
#include "IECorePython/RunTimeTypedBinding.h"

// If we ever actually moved this to Cortex, we would need to move DataBinding::dataToPython to Cortex as well
#include "GafferBindings/DataBinding.h"

#include "GafferScene/Private/IECoreScenePreview/CapturingRenderer.h"
#include "GafferScene/Private/IECoreScenePreview/CompoundRenderer.h"
#include "GafferScene/Private/IECoreScenePreview/Geometry.h"
#include "GafferScene/Private/IECoreScenePreview/Placeholder.h"
#include "GafferScene/Private/IECoreScenePreview/Procedural.h"
#include "GafferScene/Private/IECoreScenePreview/Renderer.h"
#include "GafferScene/Private/IECoreScenePreview/MeshAlgo.h"
#include "GafferScene/Private/IECoreScenePreview/PrimitiveAlgo.h"

using namespace IECoreScenePreview;
using namespace boost::python;

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

void registerTypeWrapper( const std::string &name, object creator )
{
	// The function we register will be held and destroyed from C++.
	// Wrap it so that we correctly acquire the GIL before the captured
	// Python object is destroyed.
	auto creatorPtr = std::shared_ptr<boost::python::object>(
		new boost::python::object( creator ),
		[]( boost::python::object *o ) {
			IECorePython::ScopedGILLock gilLock;
			delete o;
		}
	);

	Renderer::registerType(
		name,
		[creatorPtr] ( Renderer::RenderType renderType, const std::string &fileName, const IECore::MessageHandlerPtr &messageHandler ) -> Renderer::Ptr {
			IECorePython::ScopedGILLock gilLock;
			object o = (*creatorPtr)( renderType, fileName, messageHandler );
			return extract<Renderer::Ptr>( o );
		}
	);
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
	return GafferBindings::dataToPython(
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

list capturingRendererCapturedObjectNames( const CapturingRenderer &r )
{
	std::vector<std::string> t = r.capturedObjectNames();
	list result;
	for( auto &i : t )
	{
		result.append( i );
	}
	return result;
}

std::string capturedObjectCapturedName( const CapturingRenderer::CapturedObject &o )
{
	return o.capturedName();
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

list capturedObjectCapturedLinkTypes( const CapturingRenderer::CapturedObject &o )
{
	list l;
	for( auto &s : o.capturedLinkTypes() )
	{
		l.append( s );
	}
	return l;
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

void transformPrimitiveWrapper( IECoreScene::Primitive &primitive, Imath::M44f matrix, const IECore::Canceller *canceller = nullptr )
{
	IECorePython::ScopedGILRelease gilRelease;
	return PrimitiveAlgo::transformPrimitive( primitive, matrix, canceller );
}

IECoreScene::PrimitivePtr mergePrimitivesWrapper( object primitives, const IECore::Canceller *canceller = nullptr )
{
	std::vector< std::pair< const IECoreScene::Primitive*, Imath::M44f > > typedPrimitives;
	for (int i = 0; i < primitives.attr("__len__")(); i++)
	{
		object pair(primitives[i]);


		typedPrimitives.push_back(
			std::make_pair(
				extract<const IECoreScene::Primitive*>(pair[0])(),
				extract<Imath::M44f>(pair[1])()
			)
		);
	}

	IECorePython::ScopedGILRelease gilRelease;
	return PrimitiveAlgo::mergePrimitives( typedPrimitives, canceller );
}

} // namespace

void GafferSceneModule::bindIECoreScenePreview()
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
			.def( "link", &objectInterfaceLink )
			.def( "assignID", &Renderer::ObjectInterface::assignID )
		;
	}

	renderer

		.def( "registerType", &registerTypeWrapper )
		.def( "deregisterType", &Renderer::deregisterType )
		.def( "types", &rendererTypes )
		.staticmethod( "types" )
		.def( "create", &Renderer::create, ( arg( "type" ), arg( "renderType" ) = Renderer::Batch, arg( "fileName" ) = "", arg( "messageHandler" ) = IECore::MessageHandlerPtr() ) )
		.staticmethod( "create" )

		.def( "name", &rendererName )

		.def( "option", &Renderer::option )
		.def( "output", &Renderer::output )

		.def( "attributes", &Renderer::attributes )

		.def( "camera", &rendererCamera2, ( arg( "name" ), arg( "samples" ), arg( "times" ), arg( "attributes" ) = object() ) )
		.def( "camera", &rendererCamera1, ( arg( "name" ), arg( "camera" ), arg( "attributes" ) = object() ) )
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
			init<const std::string &, const Imath::Box3f &, const IECore::CompoundDataPtr &>(
				(
					arg( "type" ) = "",
					arg( "bound" ) = Imath::Box3f(),
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

	IECorePython::RunTimeTypedClass<Placeholder> placeholderClass( "Placeholder" );
	{
		scope s = placeholderClass;

		enum_<Placeholder::Mode>( "Mode" )
			.value( "Default", Placeholder::Default )
			.value( "Excluded", Placeholder::Excluded )
		;

		placeholderClass
			.def( init<const Imath::Box3f &, const Placeholder::Mode>( ( arg( "bound" ) = Imath::Box3f(), arg( "mode" ) = Placeholder::Mode::Default ) ) )
			.def( "setMode", &Placeholder::setMode )
			.def( "getMode", &Placeholder::getMode )
			.def( "setBound", &Placeholder::setBound )
			.def( "getBound", &Placeholder::getBound, return_value_policy<copy_const_reference>() )
		;

	}

	{
		object meshAlgoModule( borrowed( PyImport_AddModule( "GafferScene.Private.IECoreScenePreview.MeshAlgo" ) ) );
		scope().attr( "MeshAlgo" ) = meshAlgoModule;

		scope meshAlgoScope( meshAlgoModule );

		def( "tessellateMesh", MeshAlgo::tessellateMesh,
			(
				arg( "mesh" ), arg( "divisions" ),
				arg( "calculateNormals" ) = false, arg( "scheme" ) = "",
				arg( "interpolateBoundary" ) = "",
				arg( "faceVaryingLinearInterpolation" ) = "",
				arg( "triangleSubdivisionRule" ) = "",
				arg( "canceller" ) = object()
			)
		);
	}

	scope capturingRendererScope = IECorePython::RefCountedClass<CapturingRenderer, Renderer>( "CapturingRenderer" )
		.def( init<Renderer::RenderType, const std::string &, const IECore::MessageHandlerPtr &>( ( arg( "renderType" ) = Renderer::RenderType::Interactive, arg( "fileName" ) = "", arg( "messageHandler") = IECore::MessageHandlerPtr() ) ) )
		.def( "capturedObjectNames", &capturingRendererCapturedObjectNames )
		.def( "capturedObject", &capturingRendererCapturedObject )
	;

	IECorePython::RefCountedClass<CapturingRenderer::CapturedAttributes, Renderer::AttributesInterface>( "CapturedAttributes" )
		.def( "attributes", &capturedAttributesAttributes )
	;

	IECorePython::RefCountedClass<CapturingRenderer::CapturedObject, Renderer::ObjectInterface>( "CapturedObject" )
		.def( "capturedName", &capturedObjectCapturedName )
		.def( "capturedSamples", &capturedObjectCapturedSamples )
		.def( "capturedSampleTimes", &capturedObjectCapturedSampleTimes )
		.def( "capturedTransforms", &capturedObjectCapturedTransforms )
		.def( "capturedTransformTimes", &capturedObjectCapturedTransformTimes )
		.def( "capturedAttributes", &capturedObjectCapturedAttributes )
		.def( "capturedLinkTypes", &capturedObjectCapturedLinkTypes )
		.def( "capturedLinks", &capturedObjectCapturedLinks )
		.def( "numAttributeEdits", &CapturingRenderer::CapturedObject::numAttributeEdits )
		.def( "numLinkEdits", &CapturingRenderer::CapturedObject::numLinkEdits )
		.def( "id", &CapturingRenderer::CapturedObject::id )
	;

	{
		object primitiveAlgoModule( borrowed( PyImport_AddModule( "GafferScene.Private.IECoreScenePreview.PrimitiveAlgo" ) ) );
		scope().attr( "PrimitiveAlgo" ) = primitiveAlgoModule;

		scope primitiveAlgoScope( primitiveAlgoModule );

		def( "transformPrimitive", transformPrimitiveWrapper,
			(
				arg( "primitive" ), arg( "matrix" ),
				arg( "canceller" ) = object()
			)
		);

		def( "mergePrimitives", mergePrimitivesWrapper,
			(
				arg( "primitives" ),
				arg( "canceller" ) = object()
			)
		);
	}
}
