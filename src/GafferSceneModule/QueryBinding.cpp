//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Cinesite VFX Ltd. All rights reserved.
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

#include "QueryBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/Serialisation.h"

#include "GafferScene/AttributeQuery.h"
#include "GafferScene/BoundQuery.h"
#include "GafferScene/ExistenceQuery.h"
#include "GafferScene/FilterQuery.h"
#include "GafferScene/OptionQuery.h"
#include "GafferScene/TransformQuery.h"
#include "GafferScene/ShaderQuery.h"

#include "IECorePython/ScopedGILRelease.h"

using namespace boost::python;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

bool isSetup( const GafferScene::AttributeQuery& query )
{
	return query.isSetup();
}

bool canSetup( const GafferScene::AttributeQuery& query, const Gaffer::ValuePlug& plug )
{
	return query.canSetup( & plug );
}

void setup( GafferScene::AttributeQuery& query, const Gaffer::ValuePlug& plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	if( !( query.canSetup( & plug ) ) )
	{
		throw IECore::Exception( "AttributeQuery cannot be setup from specified plug" );
	}
	query.setup( & plug );
}

class AttributeQuerySerialiser : public GafferBindings::NodeSerialiser
{
	std::string postConstructor( const Gaffer::GraphComponent* component, const std::string& identifier, GafferBindings::Serialisation& serialisation ) const override
	{
		std::string result = GafferBindings::NodeSerialiser::postConstructor( component, identifier, serialisation );

		const GafferScene::AttributeQuery* const query = IECore::assertedStaticCast< const GafferScene::AttributeQuery >( component );

		if( query->isSetup() )
		{
			if( result.size() )
			{
				result += "\n";
			}

			const GafferBindings::Serialisation::Serialiser* const serialiser = Serialisation::acquireSerialiser( query->valuePlug() );
			result += identifier + ".setup( " + serialiser->constructor( query->valuePlug(), serialisation ) + " )\n";
		}

		return result;
	}
};

template<typename T>
NameValuePlugPtr addQuery( T &query, const ValuePlug &plug, const std::string &parameter )
{
	IECorePython::ScopedGILRelease gilRelease;

	NameValuePlug *result = query.addQuery( &plug, parameter );

	return result;
}

template<typename T>
void removeQuery( T &query, NameValuePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	query.removeQuery( &plug );
}

template<typename T>
const BoolPlugPtr existsPlugFromQuery( const T &q, const NameValuePlug &p )
{
	return const_cast<BoolPlug *>( q.existsPlugFromQuery( &p ) );
}

template<typename T>
const ValuePlugPtr valuePlugFromQuery( const T &q, const NameValuePlug &p )
{
	return const_cast<ValuePlug *>( q.valuePlugFromQuery( &p ) );
}

template<typename T>
const ValuePlugPtr outPlugFromQuery( const T &q, const NameValuePlug &p )
{
	return const_cast<ValuePlug *>( q.outPlugFromQuery( &p ) );
}

template<typename T>
const NameValuePlugPtr queryPlug( const T &q, const ValuePlug &p )
{
	return const_cast<NameValuePlug *>( q.queryPlug( &p ) );
}

template<typename T>
class MultiQuerySerialiser : public NodeSerialiser
{
	std::string postConstructor( const GraphComponent* component, const std::string& identifier, Serialisation& serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( component, identifier, serialisation );

		const T* const query = IECore::runTimeCast< const T >( component );

		for( const auto &queryPlug : NameValuePlug::Range( *query->queriesPlug() ) )
		{
			const Serialisation::Serialiser* serialiser = Serialisation::acquireSerialiser( queryPlug->valuePlug() );
			result +=
				identifier + ".addQuery( " +
				serialiser->constructor( queryPlug->valuePlug(), serialisation ) +
				" )\n"
			;
		}

		return result;
	}
};

template<typename T>
void bindMultiQuery()
{
	DependencyNodeClass<T>()
		.def( "addQuery", &addQuery<T>, ( arg( "plug" ), arg( "parameter" ) = "" ) )
		.def( "removeQuery", &removeQuery<T> )
		.def( "existsPlugFromQuery", &existsPlugFromQuery<T> )
		.def( "valuePlugFromQuery", &valuePlugFromQuery<T> )
		.def( "outPlugFromQuery", &outPlugFromQuery<T> )
		.def( "queryPlug", &queryPlug<T> )
	;
	Serialisation::registerSerialiser( T::staticTypeId(), new MultiQuerySerialiser<T>() );
}

} // namespace

void GafferSceneModule::bindQueries()
{
	GafferBindings::DependencyNodeClass< GafferScene::AttributeQuery >()
		.def( "isSetup", & isSetup )
		.def( "canSetup", & canSetup )
		.def( "setup", & setup )
	;

	GafferBindings::Serialisation::registerSerialiser( GafferScene::AttributeQuery::staticTypeId(), new AttributeQuerySerialiser() );

	bindMultiQuery<GafferScene::ShaderQuery>();
	bindMultiQuery<GafferScene::OptionQuery>();

	{
		boost::python::scope s = GafferBindings::DependencyNodeClass< GafferScene::BoundQuery >();

		boost::python::enum_< GafferScene::BoundQuery::Space >( "Space" )
			.value( "Local", GafferScene::BoundQuery::Space::Local )
			.value( "World", GafferScene::BoundQuery::Space::World )
			.value( "Relative", GafferScene::BoundQuery::Space::Relative )
		;
	}

	GafferBindings::DependencyNodeClass< GafferScene::ExistenceQuery >();
	GafferBindings::DependencyNodeClass< GafferScene::FilterQuery >();

	{
		boost::python::scope s = GafferBindings::DependencyNodeClass< GafferScene::TransformQuery >();

		boost::python::enum_< GafferScene::TransformQuery::Space >( "Space" )
			.value( "Local", GafferScene::TransformQuery::Space::Local )
			.value( "World", GafferScene::TransformQuery::Space::World )
			.value( "Relative", GafferScene::TransformQuery::Space::Relative )
		;
	}
}
