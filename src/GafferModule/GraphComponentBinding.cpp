//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "GraphComponentBinding.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/Serialisation.h"

#include "Gaffer/GraphComponent.h"
#include "Gaffer/Metadata.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILRelease.h"

#include "IECore/SimpleTypedData.h"

#include "boost/python/suite/indexing/container_utils.hpp"

#include "fmt/format.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

namespace
{

const char *setName( GraphComponent &c, const IECore::InternedString &name )
{
	IECorePython::ScopedGILRelease gilRelease;
	return c.setName( name ).c_str();
}

const char *getName( GraphComponent &c )
{
	return c.getName().c_str();
}

boost::python::list items( GraphComponent &c )
{
	const GraphComponent::ChildContainer &ch = c.children();
	boost::python::list l;
	for( GraphComponent::ChildContainer::const_iterator it=ch.begin(); it!=ch.end(); it++ )
	{
		l.append( boost::python::make_tuple( (*it)->getName().c_str(), *it ) );
	}
	return l;
}

boost::python::list keys( GraphComponent &c )
{
	const GraphComponent::ChildContainer &ch = c.children();
	boost::python::list l;
	for( GraphComponent::ChildContainer::const_iterator it=ch.begin(); it!=ch.end(); it++ )
	{
		l.append( (*it)->getName().c_str() );
	}
	return l;
}

boost::python::list values( GraphComponent &c )
{
	const GraphComponent::ChildContainer &ch = c.children();
	boost::python::list l;
	for( GraphComponent::ChildContainer::const_iterator it=ch.begin(); it!=ch.end(); it++ )
	{
		l.append( *it );
	}
	return l;
}

boost::python::tuple children( GraphComponent &c, IECore::TypeId typeId )
{
	const GraphComponent::ChildContainer &ch = c.children();
	boost::python::list l;
	for( GraphComponent::ChildContainer::const_iterator it=ch.begin(); it!=ch.end(); it++ )
	{
		if( (*it)->isInstanceOf( typeId ) )
		{
			l.append( *it );
		}
	}
	return boost::python::tuple( l );
}

void addChild( GraphComponent &g, GraphComponent &c )
{
	IECorePython::ScopedGILRelease gilRelease;
	g.addChild( &c );
}

void setChild( GraphComponent &g, const IECore::InternedString &n, GraphComponent &c )
{
	IECorePython::ScopedGILRelease gilRelease;
	g.setChild( n, &c );
}

void removeChild( GraphComponent &g, GraphComponent &c )
{
	IECorePython::ScopedGILRelease gilRelease;
	g.removeChild( &c );
}

void clearChildren( GraphComponent &g )
{
	IECorePython::ScopedGILRelease gilRelease;
	g.clearChildren();
}

void reorderChildren( GraphComponent &g, object pythonNewOrder )
{
	GraphComponent::ChildContainer newOrder;
	boost::python::container_utils::extend_container( newOrder, pythonNewOrder );
	IECorePython::ScopedGILRelease gilRelease;
	g.reorderChildren( newOrder );
}

GraphComponentPtr getChild( GraphComponent &g, const IECore::InternedString &n )
{
	if( const auto child = g.getChild( n ) )
	{
		return child;
	}
	else if( const auto childAlias = Gaffer::Metadata::value<IECore::StringData>( &g, fmt::format( "compatibility:childAlias:{}", n.string() ) ) )
	{
		return g.getChild( childAlias->readable() );
	}

	return nullptr;
}

GraphComponentPtr descendant( GraphComponent &g, const std::string &n )
{
	if( !n.size() )
	{
		return nullptr;
	}

	using Tokenizer = boost::tokenizer<boost::char_separator<char> >;
	Tokenizer tokens( n, boost::char_separator<char>( "." ) );
	GraphComponentPtr result = &g;
	for( const auto &token : tokens )
	{
		result = getChild( *result, token );
		if( !result )
		{
			return nullptr;
		}
	}

	return result;
}

void throwKeyError( const GraphComponent &g, const IECore::InternedString &n )
{
	const std::string error = fmt::format( "'{}' is not a child of '{}'", n.string(), g.getName().string() );
	PyErr_SetString( PyExc_KeyError, error.c_str() );
	throw_error_already_set();
}

GraphComponentPtr getItem( GraphComponent &g, const IECore::InternedString &n )
{
	GraphComponentPtr c = getChild( g, n );
	if( c )
	{
		return c;
	}

	throwKeyError( g, n );
	return nullptr; // shouldn't get here
}

GraphComponentPtr getItem( GraphComponent &g, long index )
{
	long s = g.children().size();

	if( index < 0 )
	{
		index += s;
	}

	if( index >= s || index < 0 )
	{
		PyErr_SetString( PyExc_IndexError, "GraphComponent index out of range" );
		throw_error_already_set();
	}

	return g.getChild( index );
}

void delItem( GraphComponent &g, const IECore::InternedString &n )
{
	{
		IECorePython::ScopedGILRelease gilRelease;
		if( GraphComponentPtr c = getChild( g, n ) )
		{
			g.removeChild( c );
			return;
		}
	}

	throwKeyError( g, n );
}

void delItem( GraphComponent &g, long index )
{
	GraphComponentPtr c = getItem( g, index );
	IECorePython::ScopedGILRelease gilRelease;
	g.removeChild( c );
}

int length( GraphComponent &g )
{
	return g.children().size();
}

bool toBool( GraphComponent &g )
{
	return true;
}

bool contains( GraphComponent &g, const IECore::InternedString &n )
{
	return (bool)getChild( g, n );
}

GraphComponentPtr parent( GraphComponent &g )
{
	return g.parent();
}

GraphComponentPtr ancestor( GraphComponent &g, IECore::TypeId t )
{
	return g.ancestor( t );
}

GraphComponentPtr commonAncestor( GraphComponent &g, const GraphComponent *other, IECore::TypeId t )
{
	return g.commonAncestor( other, t );
}

std::string repr( const GraphComponent *g )
{
	return Serialisation::classPath( g ) + "( \"" + g->getName().string() + "\" )";
}

struct UnarySlotCaller
{
	void operator()( boost::python::object slot, GraphComponentPtr g )
	{
		try
		{
			slot( g );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

struct NameChangedSlotCaller
{
	void operator()( boost::python::object slot, GraphComponentPtr g, IECore::InternedString oldName )
	{
		try
		{
			slot( g, oldName.string() );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

struct BinarySlotCaller
{

	void operator()( boost::python::object slot, GraphComponentPtr g, GraphComponentPtr gg )
	{
		try
		{
			slot( g, gg );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

struct ChildrenReorderedSlotCaller
{

	void operator()( boost::python::object slot, GraphComponentPtr g, const std::vector<size_t> &oldIndices )
	{
		try
		{
			boost::python::list oldIndicesList;
			for( auto i : oldIndices )
			{
				oldIndicesList.append( i );
			}
			slot( g, oldIndicesList );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

} // namespace

void GafferModule::bindGraphComponent()
{
	using Wrapper = GraphComponentWrapper<GraphComponent>;

	scope s = GraphComponentClass<GraphComponent, Wrapper>()
		.def( init<>() )
		.def( init<const std::string &>() )
		.def( "setName", &setName )
		.def( "getName", &getName )
		.def( "fullName", &GraphComponent::fullName )
		.def( "relativeName", &GraphComponent::relativeName )
		.def( "nameChangedSignal", &GraphComponent::nameChangedSignal, return_internal_reference<1>() )
		.def( "addChild", &addChild )
		.def( "removeChild", &removeChild )
		.def( "clearChildren", &clearChildren )
		.def( "reorderChildren", &reorderChildren )
		.def( "setChild", &setChild )
		.def( "getChild", &getChild )
		.def( "descendant", &descendant )
		.def( "__getitem__", (GraphComponentPtr (*)( GraphComponent &, const IECore::InternedString & ))&getItem )
		.def( "__getitem__", (GraphComponentPtr (*)( GraphComponent &, long ))&getItem )
		.def( "__setitem__", &setChild )
		.def( "__delitem__", (void (*)( GraphComponent &, const IECore::InternedString & ))delItem )
		.def( "__delitem__", (void (*)( GraphComponent &, long ))&delItem )
		.def( "__contains__", contains )
		.def( "__len__", &length )
// The default conversion to bool uses `__len__`, which trips a lot of
// people up as they expect `if graphComponent` to be equivalent to
// `if graphComponent is not None`. So we provide a more specific conversion
// which is always true.
		.def( "__bool__", &toBool )
		.def( "__repr__", &repr )
		.def( "items", &items )
		.def( "keys", &keys )
		.def( "values", &values )
		.def( "children", &children, ( arg_( "self" ), arg_( "typeId" ) = GraphComponent::staticTypeId() ) )
		.def( "parent", &parent )
		.def( "ancestor", &ancestor )
		.def( "commonAncestor", &commonAncestor, ( arg_( "self" ), arg_( "other" ), arg_( "ancestorType" ) = GraphComponent::staticTypeId() ) )
		.def( "isAncestorOf", &GraphComponent::isAncestorOf )
		.def( "childAddedSignal", &GraphComponent::childAddedSignal, return_internal_reference<1>() )
		.def( "childRemovedSignal", &GraphComponent::childRemovedSignal, return_internal_reference<1>() )
		.def( "parentChangedSignal", &GraphComponent::parentChangedSignal, return_internal_reference<1>() )
		.def( "childrenReorderedSignal", &GraphComponent::childrenReorderedSignal, return_internal_reference<1>() )
	;

	SignalClass<GraphComponent::UnarySignal, DefaultSignalCaller<GraphComponent::UnarySignal>, UnarySlotCaller>( "UnarySignal" );
	SignalClass<GraphComponent::NameChangedSignal, DefaultSignalCaller<GraphComponent::NameChangedSignal>, NameChangedSlotCaller>( "NameChangedSignal" );
	SignalClass<GraphComponent::BinarySignal, DefaultSignalCaller<GraphComponent::BinarySignal>, BinarySlotCaller>( "BinarySignal" );
	SignalClass<GraphComponent::ChildrenReorderedSignal, DefaultSignalCaller<GraphComponent::ChildrenReorderedSignal>, ChildrenReorderedSlotCaller>( "BinarySignal" );

}
