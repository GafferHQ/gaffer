//////////////////////////////////////////////////////////////////////////
//
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

#include "boost/python.hpp"

#include "IECorePython/RefCountedBinding.h"

#include "GafferBindings/SignalBinding.h"

#include "GafferUI/Pointer.h"
#include "GafferUIBindings/PointerBinding.h"

using namespace boost::python;
using namespace GafferBindings;
using namespace GafferUI;
using namespace GafferUIBindings;

static IECore::ImagePrimitivePtr image( Pointer *pointer )
{
	return const_cast<IECore::ImagePrimitive *>( pointer->image() );
}

static PointerPtr getCurrent()
{
	return const_cast<Pointer *>( Pointer::getCurrent() );
}

void GafferUIBindings::bindPointer()
{
	scope s = IECorePython::RefCountedClass<Pointer, IECore::RefCounted>( "Pointer" )
		.def( init<const IECore::ImagePrimitive *, const Imath::V2i &>() )
		.def( init<const std::string &, const Imath::V2i &>() )
		.def( "image", &image )
		.def( "hotspot", &Pointer::hotspot, return_value_policy<copy_const_reference>() )
		.def( "setCurrent", (void (*)( ConstPointerPtr ))&Pointer::setCurrent )
		.def( "setCurrent", (void (*)( const std::string & ))&Pointer::setCurrent )
		.staticmethod( "setCurrent" )
		.def( "getCurrent", &getCurrent )
		.staticmethod( "getCurrent" )
		.def( "changedSignal", &Pointer::changedSignal, return_value_policy<reference_existing_object>() ).staticmethod( "changedSignal" )
	;

	SignalBinder<Pointer::ChangedSignal>::bind( "ChangedSignal" );

}
