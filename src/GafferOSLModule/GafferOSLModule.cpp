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

#include "OSL/oslversion.h"

#include "IECorePython/ScopedGILRelease.h"
#include "IECorePython/IECoreBinding.h"

#include "Gaffer/StringPlug.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/DataBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "GafferOSL/OSLShader.h"
#include "GafferOSL/ShadingEngine.h"
#include "GafferOSL/OSLImage.h"
#include "GafferOSL/OSLObject.h"
#include "GafferOSL/OSLCode.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferOSL;

namespace
{

/// \todo Move this serialisation to the bindings for GafferScene::Shader, once we've made Shader::loadShader() virtual
/// and implemented it so reloading works in OpenGLShader.
class OSLShaderSerialiser : public GafferBindings::NodeSerialiser
{

	virtual std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
	{
		const OSLShader *oslShader = static_cast<const OSLShader *>( graphComponent );
		const std::string shaderName = oslShader->namePlug()->getValue();
		// We don't serialise a `loadShader()` call for OSLCode nodes
		// because the OSLCode node generates the shader from the plugs,
		// and not the other way around.
		if( shaderName.size() && !IECore::runTimeCast<const OSLCode>( oslShader ) )
		{
			return boost::str( boost::format( "%s.loadShader( \"%s\", keepExistingValues=True )\n" ) % identifier % shaderName );
		}

		return "";
	}

};

object shaderMetadata( const OSLShader &s, const char *key, bool copy = true )
{
	return dataToPython( s.shaderMetadata( key ), copy );
}

object parameterMetadata( const OSLShader &s, const Gaffer::Plug *plug, const char *key, bool copy = true )
{
	return dataToPython( s.parameterMetadata( plug, key ), copy );
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

} // namespace

BOOST_PYTHON_MODULE( _GafferOSL )
{

	GafferBindings::DependencyNodeClass<OSLShader>()
		.def( "loadShader", &OSLShader::loadShader, ( arg_( "shaderName" ), arg_( "keepExistingValues" ) = false ) )
		.def( "shaderMetadata", &shaderMetadata, ( boost::python::arg_( "_copy" ) = true ) )
		.def( "parameterMetadata", &parameterMetadata, ( boost::python::arg_( "plug" ), boost::python::arg_( "_copy" ) = true ) )
	;

	Serialisation::registerSerialiser( OSLShader::staticTypeId(), new OSLShaderSerialiser() );

	GafferBindings::DependencyNodeClass<OSLImage>();
	GafferBindings::DependencyNodeClass<OSLObject>();

	def( "oslLibraryVersionMajor", &oslLibraryVersionMajor );
	def( "oslLibraryVersionMinor", &oslLibraryVersionMinor );
	def( "oslLibraryVersionPatch", &oslLibraryVersionPatch );
	def( "oslLibraryVersionCode", &oslLibraryVersionCode );


	{
		scope s = IECorePython::RefCountedClass<ShadingEngine, IECore::RefCounted>( "ShadingEngine" )
			.def( init<const IECore::ObjectVector *>() )
			.def( "shade", &shadeWrapper,
				(
					boost::python::arg( "points" ),
					boost::python::arg( "transforms" ) = boost::python::dict()
				)
			)
		;

		class_<ShadingEngine::Transform>( "Transform" )
			.def( init<const Imath::M44f &>() )
			.def( init<const Imath::M44f &, const Imath::M44f&>() )
			.def_readwrite( "fromObjectSpace", &ShadingEngine::Transform::fromObjectSpace )
			.def_readwrite( "toObjectSpace", &ShadingEngine::Transform::toObjectSpace )
			.def( "__repr__", &repr )
		;
	}

	scope s = GafferBindings::DependencyNodeClass<OSLCode>()
		.def( "source", &oslCodeSource, ( arg_( "shaderName" ) = "" ) )
		.def( "shaderCompiledSignal", &OSLCode::shaderCompiledSignal, return_internal_reference<1>() )
	;

	SignalClass<OSLCode::ShaderCompiledSignal>( "ShaderCompiledSignal" );

}
