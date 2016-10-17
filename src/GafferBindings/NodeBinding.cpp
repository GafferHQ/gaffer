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

#include "Gaffer/ScriptNode.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/MetadataBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

struct UnaryPlugSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, PlugPtr p )
	{
		try
		{
			slot( p );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

struct BinaryPlugSlotCaller
{

	boost::signals::detail::unusable operator()( boost::python::object slot, PlugPtr p1, PlugPtr p2 )
	{
		try
		{
			slot( p1, p2 );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

struct ErrorSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, const Plug *plug, const Plug *source, const std::string &error )
	{
		try
		{
			slot( PlugPtr( const_cast<Plug *>( plug ) ), PlugPtr( const_cast<Plug *>( source ) ), error );
		}
		catch( const error_already_set &e )
		{
			translatePythonException();
		}
		return boost::signals::detail::unusable();
	}
};

} // namespace

void NodeSerialiser::moduleDependencies( const Gaffer::GraphComponent *graphComponent, std::set<std::string> &modules, const Serialisation &serialisation ) const
{
	Serialiser::moduleDependencies( graphComponent, modules, serialisation );
	metadataModuleDependencies( static_cast<const Gaffer::Node *>( graphComponent ), modules );
}

std::string NodeSerialiser::postHierarchy( const Gaffer::GraphComponent *graphComponent, const std::string &identifier, const Serialisation &serialisation ) const
{
	return Serialiser::postHierarchy( graphComponent, identifier, serialisation ) +
		metadataSerialisation( static_cast<const Gaffer::Node *>( graphComponent ), identifier );
}

bool NodeSerialiser::childNeedsSerialisation( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
{
	if( const Plug *childPlug = IECore::runTimeCast<const Plug>( child ) )
	{
		return childPlug->getFlags( Plug::Serialisable );
	}
	else
	{
		assert( child->isInstanceOf( Node::staticTypeId() ) );
		// Typically we expect internal nodes to be part of the private
		// implementation of the parent node, and to be created explicitly
		// in the parent constructor. Therefore we don't expect them to
		// need serialisation. But, if the root of the serialisation is
		// the node itself, it won't be included, so we must serialise the
		// children explicitly. This is most useful to allow nodes to be
		// cut + pasted out of Reference nodes, but implementing it here
		// makes it possible to inspect the internals of other nodes too.
		return serialisation.parent() == child->parent<GraphComponent>();
	}
}

bool NodeSerialiser::childNeedsConstruction( const Gaffer::GraphComponent *child, const Serialisation &serialisation ) const
{
	if( const Plug *childPlug = IECore::runTimeCast<const Plug>( child ) )
	{
		return childPlug->getFlags( Plug::Dynamic );
	}
	else
	{
		assert( child->isInstanceOf( Node::staticTypeId() ) );
		return true;
	}
}

void GafferBindings::bindNode()
{
	typedef NodeWrapper<Node> Wrapper;

	scope s = NodeClass<Node, Wrapper>()
		.def( "scriptNode", (ScriptNode *(Node::*)())&Node::scriptNode, return_value_policy<CastToIntrusivePtr>() )
		.def( "plugSetSignal", &Node::plugSetSignal, return_internal_reference<1>() )
		.def( "plugInputChangedSignal", &Node::plugInputChangedSignal, return_internal_reference<1>() )
		.def( "plugFlagsChangedSignal", &Node::plugFlagsChangedSignal, return_internal_reference<1>() )
		.def( "plugDirtiedSignal", &Node::plugDirtiedSignal, return_internal_reference<1>() )
		.def( "errorSignal", (Node::ErrorSignal &(Node::*)())&Node::errorSignal, return_internal_reference<1>() )
	;

	SignalClass<Node::UnaryPlugSignal, DefaultSignalCaller<Node::UnaryPlugSignal>, UnaryPlugSlotCaller >( "UnaryPlugSignal" );
	SignalClass<Node::BinaryPlugSignal, DefaultSignalCaller<Node::BinaryPlugSignal>, BinaryPlugSlotCaller >( "BinaryPlugSignal" );
	SignalClass<Node::ErrorSignal, DefaultSignalCaller<Node::ErrorSignal>, ErrorSlotCaller >( "ErrorSignal" );

	Serialisation::registerSerialiser( Node::staticTypeId(), new NodeSerialiser() );

}
