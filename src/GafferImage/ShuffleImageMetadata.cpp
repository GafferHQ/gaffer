//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferImage/ShuffleImageMetadata.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( ShuffleImageMetadata );

size_t ShuffleImageMetadata::g_firstPlugIndex = 0;

ShuffleImageMetadata::ShuffleImageMetadata( const std::string &name )
	:	MetadataProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ShufflesPlug( "shuffles" ) );
}

ShuffleImageMetadata::~ShuffleImageMetadata()
{
}

Gaffer::ShufflesPlug *ShuffleImageMetadata::shufflesPlug()
{
	return getChild<Gaffer::ShufflesPlug>( g_firstPlugIndex );
}

const Gaffer::ShufflesPlug *ShuffleImageMetadata::shufflesPlug() const
{
	return getChild<Gaffer::ShufflesPlug>( g_firstPlugIndex );
}

void ShuffleImageMetadata::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	MetadataProcessor::affects( input, outputs );

	if( shufflesPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->metadataPlug() );
	}
}

void ShuffleImageMetadata::hashProcessedMetadata( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	shufflesPlug()->hash( h );
}

IECore::ConstCompoundDataPtr ShuffleImageMetadata::computeProcessedMetadata( const Gaffer::Context *context, const IECore::CompoundData *inputMetadata ) const
{
	CompoundDataPtr result = new CompoundData();
	result->writable() = shufflesPlug()->shuffle( inputMetadata->readable() );
	return result;
}
