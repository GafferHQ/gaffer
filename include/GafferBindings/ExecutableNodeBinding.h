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

#ifndef GAFFERBINDINGS_EXECUTABLENODEBINDING_H
#define GAFFERBINDINGS_EXECUTABLENODEBINDING_H

#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/ExecutableNode.h"

#include "GafferBindings/DependencyNodeBinding.h"

namespace GafferBindings
{

void bindExecutableNode();

template<typename T, typename TWrapper=T>
class ExecutableNodeClass : public DependencyNodeClass<T, TWrapper>
{
	public :

		ExecutableNodeClass( const char *docString = NULL );

};

template<typename WrappedType>
class ExecutableNodeWrapper : public DependencyNodeWrapper<WrappedType>
{
	public :

		ExecutableNodeWrapper( PyObject *self, const std::string &name )
			:	DependencyNodeWrapper<WrappedType>( self, name )
		{
		}

		virtual void requirements( const Gaffer::Context *context, Gaffer::ExecutableNode::Tasks &requirements ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object req = this->methodOverride( "requirements" );
				if( req )
				{
					boost::python::list requirementList = boost::python::extract<boost::python::list>(
						req( Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) )
					);

					size_t len = boost::python::len( requirementList );
					requirements.reserve( len );
					for( size_t i = 0; i < len; i++ )
					{
						requirements.push_back( boost::python::extract<Gaffer::ExecutableNode::Task>( requirementList[i] ) );
					}
					return;
				}
			}
			WrappedType::requirements( context, requirements );
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

} // namespace GafferBindings

#include "GafferBindings/ExecutableNodeBinding.inl"

#endif // GAFFERBINDINGS_EXECUTABLENODEBINDING_H
