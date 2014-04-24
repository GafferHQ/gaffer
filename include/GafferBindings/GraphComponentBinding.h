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

#ifndef GAFFERBINDINGS_GRAPHCOMPONENTBINDING_H
#define GAFFERBINDINGS_GRAPHCOMPONENTBINDING_H

#include "IECorePython/RunTimeTypedBinding.h"

#include "Gaffer/GraphComponent.h"

namespace GafferBindings
{

template<typename T, typename Ptr=IECore::IntrusivePtr<T> >
class GraphComponentClass : public IECorePython::RunTimeTypedClass<T, Ptr>
{
	public :
	
		GraphComponentClass( const char *docString = 0 );
		
};

template<typename WrappedType>
class GraphComponentWrapper : public IECorePython::RunTimeTypedWrapper<WrappedType>
{

	public :
	
		GraphComponentWrapper( PyObject *self, const std::string &name=Gaffer::GraphComponent::defaultName<WrappedType>() )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, name )
		{
		}

		template<typename Arg1, typename Arg2>
		GraphComponentWrapper( PyObject *self, Arg1 arg1, Arg2 arg2 )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, arg1, arg2 )
		{
		}
		
		template<typename Arg1, typename Arg2, typename Arg3>
		GraphComponentWrapper( PyObject *self, Arg1 arg1, Arg2 arg2, Arg3 arg3 )
			:	IECorePython::RunTimeTypedWrapper<WrappedType>( self, arg1, arg2, arg3 )
		{
		}

		virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "acceptsChild" );
				if( f )
				{
					return f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( potentialChild ) ) );
				}
			}
			return WrappedType::acceptsChild( potentialChild );
		}
	
		virtual bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "acceptsParent" );
				if( f )
				{
					return f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( potentialParent ) ) );
				}
			}
			return WrappedType::acceptsParent( potentialParent );
		}

};
	
void bindGraphComponent();

} // namespace GafferBindings

#include "GafferBindings/GraphComponentBinding.inl"

#endif // GAFFERBINDINGS_GRAPHCOMPONENTBINDING_H
