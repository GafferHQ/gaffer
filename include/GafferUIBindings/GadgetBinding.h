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
		
		virtual Imath::Box3f bound() const
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::override f = this->get_override( "bound" );
			if( f )
			{
				return f();
			}
			return WrappedType::bound();
		}
	
		virtual std::string getToolTip( const IECore::LineSegment3f &line ) const
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::override f = this->get_override( "getToolTip" );
			if( f )
			{
				return f( line );
			}
			return WrappedType::getToolTip( line );
		}
		
		virtual void doRender( const GafferUI::Style *style ) const
		{
			IECorePython::ScopedGILLock gilLock;
			boost::python::override f = this->get_override( "doRender" );
			if( f )
			{
				f( style );
				return;
			}
			WrappedType::doRender( style );
		}

};

/// This must be used in /every/ Gadget binding. See the lengthy comments in
/// IECorePython/ParameterBinding.h for an explanation.
#define GAFFERUIBINDINGS_DEFGADGETWRAPPERFNS( CLASSNAME )\
	GAFFERBINDINGS_DEFGRAPHCOMPONENTWRAPPERFNS( CLASSNAME ) \
	.def( "bound", &bound<CLASSNAME> )\
	.def( "getToolTip", &getToolTip<CLASSNAME> )\

template<typename T>
static Imath::Box3f bound( const T &p )
{
	return p.T::bound();
}

template<typename T>
static std::string getToolTip( const T &p, const IECore::LineSegment3f &line )
{
	return p.T::getToolTip( line );
}

void bindGadget();

} // namespace GafferUIBindings

#endif // GAFFERUIBINDINGS_GADGETBINDING_H
