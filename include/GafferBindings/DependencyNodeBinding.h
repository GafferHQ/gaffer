//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#ifndef GAFFERBINDINGS_DEPENDENCYNODEBINDING_H
#define GAFFERBINDINGS_DEPENDENCYNODEBINDING_H

#include "boost/python.hpp"

#include "GafferBindings/NodeBinding.h"

#include "Gaffer/Context.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/ValuePlug.h"

#include "IECorePython/ExceptionAlgo.h"
#include "IECorePython/ScopedGILLock.h"

#include "boost/python/suite/indexing/container_utils.hpp"

namespace GafferBindings
{

template<typename T, typename TWrapper=T>
class DependencyNodeClass : public NodeClass<T, TWrapper>
{
	public :

		DependencyNodeClass( const char *docString = nullptr );
		DependencyNodeClass( const char *docString, boost::python::no_init_t );

};

class GAFFER_API DependencyNodeWrapperBase
{

	protected :

		DependencyNodeWrapperBase() : m_initialised( false ) {};
		// Returns `true` once the Python `__init__()` method has
		// completed.
		bool initialised() const { return m_initialised; };

	private :

		// Friendship with the metaclass so it can set `m_initialised` for us.
		friend PyObject *dependencyNodeMetaclassCall( PyObject *self, PyObject *args, PyObject *kw );
		bool m_initialised;

};

template<typename WrappedType>
class DependencyNodeWrapper : public NodeWrapper<WrappedType>, public DependencyNodeWrapperBase
{
	public :

		template<typename... Args>
		DependencyNodeWrapper( PyObject *self, Args&&... args )
			:	NodeWrapper<WrappedType>( self, std::forward<Args>( args )... )
		{
		}

		bool isInstanceOf( IECore::TypeId typeId ) const override
		{
			if( typeId == (IECore::TypeId)Gaffer::DependencyNodeTypeId )
			{
				// Correct for the slightly overzealous (but hugely beneficial)
				// optimisation in NodeWrapper::isInstanceOf().
				return true;
			}
			return NodeWrapper<WrappedType>::isInstanceOf( typeId );
		}

		void affects( const Gaffer::Plug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const override
		{
			if( this->isSubclassed() && this->initialised() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "affects" );
					if( f )
					{
						boost::python::object r = f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( input ) ) );
						boost::python::list pythonOutputs = boost::python::extract<boost::python::list>( r );
						for( boost::python::ssize_t i = 0, e = boost::python::len( pythonOutputs ); i < e; ++i )
						{
							const Gaffer::Plug &p = boost::python::extract<const Gaffer::Plug &>( pythonOutputs[i] );
							outputs.push_back( &p );
						}
						return;
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			WrappedType::affects( input, outputs );
		}

		Gaffer::BoolPlug *enabledPlug() override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "enabledPlug" );
					if( f )
					{
						return boost::python::extract<Gaffer::BoolPlug *>( f() );
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::enabledPlug();
		}

		const Gaffer::BoolPlug *enabledPlug() const override
		{
			// Better to make an ugly cast than repeat the implementation of the non-const version.
			return const_cast<DependencyNodeWrapper *>( this )->enabledPlug();
		}

		Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) override
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				try
				{
					boost::python::object f = this->methodOverride( "correspondingInput" );
					if( f )
					{
						Gaffer::PlugPtr value = boost::python::extract<Gaffer::PlugPtr>(
							f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( output ) ) )
						);
						return value.get();
					}
				}
				catch( const boost::python::error_already_set &e )
				{
					IECorePython::ExceptionAlgo::translatePythonException();
				}
			}
			return WrappedType::correspondingInput( output );
		}

		const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const override
		{
			// Better to make an ugly cast than repeat the implementation of the non-const version.
			return const_cast<DependencyNodeWrapper *>( this )->correspondingInput( output );
		}

};

} // namespace GafferBindings

#include "GafferBindings/DependencyNodeBinding.inl"

#endif // GAFFERBINDINGS_DEPENDENCYNODEBINDING_H
