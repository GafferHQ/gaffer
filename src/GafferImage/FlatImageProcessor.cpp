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

#include "GafferImage/FlatImageProcessor.h"
#include "GafferImage/ImageAlgo.h"
#include "Gaffer/ArrayPlug.h"

using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( FlatImageProcessor );

FlatImageProcessor::FlatImageProcessor( const std::string &name )
	:	ImageProcessor( name )
{
}

FlatImageProcessor::FlatImageProcessor( const std::string &name, size_t minInputs, size_t maxInputs )
	:	ImageProcessor( name, minInputs, maxInputs )
{
}

FlatImageProcessor::~FlatImageProcessor()
{
}

Gaffer::ValuePlug::CachePolicy FlatImageProcessor::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	const ImagePlug *imagePlug = output->parent<ImagePlug>();
	if( imagePlug && output == imagePlug->sampleOffsetsPlug() )
	{
		// This plug is faster to compute than to retreive from cache
		return ValuePlug::CachePolicy::Uncached;
	}
	return ImageProcessor::computeCachePolicy( output );
}

void FlatImageProcessor::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	auto imagePlug = input->parent<ImagePlug>();
	if(
		imagePlug &&
		( imagePlug == inPlug() || imagePlug->parent() == inPlugs() ) &&
		input == imagePlug->deepPlug()
	)
	{
		outputs.push_back( outPlug()->deepPlug() );
	}
}

void FlatImageProcessor::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDeep( parent, context, h );
	if( inPlugs() )
	{
		for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
		{
			// We ignore unconnected inputs when determining the hash - this is the correct
			// behaviour for merge, and hopefully any other deep nodes that use inPlugs()
			if( (*it)->getInput<ValuePlug>() )
			{
				if( ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) )
				{
					h.append( (*it)->deepPlug()->hash() );
				}
			}
		}
	}
	else
	{
		// We need to append to the node hash, rather than just overriding with the upstream value,
		// so that we can't reuse the plug value from upstream, and have to call compute()
		h.append( inPlug()->deepPlug()->hash() );
	}
}

bool FlatImageProcessor::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const ImagePlug *badInput = nullptr;
	if( inPlugs() )
	{
		for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++it )
		{
			if(
				ImageAlgo::viewIsValid( context, (*it)->viewNames()->readable() ) &&
				(*it)->deepPlug()->getValue()
			)
			{
				badInput = it->get();
			}
		}
	}
	else
	{
		if( inPlug()->deepPlug()->getValue() )
		{
			badInput = inPlug();
		}
	}
	if( badInput )
	{
		throw IECore::Exception( "Deep data not supported in input \"" + badInput->relativeName( this ) + "\"" );
	}
	return false;
}

void FlatImageProcessor::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = ImagePlug::flatTileSampleOffsets()->Object::hash();
}

IECore::ConstIntVectorDataPtr FlatImageProcessor::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}
