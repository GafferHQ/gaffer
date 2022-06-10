//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "ContextProcessorBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "Gaffer/ContextVariables.h"
#include "Gaffer/DeleteContextVariables.h"
#include "Gaffer/TimeWarp.h"
#include "Gaffer/Loop.h"
#include "Gaffer/ContextQuery.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

IECore::InternedString g_inPlugName( "in" );
IECore::InternedString g_outPlugName( "out" );

void setupContextProcessor( ContextProcessor &n, const Plug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	n.setup( &plug );
}

void setupLoop( Loop &n, const ValuePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	n.setup( &plug );
}

ContextPtr inPlugContext( const ContextProcessor &n )
{
	IECorePython::ScopedGILRelease gilRelease;
	return n.inPlugContext();
}

class SetupBasedNodeSerialiser : public NodeSerialiser
{

	bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		const Node *node = child->parent<Node>();
		if( child == node->getChild( g_inPlugName ) || child == node->getChild( g_outPlugName ) )
		{
			// We'll serialise a `setup()` call to construct these.
			return false;
		}
		return NodeSerialiser::childNeedsConstruction( child, serialisation );
	}

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, Serialisation &serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		auto node = static_cast<const Node *>( graphComponent );
		const Plug *inPlug = node->getChild<Plug>( g_inPlugName );
		if( !inPlug )
		{
			// `setup()` hasn't been called yet.
			return result;
		}

		if( result.size() )
		{
			result += "\n";
		}

		// Add a call to `setup()` to recreate the plugs.

		/// \todo Avoid creating a temporary plug.
		PlugPtr plug = inPlug->createCounterpart( g_inPlugName, Plug::In );
		plug->setFlags( Plug::Dynamic, false );

		const Serialiser *plugSerialiser = Serialisation::acquireSerialiser( plug.get() );
		result += identifier + ".setup( " + plugSerialiser->constructor( plug.get(), serialisation ) + " )\n";

		return result;
	}

};

NameValuePlugPtr addQuery(
	Gaffer::ContextQuery &query,
	const ValuePlug &plug,
	const std::string &variable
)
{
	IECorePython::ScopedGILRelease gilRelease;

	NameValuePlug *result = query.addQuery( &plug, variable );

	return result;
}

void removeQuery( Gaffer::ContextQuery &query, NameValuePlug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	query.removeQuery( &plug );
}

const ValuePlugPtr outPlugFromQueryPlug( const Gaffer::ContextQuery &q, const NameValuePlug &p )
{
	return const_cast<ValuePlug *>( q.outPlugFromQueryPlug( &p ) );
}

const NameValuePlugPtr queryPlugFromOutPlug( const Gaffer::ContextQuery &q, const ValuePlug &p )
{
	return const_cast<NameValuePlug *>( q.queryPlugFromOutPlug( &p ) );
}

const BoolPlugPtr existsPlugFromQueryPlug( Gaffer::ContextQuery &q, const NameValuePlug &p )
{
	return const_cast<BoolPlug *>( q.existsPlugFromQueryPlug( &p ) );
}

const ValuePlugPtr valuePlugFromQueryPlug( Gaffer::ContextQuery &q, const NameValuePlug &p )
{
	return const_cast<ValuePlug *>( q.valuePlugFromQueryPlug( &p ) );
}

class ContextQuerySerialiser : public NodeSerialiser
{
	std::string postConstructor( const GraphComponent* component, const std::string& identifier, Serialisation& serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( component, identifier, serialisation );

		const Gaffer::ContextQuery* const query = IECore::runTimeCast< const Gaffer::ContextQuery >( component );

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

} // namespace

void GafferModule::bindContextProcessor()
{

	DependencyNodeClass<Loop>()
		.def( "setup", &setupLoop )
	;

	DependencyNodeClass<ContextProcessor>()
		.def( "setup", &setupContextProcessor )
		.def( "inPlugContext", &inPlugContext )
	;

	DependencyNodeClass<TimeWarp>();
	DependencyNodeClass<ContextVariables>();
	DependencyNodeClass<DeleteContextVariables>();

	Serialisation::registerSerialiser( Loop::staticTypeId(), new SetupBasedNodeSerialiser );
	Serialisation::registerSerialiser( ContextProcessor::staticTypeId(), new SetupBasedNodeSerialiser );

	DependencyNodeClass< Gaffer::ContextQuery >()
		.def( "addQuery", &addQuery, ( arg( "plug" ), arg( "variable" ) = "" ) )
		.def( "removeQuery", &removeQuery )
		.def( "outPlugFromQueryPlug", &outPlugFromQueryPlug )
		.def( "queryPlugFromOutPlug", &queryPlugFromOutPlug )
		.def( "existsPlugFromQueryPlug", &existsPlugFromQueryPlug )
		.def( "valuePlugFromQueryPlug", &valuePlugFromQueryPlug )
	;
	Serialisation::registerSerialiser( Gaffer::ContextQuery::staticTypeId(), new ContextQuerySerialiser() );

}
