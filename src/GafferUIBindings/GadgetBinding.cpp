//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "boost/python.hpp"

#include "GafferUIBindings/GadgetBinding.h"
#include "GafferUI/Gadget.h"
#include "GafferUI/Style.h"

#include "GafferBindings/SignalBinding.h"
#include "GafferBindings/CatchingSlotCaller.h"

#include "IECorePython/RunTimeTypedBinding.h"
#include "IECorePython/Wrapper.h"

using namespace boost::python;
using namespace GafferUIBindings;
using namespace GafferBindings;
using namespace GafferUI;

struct RenderRequestSlotCaller
{
	boost::signals::detail::unusable operator()( boost::python::object slot, GadgetPtr g )
	{
		slot( g );
		return boost::signals::detail::unusable();
	}
};

static StylePtr getStyle( Gadget &g )
{
	return const_cast<Style *>( g.getStyle() );
}

static StylePtr style( Gadget &g )
{
	return const_cast<Style *>( g.style() );
}

BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS( fullTransformOverloads, fullTransform, 0, 1 );
BOOST_PYTHON_MEMBER_FUNCTION_OVERLOADS( renderOverloads, render, 0, 1 );

void GafferUIBindings::bindGadget()
{
	typedef GadgetWrapper<Gadget> Wrapper;
	IE_CORE_DECLAREPTR( Wrapper );

	scope s = IECorePython::RunTimeTypedClass<Gadget, WrapperPtr>()
		.def( init<>() )
		.def( init<const std::string &>() )
		.GAFFERUIBINDINGS_DEFGADGETWRAPPERFNS( Gadget )
		.def( "setStyle", &Gadget::setStyle )
		.def( "getStyle", &getStyle )
		.def( "style", &style )
		.def( "getTransform", &Gadget::getTransform, return_value_policy<copy_const_reference>() )
		.def( "setTransform", &Gadget::setTransform )
		.def( "fullTransform", &Gadget::fullTransform, fullTransformOverloads() )
		.def( "transformedBound", (Imath::Box3f (Gadget::*)() const)&Gadget::transformedBound )
		.def( "transformedBound", (Imath::Box3f (Gadget::*)( ConstGadgetPtr ) const)&Gadget::transformedBound )
		.def( "render", &Gadget::render, renderOverloads() )
		.def( "renderRequestSignal", &Gadget::renderRequestSignal, return_internal_reference<1>() )
		.def( "setToolTip", &Gadget::setToolTip )
		.def( "buttonPressSignal", &Gadget::buttonPressSignal, return_internal_reference<1>() )
		.def( "buttonReleaseSignal", &Gadget::buttonReleaseSignal, return_internal_reference<1>() )
		.def( "buttonDoubleClickSignal", &Gadget::buttonDoubleClickSignal, return_internal_reference<1>() )
		.def( "wheelSignal", &Gadget::wheelSignal, return_internal_reference<1>() )
		.def( "enterSignal", &Gadget::enterSignal, return_internal_reference<1>() )
		.def( "leaveSignal", &Gadget::leaveSignal, return_internal_reference<1>() )
		.def( "mouseMoveSignal", &Gadget::mouseMoveSignal, return_internal_reference<1>() )
		.def( "dragBeginSignal", &Gadget::dragBeginSignal, return_internal_reference<1>() )
		.def( "dragMoveSignal", &Gadget::dragMoveSignal, return_internal_reference<1>() )
		.def( "dragEnterSignal", &Gadget::dragEnterSignal, return_internal_reference<1>() )
		.def( "dragLeaveSignal", &Gadget::dragLeaveSignal, return_internal_reference<1>() )
		.def( "dropSignal", &Gadget::dropSignal, return_internal_reference<1>() )
		.def( "dragEndSignal", &Gadget::dragEndSignal, return_internal_reference<1>() )
		.def( "keyPressSignal", &Gadget::keyPressSignal, return_internal_reference<1>() )
		.def( "keyReleaseSignal", &Gadget::keyReleaseSignal, return_internal_reference<1>() )
		.def( "idleSignal", &Gadget::idleSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "idleSignal" )
		.def( "_idleSignalAccessedSignal", &Gadget::idleSignalAccessedSignal, return_value_policy<reference_existing_object>() )
		.staticmethod( "_idleSignalAccessedSignal" )
		.def( "select", &Gadget::select ).staticmethod( "select" )
	;
	
	SignalBinder<Gadget::RenderRequestSignal, DefaultSignalCaller<Gadget::RenderRequestSignal>, RenderRequestSlotCaller>::bind( "RenderRequestSignal" );	
	SignalBinder<Gadget::ButtonSignal, DefaultSignalCaller<Gadget::ButtonSignal>, CatchingSlotCaller<Gadget::ButtonSignal> >::bind( "ButtonSignal" );
	SignalBinder<Gadget::KeySignal, DefaultSignalCaller<Gadget::KeySignal>, CatchingSlotCaller<Gadget::KeySignal> >::bind( "KeySignal" );
	SignalBinder<Gadget::DragBeginSignal, DefaultSignalCaller<Gadget::DragBeginSignal>, CatchingSlotCaller<Gadget::DragBeginSignal> >::bind( "DragBeginSignal" );
	SignalBinder<Gadget::DragDropSignal, DefaultSignalCaller<Gadget::DragDropSignal>, CatchingSlotCaller<Gadget::DragDropSignal> >::bind( "DragDropSignal" );
	SignalBinder<Gadget::EnterLeaveSignal, DefaultSignalCaller<Gadget::EnterLeaveSignal>, CatchingSlotCaller<Gadget::EnterLeaveSignal> >::bind( "EnterLeaveSignal" );	
	SignalBinder<Gadget::IdleSignal>::bind( "IdleSignal" );	

}
