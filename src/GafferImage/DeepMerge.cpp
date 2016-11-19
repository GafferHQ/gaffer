//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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

#include "IECore/BoxOps.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/DeepMerge.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( DeepMerge );

size_t DeepMerge::g_firstPlugIndex = 0;

DeepMerge::DeepMerge( const std::string &name )
	:	ImageProcessor( name, 2 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new BoolPlug( "discardZeroAlpha" ) );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

DeepMerge::~DeepMerge()
{
}

Gaffer::BoolPlug *DeepMerge::discardZeroAlphaPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *DeepMerge::discardZeroAlphaPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

void DeepMerge::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == discardZeroAlphaPlug() )
	{
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( const ImagePlug *inputImage = input->parent<ImagePlug>() )
	{
		if( inputImage->parent<ArrayPlug>() == inPlugs() )
		{
			outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );

			if( input == inputImage->dataWindowPlug() )
			{
				outputs.push_back( outPlug()->sampleOffsetsPlug() );
				outputs.push_back( outPlug()->channelDataPlug() );
			}
			else if( input == inputImage->channelDataPlug() )
			{
				outputs.push_back( outPlug()->sampleOffsetsPlug() );
			}
			else if( input == inputImage->channelNamesPlug() )
			{
				outputs.push_back( outPlug()->sampleOffsetsPlug() );
				outputs.push_back( outPlug()->channelDataPlug() );
			}
		}

		if( input == outPlug()->sampleOffsetsPlug() )
		{
			outputs.push_back( outPlug()->channelDataPlug() );
		}
	}
}

// \todo Remove the need for enabled() by passing through identical hashes
// if enabled() would return false
bool DeepMerge::enabled() const
{
	if( !ImageProcessor::enabled() )
	{
		return false;
	}

	int numConnected = 0;
	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<Plug>() )
		{
			numConnected++;
		}
	}

	return numConnected >= 2;
}

void DeepMerge::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDataWindow( output, context, h );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if ( (*it)->getInput<ValuePlug>() )
		{
			(*it)->dataWindowPlug()->hash( h );
		}
	}
}

Imath::Box2i DeepMerge::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i dataWindow = inPlug()->dataWindowPlug()->getValue();
	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		// We don't need to check that the plug is connected here as unconnected plugs don't have data windows.
		dataWindow.extendBy( (*it)->dataWindowPlug()->getValue() );
	}

	return dataWindow;
}

void DeepMerge::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelNames( output, context, h );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			(*it)->channelNamesPlug()->hash( h );
		}
	}
}

IECore::ConstStringVectorDataPtr DeepMerge::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::StringVectorDataPtr outChannelStrVectorData( new IECore::StringVectorData() );
	std::vector<std::string> &outChannels( outChannelStrVectorData->writable() );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			IECore::ConstStringVectorDataPtr inChannelStrVectorData((*it)->channelNamesPlug()->getValue() );
			const std::vector<std::string> &inChannels( inChannelStrVectorData->readable() );
			for ( std::vector<std::string>::const_iterator cIt( inChannels.begin() ); cIt != inChannels.end(); ++cIt )
			{
				if ( std::find( outChannels.begin(), outChannels.end(), *cIt ) == outChannels.end() )
				{
					outChannels.push_back( *cIt );
				}
			}
		}
	}

	if ( !outChannels.empty() )
	{
		return outChannelStrVectorData;
	}

	return inPlug()->channelNamesPlug()->defaultValue();
}

void DeepMerge::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );

	const bool discardZeroAlpha = discardZeroAlphaPlug()->getValue();

	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	outPlug()->sampleOffsetsPlug()->hash( h );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( !(*it)->getInput<ValuePlug>() )
		{
			continue;
		}

		ConstStringVectorDataPtr inChannelNamesPtr = (*it)->channelNamesPlug()->getValue();
		const std::vector<std::string> &inChannelNames = inChannelNamesPtr->readable();

		if( std::find( inChannelNames.begin(), inChannelNames.end(), channelName ) != inChannelNames.end() )
		{
			h.append( (*it)->channelDataHash( channelName, tileOrigin ) );
		}

		if( discardZeroAlpha && std::find( inChannelNames.begin(), inChannelNames.end(), "A" ) != inChannelNames.end() )
		{
			h.append( (*it)->channelDataHash( "A", tileOrigin ) );
		}

		// The hash of the channel data we include above represents just the data in
		// the tile itself, and takes no account of the possibility that parts of the
		// tile may be outside of the data window. This simplifies the implementation of
		// nodes like Constant (where all tiles are identical, even the edge tiles) and
		// Crop (which does no processing of tiles at all). For most nodes this doesn't
		// matter, because they don't change the data window, or they use a Sampler to
		// deal with invalid pixels. But because our data window is the union of all
		// input data windows, we may be using/revealing the invalid parts of a tile. We
		// deal with this in computeChannelData() by treating the invalid parts as empty,
		// and must therefore hash in the valid bound here to take that into account.
		const Box2i validBound = intersection( tileBound, (*it)->dataWindowPlug()->getValue() );
		h.append( validBound );
	}
}

