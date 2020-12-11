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

#include "ShaderBinding.h"

#include "GafferScene/OpenGLShader.h"
#include "GafferScene/Shader.h"
#include "GafferScene/ShaderPlug.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/PlugBinding.h"

#include "Gaffer/StringPlug.h"

using namespace boost::python;

using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferScene;

namespace
{

IECore::MurmurHash shaderAttributesHash1( const Shader &s )
{
	IECorePython::ScopedGILRelease gilRelease;
	return s.attributesHash();
}

void shaderAttributesHash2( const Shader &s, IECore::MurmurHash &h )
{
	IECorePython::ScopedGILRelease gilRelease;
	s.attributesHash( h );
}

IECore::CompoundObjectPtr shaderAttributes( const Shader &s, bool copy=true )
{
	IECorePython::ScopedGILRelease gilRelease;
	IECore::ConstCompoundObjectPtr o = s.attributes();
	if( copy )
	{
		return o->copy();
	}
	else
	{
		return boost::const_pointer_cast<IECore::CompoundObject>( o );
	}
}

void loadShader( Shader &shader, const std::string &shaderName, bool keepExistingValues )
{
	// Loading a shader modifies the graph, which can trigger dirty propagation,
	// which can trigger computations, which can launch threads.
	// So we need a GIL release here.
	IECorePython::ScopedGILRelease gilRelease;
	shader.loadShader( shaderName, keepExistingValues );
}

void reloadShader( Shader &shader )
{
	// Reloading a shader modifies the graph, which can trigger dirty propagation,
	// which can trigger computations, which can launch threads.
	// So we need a GIL release here.
	IECorePython::ScopedGILRelease gilRelease;
	shader.reloadShader();
}

class ShaderSerialiser : public GafferBindings::NodeSerialiser
{

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		std::string defaultPC = GafferBindings::NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );
		const Shader *shader = static_cast<const Shader *>( graphComponent );
		const std::string shaderName = shader->namePlug()->getValue();
		if( shaderName.size() )
		{
			return defaultPC + boost::str( boost::format( "%s.loadShader( \"%s\" )\n" ) % identifier % shaderName );
		}

		return defaultPC;
	}

};

IECore::MurmurHash shaderPlugAttributesHash( const ShaderPlug &p )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.attributesHash();
}

IECore::CompoundObjectPtr shaderPlugAttributes( const ShaderPlug &p, bool copy=true )
{
	IECorePython::ScopedGILRelease gilRelease;
	IECore::ConstCompoundObjectPtr o = p.attributes();
	if( copy )
	{
		return o->copy();
	}
	else
	{
		return boost::const_pointer_cast<IECore::CompoundObject>( o );
	}
}

} // namespace

void GafferSceneModule::bindShader()
{

	GafferBindings::DependencyNodeClass<Shader>()
		.def( "attributesHash", shaderAttributesHash1 )
		.def( "attributesHash", shaderAttributesHash2 )
		.def( "attributes", &shaderAttributes, ( boost::python::arg_( "_copy" ) = true ) )
		.def( "loadShader", &loadShader, ( arg_( "shaderName" ), arg_( "keepExistingValues" ) = false ) )
		.def( "reloadShader", &reloadShader )
	;

	GafferBindings::Serialisation::registerSerialiser( Shader::staticTypeId(), new ShaderSerialiser() );

	PlugClass<ShaderPlug>()
		.def( init<const std::string &, Plug::Direction, unsigned>(
				(
					arg( "name" ) = Gaffer::GraphComponent::defaultName<ShaderPlug>(),
					arg( "direction" ) = Gaffer::Plug::In,
					arg( "flags" ) = Gaffer::Plug::Default
				)
			)
		)
		// value accessors
		.def( "attributesHash", &shaderPlugAttributesHash  )
		.def( "attributes", &shaderPlugAttributes, ( boost::python::arg_( "_copy" ) = true ) )
	;

	GafferBindings::NodeClass<OpenGLShader>();

}
