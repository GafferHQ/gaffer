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
#include "boost/format.hpp"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/Wrapper.h"

#include "Gaffer/GraphComponent.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/Serialisation.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

static const char *setName( GraphComponent &c, const char *name )
{
	return c.setName( name ).c_str();
}

static const char *getName( GraphComponent &c )
{
	return c.getName().c_str();
}

static boost::python::list items( GraphComponent &c )
{
	const GraphComponent::ChildContainer &ch = c.children();
	boost::python::list l;
	for( GraphComponent::ChildContainer::const_iterator it=ch.begin(); it!=ch.end(); it++ )
	{
		l.append( boost::python::make_tuple( (*it)->getName(), *it ) );
	}
	return l;
}

static boost::python::list keys( GraphComponent &c )
{
	const GraphComponent::ChildContainer &ch = c.children();
	boost::python::list l;
	for( GraphComponent::ChildContainer::const_iterator it=ch.begin(); it!=ch.end(); it++ )
	{
		l.append( (*it)->getName().c_str() );
	}
	return l;
}

static boost::python::list values( GraphComponent &c )
{
	const GraphComponent::ChildContainer &ch = c.children();
	boost::python::list l;
	for( GraphComponent::ChildContainer::const_iterator it=ch.begin(); it!=ch.end(); it++ )
	{
		l.append( *it );
	}
	return l;
}

static boost::python::tuple children( GraphComponent &c, IECore::TypeId typeId )
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

static GraphComponentPtr getChild( GraphComponent &g, const char *n )
{
	return g.getChild<GraphComponent>( n );
}

static GraphComponentPtr descendant( GraphComponent &g, const char *n )
{
	return g.descendant<GraphComponent>( n );
}

static GraphComponentPtr getItem( GraphComponent &g, const char *n )
{
	GraphComponentPtr c = g.getChild<GraphComponent>( n );
	if( c )
	{
		return c;
	}

	PyErr_SetString( PyExc_KeyError, n );
	throw_error_already_set();
	return 0; // shouldn't get here
}

static GraphComponentPtr getItem( GraphComponent &g, long index )
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

	return g.getChild<GraphComponent>( index );
}

static void delItem( GraphComponent &g, const char *n )
{
	GraphComponentPtr c = g.getChild<GraphComponent>( n );
	if( c )
	{
		g.removeChild( c );
		return;
	}

	PyErr_SetString( PyExc_KeyError, n );
	throw_error_already_set();
}

static int length( GraphComponent &g )
{
	return g.children().size();
}

static bool nonZero( GraphComponent &g )
{
	return true;
}

static bool contains( GraphComponent &g, const char *n )
{
	return g.getChild<GraphComponent>( n );
}

static GraphComponentPtr parent( GraphComponent &g )
{
	return g.parent<GraphComponent>();
}

static GraphComponentPtr ancestor( GraphComponent &g, IECore::TypeId t )
{
	return g.ancestor( t );
}

static GraphComponentPtr commonAncestor( GraphComponent &g, const GraphComponent *other, IECore::TypeId t )
{
	return g.commonAncestor( other, t );
}

static std::string repr( const GraphComponent *g )
{
	return Serialisation::classPath( g ) + "( \"" + g->getName().string() + "\" )";
}

struct UnarySlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, GraphComponentPtr g )
	{
		try
		{
			slot( g );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

struct BinarySlotCaller
{

	boost::signals::detail::unusable operator()( boost::python::object slot, GraphComponentPtr g, GraphComponentPtr gg )
	{
		try
		{
			slot( g, gg );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

void GafferBindings::bindGraphComponent()
{
	typedef GraphComponentWrapper<GraphComponent> Wrapper;

	scope s = GraphComponentClass<GraphComponent, Wrapper>()
		.def( init<>() )
		.def( init<const std::string &>() )
		.def( "setName", &setName )
		.def( "getName", &getName )
		.def( "fullName", &GraphComponent::fullName )
		.def( "relativeName", &GraphComponent::relativeName )
		.def( "nameChangedSignal", &GraphComponent::nameChangedSignal, return_internal_reference<1>() )
		.def( "addChild", &GraphComponent::addChild )
		.def( "removeChild", &GraphComponent::removeChild )
		.def( "clearChildren", &GraphComponent::clearChildren )
		.def( "setChild", &GraphComponent::setChild )
		.def( "getChild", &getChild )
		.def( "descendant", &descendant )
		.def( "__getitem__", (GraphComponentPtr (*)( GraphComponent &, const char * ))&getItem )
		.def( "__getitem__", (GraphComponentPtr (*)( GraphComponent &, long ))&getItem )
		.def( "__setitem__", &GraphComponent::setChild )
		.def( "__delitem__", delItem )
		.def( "__contains__", contains )
		.def( "__len__", &length )
		.def( "__nonzero__", &nonZero )
		.def( "__repr__", &repr )
		.def( "items", &items )
		.def( "keys", &keys )
		.def( "values", &values )
		.def( "children", &children, ( arg_( "self" ), arg_( "typeId" ) = GraphComponent::staticTypeId() ) )
		.def( "parent", &parent )
		.def( "ancestor", &ancestor )
		.def( "commonAncestor", &commonAncestor )
		.def( "isAncestorOf", &GraphComponent::isAncestorOf )
		.def( "childAddedSignal", &GraphComponent::childAddedSignal, return_internal_reference<1>() )
		.def( "childRemovedSignal", &GraphComponent::childRemovedSignal, return_internal_reference<1>() )
		.def( "parentChangedSignal", &GraphComponent::parentChangedSignal, return_internal_reference<1>() )
	;

	SignalBinder<GraphComponent::UnarySignal, DefaultSignalCaller<GraphComponent::UnarySignal>, UnarySlotCaller>::bind( "UnarySignal" );
	SignalBinder<GraphComponent::BinarySignal, DefaultSignalCaller<GraphComponent::BinarySignal>, BinarySlotCaller>::bind( "BinarySignal" );

}
