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

namespace GafferUIBindings
{

namespace Detail
{

template<typename T>
static void setHighlighted( T &p, bool highlighted )
{
	IECorePython::ScopedGILRelease gilRelease;
	p.T::setHighlighted( highlighted );
}

template<typename T>
static Imath::Box3f bound( const T &p )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.T::bound();
}

template<typename T>
static std::string getToolTip( const T &p, const IECore::LineSegment3f &line )
{
	IECorePython::ScopedGILRelease gilRelease;
	return p.T::getToolTip( line );
}

} // namespace Detail

template<typename T, typename TWrapper>
GadgetClass<T, TWrapper>::GadgetClass( const char *docString )
	:	GafferBindings::GraphComponentClass<T, TWrapper>( docString )
{
	this->def( "setHighlighted", &Detail::setHighlighted<T> );
	this->def( "bound", &Detail::bound<T> );
	this->def( "getToolTip", &Detail::getToolTip<T> );
}

} // namespace GafferUIBindings
