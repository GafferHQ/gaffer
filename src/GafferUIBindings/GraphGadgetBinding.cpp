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

#include "Gaffer/Node.h"

#include "GafferBindings/SignalBinding.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphLayout.h"

#include "GafferUIBindings/GraphGadgetBinding.h"
#include "GafferUIBindings/GadgetBinding.h"

using namespace boost::python;
using namespace IECorePython;
using namespace GafferUI;
using namespace GafferUIBindings;

namespace
{

struct RootChangedSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, GraphGadgetPtr g, Gaffer::NodePtr n )
	{
		slot( g , n );
		return boost::signals::detail::unusable();
	}
};

list connectionGadgets1( GraphGadget &graphGadget, const Gaffer::Plug *plug, const Gaffer::Set *excludedNodes = 0 )
{
	std::vector<ConnectionGadget *> connections;
	graphGadget.connectionGadgets( plug, connections, excludedNodes );

	boost::python::list l;
	for( std::vector<ConnectionGadget *>::const_iterator it=connections.begin(), eIt=connections.end(); it!=eIt; ++it )
	{
		l.append( ConnectionGadgetPtr( *it ) );
	}
	return l;
}

list connectionGadgets2( GraphGadget &graphGadget, const Gaffer::Node *node, const Gaffer::Set *excludedNodes = 0 )
{
	std::vector<ConnectionGadget *> connections;
	graphGadget.connectionGadgets( node, connections, excludedNodes );

	boost::python::list l;
	for( std::vector<ConnectionGadget *>::const_iterator it=connections.begin(), eIt=connections.end(); it!=eIt; ++it )
	{
		l.append( ConnectionGadgetPtr( *it ) );
	}
	return l;
}

list upstreamNodeGadgets( GraphGadget &graphGadget, const Gaffer::Node *node, size_t degreesOfSeparation )
{
	std::vector<NodeGadget *> nodeGadgets;
	graphGadget.upstreamNodeGadgets( node, nodeGadgets, degreesOfSeparation );

	boost::python::list l;
	for( std::vector<NodeGadget *>::const_iterator it=nodeGadgets.begin(), eIt=nodeGadgets.end(); it!=eIt; ++it )
	{
		l.append( NodeGadgetPtr( *it ) );
	}
	return l;
}

list downstreamNodeGadgets( GraphGadget &graphGadget, const Gaffer::Node *node, size_t degreesOfSeparation )
{
	std::vector<NodeGadget *> nodeGadgets;
	graphGadget.downstreamNodeGadgets( node, nodeGadgets, degreesOfSeparation );

	boost::python::list l;
	for( std::vector<NodeGadget *>::const_iterator it=nodeGadgets.begin(), eIt=nodeGadgets.end(); it!=eIt; ++it )
	{
		l.append( NodeGadgetPtr( *it ) );
	}
	return l;
}

list connectedNodeGadgets( GraphGadget &graphGadget, const Gaffer::Node *node, Gaffer::Plug::Direction direction, size_t degreesOfSeparation )
{
	std::vector<NodeGadget *> nodeGadgets;
	graphGadget.connectedNodeGadgets( node, nodeGadgets, direction, degreesOfSeparation );

	boost::python::list l;
	for( std::vector<NodeGadget *>::const_iterator it=nodeGadgets.begin(), eIt=nodeGadgets.end(); it!=eIt; ++it )
	{
		l.append( NodeGadgetPtr( *it ) );
	}
	return l;
}

list unpositionedNodeGadgets( GraphGadget &graphGadget )
{
	std::vector<NodeGadget *> nodeGadgets;
	graphGadget.unpositionedNodeGadgets( nodeGadgets );

	boost::python::list l;
	for( std::vector<NodeGadget *>::const_iterator it=nodeGadgets.begin(), eIt=nodeGadgets.end(); it!=eIt; ++it )
	{
		l.append( NodeGadgetPtr( *it ) );
	}
	return l;
}

} // namespace

void GafferUIBindings::bindGraphGadget()
{
	scope s = GadgetClass<GraphGadget>()
		.def( init<Gaffer::NodePtr, Gaffer::SetPtr>( ( arg_( "root" ), arg_( "filter" ) = object() ) ) )
		.def( "getRoot", (Gaffer::Node *(GraphGadget::*)())&GraphGadget::getRoot, return_value_policy<CastToIntrusivePtr>() )
		.def( "setRoot", &GraphGadget::setRoot, ( arg_( "root" ), arg_( "filter" ) = object() ) )
		.def( "rootChangedSignal", &GraphGadget::rootChangedSignal, return_internal_reference<1>() )
		.def( "getFilter", (Gaffer::Set *(GraphGadget::*)())&GraphGadget::getFilter, return_value_policy<CastToIntrusivePtr>() )
		.def( "setFilter", &GraphGadget::setFilter )
		.def( "nodeGadget", (NodeGadget *(GraphGadget::*)( const Gaffer::Node * ))&GraphGadget::nodeGadget, return_value_policy<CastToIntrusivePtr>() )
		.def( "connectionGadget", (ConnectionGadget *(GraphGadget::*)( const Gaffer::Plug * ))&GraphGadget::connectionGadget, return_value_policy<CastToIntrusivePtr>() )
		.def( "connectionGadgets", &connectionGadgets1, ( arg_( "plug" ), arg_( "excludedNodes" ) = object() ) )
		.def( "connectionGadgets", &connectionGadgets2, ( arg_( "node" ), arg_( "excludedNodes" ) = object() ) )
		.def( "upstreamNodeGadgets", &upstreamNodeGadgets, ( arg( "node" ), arg( "degreesOfSeparation" ) = Imath::limits<size_t>::max() ) )
		.def( "downstreamNodeGadgets", &downstreamNodeGadgets, ( arg( "node" ), arg( "degreesOfSeparation" ) = Imath::limits<size_t>::max() ) )
		.def( "connectedNodeGadgets", &connectedNodeGadgets, ( arg( "node" ), arg( "direction" ) = Gaffer::Plug::Invalid, arg( "degreesOfSeparation" ) = Imath::limits<size_t>::max() ) )
		.def( "unpositionedNodeGadgets", &unpositionedNodeGadgets )
		.def( "setNodePosition", &GraphGadget::setNodePosition )
		.def( "getNodePosition", &GraphGadget::getNodePosition )
		.def( "hasNodePosition", &GraphGadget::hasNodePosition )
		.def( "setNodeInputConnectionsMinimised", &GraphGadget::setNodeInputConnectionsMinimised )
		.def( "getNodeInputConnectionsMinimised", &GraphGadget::getNodeInputConnectionsMinimised )
		.def( "setNodeOutputConnectionsMinimised", &GraphGadget::setNodeOutputConnectionsMinimised )
		.def( "getNodeOutputConnectionsMinimised", &GraphGadget::getNodeOutputConnectionsMinimised )
		.def( "setLayout", &GraphGadget::setLayout )
		.def( "getLayout", (GraphLayout *(GraphGadget::*)())&GraphGadget::getLayout, return_value_policy<CastToIntrusivePtr>() )
		.def( "nodeGadgetAt", &GraphGadget::nodeGadgetAt, return_value_policy<CastToIntrusivePtr>() )
		.def( "connectionGadgetAt", &GraphGadget::connectionGadgetAt, return_value_policy<CastToIntrusivePtr>() )
	;

	GafferBindings::SignalClass<GraphGadget::RootChangedSignal, GafferBindings::DefaultSignalCaller<GraphGadget::RootChangedSignal>, RootChangedSlotCaller>( "RootChangedSignal" );

}
