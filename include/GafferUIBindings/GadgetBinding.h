//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#define GAFFERUIBINDINGS_GADGETWRAPPERFNS( CLASSNAME )\
	GAFFERBINDINGS_GRAPHCOMPONENTWRAPPERFNS( CLASSNAME)\
\
	virtual Imath::Box3f bound() const\
	{\
		IECorePython::ScopedGILLock gilLock;\
		override f = this->get_override( "bound" );\
		if( f )\
		{\
			return f();\
		}\
		return CLASSNAME::bound();\
	}\
\
	virtual std::string getToolTip() const\
	{\
		IECorePython::ScopedGILLock gilLock;\
		override f = this->get_override( "getToolTip" );\
		if( f )\
		{\
			return f();\
		}\
		return CLASSNAME::getToolTip();\
	}\
	\
	virtual void doRender( const Style *style ) const\
	{\
		IECorePython::ScopedGILLock gilLock;\
		override f = this->get_override( "doRender" );\
		if( f )\
		{\
			f( style );\
			return;\
		}\
		CLASSNAME::doRender( style );\
	}\

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
static std::string getToolTip( const T &p )
{
	return p.T::getToolTip();
}

void bindGadget();

} // namespace GafferUIBindings

#endif // GAFFERUIBINDINGS_GADGETBINDING_H
