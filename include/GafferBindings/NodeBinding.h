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

#ifndef GAFFERBINDINGS_NODEBINDING_H
#define GAFFERBINDINGS_NODEBINDING_H

#include "boost/python.hpp"

#include "IECorePython/ScopedGILLock.h"

#include "Gaffer/Node.h"

#include "GafferBindings/GraphComponentBinding.h"
#include "GafferBindings/Serialisation.h"

namespace GafferBindings
{

void bindNode();

template<typename T, typename Ptr=IECore::IntrusivePtr<T> >
class NodeClass : public IECorePython::RunTimeTypedClass<T, Ptr>
{
	public :
	
		NodeClass( const char *docString = 0 );
		
};

template<typename T>
class NodeWrapper : public GraphComponentWrapper<T>
{
	public :
	
		typedef T WrappedType;
	
		NodeWrapper( PyObject *self, const std::string &name )
			:	GraphComponentWrapper<T>( self, name )
		{
		}		
		
		virtual bool acceptsInput( const Gaffer::Plug *plug, const Gaffer::Plug *inputPlug ) const
		{
			IECorePython::ScopedGILLock gilLock;
			if( PyObject_HasAttrString( GraphComponentWrapper<T>::m_pyObject, "acceptsInput" ) )
			{
				boost::python::override f = this->get_override( "acceptsInput" );
				if( f )
				{
					return f( Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( plug ) ), Gaffer::PlugPtr( const_cast<Gaffer::Plug *>( inputPlug ) ) );
				}
			}
			return T::acceptsInput( plug, inputPlug );
		}
	
};

#define GAFFERBINDINGS_DEFNODEWRAPPERFNS( CLASSNAME ) \
	GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( CLASSNAME )

class NodeSerialiser : public Serialisation::Serialiser
{

	public :
	
		/// Implemented so that only plugs are serialised - child nodes are expected to
		/// be a part of the implementation of the node rather than something the user
		/// has created themselves.
		virtual bool childNeedsSerialisation( const Gaffer::GraphComponent *child ) const;
		/// Implemented so that dynamic plugs are constructed appropriately.
		virtual bool childNeedsConstruction( const Gaffer::GraphComponent *child ) const;

};

} // namespace GafferBindings

#include "GafferBindings/NodeBinding.inl"

#endif // GAFFERBINDINGS_NODEBINDING_H
