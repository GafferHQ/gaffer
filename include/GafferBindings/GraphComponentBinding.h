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
#include "IECorePython/Wrapper.h"

#include "Gaffer/GraphComponent.h"

namespace GafferBindings
{

template<typename WrappedType>
class GraphComponentWrapper : public WrappedType, public IECorePython::Wrapper<WrappedType>
{

	public :
	
		GraphComponentWrapper( PyObject *self, const std::string &name=Gaffer::GraphComponent::defaultName<WrappedType>() )
			:	WrappedType( name ), IECorePython::Wrapper<WrappedType>( self, this )
		{
		}

		template<typename Arg1, typename Arg2>
		GraphComponentWrapper( PyObject *self, Arg1 arg1, Arg2 arg2 )
			:	WrappedType( arg1, arg2 ), IECorePython::Wrapper<WrappedType>( self, this )
		{
		}
		
		template<typename Arg1, typename Arg2, typename Arg3>
		GraphComponentWrapper( PyObject *self, Arg1 arg1, Arg2 arg2, Arg3 arg3 )
			:	WrappedType( arg1, arg2, arg3 ), IECorePython::Wrapper<WrappedType>( self, this )
		{
		}

		IECOREPYTHON_RUNTIMETYPEDWRAPPERFNS( WrappedType )

		virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
		{
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( IECorePython::Wrapper<WrappedType>::m_pyObject, "acceptsChild" ) )
			{
				boost::python::override f = this->get_override( "acceptsChild" );
				if( f )
				{
					return f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( potentialChild ) ) );
				}
			}
			return WrappedType::acceptsChild( potentialChild );
		}
	
		virtual bool acceptsParent( const Gaffer::GraphComponent *potentialParent ) const
		{
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( IECorePython::Wrapper<WrappedType>::m_pyObject, "acceptsParent" ) )
			{
				boost::python::override f = this->get_override( "acceptsParent" );
				if( f )
				{
					return f( Gaffer::GraphComponentPtr( const_cast<Gaffer::GraphComponent *>( potentialParent ) ) );
				}
			}
			return WrappedType::acceptsParent( potentialParent );
		}

};

/// This must be used in /every/ GraphComponent binding. See the lengthy comments in
/// IECorePython/ParameterBinding.h for an explanation.
#define GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( CLASSNAME )\
	def( "acceptsChild", &GafferBindings::acceptsChild<CLASSNAME> )\
	.def( "acceptsParent", &GafferBindings::acceptsParent<CLASSNAME> )

template<typename T>
static bool acceptsChild( const T &p, const Gaffer::GraphComponent *potentialChild )
{
	return p.T::acceptsChild( potentialChild );
}

template<typename T>
static bool acceptsParent( const T &p, const Gaffer::GraphComponent *potentialParent )
{
	return p.T::acceptsParent( potentialParent );
}
	
void bindGraphComponent();

} // namespace GafferBindings

#endif // GAFFERBINDINGS_GRAPHCOMPONENTBINDING_H
