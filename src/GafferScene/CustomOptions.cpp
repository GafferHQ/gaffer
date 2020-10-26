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

#include "GafferScene/CustomOptions.h"

using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( CustomOptions );

size_t CustomOptions::g_firstPlugIndex = 0;

CustomOptions::CustomOptions( const std::string &name )
	:	Options( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "prefix" ) );
}

CustomOptions::~CustomOptions()
{
}

Gaffer::StringPlug *CustomOptions::prefixPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *CustomOptions::prefixPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

void CustomOptions::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	Options::affects( input, outputs );

	if( input == prefixPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void CustomOptions::hashPrefix( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	prefixPlug()->hash( h );
}

std::string CustomOptions::computePrefix( const Gaffer::Context *context ) const
{
	return "option:" + prefixPlug()->getValue();
}
