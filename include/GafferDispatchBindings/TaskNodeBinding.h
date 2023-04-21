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

#pragma once

#include "GafferDispatch/TaskNode.h"

#include "GafferBindings/DependencyNodeBinding.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILLock.h"

#include "boost/python/suite/indexing/container_utils.hpp"

#include <utility>

namespace GafferDispatchBindings
{

template<typename T, typename TWrapper=T>
class TaskNodeClass : public GafferBindings::DependencyNodeClass<T, TWrapper>
{
	public :

		TaskNodeClass( const char *docString = nullptr );

};

template<typename WrappedType>
class TaskNodeWrapper : public GafferBindings::DependencyNodeWrapper<WrappedType>
{
	public :

		template<typename... Args>
		TaskNodeWrapper( PyObject *self, Args&&... args )
			:	GafferBindings::DependencyNodeWrapper<WrappedType>( self, std::forward<Args>( args )... )
		{
		}

		bool affectsTask( const Gaffer::Plug *input ) const override
		{
			if( this->isSubclassed() && this->initialised() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object override = this->methodOverride( "affectsTask" );
					if( override )
					{
						return boost::python::extract<bool>(
							override( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( input ) ) )
						);
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::affectsTask( input );
		}

		void preTasks( const Gaffer::Context *context, GafferDispatch::TaskNode::Tasks &tasks ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object override = this->methodOverride( "preTasks" );
					if( override )
					{
						boost::python::list pythonTasks = boost::python::extract<boost::python::list>(
							override( Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) )
						);
						boost::python::container_utils::extend_container( tasks, pythonTasks );
						return;
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::preTasks( context, tasks );
		}

		void postTasks( const Gaffer::Context *context, GafferDispatch::TaskNode::Tasks &tasks ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object override = this->methodOverride( "postTasks" );
					if( override )
					{
						boost::python::list pythonTasks = boost::python::extract<boost::python::list>(
							override( Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) )
						);
						boost::python::container_utils::extend_container( tasks, pythonTasks );
						return;
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::postTasks( context, tasks );
		}

		IECore::MurmurHash hash( const Gaffer::Context *context ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object h = this->methodOverride( "hash" );
					if( h )
					{
						return boost::python::extract<IECore::MurmurHash>(
							h( Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) )
						);
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::hash( context );
		}

		void execute() const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object exec = this->methodOverride( "execute" );
					if( exec )
					{
						exec();
						return;
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::execute();
		}

		void executeSequence( const std::vector<float> &frames ) const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object execSeq = this->methodOverride( "executeSequence" );
					if( execSeq )
					{
						boost::python::list frameList;
						for( std::vector<float>::const_iterator it = frames.begin(); it != frames.end(); ++it )
						{
							frameList.append( *it );
						}
						execSeq( frameList );
						return;
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::executeSequence( frames );
		}

		bool requiresSequenceExecution() const override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object reqSecExec = this->methodOverride( "requiresSequenceExecution" );
					if( reqSecExec )
					{
						return reqSecExec();
					}
				}
				catch( const boost::python::error_already_set & )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::requiresSequenceExecution();
		}

};

} // namespace GafferDispatchBindings

#include "GafferDispatchBindings/TaskNodeBinding.inl"
