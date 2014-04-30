//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2012, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUIBINDINGS_GADGETBINDING_H
#define GAFFERUIBINDINGS_GADGETBINDING_H

#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"

#include "GafferBindings/GraphComponentBinding.h"

namespace GafferUIBindings
{

template<typename T, typename Ptr=IECore::IntrusivePtr<T> >
class GadgetClass : public GafferBindings::GraphComponentClass<T, Ptr>
{
	public :
	
		GadgetClass( const char *docString = 0 );
		
};

template<typename WrappedType>
class GadgetWrapper : public GafferBindings::GraphComponentWrapper<WrappedType>
{
	public :
	
		GadgetWrapper( PyObject *self, const std::string &name=Gaffer::GraphComponent::defaultName<WrappedType>() )
			:	GafferBindings::GraphComponentWrapper<WrappedType>( self, name )
		{
		}

		template<typename Arg1, typename Arg2>
		GadgetWrapper( PyObject *self, Arg1 arg1, Arg2 arg2 )
			:	GafferBindings::GraphComponentWrapper<WrappedType>( self, arg1, arg2 )
		{
		}
		
		virtual void setHighlighted( bool highlighted )
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "setHighlighted" );
				if( f )
				{
					f( highlighted );
					return;
				}
			}
			WrappedType::setHighlighted( highlighted );
		}

		virtual Imath::Box3f bound() const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "bound" );
				if( f )
				{
					return boost::python::extract<Imath::Box3f>( f() );
				}
			}
			return WrappedType::bound();
		}
	
		virtual std::string getToolTip( const IECore::LineSegment3f &line ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "getToolTip" );
				if( f )
				{
					return boost::python::extract<std::string>( f( line ) );
				}
			}
			return WrappedType::getToolTip( line );
		}
		
		virtual void doRender( const GafferUI::Style *style ) const
		{
			if( this->isSubclassed() )
			{
				IECorePython::ScopedGILLock gilLock;
				boost::python::object f = this->methodOverride( "doRender" );
				if( f )
				{
					f( style );
					return;
				}
			}
			WrappedType::doRender( style );
		}

};

void bindGadget();

} // namespace GafferUIBindings

#include "GafferUIBindings/GadgetBinding.inl"

#endif // GAFFERUIBINDINGS_GADGETBINDING_H