IECore::ConstFloatVectorDataPtr DeepMerge::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	FloatVectorDataPtr resultData = new FloatVectorData;
	std::vector<float> &result = resultData->writable();

	result.reserve( outPlug()->sampleOffsets( tileOrigin )->readable().back() );

	const bool discardZeroAlpha = discardZeroAlphaPlug()->getValue();

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	std::vector<ConstFloatVectorDataPtr> inputChannelData;
	std::vector<ConstFloatVectorDataPtr> inputAlphaData;
	std::vector<ConstIntVectorDataPtr> inputSampleOffsets;
	std::vector<Box2i> inputValidBounds;

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			const Box2i validBound = intersection( tileBound, (*it)->dataWindowPlug()->getValue() );

			if( ! empty( validBound ) )
			{
				ConstStringVectorDataPtr inChannelNamesPtr = (*it)->channelNamesPlug()->getValue();
				const std::vector<std::string> &inChannelNames = inChannelNamesPtr->readable();

				inputSampleOffsets.push_back( (*it)->sampleOffsets( tileOrigin ) );

				if( std::find( inChannelNames.begin(), inChannelNames.end(), channelName ) != inChannelNames.end() )
				{
					inputChannelData.push_back( (*it)->channelData( channelName, tileOrigin ) );
				}
				else
				{
					inputChannelData.push_back( NULL );
				}

				inputValidBounds.push_back( validBound );

				if( discardZeroAlpha )
				{
					if( std::find( inChannelNames.begin(), inChannelNames.end(), "A" ) != inChannelNames.end() )
					{
						inputAlphaData.push_back( (*it)->channelData( "A", tileOrigin ) );
					}
					else
					{
						inputAlphaData.push_back( NULL );
					}
				}
			}
		}
	}

	Imath::V2i pixel;
	for( pixel.y = tileBound.min.y; pixel.y < tileBound.max.y; ++pixel.y )
	{
		for( pixel.x = tileBound.min.x; pixel.x < tileBound.max.x; ++pixel.x )
		{
			std::vector<ConstFloatVectorDataPtr>::const_iterator inputChannelDataIt = inputChannelData.begin();
			std::vector<ConstFloatVectorDataPtr>::const_iterator inputAlphaDataIt = inputAlphaData.begin();
			std::vector<ConstIntVectorDataPtr>::const_iterator inputSampleOffsetsIt = inputSampleOffsets.begin();
			std::vector<Box2i>::const_iterator inputValidBoundsIt = inputValidBounds.begin();

			for( ; inputChannelDataIt != inputChannelData.end(); ++inputChannelDataIt, ++inputSampleOffsetsIt, ++inputValidBoundsIt )
			{
				if( contains( *inputValidBoundsIt, pixel ) )
				{
					if( discardZeroAlpha )
					{
						if( (*inputAlphaDataIt) != NULL )
						{
							// If (*inputAlphaDataIt) is NULL, then there is no alpha channel, and
							// we're assuming a value of 0.0, so don't bother with the next steps,
							// as they'd result in not putting anything in.
							ConstFloatSampleRange alphaSamples = sampleRange( (*inputAlphaDataIt)->readable(), (*inputSampleOffsetsIt)->readable(), pixel - tileOrigin );
							std::vector<float>::const_iterator alphaIt = alphaSamples.begin();

							if( (*inputChannelDataIt) != NULL )
							{
								ConstFloatSampleRange samples = sampleRange( (*inputChannelDataIt)->readable(), (*inputSampleOffsetsIt)->readable(), pixel - tileOrigin );
								std::vector<float>::const_iterator samplesIt = samples.begin();

								for( ; alphaIt != alphaSamples.end(); ++alphaIt, ++samplesIt )
								{
									if( (*alphaIt) != 0.0f )
									{
										result.push_back( *samplesIt );
									}
								}
							}
							else
							{
								for( ; alphaIt != alphaSamples.end(); ++alphaIt )
								{
									if( (*alphaIt) != 0.0f )
									{
										result.push_back( 0.0f );
									}
								}
							}
						}

						++inputAlphaDataIt;
					}
					else
					{
						if( (*inputChannelDataIt) != NULL )
						{
							ConstFloatSampleRange samples = sampleRange( (*inputChannelDataIt)->readable(), (*inputSampleOffsetsIt)->readable(), pixel - tileOrigin );

							result.insert( result.end(), samples.begin(), samples.end() );
						}
						else
						{
							const size_t numSamples = sampleCount( (*inputSampleOffsetsIt)->readable(), pixel - tileOrigin );
							result.insert( result.end(), numSamples, 0.0f );
						}
					}
				}
			}
		}
	}

	return resultData;
}

