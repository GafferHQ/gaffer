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

#include "Gaffer/ScriptNode.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/ValuePlugBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/RawConstructor.h"
#include "GafferBindings/CatchingSlotCaller.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace Gaffer;

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

bool NodeSerialiser::childNeedsSerialisation( const Gaffer::GraphComponent *child ) const
{
	if( const Plug *childPlug = IECore::runTimeCast<const Plug>( child ) )
	{
		return childPlug->getFlags( Plug::Serialisable );
	}
	return false;
}

bool NodeSerialiser::childNeedsConstruction( const Gaffer::GraphComponent *child ) const
{
	if( const Plug *childPlug = IECore::runTimeCast<const Plug>( child ) )
	{
		return childPlug->getFlags( Plug::Dynamic );
	}
	return false;
}

void GafferBindings::bindNode()
{
	typedef NodeWrapper<Node> Wrapper;
	IE_CORE_DECLAREPTR( Wrapper );

	scope s = NodeClass<Node, WrapperPtr>()
		.def( "scriptNode", &scriptNode )
		.def( "plugSetSignal", &Node::plugSetSignal, return_internal_reference<1>() )
		.def( "plugInputChangedSignal", &Node::plugInputChangedSignal, return_internal_reference<1>() )
		.def( "plugFlagsChangedSignal", &Node::plugFlagsChangedSignal, return_internal_reference<1>() )
		.def( "plugDirtiedSignal", &Node::plugDirtiedSignal, return_internal_reference<1>() )
	;
	
	SignalBinder<Node::UnaryPlugSignal, DefaultSignalCaller<Node::UnaryPlugSignal>, UnaryPlugSlotCaller >::bind( "UnaryPlugSignal" );
	SignalBinder<Node::BinaryPlugSignal, DefaultSignalCaller<Node::BinaryPlugSignal>, BinaryPlugSlotCaller >::bind( "BinaryPlugSignal" );
	
	Serialisation::registerSerialiser( Node::staticTypeId(), new NodeSerialiser() );
	
}
