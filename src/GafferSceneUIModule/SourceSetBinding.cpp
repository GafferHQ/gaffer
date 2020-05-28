//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#include "IECorePython/RunTimeTypedBinding.h"

#include "SourceSetBinding.h"

#include "GafferSceneUI/SourceSet.h"

using namespace Gaffer;
using namespace GafferSceneUI;

using namespace IECorePython;
using namespace boost::python;

namespace
{

SourceSetPtr sourceSetConstructor( Context &c, Set &s )
{
	// Must release GIL because SourceSet constructor triggers computes.
	ScopedGILRelease gilRelease;
	return new SourceSet( &c, &s );
}

void setContext( SourceSet &s, Context &c )
{
	IECorePython::ScopedGILRelease gilRelease;
	s.setContext( &c );
}

void setNodeSet( SourceSet &s, Set &t )
{
	IECorePython::ScopedGILRelease gilRelease;
	s.setNodeSet( &t );
}

} // namespace

void GafferSceneUIModule::bindSourceSet()
{
	RunTimeTypedClass<SourceSet>()
		.def( "__init__", make_constructor( &sourceSetConstructor, default_call_policies() ) )
		.def( "setContext", &setContext )
		.def( "getContext", &SourceSet::getContext, return_value_policy<CastToIntrusivePtr>() )
		.def( "setNodeSet", &setNodeSet )
		.def( "getNodeSet", &SourceSet::getNodeSet, return_value_policy<CastToIntrusivePtr>() )
	;
}

