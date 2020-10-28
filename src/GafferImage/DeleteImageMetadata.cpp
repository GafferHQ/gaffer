//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/DeleteImageMetadata.h"

#include "Gaffer/StringPlug.h"

#include "IECore/StringAlgo.h"

using namespace IECore;
using namespace Gaffer;

namespace GafferImage
{

GAFFER_NODE_DEFINE_TYPE( DeleteImageMetadata );

size_t DeleteImageMetadata::g_firstPlugIndex = 0;

DeleteImageMetadata::DeleteImageMetadata( const std::string &name )
	:	MetadataProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "names" ) );
	addChild( new BoolPlug( "invertNames" ) );
}

DeleteImageMetadata::~DeleteImageMetadata()
{
}

Gaffer::StringPlug *DeleteImageMetadata::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *DeleteImageMetadata::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *DeleteImageMetadata::invertNamesPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *DeleteImageMetadata::invertNamesPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

void DeleteImageMetadata::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	MetadataProcessor::affects( input, outputs );

	if ( input == namesPlug() || input == invertNamesPlug() )
	{
		outputs.push_back( outPlug()->metadataPlug() );
	}
}

void DeleteImageMetadata::hashProcessedMetadata( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	namesPlug()->hash( h );
	invertNamesPlug()->hash( h );
}

IECore::ConstCompoundDataPtr DeleteImageMetadata::computeProcessedMetadata( const Gaffer::Context *context, const IECore::CompoundData *inputMetadata ) const
{
	if( inputMetadata->readable().empty() )
	{
		return inputMetadata;
	}

	const std::string names = namesPlug()->getValue();
	const bool invert = invertNamesPlug()->getValue();
	if ( !invert && !names.size() )
	{
		return inputMetadata;
	}

	IECore::CompoundDataPtr result = new IECore::CompoundData;
	for( IECore::CompoundData::ValueType::const_iterator it = inputMetadata->readable().begin(), eIt = inputMetadata->readable().end(); it != eIt; ++it )
	{
		if( StringAlgo::matchMultiple( it->first.c_str(), names.c_str() ) == invert )
		{
			result->writable()[it->first] = it->second;
		}
	}

	return result;
}

} // namespace GafferImage
