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
#include "boost/python/suite/indexing/container_utils.hpp"

#include "NodeGadgetBinding.h"

#include "GafferUIBindings/NodeGadgetBinding.h"

#include "GafferUI/NodeGadget.h"
#include "GafferUI/Nodule.h"
#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/BackdropNodeGadget.h"
#include "GafferUI/DotNodeGadget.h"
#include "GafferUI/AuxiliaryNodeGadget.h"

#include "Gaffer/Plug.h"
#include "GafferBindings/SignalBinding.h"

#include "IECorePython/ExceptionAlgo.h"

using namespace boost::python;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferUI;
using namespace GafferUIBindings;

namespace
{

struct NoduleSlotCaller
{
	void operator()( boost::python::object slot, NodeGadget *nodeGadget, Nodule *nodule )
	{
		try
		{
			slot( NodeGadgetPtr( nodeGadget ), NodulePtr( nodule ) );
		}
		catch( const error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

struct InstanceCreatedSlotCaller
{
	void operator()( boost::python::object slot, NodeGadget *nodeGadget )
	{
		try
		{
			slot( NodeGadgetPtr( nodeGadget ) );
		}
		catch( const error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

NodeGadgetPtr nodeGadgetCreateWrapper( Gaffer::Node &node )
{
	IECorePython::ScopedGILRelease gilRelease;
	return NodeGadget::create( &node );
}

struct NodeGadgetCreator
{
	NodeGadgetCreator( object fn )
		:	m_fn( fn )
	{
	}

	NodeGadgetPtr operator()( Gaffer::NodePtr node )
	{
		IECorePython::ScopedGILLock gilLock;
		NodeGadgetPtr result = extract<NodeGadgetPtr>( m_fn( node ) );
		return result;
	}

	private :

		object m_fn;

};

void registerNodeGadget1( IECore::TypeId nodeType, object creator )
{
	NodeGadget::registerNodeGadget( nodeType, NodeGadgetCreator( creator ) );
}

void registerNodeGadget2( const std::string &nodeGadgetType, object creator, IECore::TypeId nodeType )
{
	NodeGadget::registerNodeGadget( nodeGadgetType, NodeGadgetCreator( creator ), nodeType );
}

class StandardNodeGadgetWrapper : public NodeGadgetWrapper<StandardNodeGadget>
{

	public :

		StandardNodeGadgetWrapper( PyObject *self, Gaffer::NodePtr node )
			:	NodeGadgetWrapper<StandardNodeGadget>( self, node )
		{
		}

};

GadgetPtr getContents( StandardNodeGadget &g )
{
	return g.getContents();
}

GadgetPtr getEdgeGadget( StandardNodeGadget &g, StandardNodeGadget::Edge edge )
{
	return g.getEdgeGadget( edge );
}

void setBound( BackdropNodeGadget &g, const Imath::Box2f &b )
{
	IECorePython::ScopedGILRelease gilRelease;
	g.setBound( b );
}

Imath::Box2f getBound( BackdropNodeGadget &g )
{
	IECorePython::ScopedGILRelease gilRelease;
	return g.getBound();
}

void frame( BackdropNodeGadget &b, object nodes )
{
	std::vector<Node *> n;
	boost::python::container_utils::extend_container( n, nodes );

	IECorePython::ScopedGILRelease gilRelease;
	b.frame( n );
}

list framed( BackdropNodeGadget &b )
{
	std::vector<Node *> n;
	b.framed( n );

	list result;
	for( std::vector<Node *>::const_iterator it = n.begin(), eIt = n.end(); it != eIt; ++it )
	{
		result.append( NodePtr( *it ) );
	}

	return result;
}

// This is the `__call__` operator for the metaclass we use for NodeGadgets.
// It is responsible for creating and initialising NodeGadget instances in
// Python, which allows us to emit `instanceCreatedSignal()` only when the Python
// `__init__` call has completed fully.
PyObject *nodeGadgetMetaclassCall( PyObject *self, PyObject *args, PyObject *kw )
{
	// Delegate the actual work to the default `type.__call__` method.
	// This will call `__new__` and `__init__` and return a new NodeGadget
	// instance.
	PyObject *result = PyType_Type.tp_call( self, args, kw );
	if( result )
	{
		// Emit the `instanceCreatedSignal()`, now that the Python instance
		// has fully constructed.
		auto n = boost::python::extract<GafferUI::NodeGadget *>( result )();
		GafferUI::NodeGadget::instanceCreatedSignal()( n );
	}
	return result;
}

} // namespace

/// \todo We're doing something similar for the DependencyNode binding. Consider
/// consolidating everything into the binding for RefCounted, perhaps by calling
/// a new `RefCounted::postConstructor()` virtual method.
PyTypeObject *GafferUIBindings::Detail::nodeGadgetMetaclass()
{
	static PyTypeObject g_nodeGadgetMetaclass;
	if( !g_nodeGadgetMetaclass.tp_name )
	{
		// Initialise. We derive from the standard Boost Python metaclass
		// because it has functionality critical to making the Boost bindings
		// work. The only thing we're doing is adding `nodeGadgetMetaclassCall`
		// as the implementation of the `__call__` method.
		Py_SET_TYPE( &g_nodeGadgetMetaclass, &PyType_Type );
		g_nodeGadgetMetaclass.tp_name = "GafferUI.NodeGadgetMetaclass";
		g_nodeGadgetMetaclass.tp_basicsize = PyType_Type.tp_basicsize,
		g_nodeGadgetMetaclass.tp_base = boost::python::objects::class_metatype().get();
		g_nodeGadgetMetaclass.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE;
		g_nodeGadgetMetaclass.tp_call = nodeGadgetMetaclassCall;
		PyType_Ready( &g_nodeGadgetMetaclass );
	}

	return &g_nodeGadgetMetaclass;
}

void GafferUIModule::bindNodeGadget()
{
	using Wrapper = NodeGadgetWrapper<NodeGadget>;

	NodeGadgetClass<NodeGadget, Wrapper>()
		.def( "node", (Gaffer::Node *(NodeGadget::*)())&NodeGadget::node, return_value_policy<CastToIntrusivePtr>() )
		.def( "noduleAddedSignal", &NodeGadget::noduleAddedSignal, return_internal_reference<1>() )
		.def( "noduleRemovedSignal", &NodeGadget::noduleRemovedSignal, return_internal_reference<1>() )
		.def( "create", &nodeGadgetCreateWrapper ).staticmethod( "create" )
		.def( "instanceCreatedSignal", &NodeGadget::instanceCreatedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "instanceCreatedSignal" )
		.def( "registerNodeGadget", &registerNodeGadget1 )
		.def( "registerNodeGadget", &registerNodeGadget2,
			(
				arg( "nodeGadgetType" ),
				arg( "creator" ),
				arg( "nodeType" ) = IECore::InvalidTypeId
			)
		)
		.staticmethod( "registerNodeGadget" )
	;

	SignalClass<NodeGadget::NoduleSignal, DefaultSignalCaller<NodeGadget::NoduleSignal>, NoduleSlotCaller >( "NoduleSignal" );
	SignalClass<NodeGadget::InstanceCreatedSignal, DefaultSignalCaller<NodeGadget::InstanceCreatedSignal>, InstanceCreatedSlotCaller>( "InstanceCreatedSignal" );

	{
		scope s = NodeGadgetClass<StandardNodeGadget, StandardNodeGadgetWrapper>()
			.def( init<Gaffer::NodePtr>( arg( "node" ) ) )
			.def( "setContents", &StandardNodeGadget::setContents )
			.def( "getContents", &getContents )
			.def( "setEdgeGadget", &StandardNodeGadget::setEdgeGadget )
			.def( "getEdgeGadget", &getEdgeGadget )
		;

		enum_<StandardNodeGadget::Edge>( "Edge" )
			.value( "TopEdge", StandardNodeGadget::TopEdge )
			.value( "BottomEdge", StandardNodeGadget::BottomEdge )
			.value( "LeftEdge", StandardNodeGadget::LeftEdge )
			.value( "RightEdge", StandardNodeGadget::RightEdge )
		;
	}

	NodeGadgetClass<BackdropNodeGadget>()
		.def( init<Gaffer::NodePtr>() )
		.def( "setBound", &setBound )
		.def( "getBound", &getBound )
		.def( "frame", &frame )
		.def( "framed", &framed )
	;

	NodeGadgetClass<DotNodeGadget>()
		.def( init<Gaffer::NodePtr>() )
	;

	NodeGadgetClass<AuxiliaryNodeGadget>()
		.def( init<Gaffer::NodePtr>() )
	;

}
