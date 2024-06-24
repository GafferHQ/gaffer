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

#include "GraphGadgetBinding.h"

#include "GafferUIBindings/GadgetBinding.h"

#include "GafferUI/AnnotationsGadget.h"
#include "GafferUI/AuxiliaryConnectionsGadget.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphGadget.h"
#include "GafferUI/GraphLayout.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/StandardGraphLayout.h"
#include "GafferUI/ContextTracker.h"

#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"
#include "Gaffer/Node.h"
#include "Gaffer/ScriptNode.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferUI;
using namespace GafferUIBindings;

namespace
{

void setRoot( GraphGadget &graphGadget, Gaffer::NodePtr root, Gaffer::SetPtr filter )
{
	ScopedGILRelease gilRelease;
	graphGadget.setRoot( root, filter );
}

void setFilter( GraphGadget &graphGadget, Gaffer::SetPtr filter )
{
	ScopedGILRelease gilRelease;
	graphGadget.setFilter( filter );
}

struct RootChangedSlotCaller
{
	void operator()( boost::python::object slot, GraphGadgetPtr g, Gaffer::NodePtr n )
	{
		slot( g , n );
	}
};

list connectionGadgets1( GraphGadget &graphGadget, const Gaffer::Plug *plug, const Gaffer::Set *excludedNodes = nullptr )
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

list connectionGadgets2( GraphGadget &graphGadget, const Gaffer::Node *node, const Gaffer::Set *excludedNodes = nullptr )
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

void setNodePosition( GraphGadget &graphGadget, Gaffer::Node &node, const Imath::V2f &position )
{
	IECorePython::ScopedGILRelease gilRelease;
	graphGadget.setNodePosition( &node, position );
}

void setNodeInputConnectionsMinimised( GraphGadget &graphGadget, Gaffer::Node &node, bool minimised )
{
	IECorePython::ScopedGILRelease gilRelease;
	graphGadget.setNodeInputConnectionsMinimised( &node, minimised );
}

void setNodeOutputConnectionsMinimised( GraphGadget &graphGadget, Gaffer::Node &node, bool minimised )
{
	IECorePython::ScopedGILRelease gilRelease;
	graphGadget.setNodeOutputConnectionsMinimised( &node, minimised );
}

tuple connectionAt( AuxiliaryConnectionsGadget &g, IECore::LineSegment3f position )
{
	auto nodeGadgets = g.connectionAt( position );
	return make_tuple( nodeGadgets.first, nodeGadgets.second );
}

const std::string &annotationTextWrapper( const AnnotationsGadget &gadget, const Gaffer::Node &node, IECore::InternedString annotation )
{
	IECorePython::ScopedGILRelease gilRelease;
	return gadget.annotationText( &node, annotation );
}

bool connectNode( const GraphLayout &layout, GraphGadget &graph, Gaffer::Node &node, Gaffer::Set &potentialInputs )
{
	IECorePython::ScopedGILRelease gilRelease;
	return layout.connectNode( &graph, &node, &potentialInputs );
}

bool connectNodes( const GraphLayout &layout, GraphGadget &graph, Gaffer::Set &nodes, Gaffer::Set &potentialInputs )
{
	IECorePython::ScopedGILRelease gilRelease;
	return layout.connectNodes( &graph, &nodes, &potentialInputs );
}

void positionNode( const GraphLayout &layout, GraphGadget &graph, Gaffer::Node &node, const Imath::V2f &fallbackPosition )
{
	IECorePython::ScopedGILRelease gilRelease;
	layout.positionNode( &graph, &node, fallbackPosition );
}

void positionNodes( const GraphLayout &layout, GraphGadget &graph, Gaffer::Set &nodes, const Imath::V2f &fallbackPosition )
{
	IECorePython::ScopedGILRelease gilRelease;
	layout.positionNodes( &graph, &nodes, fallbackPosition );
}

void layoutNodes( const GraphLayout &layout, GraphGadget &graph, Gaffer::Set *nodes )
{
	IECorePython::ScopedGILRelease gilRelease;
	layout.layoutNodes( &graph, nodes );
}

NodePtr targetNodeWrapper( const ContextTracker &contextTracker )
{
	return const_cast<Node *>( contextTracker.targetNode() );
}

ContextPtr targetContextWrapper( const ContextTracker &contextTracker )
{
	return const_cast<Context *>( contextTracker.targetContext() );
}

struct ContextTrackerSlotCaller
{
	void operator()( boost::python::object slot, ContextTracker &contextTracker )
	{
		try
		{
			slot( ContextTrackerPtr( &contextTracker ) );
		}
		catch( const boost::python::error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

ContextPtr contextWrapper1( const ContextTracker &contextTracker, const Node &node, bool copy = false )
{
	ConstContextPtr c = contextTracker.context( &node );
	return copy ? new Context( *c ) : boost::const_pointer_cast<Context>( c );
}

ContextPtr contextWrapper2( const ContextTracker &contextTracker, const Plug &plug, bool copy = false )
{
	ConstContextPtr c = contextTracker.context( &plug );
	return copy ? new Context( *c ) : boost::const_pointer_cast<Context>( c );
}

} // namespace

void GafferUIModule::bindGraphGadget()
{
	{
		scope s = GadgetClass<GraphGadget>()
			.def( init<Gaffer::NodePtr, Gaffer::SetPtr>( ( arg_( "root" ), arg_( "filter" ) = object() ) ) )
			.def( "getRoot", (Gaffer::Node *(GraphGadget::*)())&GraphGadget::getRoot, return_value_policy<CastToIntrusivePtr>() )
			.def( "setRoot", &setRoot, ( arg_( "root" ), arg_( "filter" ) = object() ) )
			.def( "rootChangedSignal", &GraphGadget::rootChangedSignal, return_internal_reference<1>() )
			.def( "getFilter", (Gaffer::Set *(GraphGadget::*)())&GraphGadget::getFilter, return_value_policy<CastToIntrusivePtr>() )
			.def( "setFilter", &setFilter )
			.def( "nodeGadget", (NodeGadget *(GraphGadget::*)( const Gaffer::Node * ))&GraphGadget::nodeGadget, return_value_policy<CastToIntrusivePtr>() )
			.def( "connectionGadget", (ConnectionGadget *(GraphGadget::*)( const Gaffer::Plug * ))&GraphGadget::connectionGadget, return_value_policy<CastToIntrusivePtr>() )
			.def( "connectionGadgets", &connectionGadgets1, ( arg_( "plug" ), arg_( "excludedNodes" ) = object() ) )
			.def( "connectionGadgets", &connectionGadgets2, ( arg_( "node" ), arg_( "excludedNodes" ) = object() ) )
			.def( "auxiliaryConnectionsGadget", (AuxiliaryConnectionsGadget *(GraphGadget::*)())&GraphGadget::auxiliaryConnectionsGadget, return_value_policy<CastToIntrusivePtr>() )
			.def( "upstreamNodeGadgets", &upstreamNodeGadgets, ( arg( "node" ), arg( "degreesOfSeparation" ) = std::numeric_limits<size_t>::max() ) )
			.def( "downstreamNodeGadgets", &downstreamNodeGadgets, ( arg( "node" ), arg( "degreesOfSeparation" ) = std::numeric_limits<size_t>::max() ) )
			.def( "connectedNodeGadgets", &connectedNodeGadgets, ( arg( "node" ), arg( "direction" ) = Gaffer::Plug::Invalid, arg( "degreesOfSeparation" ) = std::numeric_limits<size_t>::max() ) )
			.def( "unpositionedNodeGadgets", &unpositionedNodeGadgets )
			.def( "setNodePosition", &setNodePosition )
			.def( "getNodePosition", &GraphGadget::getNodePosition )
			.def( "hasNodePosition", &GraphGadget::hasNodePosition )
			.def( "setNodeInputConnectionsMinimised", &setNodeInputConnectionsMinimised )
			.def( "getNodeInputConnectionsMinimised", &GraphGadget::getNodeInputConnectionsMinimised )
			.def( "setNodeOutputConnectionsMinimised", &setNodeOutputConnectionsMinimised )
			.def( "getNodeOutputConnectionsMinimised", &GraphGadget::getNodeOutputConnectionsMinimised )
			.def( "setLayout", &GraphGadget::setLayout )
			.def( "getLayout", (GraphLayout *(GraphGadget::*)())&GraphGadget::getLayout, return_value_policy<CastToIntrusivePtr>() )
			.def( "nodeGadgetAt", &GraphGadget::nodeGadgetAt, return_value_policy<CastToIntrusivePtr>() )
			.def( "connectionGadgetAt", &GraphGadget::connectionGadgetAt, return_value_policy<CastToIntrusivePtr>() )
		;

		GafferBindings::SignalClass<GraphGadget::RootChangedSignal, GafferBindings::DefaultSignalCaller<GraphGadget::RootChangedSignal>, RootChangedSlotCaller>( "RootChangedSignal" );
	}

	GadgetClass<AuxiliaryConnectionsGadget>()
		.def( "hasConnection", (bool (AuxiliaryConnectionsGadget::*)( const Gadget *, const Gadget * ) const)&AuxiliaryConnectionsGadget::hasConnection )
		.def( "hasConnection", (bool (AuxiliaryConnectionsGadget::*)( const Node *, const Node * ) const)&AuxiliaryConnectionsGadget::hasConnection )
		.def( "connectionAt", &connectionAt )
	;

	GadgetClass<AnnotationsGadget>()
		.def_readonly( "untemplatedAnnotations", &AnnotationsGadget::untemplatedAnnotations )
		.def( "setVisibleAnnotations", &AnnotationsGadget::setVisibleAnnotations )
		.def( "getVisibleAnnotations", &AnnotationsGadget::getVisibleAnnotations, return_value_policy<copy_const_reference>() )
		.def( "annotationText", &annotationTextWrapper, return_value_policy<copy_const_reference>(), ( arg( "node" ), arg( "annotation" ) = "user" ) )
	;

	IECorePython::RunTimeTypedClass<GraphLayout>()
		.def( "connectNode", &connectNode )
		.def( "connectNodes", &connectNodes )
		.def( "positionNode", &positionNode, ( arg_( "graph" ), arg_( "node" ), arg_( "fallbackPosition" ) = Imath::V2f( 0 ) ) )
		.def( "positionNodes", &positionNodes, ( arg_( "graph" ), arg_( "nodes" ), arg_( "fallbackPosition" ) = Imath::V2f( 0 ) ) )
		.def( "layoutNodes", &layoutNodes, ( arg_( "graph" ), arg_( "nodes" ) = object() ) )
	;

	IECorePython::RunTimeTypedClass<StandardGraphLayout>()
		.def( init<>() )
		.def( "setConnectionScale", &StandardGraphLayout::setConnectionScale )
		.def( "getConnectionScale", &StandardGraphLayout::getConnectionScale )
		.def( "setNodeSeparationScale", &StandardGraphLayout::setNodeSeparationScale )
		.def( "getNodeSeparationScale", &StandardGraphLayout::getNodeSeparationScale )
	;

	{
		scope s = IECorePython::RefCountedClass<ContextTracker, IECore::RefCounted>( "ContextTracker" )
			.def( init<const NodePtr &, const ContextPtr &>() )
			.def( "acquire", &ContextTracker::acquire ).staticmethod( "acquire" )
			.def( "acquireForFocus", &ContextTracker::acquireForFocus ).staticmethod( "acquireForFocus" )
			.def( "targetNode", &targetNodeWrapper )
			.def( "targetContext", &targetContextWrapper )
			.def( "isActive", (bool (ContextTracker::*)( const Plug *plug ) const)&ContextTracker::isActive )
			.def( "isActive", (bool (ContextTracker::*)( const Node *node ) const)&ContextTracker::isActive )
			.def( "context", &contextWrapper1, ( arg( "node" ), arg( "_copy" ) = true ) )
			.def( "context", &contextWrapper2, ( arg( "plug" ), arg( "_copy" ) = true ) )
			.def( "updatePending", &ContextTracker::updatePending )
			.def( "changedSignal", &ContextTracker::changedSignal, return_internal_reference<1>() )
		;

		SignalClass<ContextTracker::Signal, DefaultSignalCaller<ContextTracker::Signal>, ContextTrackerSlotCaller>( "Signal" );

	}

}
