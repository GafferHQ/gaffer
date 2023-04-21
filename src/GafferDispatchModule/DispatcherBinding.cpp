//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "DispatcherBinding.h"

#include "GafferDispatch/Dispatcher.h"

#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/SignalBinding.h"

#include "Gaffer/Context.h"
#include "Gaffer/ScriptNode.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILRelease.h"

#include "boost/python/suite/indexing/container_utils.hpp"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;
using namespace GafferDispatch;

namespace
{

class DispatcherWrapper : public NodeWrapper<Dispatcher>
{
	public :

		DispatcherWrapper( PyObject *self, const std::string &name )
			: NodeWrapper<Dispatcher>( self, name )
		{
		}

		~DispatcherWrapper() override
		{
		}

		void doDispatch( const TaskBatch *batch ) const override
		{
			ScopedGILLock gilLock;

			boost::python::object f = this->methodOverride( "_doDispatch" );
			if( f )
			{
				try
				{
					f( boost::const_pointer_cast<Dispatcher::TaskBatch>( ConstTaskBatchPtr( batch ) ) );
				}
				catch( const boost::python::error_already_set & )
				{
					ExceptionAlgo::translatePythonException();
				}
			}
			else
			{
				throw Exception( "doDispatch() python method not defined" );
			}
		}

		FrameListPtr frameRange( const ScriptNode *script, const Context *context ) const override
		{
			ScopedGILLock gilLock;

			boost::python::object f = this->methodOverride( "frameRange" );
			if( f )
			{
				try
				{
					object obj = f(
						ScriptNodePtr( const_cast<ScriptNode *>( script ) ),
						ContextPtr( const_cast<Context *>( context ) )
					);

					return extract<FrameListPtr>( obj );
				}
				catch( const boost::python::error_already_set & )
				{
					ExceptionAlgo::translatePythonException();
				}
			}

			return Dispatcher::frameRange( script, context );
		}

		//////////////////////////////////////////////////////////////////////////
		// TashBatch method wrappers. These are defined here rather than as free
		// functions because TaskBatch is a protected member of Dispatcher.
		//////////////////////////////////////////////////////////////////////////

		using TaskBatch = Dispatcher::TaskBatch;

		static void taskBatchExecute( const Dispatcher::TaskBatch &batch )
		{
			ScopedGILRelease gilRelease;
			batch.execute();
		}

		static TaskNodePtr taskBatchGetNode( const Dispatcher::TaskBatchPtr &batch )
		{
			if ( ConstTaskNodePtr node = batch->node() )
			{
				return boost::const_pointer_cast<TaskNode>( node );
			}
			return nullptr;
		}

		static TaskNode::TaskPlugPtr taskBatchPlug( const Dispatcher::TaskBatchPtr &batch )
		{
			if( const TaskNode::TaskPlug *p = batch->plug() )
			{
				return const_cast<TaskNode::TaskPlug *>( p );
			}
			return nullptr;
		}

		static ContextPtr taskBatchGetContext( const Dispatcher::TaskBatchPtr &batch, bool copy = true )
		{
			if ( ConstContextPtr context = batch->context() )
			{
				if ( copy )
				{
					return new Context( *context );
				}

				return boost::const_pointer_cast<Context>( context );
			}

			return nullptr;
		}

		static boost::python::list taskBatchGetFrames( const Dispatcher::TaskBatchPtr &batch )
		{
			boost::python::list result;
			for ( std::vector<float>::const_iterator it = batch->frames().begin(); it != batch->frames().end(); ++it )
			{
				result.append( *it );
			}
			return result;
		}

		static boost::python::list taskBatchGetPreTasks( const Dispatcher::TaskBatchPtr &batch )
		{
			boost::python::list result;
			for( std::vector<TaskBatchPtr>::const_iterator it = batch->preTasks().begin(); it != batch->preTasks().end(); ++it )
			{
				result.append( *it );
			}
			return result;
		}

		static CompoundDataPtr taskBatchGetBlindData( Dispatcher::TaskBatch &batch )
		{
			return batch.blindData();
		}

};

struct DispatcherHelper
{
	DispatcherHelper( object fn, object setupPlugsFn )
		:	m_fn( fn ), m_setupFn( setupPlugsFn )
	{
	}

	DispatcherPtr operator()()
	{
		IECorePython::ScopedGILLock gilLock;

		try
		{
			DispatcherPtr result = extract<DispatcherPtr>( m_fn() );
			return result;
		}
		catch( const boost::python::error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}

		return nullptr;
	}

	void operator()( Plug *parentPlug )
	{
		IECorePython::ScopedGILLock gilLock;
		if ( m_setupFn )
		{
			try
			{
				m_setupFn( PlugPtr( parentPlug ) );
			}
			catch( const boost::python::error_already_set & )
			{
				ExceptionAlgo::translatePythonException();
			}
		}
	}

	private :

