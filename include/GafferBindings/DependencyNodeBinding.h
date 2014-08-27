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
#include "boost/python/suite/indexing/container_utils.hpp"

#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/DependencyNode.h"
#include "Gaffer/Context.h"
#include "Gaffer/ValuePlug.h"

#include "GafferBindings/NodeBinding.h"

namespace GafferBindings
{

void bindDependencyNode();

template<typename T, typename TWrapper=T>
class DependencyNodeClass : public NodeClass<T, TWrapper>
{
	public :

		DependencyNodeClass( const char *docString = 0 );

};

template<typename WrappedType>
class DependencyNodeWrapper : public NodeWrapper<WrappedType>
{
	public :

		DependencyNodeWrapper( PyObject *self, const std::string &name )
			:	NodeWrapper<WrappedType>( self, name )
		{
		}

		virtual void affects( const Gaffer::Plug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "affects" );
				if( f )
				{
					boost::python::object r = f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( input ) ) );
					boost::python::list pythonOutputs = boost::python::extract<boost::python::list>( r );
					boost::python::container_utils::extend_container( outputs, pythonOutputs );
					return;
				}
			}
			WrappedType::affects( input, outputs );
		}

		virtual Gaffer::BoolPlug *enabledPlug()
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "enabledPlug" );
				if( f )
				{
					return boost::python::extract<Gaffer::BoolPlug *>( f() );
				}
			}
			return WrappedType::enabledPlug();
		}

		virtual const Gaffer::BoolPlug *enabledPlug() const
		{
			// Better to make an ugly cast than repeat the implementation of the non-const version.
			return const_cast<DependencyNodeWrapper *>( this )->enabledPlug();
		}

		virtual Gaffer::Plug *correspondingInput( const Gaffer::Plug *output )
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "correspondingInput" );
				if( f )
				{
					Gaffer::PlugPtr value = boost::python::extract<Gaffer::PlugPtr>(
						f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( output ) ) )
					);
					return value.get();
				}
			}
			return WrappedType::correspondingInput( output );
		}

		virtual const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const
		{
			// Better to make an ugly cast than repeat the implementation of the non-const version.
			return const_cast<DependencyNodeWrapper *>( this )->correspondingInput( output );
		}

};

} // namespace GafferBindings

#include "GafferBindings/DependencyNodeBinding.inl"

#endif // GAFFERBINDINGS_DEPENDENCYNODEBINDING_H
