//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, John Haddon. All rights reserved.
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

#include "GafferOSL/ClosurePlug.h"
#include "GafferOSL/OSLCode.h"
#include "GafferOSL/OSLImage.h"
#include "GafferOSL/OSLLight.h"
#include "GafferOSL/OSLObject.h"
#include "GafferOSL/OSLShader.h"
#include "GafferOSL/ShadingEngine.h"
#include "GafferOSL/ShadingEngineAlgo.h"

#include "GafferBindings/DataBinding.h"
#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/PlugBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Plug.h"

#include "IECorePython/IECoreBinding.h"
#include "IECorePython/ScopedGILRelease.h"

#include "OSL/oslversion.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferOSL;

namespace
{

object shaderMetadata( const OSLShader &s, const char *key, bool copy = true )
{
	return dataToPython( s.shaderMetadata( key ), copy );
}

object parameterMetadata( const OSLShader &s, const Gaffer::Plug *plug, const char *key, bool copy = true )
{
	return dataToPython( s.parameterMetadata( plug, key ), copy );
}

ShadingEnginePtr oslShaderShadingEngine( const OSLShader &s, const IECore::CompoundObject *substitutions )
{
	IECorePython::ScopedGILRelease gilRelease;
	return const_cast<ShadingEngine*>( s.shadingEngine( substitutions ).get() );
}

int oslLibraryVersionMajor()
{
	return OSL_LIBRARY_VERSION_MAJOR;
}

int oslLibraryVersionMinor()
{
	return OSL_LIBRARY_VERSION_MINOR;
}

int oslLibraryVersionPatch()
{
	return OSL_LIBRARY_VERSION_PATCH;
}

int oslLibraryVersionCode()
{
	return OSL_LIBRARY_VERSION_CODE;
}

std::string oslCodeSource( const OSLCode &oslCode, const std::string &shaderName )
{
	IECorePython::ScopedGILRelease gilRelease;
	return oslCode.source( shaderName );
}

std::string repr( ShadingEngine::Transform &s )
{
	return boost::str(
		boost::format( "GafferOSL.ShadingEngine.Transform( fromObjectSpace = %s, toObjectSpace = %s )" )
			% IECorePython::repr<Imath::M44f>( s.fromObjectSpace )
			% IECorePython::repr<Imath::M44f>( s.toObjectSpace )
	);
}

IECore::CompoundDataPtr shadeWrapper( ShadingEngine &shadingEngine, const IECore::CompoundData *points, boost::python::dict pythonTransforms )
{
	ShadingEngine::Transforms transforms;

	list values = pythonTransforms.values();
	list keys = pythonTransforms.keys();

	for (int i = 0; i < boost::python::len( keys ); i++)
	{
		object key( keys[i] );
		object value( values[i] );

		extract<const char *> keyElem( key );
		if( !keyElem.check() )
		{
			PyErr_SetString( PyExc_TypeError, "Incompatible key type. Only strings accepted." );
			throw_error_already_set();
		}

		extract<ShadingEngine::Transform> valueElem( value );
		if( !valueElem.check() )
		{
			PyErr_SetString( PyExc_TypeError, "Incompatible value type. Only GafferOSL.ShadingEngine.Transform accepted." );
			throw_error_already_set();
		}

		transforms[ keyElem() ] = valueElem();
	}

	return shadingEngine.shade( points, transforms );
}

IECore::CompoundDataPtr shadeUVTextureWrapper( const IECoreScene::ShaderNetwork &shaderNetwork, const Imath::V2i &resolution, const IECoreScene::ShaderNetwork::Parameter &output )
{
	IECorePython::ScopedGILRelease gilRelease;
	return ShadingEngineAlgo::shadeUVTexture( &shaderNetwork, resolution, output );
}

void loadShader( OSLLight &l, const std::string &shaderName )
{
	IECorePython::ScopedGILRelease gilRelease;
	l.loadShader( shaderName );
}

} // namespace

BOOST_PYTHON_MODULE( _GafferOSL )
{

	GafferBindings::DependencyNodeClass<OSLShader>()
		.def( "shaderMetadata", &shaderMetadata, ( boost::python::arg_( "_copy" ) = true ) )
		.def( "parameterMetadata", &parameterMetadata, ( boost::python::arg_( "plug" ), boost::python::arg_( "_copy" ) = true ) )
		.def( "shadingEngine", &oslShaderShadingEngine, ( boost::python::arg_( "substitutions" ) = object() ) )
	;

	GafferBindings::DependencyNodeClass<OSLImage>();
	GafferBindings::DependencyNodeClass<OSLObject>();

	PlugClass<ClosurePlug>()
		.def( init<const std::string &, Gaffer::Plug::Direction, unsigned>(
				(
					arg( "name" ) = Gaffer::GraphComponent::defaultName<ClosurePlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
	;


	def( "oslLibraryVersionMajor", &oslLibraryVersionMajor );
	def( "oslLibraryVersionMinor", &oslLibraryVersionMinor );
	def( "oslLibraryVersionPatch", &oslLibraryVersionPatch );
	def( "oslLibraryVersionCode", &oslLibraryVersionCode );


	{
		scope s = IECorePython::RefCountedClass<ShadingEngine, IECore::RefCounted>( "ShadingEngine" )
			.def( init<const IECoreScene::ShaderNetwork *>() )
			.def( "hash", &ShadingEngine::hash )
			.def( "shade", &shadeWrapper,
				(
					boost::python::arg( "points" ),
					boost::python::arg( "transforms" ) = boost::python::dict()
				)
			)
			.def( "needsAttribute", &ShadingEngine::needsAttribute )
			.def( "hasDeformation", &ShadingEngine::hasDeformation )
		;

		class_<ShadingEngine::Transform>( "Transform" )
			.def( init<const Imath::M44f &>() )
			.def( init<const Imath::M44f &, const Imath::M44f&>() )
			.def_readwrite( "fromObjectSpace", &ShadingEngine::Transform::fromObjectSpace )
			.def_readwrite( "toObjectSpace", &ShadingEngine::Transform::toObjectSpace )
			.def( "__repr__", &repr )
		;
	}

	{
		object module( borrowed( PyImport_AddModule( "GafferOSL.ShadingEngineAlgo" ) ) );
		scope().attr( "ShadingEngineAlgo" ) = module;
		scope moduleScope( module );

		def( "shadeUVTexture", &shadeUVTextureWrapper,
			(
				boost::python::arg( "shaderNetwork" ),
				boost::python::arg( "resolution" ),
				boost::python::arg( "output" ) = IECoreScene::ShaderNetwork::Parameter()
			)
		);
	}

	{
		scope s = GafferBindings::DependencyNodeClass<OSLCode>()
			.def( "source", &oslCodeSource, ( arg_( "shaderName" ) = "" ) )
			.def( "shaderCompiledSignal", &OSLCode::shaderCompiledSignal, return_internal_reference<1>() )
		;

		SignalClass<OSLCode::ShaderCompiledSignal>( "ShaderCompiledSignal" );

		// Use a default serialiser for OSLCode, so that we don't get a
		// loadShader call like every other kind of shader.
		GafferBindings::Serialisation::registerSerialiser( OSLCode::staticTypeId(), new GafferBindings::NodeSerialiser() );
	}

	{
		scope s = GafferBindings::DependencyNodeClass<OSLLight>()
			.def( "loadShader", &loadShader )
		;

		enum_<OSLLight::Shape>( "Shape" )
			.value( "Disk", OSLLight::Disk )
			.value( "Sphere", OSLLight::Sphere )
			.value( "Geometry", OSLLight::Geometry )
		;
	}

}
