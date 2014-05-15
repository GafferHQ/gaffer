//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
#include "IECorePython/Wrapper.h"
#include "GafferBindings/DespatcherBinding.h"
#include "GafferBindings/SignalBinding.h"
#include "Gaffer/Node.h"
#include "Gaffer/Context.h"
#include "Gaffer/Despatcher.h"
#include "Gaffer/CompoundPlug.h"

using namespace boost::python;
using namespace IECore;
using namespace IECorePython;
using namespace Gaffer;
using namespace GafferBindings;

class DespatcherWrap : public Despatcher, public Wrapper<Despatcher>
{
	public :

		DespatcherWrap( PyObject *self ) : Despatcher(), Wrapper<Despatcher>( self, this )
		{
		}

		void despatch( list nodeList ) const
		{
			ScopedGILLock gilLock;
			size_t len = boost::python::len( nodeList );
			std::vector<ExecutableNodePtr> nodes;
			nodes.reserve( len );
			for ( size_t i = 0; i < len; i++ )
			{
				nodes.push_back( extract<ExecutableNodePtr>( nodeList[i] ) );
			}
			Despatcher::despatch(nodes);
		}

		void doDespatch( const std::vector<ExecutableNodePtr> &nodes ) const
		{
			ScopedGILLock gilLock;
			list nodeList;
			for ( std::vector<ExecutableNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); nIt++ )
			{
				nodeList.append( *nIt );
			}
			override d = this->get_override( "_doDespatch" );
			if( d )
			{
				d( nodeList );
			}
			else
			{
				throw Exception( "doDespatch() python method not defined" );
			}
		}

		void addPlugs( CompoundPlug *despatcherPlug ) const
		{
			ScopedGILLock gilLock;
			override b = this->get_override( "_addPlugs" );
			if( b )
			{
				CompoundPlugPtr tmpPointer = despatcherPlug;
				b( tmpPointer );
			}
		}

		static list despatcherNames()
		{
			std::vector<std::string> names;
			Despatcher::despatcherNames( names );
			list result;
			for ( std::vector<std::string>::const_iterator nIt = names.begin(); nIt != names.end(); nIt++ )
			{
				result.append( *nIt );
			}
			return result;
		}

		static list uniqueTasks( list taskList )
		{
			ExecutableNode::Tasks tasks;
			
			size_t len = boost::python::len( taskList );
			tasks.reserve( len );
			for ( size_t i = 0; i < len; i++ )
			{
				tasks.push_back( extract< ExecutableNode::Task >( taskList[i] ) );
			}

			std::vector< Despatcher::TaskDescription > uniqueTasks;
			Despatcher::uniqueTasks( tasks, uniqueTasks );
			
			list result;
			for( std::vector< TaskDescription >::const_iterator fIt = uniqueTasks.begin(); fIt != uniqueTasks.end(); fIt++ )
			{
				list requirements;
				for ( std::set<ExecutableNode::Task>::const_iterator rIt = fIt->requirements.begin(); rIt != fIt->requirements.end(); rIt++ )
				{
					requirements.append( *rIt );
				}
				result.append( make_tuple( fIt->task, requirements ) );
			}
			return result;
		}

		static void registerDespatcher( std::string name, Despatcher *despatcher )
		{
			Despatcher::registerDespatcher( name, despatcher );
		}

		static DespatcherPtr despatcher( std::string name )
		{
			const Despatcher *d = Despatcher::despatcher( name );
			return const_cast< Despatcher *>(d);
		}

		IECOREPYTHON_RUNTIMETYPEDWRAPPERFNS( Despatcher );
};

struct DespatchSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, const Despatcher *d, const std::vector<ExecutableNodePtr> &nodes )
	{
		try
		{
			list nodeList;
			for( std::vector<ExecutableNodePtr>::const_iterator nIt = nodes.begin(); nIt != nodes.end(); nIt++ )
			{
				nodeList.append( *nIt );
			}
			DespatcherPtr dd = const_cast<Despatcher*>(d);
			slot( dd, nodeList );
		}
		catch( const error_already_set &e )
		{
			PyErr_PrintEx( 0 ); // clears the error status
		}
		return boost::signals::detail::unusable();
	}
};

IE_CORE_DECLAREPTR( DespatcherWrap );

void GafferBindings::bindDespatcher()
{
	IECorePython::RunTimeTypedClass<Despatcher, DespatcherWrapPtr>()
		.def( init<>() )
		.def( "despatch", &DespatcherWrap::despatch )
		.def( "despatcher", &DespatcherWrap::despatcher ).staticmethod( "despatcher" )
		.def( "despatcherNames", &DespatcherWrap::despatcherNames ).staticmethod( "despatcherNames" )
		.def( "_registerDespatcher", &DespatcherWrap::registerDespatcher ).staticmethod( "_registerDespatcher" )
		.def( "_uniqueTasks", &DespatcherWrap::uniqueTasks ).staticmethod( "_uniqueTasks" )
		.def( "preDespatchSignal", &Despatcher::preDespatchSignal, return_value_policy<reference_existing_object>() ).staticmethod( "preDespatchSignal" )
		.def( "postDespatchSignal", &Despatcher::postDespatchSignal, return_value_policy<reference_existing_object>() ).staticmethod( "postDespatchSignal" )
	;

	SignalBinder<Despatcher::DespatchSignal, DefaultSignalCaller<Despatcher::DespatchSignal>, DespatchSlotCaller >::bind( "DespatchSignal" );
}