void DeepMerge::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashSampleOffsets( parent, context, h );

	const bool discardZeroAlpha = discardZeroAlphaPlug()->getValue();

	V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			const Box2i validBound = intersection( tileBound, (*it)->dataWindowPlug()->getValue() );
			h.append( validBound );

			ConstStringVectorDataPtr inChannelNamesPtr = (*it)->channelNamesPlug()->getValue();
			const std::vector<std::string> &inChannelNames = inChannelNamesPtr->readable();

			(*it)->dataWindowPlug()->hash( h );
			(*it)->sampleOffsetsPlug()->hash( h );

			if( discardZeroAlpha && std::find( inChannelNames.begin(), inChannelNames.end(), "A" ) != inChannelNames.end() )
			{
				h.append( (*it)->channelDataHash( "A", tileOrigin ) );
			}
		}
	}
}

IECore::ConstIntVectorDataPtr DeepMerge::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IntVectorDataPtr resultData = new IntVectorData;
	vector<int> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize(), 0 );

	const bool discardZeroAlpha = discardZeroAlphaPlug()->getValue();

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	for( ImagePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		if( (*it)->getInput<ValuePlug>() )
		{
			const Box2i validBound = intersection( tileBound, (*it)->dataWindowPlug()->getValue() );

			ConstStringVectorDataPtr inChannelNamesPtr = (*it)->channelNamesPlug()->getValue();
			const std::vector<std::string> &inChannelNames = inChannelNamesPtr->readable();

			ConstIntVectorDataPtr inSampleOffsets = (*it)->sampleOffsetsPlug()->getValue();
			ConstFloatVectorDataPtr inAlpha = NULL;

			if( discardZeroAlpha )
			{
				if( std::find( inChannelNames.begin(), inChannelNames.end(), "A" ) != inChannelNames.end() )
				{
					inAlpha = (*it)->channelData( "A", tileOrigin );
				}
				else
				{
					// If there is no alpha channel, and we want to discard zero alpha values,
					// then we can skip this entire loop, as all values would be discarded.
					continue;
				}
			}

			vector<int>::const_iterator sampleOffsetsIt = inSampleOffsets->readable().begin();
			vector<int>::const_iterator sampleOffsetsBegin = sampleOffsetsIt;
			vector<int>::iterator resultIt = result.begin();

			int lastSampleOffset = 0;
			int invalidOffset = 0;

			for( int y = tileBound.min.y; y < tileBound.max.y; ++y )
			{
				const bool yValid = y >= validBound.min.y && y < validBound.max.y;
				for( int x = tileBound.min.x; x < tileBound.max.x; ++x, ++sampleOffsetsIt, ++resultIt )
				{
					if( !yValid || x < validBound.min.x || x >= validBound.max.x )
					{
						invalidOffset += *sampleOffsetsIt - lastSampleOffset;
					}

					if( discardZeroAlpha )
					{
						ConstFloatSampleRange alphaRange = sampleRange( inAlpha->readable(), sampleOffsetsIt, sampleOffsetsBegin );
						for( vector<float>::const_iterator alphaIt = alphaRange.begin(); alphaIt != alphaRange.end(); ++alphaIt )
						{
							if( (*alphaIt) == 0.0f )
							{
								invalidOffset++;
							}
						}

					}

					*resultIt += (*sampleOffsetsIt) - invalidOffset;
					lastSampleOffset = *sampleOffsetsIt;
				}
			}
		}
	}

	return resultData;
}

void DeepMerge::hashDeepState( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashDeepState( parent, context, h );
}

int DeepMerge::computeDeepState( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::Messy;
}

