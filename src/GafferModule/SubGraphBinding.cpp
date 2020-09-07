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

#include "SubGraphBinding.h"

#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Box.h"
#include "Gaffer/BoxIn.h"
#include "Gaffer/BoxOut.h"
#include "Gaffer/EditScope.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Reference.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

// Box
// ===

class BoxSerialiser : public NodeSerialiser
{

	bool childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		if( child->isInstanceOf( Node::staticTypeId() ) )
		{
			return true;
		}
		return NodeSerialiser::childNeedsSerialisation( child, serialisation );
	}

	bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		if( child->isInstanceOf( Node::staticTypeId() ) )
		{
			return true;
		}
		return NodeSerialiser::childNeedsConstruction( child, serialisation );
	}

};

} // namespace

// BoxIO
// =====

namespace GafferModule
{

class BoxIOSerialiser : public NodeSerialiser
{

	bool childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const override
	{
		const BoxIO *boxIO = child->parent<BoxIO>();
		if( child == boxIO->inPlugInternal() || child == boxIO->outPlugInternal() || child == boxIO->passThroughPlugInternal() )
		{
			// We'll serialise a `setup()` call to construct these.
			return false;
		}
		return NodeSerialiser::childNeedsConstruction( child, serialisation );
	}

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const override
	{
		std::string result = NodeSerialiser::postConstructor( graphComponent, identifier, serialisation );

		const BoxIO *boxIO = static_cast<const BoxIO *>( graphComponent );
		if( !boxIO->plug() )
		{
			// BoxIO::setup() hasn't been called yet.
			return result;
		}

		// Only serialise a call to setup() when we need to construct this node
		if( !Serialisation::acquireSerialiser( graphComponent->parent() )->childNeedsConstruction(
			graphComponent, serialisation ) )
		{
			return result;
		}

		if( result.size() )
		{
			result += "\n";
		}

		// Add a call to `setup()` to recreate the plugs.

		PlugPtr plug = boxIO->plug()->createCounterpart( boxIO->plug()->getName(), Plug::In );
		plug->setFlags( Plug::Dynamic, false );

		const Serialiser *plugSerialiser = Serialisation::acquireSerialiser( plug.get() );
		result += identifier + ".setup( " + plugSerialiser->constructor( plug.get(), serialisation ) + " )\n";

		return result;
	}

	std::string postScript( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const override
	{
		std::string result = NodeSerialiser::postScript( graphComponent, identifier, serialisation );

		const BoxIO *boxIO = static_cast<const BoxIO *>( graphComponent );
		if( !boxIO->plug() )
		{
			// BoxIO::setup() hasn't been called yet.
			return result;
		}

		const Plug *promoted = boxIO->promotedPlug();
		if( promoted && serialisation.identifier( promoted ) != "" )
		{
			return result;
		}

		// The BoxIO node has been set up, but its promoted plug isn't
		// being serialised (for instance, because someone is copying a
		// selection from inside a box). Add a `setupPromotedPlug()` call
		// so that the promoted plug will be created if we happen to be
		// pasted into another box.

		if( !result.empty() )
		{
			result += "\n";
		}
		result += identifier + ".setupPromotedPlug()\n";

		return result;
	}

};

} // namespace GafferModule

namespace
{

template<typename T>
void setup( T &n, const Plug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	n.setup( &plug );
}

void setupPromotedPlug( BoxIO &b )
{
	IECorePython::ScopedGILRelease gilRelease;
	b.setupPromotedPlug();
}

PlugPtr plug( BoxIO &b )
{
	return b.plug();
}

PlugPtr promotedPlug( BoxIO &b )
{
	return b.promotedPlug();
}

PlugPtr promote( Plug &plug )
{
	IECorePython::ScopedGILRelease gilRelease;
	return BoxIO::promote( &plug );
}

void insert( Box &box )
{
	IECorePython::ScopedGILRelease gilRelease;
	BoxIO::insert( &box );
}

DependencyNodePtr acquireProcessor( EditScope &e, const std::string &type, bool createIfNecessary )
{
	IECorePython::ScopedGILRelease gilRelease;
	return e.acquireProcessor( type, createIfNecessary );
}

list processors( EditScope &e )
{
	list result;
	for( const auto &n : e.processors() )
	{
		result.append( DependencyNodePtr( n ) );
	}
	return result;
}

list registeredProcessors()
{
	list result;
	for( const auto &n : EditScope::registeredProcessors() )
	{
		result.append( n );
	}
	return result;
}

void registerProcessor( const std::string &name, object creator )
{
	EditScope::registerProcessor(
		name,
		[creator]() {
			IECorePython::ScopedGILLock gilLock;
			object n = creator();
			return extract<DependencyNodePtr>( n )();
		}
	);
}

} // namespace

// Reference
// =========

namespace
{

struct ReferenceLoadedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, ReferencePtr r )
	{
		try
		{
			slot( r );
		}
		catch( const error_already_set &e )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

class ReferenceSerialiser : public NodeSerialiser
{

