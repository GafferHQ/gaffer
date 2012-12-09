//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

template<typename T, typename Ptr=IECore::IntrusivePtr<T> >
class DependencyNodeClass : public NodeClass<T, Ptr>
{
	public :
	
		DependencyNodeClass( const char *docString = 0 );
		
};

template<typename WrappedType>
class DependencyNodeWrapper : public NodeWrapper<WrappedType>
{
	public :
	
		DependencyNodeWrapper( PyObject *self, const std::string &name, const boost::python::dict &inputs, const boost::python::tuple &dynamicPlugs )
			:	NodeWrapper<WrappedType>( self, name, inputs, dynamicPlugs )
		{
			initNode( this, inputs, dynamicPlugs );
		}		
		
		virtual void affects( const Gaffer::ValuePlug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const
		{
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( GraphComponentWrapper<WrappedType>::m_pyObject, "affects" ) )
			{
				boost::python::override f = this->get_override( "affects" );
				if( f )
				{
					boost::python::list pythonOutputs = f( Gaffer::ValuePlugPtr( const_cast<Gaffer::ValuePlug *>( input ) ) );
					boost::python::container_utils::extend_container( outputs, pythonOutputs );
					return;
				}
			}
			WrappedType::affects( input, outputs );
		}
	
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
		{
			WrappedType::hash( output, context, h );
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( GraphComponentWrapper<WrappedType>::m_pyObject, "hash" ) )
			{
				boost::python::override f = this->get_override( "hash" );
				if( f )
				{
					boost::python::object pythonHash( h );
					f(
						Gaffer::ValuePlugPtr( const_cast<Gaffer::ValuePlug *>( output ) ),
						Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ),
						pythonHash
					);
					h = boost::python::extract<IECore::MurmurHash>( pythonHash );
				}
			}
		}

		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
		{
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( GraphComponentWrapper<WrappedType>::m_pyObject, "compute" ) )
			{
				boost::python::override f = this->get_override( "compute" );
				if( f )
				{
					f( Gaffer::ValuePlugPtr( output ), Gaffer::ContextPtr( const_cast<Gaffer::Context *>( context ) ) );
					return;
				}
			}
			WrappedType::compute( output, context );
		}
	
};

#define GAFFERBINDINGS_DEFDEPENDENCYNODEWRAPPERFNS( CLASSNAME ) \
	GAFFERBINDINGS_DEFNODEWRAPPERFNS( CLASSNAME )

} // namespace GafferBindings

#include "GafferBindings/DependencyNodeBinding.inl"

#endif // GAFFERBINDINGS_DEPENDENCYNODEBINDING_H