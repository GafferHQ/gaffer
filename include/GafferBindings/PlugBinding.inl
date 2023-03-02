//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2014, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "IECorePython/ScopedGILRelease.h"

namespace GafferBindings
{

namespace Detail
{

template<typename T>
static bool acceptsInput( const T &p, const Gaffer::Plug *input )
{
	return p.T::acceptsInput( input );
}

template<typename T>
static void setInput( T &p, Gaffer::PlugPtr input )
{
	IECorePython::ScopedGILRelease r;
	p.T::setInput( input );
}

template<typename T>
static Gaffer::PlugPtr createCounterpart( T &p, const std::string &name, Gaffer::Plug::Direction direction )
{
	return p.T::createCounterpart( name, direction );
}

} // namespace Detail

template<typename T, typename TWrapper>
PlugClass<T, TWrapper>::PlugClass( const char *docString )
	:	GraphComponentClass<T, TWrapper>( docString )
{
	this->def( "acceptsInput", &Detail::acceptsInput<T> );
	this->def( "setInput", &Detail::setInput<T> );
	this->def( "createCounterpart", &Detail::createCounterpart<T> );
}

} // namespace GafferBindings
