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

#include "IECorePython/ScopedGILRelease.h"

#include "Gaffer/Context.h"
#include "Gaffer/Dispatcher.h"
#include "Gaffer/CompoundPlug.h"

#include "GafferBindings/DispatcherBinding.h"
#include "GafferBindings/NodeBinding.h"
#include "GafferBindings/SignalBinding.h"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

namespace
{

class DispatcherWrapper : public NodeWrapper<Dispatcher>
{
	public :

		DispatcherWrapper( PyObject *self, const std::string &name )
			: NodeWrapper<Dispatcher>( self, name )
		{
		}

		virtual ~DispatcherWrapper()
		{
		}

		void dispatch( list nodeList ) const
		{
			ScopedGILLock gilLock;
			size_t len = boost::python::len( nodeList );
			std::vector<NodePtr> nodes;
			nodes.reserve( len );
			for ( size_t i = 0; i < len; i++ )
			{
				nodes.push_back( extract<NodePtr>( nodeList[i] ) );
			}
			Dispatcher::dispatch( nodes );
		}

		void doDispatch( const TaskBatch *batch ) const
		{
			ScopedGILLock gilLock;

			boost::python::object f = this->methodOverride( "_doDispatch" );
			if( f )
			{
				f( boost::const_pointer_cast<Dispatcher::TaskBatch>( ConstTaskBatchPtr( batch ) ) );
			}
			else
			{
				throw Exception( "doDispatch() python method not defined" );
			}
		}

		void doSetupPlugs( CompoundPlug *parentPlug ) const
		{
			ScopedGILLock gilLock;
			boost::python::object f = this->methodOverride( "_doSetupPlugs" );
			if( f )
			{
				CompoundPlugPtr tmpPointer = parentPlug;
				f( tmpPointer );
			}
		}

		static list dispatcherNames()
		{
			std::vector<std::string> names;
			Dispatcher::dispatcherNames( names );
			list result;
			for ( std::vector<std::string>::const_iterator nIt = names.begin(); nIt != names.end(); nIt++ )
			{
				result.append( *nIt );
			}
			return result;
		}

		static void registerDispatcher( std::string name, Dispatcher *dispatcher )
		{
			Dispatcher::registerDispatcher( name, dispatcher );
		}

		static DispatcherPtr dispatcher( std::string name )
		{
			const Dispatcher *d = Dispatcher::dispatcher( name );
			return const_cast< Dispatcher *>(d);
		}

		static void taskBatchExecute( const Dispatcher::TaskBatch &batch )
		{
			ScopedGILRelease gilRelease;
			batch.execute();
		}

		static ExecutableNodePtr taskBatchGetNode( const Dispatcher::TaskBatchPtr &batch )
		{
			if ( ConstExecutableNodePtr node = batch->node() )
			{
				return boost::const_pointer_cast<ExecutableNode>( node );
			}

			return 0;
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

			return 0;
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

		static boost::python::list taskBatchGetRequirements( const Dispatcher::TaskBatchPtr &batch )
		{
			boost::python::list result;
			for ( std::vector<TaskBatchPtr>::const_iterator it = batch->requirements().begin(); it != batch->requirements().end(); ++it )
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

struct PreDispatchSlotCaller
{
	bool operator()( boost::python::object slot, const Dispatcher *d, const std::vector<ExecutableNodePtr> &nodes )
	{
		try
		{
			list nodeList;
			for( std::vector<ExecutableNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); nIt++ )
			{
				nodeList.append( *nIt );
			}
			DispatcherPtr dd = const_cast<Dispatcher*>(d);
			return slot( dd, nodeList );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return false;
	}
};

struct PostDispatchSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, const Dispatcher *d, const std::vector<ExecutableNodePtr> &nodes, bool success )
	{
		try
		{
			list nodeList;
			for( std::vector<ExecutableNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); nIt++ )
			{
				nodeList.append( *nIt );
			}
			DispatcherPtr dd = const_cast<Dispatcher*>(d);
			slot( dd, nodeList, success );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

} // namespace

void GafferBindings::bindDispatcher()
{
	scope s = NodeClass<Dispatcher, DispatcherWrapper>()
		.def( "dispatch", &DispatcherWrapper::dispatch )
		.def( "jobDirectory", &Dispatcher::jobDirectory )
		.def( "dispatcher", &DispatcherWrapper::dispatcher ).staticmethod( "dispatcher" )
		.def( "dispatcherNames", &DispatcherWrapper::dispatcherNames ).staticmethod( "dispatcherNames" )
		.def( "registerDispatcher", &DispatcherWrapper::registerDispatcher ).staticmethod( "registerDispatcher" )
		.def( "preDispatchSignal", &Dispatcher::preDispatchSignal, return_value_policy<reference_existing_object>() ).staticmethod( "preDispatchSignal" )
		.def( "postDispatchSignal", &Dispatcher::postDispatchSignal, return_value_policy<reference_existing_object>() ).staticmethod( "postDispatchSignal" )
	;

	enum_<Dispatcher::FramesMode>( "FramesMode" )
		.value( "CurrentFrame", Dispatcher::CurrentFrame )
		.value( "FullRange", Dispatcher::FullRange )
		.value( "CustomRange", Dispatcher::CustomRange )
	;

	RefCountedClass<Dispatcher::TaskBatch, RefCounted>( "_TaskBatch" )
		.def( "execute", &DispatcherWrapper::taskBatchExecute )
		.def( "node", &DispatcherWrapper::taskBatchGetNode )
		.def( "context", &DispatcherWrapper::taskBatchGetContext, ( boost::python::arg_( "_copy" ) = true ) )
		.def( "frames", &DispatcherWrapper::taskBatchGetFrames )
		.def( "requirements", &DispatcherWrapper::taskBatchGetRequirements )
		.def( "blindData", &DispatcherWrapper::taskBatchGetBlindData )
	;

	SignalBinder<Dispatcher::PreDispatchSignal, DefaultSignalCaller<Dispatcher::PreDispatchSignal>, PreDispatchSlotCaller >::bind( "PreDispatchSignal" );
	SignalBinder<Dispatcher::PostDispatchSignal, DefaultSignalCaller<Dispatcher::PostDispatchSignal>, PostDispatchSlotCaller >::bind( "PostDispatchSignal" );
}
