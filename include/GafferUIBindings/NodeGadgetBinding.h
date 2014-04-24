//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUIBINDINGS_NODEGADGETBINDING_H
#define GAFFERUIBINDINGS_NODEGADGETBINDING_H

#include "GafferUI/NodeGadget.h"

#include "GafferUIBindings/GadgetBinding.h"

namespace GafferUIBindings
{

template<typename T, typename Ptr=IECore::IntrusivePtr<T> >
class NodeGadgetClass : public GadgetClass<T, Ptr>
{
	public :
	
		NodeGadgetClass( const char *docString = 0 );
		
};

template<typename WrappedType>
class NodeGadgetWrapper : public GadgetWrapper<WrappedType>
{
	
	public :

		NodeGadgetWrapper( PyObject *self, Gaffer::NodePtr node )
			:	GadgetWrapper<WrappedType>( self, node )
		{
		}
		
		template<typename Arg1, typename Arg2>
		NodeGadgetWrapper( PyObject *self, Arg1 arg1, Arg2 arg2 )
			:	GadgetWrapper<WrappedType>( self, arg1, arg2 )
		{
		}
				
		virtual GafferUI::NodulePtr nodule( Gaffer::ConstPlugPtr plug )
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "nodule" );
				if( f )
				{
					return boost::python::extract<GafferUI::NodulePtr>(
						f( IECore::constPointerCast<Gaffer::Plug>( plug ) )
					);
				}
			}
			return WrappedType::nodule( plug );
		}
		
		virtual Imath::V3f noduleTangent( const GafferUI::Nodule *nodule ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "noduleTangent" );
				if( f )
				{
					return boost::python::extract<Imath::V3f>(
						f( GafferUI::NodulePtr( const_cast<GafferUI::Nodule *>( nodule ) ) )
					);
				}
			}
			return WrappedType::noduleTangent( nodule );
		}

};

void bindNodeGadget();

} // namespace GafferUIBindings

#include "GafferUIBindings/NodeGadgetBinding.inl"

#endif // GAFFERUIBINDINGS_NODEGADGETBINDING_H
