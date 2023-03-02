//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "Gaffer/BoxPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"

namespace Gaffer
{

/// This structure can be used to determine the appropriate Plug subclass
/// to use to store a value of type T.
template<typename T>
struct PlugType
{
	using Type = void;
};

#define GAFFER_PLUGTYPE_SPECIALISE( VALUETYPE, PLUGTYPE ) 	\
	template<>												\
	struct PlugType<VALUETYPE>								\
	{														\
		using Type = PLUGTYPE;								\
	};														\

GAFFER_PLUGTYPE_SPECIALISE( float, FloatPlug )
GAFFER_PLUGTYPE_SPECIALISE( int, IntPlug )
GAFFER_PLUGTYPE_SPECIALISE( bool, BoolPlug )

GAFFER_PLUGTYPE_SPECIALISE( Imath::V2f, V2fPlug )
GAFFER_PLUGTYPE_SPECIALISE( Imath::V3f, V3fPlug )

GAFFER_PLUGTYPE_SPECIALISE( Imath::V2i, V2iPlug )
GAFFER_PLUGTYPE_SPECIALISE( Imath::V3i, V3iPlug )

GAFFER_PLUGTYPE_SPECIALISE( Imath::Color3f, Color3fPlug )
GAFFER_PLUGTYPE_SPECIALISE( Imath::Color4f, Color4fPlug )

GAFFER_PLUGTYPE_SPECIALISE( std::string, StringPlug )

GAFFER_PLUGTYPE_SPECIALISE( Imath::M33f, M33fPlug )
GAFFER_PLUGTYPE_SPECIALISE( Imath::M44f, M44fPlug )

GAFFER_PLUGTYPE_SPECIALISE( Imath::Box2i, Box2iPlug )
GAFFER_PLUGTYPE_SPECIALISE( Imath::Box3i, Box3iPlug )

GAFFER_PLUGTYPE_SPECIALISE( Imath::Box2f, Box2fPlug )
GAFFER_PLUGTYPE_SPECIALISE( Imath::Box3f, Box3fPlug )

} // namespace Gaffer
