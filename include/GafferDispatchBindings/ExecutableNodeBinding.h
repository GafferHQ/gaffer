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

#ifndef GAFFERDISPATCHBINDINGS_EXECUTABLENODEBINDING_H
#define GAFFERDISPATCHBINDINGS_EXECUTABLENODEBINDING_H

#include "boost/python/suite/indexing/container_utils.hpp"

#include "IECorePython/ScopedGILLock.h"

#include "GafferBindings/NodeBinding.h"

#include "GafferDispatch/ExecutableNode.h"

namespace GafferDispatchBindings
{

void bindExecutableNode();

template<typename T, typename TWrapper=T>
class ExecutableNodeClass : public GafferBindings::NodeClass<T, TWrapper>
{
	public :

		ExecutableNodeClass( const char *docString = NULL );

};

template<typename WrappedType>
class ExecutableNodeWrapper : public GafferBindings::NodeWrapper<WrappedType>
{
	public :

		ExecutableNodeWrapper( PyObject *self, const std::string &name )
			:	GafferBindings::NodeWrapper<WrappedType>( self, name )
		{
		}

		virtual void preTasks( const Gaffer::Context *context, GafferDispatch::ExecutableNode::Tasks &tasks ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object override = this->methodOverride( "preTasks" );
				if( !override )
				{
					// backwards compatibility with old method name
					override = this->methodOverride( "requirements" );
				}

				if( override )
				{
					boost::python::list pythonTasks = boost::python::extract<boost::python::list>(
						override( Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) )
					);
					boost::python::container_utils::extend_container( tasks, pythonTasks );
					return;
				}
			}
			WrappedType::preTasks( context, tasks );
		}

		virtual IECore::MurmurHash hash( const Gaffer::Context *context ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object h = this->methodOverride( "hash" );
				if( h )
				{
					return boost::python::extract<IECore::MurmurHash>(
						h( Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) )
					);
				}
			}
			return WrappedType::hash( context );
		}

		virtual void execute() const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object exec = this->methodOverride( "execute" );
				if( exec )
				{
					exec();
					return;
				}
			}
			WrappedType::execute();
		}

		virtual void executeSequence( const std::vector<float> &frames ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
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
			WrappedType::executeSequence( frames );
		}

		virtual bool requiresSequenceExecution() const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object reqSecExec = this->methodOverride( "requiresSequenceExecution" );
				if( reqSecExec )
				{
					return reqSecExec();
				}
			}
			return WrappedType::requiresSequenceExecution();
		}

};

} // namespace GafferDispatchBindings

#include "GafferDispatchBindings/ExecutableNodeBinding.inl"

#endif // GAFFERDISPATCHBINDINGS_EXECUTABLENODEBINDING_H
