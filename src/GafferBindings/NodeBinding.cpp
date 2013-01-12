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
#include "boost/python/raw_function.hpp"

#include "boost/format.hpp"

#include "IECorePython/Wrapper.h"
#include "IECorePython/RunTimeTypedBinding.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/RawConstructor.h"
#include "GafferBindings/CatchingSlotCaller.h"
#include "GafferBindings/Serialiser.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/CompoundPlug.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

static std::string serialisePlug( Serialiser &s, ConstGraphComponentPtr ancestor, PlugPtr plug )
{
	// not dynamic, we can just serialise the connection/value				
	if( plug->isInstanceOf( CompoundPlug::staticTypeId() ) && !plug->getInput<Plug>() )
	{
		std::string result;
		CompoundPlug *cPlug = static_cast<CompoundPlug *>( plug.get() );
		InputPlugIterator pIt( cPlug->children().begin(), cPlug->children().end() );
		while( pIt!=cPlug->children().end() )
		{
			if( (*pIt)->getFlags( Plug::Serialisable ) )
			{
				result += serialisePlug( s, ancestor, *pIt );
			}
			pIt++;
		}
		return result;
	}

	std::string value = serialisePlugValue( s, plug );
	if( value!="" )
	{
		return "\"" + plug->relativeName( ancestor ) + "\" : " + value + ", ";		
	}

	return "";
}

static std::string serialiseNode( Serialiser &s, ConstGraphComponentPtr g )
{
	ConstNodePtr node = IECore::staticPointerCast<const Node>( g );
	
	std::string result = boost::str( boost::format( "%s.%s( \"%s\", " )
		% s.modulePath( g )
		% node->typeName()
		% node->getName()
	);

	// non dynamic input plugs
	std::string inputs = "";
	for( InputPlugIterator pIt( node ); pIt!=pIt.end(); pIt++ )
	{
		PlugPtr plug = *pIt;
		if( !plug->getFlags( Plug::Dynamic ) && plug->getFlags( Plug::Serialisable ) )
		{
			inputs += serialisePlug( s, node, *pIt );
		}
	}
	
	if( inputs.size() )
	{
		result += "inputs = { " + inputs + "}, ";
	}

	// dynamic plugs of any direction
	std::string dynamicPlugs = "";
	for( PlugIterator pIt( node ); pIt!=pIt.end(); pIt++ )
	{
		PlugPtr plug = *pIt;
		if( plug->getFlags( Plug::Dynamic ) && plug->getFlags( Plug::Serialisable ) )
		{
			dynamicPlugs += s.serialiseC( plug ) + ", ";
		}	
	}

	if( dynamicPlugs.size() )
	{
		result += "dynamicPlugs = ( " + dynamicPlugs + "), ";
	}
	
	result += ")";
	return result;
}

static void setPlugs( Node *node, const boost::python::dict &inputs )
{
	list items = inputs.items();
	long l = len( items );
	for( long i=0; i<l; i++ )
	{
		std::string name = extract<std::string>( items[i][0] );

		PlugPtr plug = node->getChild<Plug>( name );
		if( !plug )
		{
			std::string err = boost::str( boost::format( "No plug named \"%s\"." ) % name );
			throw std::invalid_argument( err.c_str() );	
		}
		else
		{
			setPlugValue( plug, items[i][1] );
		}
	}
}

static void addDynamicPlugs( Node *node, const boost::python::tuple &dynamicPlugs )
{
	long l = len( dynamicPlugs );
	for( long i=0; i<l; i++ )
	{
		PlugPtr p = extract<PlugPtr>( dynamicPlugs[i] );
		node->setChild( p->getName(), p );
	}
}

void GafferBindings::initNode( Node *node, const boost::python::dict &inputs, const boost::python::tuple &dynamicPlugs )
{
	setPlugs( node, inputs );
	addDynamicPlugs( node, dynamicPlugs );
}

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

static ScriptNodePtr scriptNode( Node &node )
{
	return node.scriptNode();
}

void GafferBindings::bindNode()
{
	typedef NodeWrapper<Node> Wrapper;
	IE_CORE_DECLAREPTR( Wrapper );

	scope s = NodeClass<Node, WrapperPtr>()
		.def( "scriptNode", &scriptNode )
		.def( "_init", &initNode )
		.def( "plugSetSignal", &Node::plugSetSignal, return_internal_reference<1>() )
		.def( "plugInputChangedSignal", &Node::plugInputChangedSignal, return_internal_reference<1>() )
		.def( "plugFlagsChangedSignal", &Node::plugFlagsChangedSignal, return_internal_reference<1>() )
	;
	
	SignalBinder<Node::UnaryPlugSignal, DefaultSignalCaller<Node::UnaryPlugSignal>, UnaryPlugSlotCaller >::bind( "UnaryPlugSignal" );
	SignalBinder<Node::BinaryPlugSignal, DefaultSignalCaller<Node::BinaryPlugSignal>, BinaryPlugSlotCaller >::bind( "BinaryPlugSignal" );
	
	Serialiser::registerSerialiser( Node::staticTypeId(), serialiseNode );
		
}