	std::string postConstructor( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const override
	{
		const Reference *r = static_cast<const Reference *>( graphComponent );

		const std::string &fileName = r->fileName();
		if( fileName.empty() )
		{
			return "";
		};

		return identifier + ".load( \"" + fileName + "\" )\n";
	}

};

void load( Reference &r, const std::string &f )
{
	IECorePython::ScopedGILRelease gilRelease;
	r.load( f );
}

} // namespace

void GafferModule::bindSubGraph()
{
	typedef DependencyNodeWrapper<SubGraph> SubGraphWrapper;
	DependencyNodeClass<SubGraph, SubGraphWrapper>();

	typedef DependencyNodeWrapper<Box> BoxWrapper;

	DependencyNodeClass<Box, BoxWrapper>()
		.def( "canPromotePlug", &Box::canPromotePlug, ( arg( "descendantPlug" ) ) )
		.def( "promotePlug", &Box::promotePlug, ( arg( "descendantPlug" ) ), return_value_policy<CastToIntrusivePtr>() )
		.def( "plugIsPromoted", &Box::plugIsPromoted )
		.def( "unpromotePlug", &Box::unpromotePlug )
		.def( "exportForReference", &Box::exportForReference )
		.def( "create", &Box::create )
		.staticmethod( "create" )
	;

	Serialisation::registerSerialiser( Box::staticTypeId(), new BoxSerialiser );

	NodeClass<BoxIO>( nullptr, no_init )
		.def( "setup", &setup<BoxIO>, ( arg( "plug" ) = object() ) )
		.def( "setupPromotedPlug", &setupPromotedPlug )
		.def( "plug", &plug )
		.def( "promotedPlug", &promotedPlug )
		.def( "promote", &promote )
		.staticmethod( "promote" )
		.def( "insert", &insert )
		.staticmethod( "insert" )
		.def( "canInsert", &BoxIO::canInsert )
		.staticmethod( "canInsert" )
	;

	Serialisation::registerSerialiser( BoxIO::staticTypeId(), new BoxIOSerialiser );

	NodeClass<BoxIn>();
	NodeClass<BoxOut>();

	NodeClass<Reference>()
		.def( "load", &load )
		.def( "fileName", &Reference::fileName, return_value_policy<copy_const_reference>() )
		.def( "referenceLoadedSignal", &Reference::referenceLoadedSignal, return_internal_reference<1>() )
		.def( "hasMetadataEdit", &Reference::hasMetadataEdit )
	;

	SignalClass<Reference::ReferenceLoadedSignal, DefaultSignalCaller<Reference::ReferenceLoadedSignal>, ReferenceLoadedSlotCaller >( "ReferenceLoadedSignal" );

	Serialisation::registerSerialiser( Reference::staticTypeId(), new ReferenceSerialiser );

	NodeClass<EditScope>()
		.def( "setup", &setup<EditScope>, ( arg( "plug" ) ) )
		.def( "acquireProcessor", &acquireProcessor, ( arg( "type" ), arg( "createIfNecessary" ) = true ) )
		.def( "processors", &processors )
		.def( "registerProcessor", &registerProcessor )
		.staticmethod( "registerProcessor" )
		.def( "deregisterProcessor", &EditScope::deregisterProcessor )
		.staticmethod( "deregisterProcessor" )
		.def( "registeredProcessors", &registeredProcessors )
		.staticmethod( "registeredProcessors" )
	;

}
