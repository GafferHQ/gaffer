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

#include "NodeBinding.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/DependencyNodeBinding.h"
#include "GafferBindings/ComputeNodeBinding.h"
#include "GafferBindings/SerialisationBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/MetadataBinding.h"

#include "Gaffer/ScriptNode.h"

#include "IECorePython/ExceptionAlgo.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

struct UnaryPlugSlotCaller
{
	void operator()( boost::python::object slot, PlugPtr p )
	{
		try
		{
			slot( p );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

struct BinaryPlugSlotCaller
{

	void operator()( boost::python::object slot, PlugPtr p1, PlugPtr p2 )
	{
		try
		{
			slot( p1, p2 );
		}
		catch( const error_already_set & )
		{
			IECorePython::ExceptionAlgo::translatePythonException();
		}
	}
};

struct ErrorSlotCaller
{
	void operator()( boost::python::object slot, const Plug *plug, const Plug *source, const std::string &error )
	{
		try
		{
			slot( PlugPtr( const_cast<Plug *>( plug ) ), PlugPtr( const_cast<Plug *>( source ) ), error );
		}
		catch( const error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

} // namespace

void GafferModule::bindNode()
{
	using NodeWrapper = NodeWrapper<Node>;

	{
		scope s = NodeClass<Node, NodeWrapper>()
			.def( "scriptNode", (ScriptNode *(Node::*)())&Node::scriptNode, return_value_policy<CastToIntrusivePtr>() )
			.def( "plugSetSignal", &Node::plugSetSignal, return_internal_reference<1>() )
			.def( "plugInputChangedSignal", &Node::plugInputChangedSignal, return_internal_reference<1>() )
			.def( "plugDirtiedSignal", &Node::plugDirtiedSignal, return_internal_reference<1>() )
			.def( "errorSignal", (Node::ErrorSignal &(Node::*)())&Node::errorSignal, return_internal_reference<1>() )
		;

		SignalClass<Node::UnaryPlugSignal, DefaultSignalCaller<Node::UnaryPlugSignal>, UnaryPlugSlotCaller >( "UnaryPlugSignal" );
		SignalClass<Node::BinaryPlugSignal, DefaultSignalCaller<Node::BinaryPlugSignal>, BinaryPlugSlotCaller >( "BinaryPlugSignal" );
		SignalClass<Node::ErrorSignal, DefaultSignalCaller<Node::ErrorSignal>, ErrorSlotCaller >( "ErrorSignal" );
	}

	Serialisation::registerSerialiser( Node::staticTypeId(), new NodeSerialiser() );

	using NodeSerialiserWrapper = SerialiserWrapper<NodeSerialiser>;
	SerialiserClass<NodeSerialiser, Serialisation::Serialiser, NodeSerialiserWrapper>( "NodeSerialiser" );

	using DependencyNodeWrapper = DependencyNodeWrapper<DependencyNode>;
	DependencyNodeClass<DependencyNode, DependencyNodeWrapper>();

	using ComputeNodeWrapper = ComputeNodeWrapper<ComputeNode>;
	DependencyNodeClass<ComputeNode, ComputeNodeWrapper>();

}
