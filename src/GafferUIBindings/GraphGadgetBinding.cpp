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

#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/Node.h"

#include "GafferBindings/SignalBinding.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/ConnectionGadget.h"
#include "GafferUI/GraphLayout.h"

#include "GafferUIBindings/GraphGadgetBinding.h"
#include "GafferUIBindings/GadgetBinding.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferUI;

struct GraphGadgetSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, GraphGadgetPtr g )
	{
		slot( g );
		return boost::signals::detail::unusable();
	}
};

static Gaffer::NodePtr getRoot( GraphGadget &graphGadget )
{
	return graphGadget.getRoot();
}

static Gaffer::SetPtr getFilter( GraphGadget &graphGadget )
{
	return graphGadget.getFilter();
}

static NodeGadgetPtr nodeGadget( GraphGadget &graphGadget, const Gaffer::Node *node )
{
	return graphGadget.nodeGadget( node );
}

static ConnectionGadgetPtr connectionGadget( GraphGadget &graphGadget, const Gaffer::Plug *dstPlug )
{
	return graphGadget.connectionGadget( dstPlug );
}

static void setLayout( GraphGadget &g, GraphLayoutPtr l )
{
	return g.setLayout( l );
}

static GraphLayoutPtr getLayout( GraphGadget &g )
{
	return g.getLayout();
}

static NodeGadgetPtr nodeGadgetAt( GraphGadget &g, const IECore::LineSegment3f lineSegmentInGadgetSpace )
{
	return g.nodeGadgetAt( lineSegmentInGadgetSpace );
}

static ConnectionGadgetPtr connectionGadgetAt( GraphGadget &g, const IECore::LineSegment3f lineSegmentInGadgetSpace )
{
	return g.connectionGadgetAt( lineSegmentInGadgetSpace );
}

void GafferUIBindings::bindGraphGadget()
{
	scope s = IECorePython::RunTimeTypedClass<GraphGadget>()
		.def( init<Gaffer::NodePtr, Gaffer::SetPtr>( ( arg_( "root" ), arg_( "filter" ) = object() ) ) )
		.GAFFERUIBINDINGS_DEFGADGETWRAPPERFNS( GraphGadget )
		.def( "getRoot", &getRoot )
		.def( "setRoot", &GraphGadget::setRoot, ( arg_( "root" ), arg_( "filter" ) = object() ) )
		.def( "rootChangedSignal", &GraphGadget::rootChangedSignal, return_internal_reference<1>() )
		.def( "getFilter", &getFilter )
		.def( "setFilter", &GraphGadget::setFilter )
		.def( "nodeGadget", &nodeGadget )
		.def( "connectionGadget", &connectionGadget )
		.def( "setNodePosition", &GraphGadget::setNodePosition )
		.def( "getNodePosition", &GraphGadget::getNodePosition )
		.def( "setLayout", &setLayout )
		.def( "getLayout", &getLayout )
		.def( "nodeGadgetAt", &nodeGadgetAt )
		.def( "connectionGadgetAt", &connectionGadgetAt )
	;

	GafferBindings::SignalBinder<GraphGadget::GraphGadgetSignal, GafferBindings::DefaultSignalCaller<GraphGadget::GraphGadgetSignal>, GraphGadgetSlotCaller>::bind( "GraphGadgetSignal" );	

}
