//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/FlatImageSource.h"
#include "GafferImage/ImageAlgo.h"
#include "Gaffer/ArrayPlug.h"

using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( FlatImageSource );

FlatImageSource::FlatImageSource( const std::string &name )
	:	ImageNode( name )
{
}

FlatImageSource::~FlatImageSource()
{
}

Gaffer::ValuePlug::CachePolicy FlatImageSource::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	const ImagePlug *imagePlug = output->parent<ImagePlug>();
	if( imagePlug && ( output == imagePlug->sampleOffsetsPlug() || output == imagePlug->deepPlug() ) )
	{
		// These plugs are faster to compute than to retreive from cache
		return ValuePlug::CachePolicy::Uncached;
	}
	return ImageNode::computeCachePolicy( output );
}

void FlatImageSource::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageNode::hashDeep( parent, context, h );
}

bool FlatImageSource::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return false;
}

void FlatImageSource::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::flatTileSampleOffsets()->IECore::Object::hash();
}

IECore::ConstIntVectorDataPtr FlatImageSource::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}
