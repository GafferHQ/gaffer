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

#include "GafferImage/ImageMetadata.h"

using namespace IECore;
using namespace Gaffer;

namespace GafferImage
{

GAFFER_NODE_DEFINE_TYPE( ImageMetadata );

size_t ImageMetadata::g_firstPlugIndex = 0;

ImageMetadata::ImageMetadata( const std::string &name )
	:	MetadataProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new CompoundDataPlug( "metadata" ) );
}

ImageMetadata::~ImageMetadata()
{
}

Gaffer::CompoundDataPlug *ImageMetadata::metadataPlug()
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

const Gaffer::CompoundDataPlug *ImageMetadata::metadataPlug() const
{
	return getChild<CompoundDataPlug>( g_firstPlugIndex );
}

void ImageMetadata::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	MetadataProcessor::affects( input, outputs );

	if( metadataPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->metadataPlug() );
	}
}

void ImageMetadata::hashProcessedMetadata( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	metadataPlug()->hash( h );
}

IECore::ConstCompoundDataPtr ImageMetadata::computeProcessedMetadata( const Gaffer::Context *context, const IECore::CompoundData *inputMetadata ) const
{
	const CompoundDataPlug *p = metadataPlug();
	if ( !p->children().size() )
	{
		return inputMetadata;
	}

	IECore::CompoundDataPtr result = new IECore::CompoundData;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->writable() = inputMetadata->readable();

	std::string name;
	for ( NameValuePlugIterator it( p ); !it.done(); ++it )
	{
		IECore::DataPtr d = p->memberDataAndName( it->get(), name );
		if ( d )
		{
			result->writable()[name] = d;
		}
	}

	return result;
}

} // namespace GafferImage
