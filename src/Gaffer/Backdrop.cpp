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

#include "Gaffer/Backdrop.h"

#include "Gaffer/StringPlug.h"

using namespace Gaffer;

GAFFER_NODE_DEFINE_TYPE( Backdrop );

size_t Backdrop::g_firstPlugIndex = 0;

Backdrop::Backdrop( const std::string &name )
	:	Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "title", Plug::In, "Title" ) );
	addChild( new FloatPlug( "scale", Plug::In, 1.0f, 1.0f ) );
	addChild( new StringPlug( "description" ) );
	addChild( new IntPlug( "depth", Plug::In, 0, -1, 1 ) );
}

Backdrop::~Backdrop()
{
}

Gaffer::StringPlug *Backdrop::titlePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Backdrop::titlePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

FloatPlug *Backdrop::scalePlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

const FloatPlug *Backdrop::scalePlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Backdrop::descriptionPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Backdrop::descriptionPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

IntPlug *Backdrop::depthPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}

const IntPlug *Backdrop::depthPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 3 );
}
