//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "AttributesBinding.h"

#include "GafferScene/AttributeProcessor.h"
#include "GafferScene/AttributeVisualiser.h"
#include "GafferScene/Attributes.h"
#include "GafferScene/AttributeQuery.h"
#include "GafferScene/CollectTransforms.h"
#include "GafferScene/CopyAttributes.h"
#include "GafferScene/CustomAttributes.h"
#include "GafferScene/DeleteAttributes.h"
#include "GafferScene/LocaliseAttributes.h"
#include "GafferScene/OpenGLAttributes.h"
#include "GafferScene/SetVisualiser.h"
#include "GafferScene/ShaderAssignment.h"
#include "GafferScene/ShuffleAttributes.h"
#include "GafferScene/StandardAttributes.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/Serialisation.h"

#include <cassert>

using namespace boost::python;
using namespace GafferScene;

namespace AttributeQueryBinding
{

bool isSetup( const AttributeQuery& query )
{
	return query.isSetup();
}

bool canSetup( const AttributeQuery& query, const Gaffer::ValuePlug& plug )
{
	return query.canSetup( & plug );
}

void setup( AttributeQuery& query, const Gaffer::ValuePlug& plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	if( !( query.canSetup( & plug ) ) )
	{
		throw IECore::Exception( "AttributeQuery cannot be setup from specified plug" );
	}
	query.setup( & plug );
}

class Serialiser : public GafferBindings::NodeSerialiser
{
	std::string postConstructor( const Gaffer::GraphComponent* component, const std::string& identifier, GafferBindings::Serialisation& serialisation ) const override;
};

std::string Serialiser::postConstructor( const Gaffer::GraphComponent* const component, const std::string& identifier, GafferBindings::Serialisation& serialisation ) const
{
	std::string result = GafferBindings::NodeSerialiser::postConstructor( component, identifier, serialisation );

	const AttributeQuery* const query = IECore::assertedStaticCast< const AttributeQuery >( component );

	if( query->isSetup() )
	{
		if( result.size() )
		{
			result += "\n";
		}

		const GafferBindings::Serialisation::Serialiser* const serialiser = GafferBindings::Serialisation::acquireSerialiser( query->valuePlug() );
		result += identifier + ".setup( " + serialiser->constructor( query->valuePlug(), serialisation ) + " )\n";
	}

	return result;
}

} // AttributeQueryBinding

void GafferSceneModule::bindAttributes()
{

	GafferBindings::DependencyNodeClass<AttributeProcessor>();
	GafferBindings::DependencyNodeClass<ShaderAssignment>();
	GafferBindings::DependencyNodeClass<Attributes>();
	GafferBindings::DependencyNodeClass<OpenGLAttributes>();
	GafferBindings::DependencyNodeClass<StandardAttributes>();
	GafferBindings::DependencyNodeClass<CustomAttributes>();
	GafferBindings::DependencyNodeClass<DeleteAttributes>();
	GafferBindings::DependencyNodeClass<CopyAttributes>();
	GafferBindings::DependencyNodeClass<ShuffleAttributes>();
	GafferBindings::DependencyNodeClass<SetVisualiser>();
	GafferBindings::DependencyNodeClass<CollectTransforms>();
	GafferBindings::DependencyNodeClass<LocaliseAttributes>();

	{
		scope s = GafferBindings::DependencyNodeClass<AttributeVisualiser>();

		enum_<AttributeVisualiser::Mode>( "Mode" )
			.value( "Color", AttributeVisualiser::Color )
			.value( "FalseColor", AttributeVisualiser::FalseColor )
			.value( "Random", AttributeVisualiser::Random )
			.value( "ShaderNodeColor", AttributeVisualiser::ShaderNodeColor )
		;
	}

	GafferBindings::DependencyNodeClass<AttributeQuery>()
		.def( "isSetup", & AttributeQueryBinding::isSetup )
		.def( "canSetup", & AttributeQueryBinding::canSetup )
		.def( "setup", & AttributeQueryBinding::setup )
		;

	GafferBindings::Serialisation::registerSerialiser( AttributeQuery::staticTypeId(), new AttributeQueryBinding::Serialiser() );
}