		object m_fn;
		object m_setupFn;

};

void dispatch( Dispatcher &dispatcher, object pythonNodes )
{
	std::vector<NodePtr> nodes;
	boost::python::container_utils::extend_container( nodes, pythonNodes );
	IECorePython::ScopedGILRelease gilRelease;
	dispatcher.dispatch( nodes );
}

IECore::FrameListPtr frameRange( Dispatcher &n, const ScriptNode &script, const Context &context )
{
	return n.Dispatcher::frameRange( &script, &context );
}

void registerDispatcher( std::string type, object creator, object setupPlugsFn )
{
	DispatcherHelper helper( creator, setupPlugsFn );
	Dispatcher::registerDispatcher( type, helper, helper );
}

tuple registeredDispatchersWrapper()
{
	std::vector<std::string> types;
	Dispatcher::registeredDispatchers( types );
	list result;
	for ( std::vector<std::string>::const_iterator it = types.begin(); it != types.end(); ++it )
	{
		result.append( *it );
	}
	return boost::python::tuple( result );
}

list createMatching( std::string pattern )
{
	std::vector<DispatcherPtr> dispatchers = Dispatcher::createMatching( pattern );
	list result;
	for( auto &d : dispatchers )
	{
		result.append( d );
	}
	return result;
}

struct PreDispatchSlotCaller
{
	bool operator()( boost::python::object slot, const Dispatcher *d, const std::vector<TaskNodePtr> &nodes )
	{
		try
		{
			list nodeList;
			for( std::vector<TaskNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); nIt++ )
			{
				nodeList.append( *nIt );
			}
			DispatcherPtr dd = const_cast<Dispatcher*>(d);
			return slot( dd, nodeList );
		}
		catch( const boost::python::error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
		return false;
	}
};

struct DispatchSlotCaller
{
	void operator()( boost::python::object slot, const Dispatcher *d, const std::vector<TaskNodePtr> &nodes )
	{
		try
		{
			list nodeList;
			for( std::vector<TaskNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); nIt++ )
			{
				nodeList.append( *nIt );
			}
			DispatcherPtr dd = const_cast<Dispatcher*>(d);
			slot( dd, nodeList );
		}
		catch( const boost::python::error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

struct PostDispatchSlotCaller
{
	void operator()( boost::python::object slot, const Dispatcher *d, const std::vector<TaskNodePtr> &nodes, bool success )
	{
		try
		{
			list nodeList;
			for( std::vector<TaskNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); nIt++ )
			{
				nodeList.append( *nIt );
			}
			DispatcherPtr dd = const_cast<Dispatcher*>(d);
			slot( dd, nodeList, success );
		}
		catch( const boost::python::error_already_set & )
		{
			ExceptionAlgo::translatePythonException();
		}
	}
};

} // namespace

void GafferDispatchModule::bindDispatcher()
{
	scope s = NodeClass<Dispatcher, DispatcherWrapper>()
		.def( "dispatch", &dispatch )
		.def( "jobDirectory", &Dispatcher::jobDirectory )
		.def( "frameRange", &frameRange )
		.def( "create", &Dispatcher::create ).staticmethod( "create" )
		.def( "createMatching", &createMatching, ( arg( "matchPattern" ) ) ).staticmethod( "createMatching" )
		.def( "getDefaultDispatcherType", &Dispatcher::getDefaultDispatcherType, return_value_policy<copy_const_reference>() ).staticmethod( "getDefaultDispatcherType" )
		.def( "setDefaultDispatcherType", &Dispatcher::setDefaultDispatcherType ).staticmethod( "setDefaultDispatcherType" )
		.def( "registerDispatcher", &registerDispatcher, ( arg( "dispatcherType" ), arg( "creator" ), arg( "setupPlugsFn" ) = 0 ) ).staticmethod( "registerDispatcher" )
		.def( "registeredDispatchers", &registeredDispatchersWrapper ).staticmethod( "registeredDispatchers" )
		.def( "deregisterDispatcher", &Dispatcher::deregisterDispatcher, ( arg( "dispatcherType" ) ) ).staticmethod( "deregisterDispatcher" )
		.def( "preDispatchSignal", &Dispatcher::preDispatchSignal, return_value_policy<reference_existing_object>() ).staticmethod( "preDispatchSignal" )
		.def( "dispatchSignal", &Dispatcher::dispatchSignal, return_value_policy<reference_existing_object>() ).staticmethod( "dispatchSignal" )
		.def( "postDispatchSignal", &Dispatcher::postDispatchSignal, return_value_policy<reference_existing_object>() ).staticmethod( "postDispatchSignal" )
	;

	enum_<Dispatcher::FramesMode>( "FramesMode" )
		.value( "CurrentFrame", Dispatcher::CurrentFrame )
		.value( "FullRange", Dispatcher::FullRange )
		.value( "CustomRange", Dispatcher::CustomRange )
	;

	RefCountedClass<DispatcherWrapper::TaskBatch, RefCounted>( "_TaskBatch" )
		.def( "execute", &DispatcherWrapper::taskBatchExecute )
		.def( "node", &DispatcherWrapper::taskBatchGetNode )
		.def( "plug", &DispatcherWrapper::taskBatchPlug )
		.def( "context", &DispatcherWrapper::taskBatchGetContext, ( boost::python::arg_( "_copy" ) = true ) )
		.def( "frames", &DispatcherWrapper::taskBatchGetFrames )
		.def( "preTasks", &DispatcherWrapper::taskBatchGetPreTasks )
		.def( "blindData", &DispatcherWrapper::taskBatchGetBlindData )
	;

	SignalClass<Dispatcher::PreDispatchSignal, DefaultSignalCaller<Dispatcher::PreDispatchSignal>, PreDispatchSlotCaller >( "PreDispatchSignal" );
	SignalClass<Dispatcher::DispatchSignal, DefaultSignalCaller<Dispatcher::DispatchSignal>, DispatchSlotCaller >( "DispatchSignal" );
	SignalClass<Dispatcher::PostDispatchSignal, DefaultSignalCaller<Dispatcher::PostDispatchSignal>, PostDispatchSlotCaller >( "PostDispatchSignal" );
}
