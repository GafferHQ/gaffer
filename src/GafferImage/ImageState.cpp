//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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

#include "boost/iterator/counting_iterator.hpp"

#include "IECore/BoxOps.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"

#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImageState.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ImageState );

namespace
{

struct CompareDepth
{
	vector<float>::const_iterator m_zSamples;
	vector<float>::const_iterator m_zBackSamples;
	bool hasZBack;

	CompareDepth( const vector<float>::const_iterator &zSamples )
	: m_zSamples( zSamples ), hasZBack( false )
	{}

	CompareDepth( const vector<float>::const_iterator &zSamples, const vector<float>::const_iterator &zBackSamples )
	: m_zSamples( zSamples ), m_zBackSamples( zBackSamples ), hasZBack( true )
	{}

	void addZBack( const vector<float>::const_iterator &zBackSamples )
	{
		m_zBackSamples = zBackSamples;
		hasZBack = true;
	}

	bool operator()( int a, int b ) const
	{
		if( m_zSamples[a] == m_zSamples[b] && hasZBack )
		{
			return std::max( m_zSamples[a], m_zBackSamples[a] ) < std::max( m_zSamples[b], m_zBackSamples[b] );
		}
		else
		{
			return m_zSamples[a] < m_zSamples[b];
		}
	}
};

class SampleMerge
{
	public :
		SampleMerge( CompoundObjectPtr resultData );

		void addPointSample( const float z, const int sampleId );
		void addVolumeSample( const float z, const float zBack, const int sampleId );
		void endPixel();

	private :

		enum SampleType
		{
			None = 0,
			Point,
			Volume,
			Unknown
		};

		void addOpenSample( const float z, const float zBack, const int sampleId );

		void closeOpenSamples( const float z );
		void closeOpenSamples();

		void addSplitSampleContributions( const float z, const float zBack );
		void addSampleContribution( const int sampleId, const float contribution );

		void startSample( const float z, const SampleType type = Unknown );
		void endSample( const float zBack );

		FloatVectorDataPtr zData;
		FloatVectorDataPtr zBackData;
		IntVectorDataPtr sampleOffsetsData;
		IntVectorDataPtr contributionIdsData;
		FloatVectorDataPtr contributionAmountsData;
		IntVectorDataPtr contributionOffsetsData;

		vector<float> openFronts;
		vector<float> openBacks;
		vector<int> openIds;

		SampleType inSample;
		float inSampleZ;
};

SampleMerge::SampleMerge( CompoundObjectPtr resultData )
{
	 zData = resultData->member<FloatVectorData>( ImageState::sampleMergingZName, false );
	 zBackData = resultData->member<FloatVectorData>( ImageState::sampleMergingZBackName, false );
	 sampleOffsetsData = resultData->member<IntVectorData>( ImageState::sampleMergingSampleOffsetsName, false );
	 contributionIdsData = resultData->member<IntVectorData>( ImageState::sampleMergingSampleContributionIdsName, false );
	 contributionAmountsData = resultData->member<FloatVectorData>( ImageState::sampleMergingSampleContributionAmountsName, false );
	 contributionOffsetsData = resultData->member<IntVectorData>( ImageState::sampleMergingSampleContributionOffsetsName, false );

	 inSample = None;
}

void SampleMerge::addPointSample( const float z, const int sampleId )
{
	if( ( inSample == Point || inSample == Unknown ) && z == inSampleZ )
	{
		addSampleContribution( sampleId, 1.0 );
		inSample = Point;
	}
	else
	{
		closeOpenSamples( z );
		if( inSample == None || z != inSampleZ )
		{
			startSample( z, Point );
		}
		else
		{
			inSample = Point;
			inSampleZ = z;
		}

		addSampleContribution( sampleId, 1.0 );
	}
}

void SampleMerge::addSampleContribution( const int sampleId, const float contribution )
{
	contributionIdsData->writable().push_back( sampleId );
	contributionAmountsData->writable().push_back( contribution );
}

void SampleMerge::addVolumeSample( const float z, const float zBack, const int sampleId )
{
	if( ( inSample == Volume || inSample == Unknown ) && inSampleZ == z )
	{
		addOpenSample( z, std::max( z, zBack ), sampleId );
	}
	else
	{
		closeOpenSamples( z );
		startSample( z, Volume );
		addOpenSample( z, zBack, sampleId );
	}
}

void SampleMerge::startSample( const float z, const SampleType type )
{
	if( ( inSample == Unknown || inSample == type ) && z == inSampleZ )
	{
		inSample = type;
	}
	else
	{
		if( inSample != None )
		{
			endSample( z );
		}

		zData->writable().push_back( z );

		inSample = type;
		inSampleZ = z;
	}
}

void SampleMerge::closeOpenSamples( const float z )
{
	float nextFront = 0.0;

	if( inSample == Point )
	{
		nextFront = inSampleZ;
		endSample( inSampleZ );
	}

	if( openIds.size() && inSample == None )
	{
		startSample( nextFront );
	}

	while( openIds.size() && openBacks.back() <= z )
	{
		const float closeBack = openBacks.back();

		addSplitSampleContributions( inSampleZ, closeBack );

		while( openIds.size() && openBacks.back() == closeBack )
		{
			openFronts.pop_back();
			openBacks.pop_back();
			openIds.pop_back();
		}

		endSample( closeBack );
		nextFront = closeBack;

		if( openIds.size() )
		{
			startSample( closeBack );
		}
	}

	if( openIds.size() )
	{
		if( inSampleZ != z )
		{
			addSplitSampleContributions( inSampleZ, z );
			endSample( z );
		}
	}
}

void SampleMerge::addSplitSampleContributions( const float z, const float zBack )
{
	vector<float>::const_iterator frontIt = openFronts.begin();
	vector<float>::const_iterator backIt = openBacks.begin();
	vector<int>::const_iterator idIt = openIds.begin();

	for( ; idIt != openIds.end(); ++frontIt, ++backIt, ++idIt )
	{
		const float contribution = ( zBack - z ) / ( (*backIt) - (*frontIt) );
		addSampleContribution( *idIt, contribution );
	}
}

void SampleMerge::closeOpenSamples()
{
	closeOpenSamples( numeric_limits<float>::max() );
}

void SampleMerge::endSample( const float zBack )
{
	if( inSample != None )
	{
		zBackData->writable().push_back( zBack );
		contributionOffsetsData->writable().push_back( contributionIdsData->readable().size() );

		inSample = None;
	}
}

void SampleMerge::endPixel()
{
	closeOpenSamples();
	sampleOffsetsData->writable().push_back( zData->readable().size() );
}

void SampleMerge::addOpenSample( const float z, const float zBack, const int sampleId )
{
	int index = 0;

	for( vector<float>::const_iterator it = openBacks.begin(); it != openBacks.end(); ++it, ++index )
	{
		if( zBack > *it )
		{
			break;
		}
	}

	openFronts.insert( openFronts.begin() + index, z );
	openBacks.insert( openBacks.begin() + index, zBack );
	openIds.insert( openIds.begin() + index, sampleId );
}

};

const IECore::InternedString ImageState::sampleMergingZName = "Z";
const IECore::InternedString ImageState::sampleMergingZBackName = "ZBack";
const IECore::InternedString ImageState::sampleMergingSampleOffsetsName = "sampleOffsets";
const IECore::InternedString ImageState::sampleMergingSampleContributionIdsName = "sampleContributionIds";
const IECore::InternedString ImageState::sampleMergingSampleContributionAmountsName = "sampleContributionAmounts";
const IECore::InternedString ImageState::sampleMergingSampleContributionOffsetsName = "sampleContributionOffsets";

size_t ImageState::g_firstPlugIndex = 0;

ImageState::ImageState( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "deepState", Gaffer::Plug::In, ImagePlug::Tidy ) );

	addChild( new IntVectorDataPlug( "__sampleSorting", Gaffer::Plug::Out, ImagePlug::emptyTileSampleOffsets() ) );
	addChild( new CompoundObjectPlug( "__sampleMerging", Gaffer::Plug::Out, new IECore::CompoundObject ) );
	addChild( new FloatVectorDataPlug( "__sortedChannelData", Gaffer::Plug::Out, ImagePlug::emptyTile() ) );
	addChild( new FloatVectorDataPlug( "__tidyChannelData", Gaffer::Plug::Out, ImagePlug::emptyTile() ) );

	// We don't ever want to change these, so we make pass-through connections.
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
}

ImageState::~ImageState()
{
}

Gaffer::IntPlug *ImageState::deepStatePlug()
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *ImageState::deepStatePlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex );
}

Gaffer::IntVectorDataPlug *ImageState::sampleSortingPlug()
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex+1 );
}

const Gaffer::IntVectorDataPlug *ImageState::sampleSortingPlug() const
{
	return getChild<IntVectorDataPlug>( g_firstPlugIndex+1 );
}

Gaffer::CompoundObjectPlug *ImageState::sampleMergingPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex+2 );
}

const Gaffer::CompoundObjectPlug *ImageState::sampleMergingPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex+2 );
}

Gaffer::FloatVectorDataPlug *ImageState::sortedChannelDataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+3 );
}

const Gaffer::FloatVectorDataPlug *ImageState::sortedChannelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+3 );
}

Gaffer::FloatVectorDataPlug *ImageState::tidyChannelDataPlug()
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+4 );
}

const Gaffer::FloatVectorDataPlug *ImageState::tidyChannelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( g_firstPlugIndex+4 );
}


void ImageState::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->sampleOffsetsPlug() )
	{
		outputs.push_back( sampleSortingPlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
	}
	else if( input == inPlug()->channelDataPlug() )
	{
		outputs.push_back( sampleSortingPlug() );
		outputs.push_back( sampleMergingPlug() );
		outputs.push_back( sortedChannelDataPlug() );
		outputs.push_back( tidyChannelDataPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
	}
	else if( input == inPlug()->channelNamesPlug() )
	{
		outputs.push_back( sampleSortingPlug() );
		outputs.push_back( sortedChannelDataPlug() );
		outputs.push_back( tidyChannelDataPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == inPlug()->deepStatePlug() )
	{
		outputs.push_back( outPlug()->deepStatePlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
		outputs.push_back( sortedChannelDataPlug() );
		outputs.push_back( tidyChannelDataPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == sampleSortingPlug() )
	{
		outputs.push_back( sampleMergingPlug() );
	}
	else if( input == sampleMergingPlug() )
	{
		outputs.push_back( sortedChannelDataPlug() );
		outputs.push_back( tidyChannelDataPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == deepStatePlug() )
	{
		outputs.push_back( sortedChannelDataPlug() );
		outputs.push_back( tidyChannelDataPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
		outputs.push_back( outPlug()->deepStatePlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
	}
	else if( input == sortedChannelDataPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input == tidyChannelDataPlug() )
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void ImageState::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output == sampleSortingPlug() )
	{
		hashSampleSorting( output, context, h );
	}
	else if( output == sampleMergingPlug() )
	{
		hashSampleMerging( output, context, h );
	}
	else if( output == sortedChannelDataPlug() )
	{
		hashSortedChannelData( output, context, h );
	}
	else if( output == tidyChannelDataPlug() )
	{
		hashTidyChannelData( output, context, h );
	}
}

void ImageState::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	ImageProcessor::compute( output, context );

	if( output == sampleSortingPlug() )
	{
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

		static_cast<IntVectorDataPlug *>( output )->setValue( computeSampleSorting( tileOrigin ) );
	}
	else if( output == sampleMergingPlug() )
	{
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

		static_cast<CompoundObjectPlug *>( output )->setValue( computeSampleMerging( tileOrigin ) );
	}
	else if( output == sortedChannelDataPlug() )
	{
		const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

		static_cast<FloatVectorDataPlug *>( output )->setValue( computeSortedChannelData( channelName, tileOrigin, context ) );
	}
	else if( output == tidyChannelDataPlug() )
	{
		const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
		const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

		static_cast<FloatVectorDataPlug *>( output )->setValue( computeTidyChannelData( channelName, tileOrigin, context ) );
	}
}

IECore::MurmurHash ImageState::sampleSortingHash( const Imath::V2i &tileOrigin ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::tileOriginContextName, tileOrigin );
	Context::Scope scopedContext( tmpContext.get() );

	return sampleSortingPlug()->hash();
}

void ImageState::hashSampleSorting( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

	h.append( inPlug()->sampleOffsetsHash( tileOrigin ) );
	inPlug()->channelNamesPlug()->hash( h );
	h.append( inPlug()->channelDataHash( "Z", tileOrigin ) );
	h.append( inPlug()->channelDataHash( "ZBack", tileOrigin ) );
}

IECore::ConstIntVectorDataPtr ImageState::computeSampleSorting( const Imath::V2i &tileOrigin ) const
{
	ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const std::vector<std::string> &channelNames = channelNamesData->readable();

	const std::vector<int> &sampleOffsets = inPlug()->sampleOffsets( tileOrigin )->readable();

	boost::counting_iterator<int> begin( 0 ), end( sampleOffsets.back() );
	IntVectorDataPtr resultData = new IntVectorData( std::vector<int>( begin, end ) );

	if( std::find( channelNames.begin(), channelNames.end(), "Z" ) != channelNames.end() )
	{
		const std::vector<float> &zData = inPlug()->channelData( "Z", tileOrigin )->readable();

		CompareDepth compare( zData.begin() );

		if( std::find( channelNames.begin(), channelNames.end(), "ZBack" ) != channelNames.end() )
		{
			const std::vector<float> &zBackData = inPlug()->channelData( "ZBack", tileOrigin )->readable();
			compare.addZBack( zBackData.begin() );
		}

		std::vector<int> &result = resultData->writable();

		for( std::vector<int>::const_iterator sampleOffsetIt = sampleOffsets.begin(); sampleOffsetIt != sampleOffsets.end(); ++sampleOffsetIt )
		{
			IntSampleRange sortSamples = sampleRange( result, sampleOffsetIt, sampleOffsets.begin() );
			std::sort( sortSamples.begin(), sortSamples.end(), compare );
		}
	}

	return resultData;
}

IECore::ConstIntVectorDataPtr ImageState::sampleSorting( const Imath::V2i &tileOrigin ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::tileOriginContextName, tileOrigin );
	Context::Scope scopedContext( tmpContext.get() );

	return sampleSortingPlug()->getValue();
}

IECore::MurmurHash ImageState::sampleMergingHash( const Imath::V2i &tileOrigin ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::tileOriginContextName, tileOrigin );
	Context::Scope scopedContext( tmpContext.get() );

	return sampleMergingPlug()->hash();
}

void ImageState::hashSampleMerging( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

	h.append( inPlug()->channelDataHash( "Z", tileOrigin ) );
	h.append( inPlug()->channelDataHash( "ZBack", tileOrigin ) );
	inPlug()->channelNamesPlug()->hash( h );
	h.append( sampleSortingHash( tileOrigin ) );
}

IECore::ConstCompoundObjectPtr ImageState::computeSampleMerging( const Imath::V2i &tileOrigin ) const
{
	ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const std::vector<std::string> &channelNames = channelNamesData->readable();

	ConstIntVectorDataPtr sampleOffsetsData = inPlug()->sampleOffsets( tileOrigin );

	CompoundObjectPtr resultData = new CompoundObject;

	FloatVectorDataPtr mergedZData = resultData->member<FloatVectorData>( ImageState::sampleMergingZName, false, true );
	FloatVectorDataPtr mergedZBackData = resultData->member<FloatVectorData>( ImageState::sampleMergingZBackName, false, true );
	IntVectorDataPtr mergedSampleOffsetsData = resultData->member<IntVectorData>( ImageState::sampleMergingSampleOffsetsName, false, true );

	// Which sorted samples are contributing to which tidy samples, and by how much.
	// mergedSampleContributionIds : The indices of the original samples that will
	//    be used in each new sample
	// mergedSampleContributionAmounts : The proportion of each of the original samples
	//    that will be used in the new samples
	// mergedSampleContributionOffsets : The offsets in the mergedSampleContribution
	//    vectors for each of the new samples
	IntVectorDataPtr mergedSampleContributionIdsData = resultData->member<IntVectorData>( ImageState::sampleMergingSampleContributionIdsName, false, true );
	FloatVectorDataPtr mergedSampleContributionAmountsData = resultData->member<FloatVectorData>( ImageState::sampleMergingSampleContributionAmountsName, false, true );
	IntVectorDataPtr mergedSampleContributionOffsetsData = resultData->member<IntVectorData>( ImageState::sampleMergingSampleContributionOffsetsName, false, true );

	SampleMerge sampleMerge = SampleMerge( resultData );

	// If there is no Z data, then all samples will be assumed to be point samples
	// with Z and ZBack values of 1.0
	if( std::find( channelNames.begin(), channelNames.end(), "Z" ) == channelNames.end() )
	{
		const vector<int> &sampleOffsets = sampleOffsetsData->readable();

		int currentSampleId = 0;

		for( vector<int>::const_iterator sampleOffsetsIt = sampleOffsets.begin(); sampleOffsetsIt != sampleOffsets.end(); ++sampleOffsetsIt )
		{
			for( ; currentSampleId < *sampleOffsetsIt ; ++currentSampleId )
			{
				sampleMerge.addPointSample( 1.0, currentSampleId );
			}

			sampleMerge.endPixel();
		}
	}
	else
	{
		ConstFloatVectorDataPtr zData = sortedChannelData( inPlug()->channelData( "Z", tileOrigin ), tileOrigin );

		ConstFloatVectorDataPtr zBackData;
		if( std::find( channelNames.begin(), channelNames.end(), "ZBack" ) != channelNames.end() )
		{
			zBackData = sortedChannelData( inPlug()->channelData( "ZBack", tileOrigin ), tileOrigin );
		}
		else
		{
			zBackData = zData;
		}

		const vector<float> &z = zData->readable();
		const vector<float> &zBack = zBackData->readable();
		const vector<int> &sampleOffsets = sampleOffsetsData->readable();

		int currentSampleId = 0;

		for( vector<int>::const_iterator sampleOffsetsIt = sampleOffsets.begin(); sampleOffsetsIt != sampleOffsets.end(); ++sampleOffsetsIt )
		{
			ConstFloatSampleRange zRange = sampleRange( z, sampleOffsetsIt, sampleOffsets.begin() );
			ConstFloatSampleRange zBackRange = sampleRange( zBack, sampleOffsetsIt, sampleOffsets.begin() );

			vector<float>::const_iterator zIt = zRange.begin();
			vector<float>::const_iterator zBackIt = zBackRange.begin();

			for( ; zIt != zRange.end(); ++zIt, ++zBackIt, ++currentSampleId )
			{
				if( *zIt == *zBackIt )
				{
					sampleMerge.addPointSample( *zIt, currentSampleId );
				}
				else
				{
					sampleMerge.addVolumeSample( *zIt, *zBackIt, currentSampleId );
				}
			}

			sampleMerge.endPixel();
		}
	}

	return resultData;
}

ConstCompoundObjectPtr ImageState::sampleMerging( const Imath::V2i &tileOrigin ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::tileOriginContextName, tileOrigin );
	Context::Scope scopedContext( tmpContext.get() );

	return sampleMergingPlug()->getValue();
}

IECore::MurmurHash ImageState::sortedChannelDataHash( const std::string &channelName, const Imath::V2i &tileOrigin ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	tmpContext->set( ImagePlug::tileOriginContextName, tileOrigin );
	Context::Scope scopedContext( tmpContext.get() );

	return sortedChannelDataPlug()->hash();
}

void ImageState::hashSortedChannelData( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

	h.append( ImagePlug::Tidy );

	hashChannelData( channelName, tileOrigin, ImagePlug::Sorted, NULL, context, h, false );
}

IECore::ConstFloatVectorDataPtr ImageState::computeSortedChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	return computeChannelData( channelName, tileOrigin, ImagePlug::Sorted, context, NULL, false );
}

IECore::ConstFloatVectorDataPtr ImageState::sortedChannelData( const std::string &channelName, const Imath::V2i &tileOrigin ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	tmpContext->set( ImagePlug::tileOriginContextName, tileOrigin );
	Context::Scope scopedContext( tmpContext.get() );

	return sortedChannelDataPlug()->getValue();
}

IECore::MurmurHash ImageState::tidyChannelDataHash( const std::string &channelName, const Imath::V2i &tileOrigin ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	tmpContext->set( ImagePlug::tileOriginContextName, tileOrigin );
	Context::Scope scopedContext( tmpContext.get() );

	return tidyChannelDataPlug()->hash();
}

void ImageState::hashTidyChannelData( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

	h.append( ImagePlug::Tidy );

	hashChannelData( channelName, tileOrigin, ImagePlug::Tidy, NULL, context, h, false );
}

IECore::ConstFloatVectorDataPtr ImageState::computeTidyChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	return computeChannelData( channelName, tileOrigin, ImagePlug::Tidy, context, NULL, false );
}

IECore::ConstFloatVectorDataPtr ImageState::tidyChannelData( const std::string &channelName, const Imath::V2i &tileOrigin ) const
{
	ContextPtr tmpContext = new Context( *Context::current(), Context::Borrowed );
	tmpContext->set( ImagePlug::channelNameContextName, channelName );
	tmpContext->set( ImagePlug::tileOriginContextName, tileOrigin );
	Context::Scope scopedContext( tmpContext.get() );

	return tidyChannelDataPlug()->getValue();
}

void ImageState::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashChannelData( output, context, h );

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const std::string channelName = context->get<std::string>( ImagePlug::channelNameContextName );

	deepStatePlug()->hash( h );

	const int deepState = deepStatePlug()->getValue();

	hashChannelData( channelName, tileOrigin, deepState, output, context, h, true );
}

IECore::ConstFloatVectorDataPtr ImageState::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const int deepState = outPlug()->deepStatePlug()->getValue();

	return computeChannelData( channelName, tileOrigin, deepState, context, parent, true );
}

void ImageState::hashChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const int deepState, const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h, const bool useCached ) const
{

	const int inDeepState = inPlug()->deepStatePlug()->getValue();

	if( inDeepState == deepState )
	{
		// If we aren't going to be changing the state, pass through the hash
		h = inPlug()->channelDataHash( channelName, tileOrigin );
		return;
	}

	inPlug()->deepStatePlug()->hash( h );

	inPlug()->channelNamesPlug()->hash( h );
	sampleMergingPlug()->hash( h );
	h.append( inPlug()->channelDataHash( channelName, tileOrigin ) );

	int deepStateChange = ( deepState | inDeepState ) - inDeepState;

	ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const std::vector<std::string> &channelNames = channelNamesData->readable();

	const std::string associatedAlpha = channelAlpha( channelName, channelNames );
	const bool isAlpha = associatedAlpha == "" && channelName[0] == 'A';
	const bool isZ = associatedAlpha == "" && channelName[0] == 'Z';

	if( deepStateChange & ImagePlug::Sorted )
	{
		if( isAlpha && useCached )
		{
			h.append( sortedChannelDataHash( channelName, tileOrigin ) );
		}

		if( deepStateChange == ImagePlug::Sorted )
		{
			return;
		}
		else
		{
			deepStateChange -= ImagePlug::Sorted;
		}
	}

	if( deepStateChange & ImagePlug::NonOverlapping )
	{
		if( isZ )
		{
			h.append( sampleMergingHash( tileOrigin ) );
		}
		else if( isAlpha && useCached )
		{
			h.append( tidyChannelDataHash( channelName, tileOrigin ) );
		}
		else if( associatedAlpha != "" )
		{
			h.append( sortedChannelDataHash( associatedAlpha, tileOrigin ) );
		}

		if( deepStateChange == ImagePlug::NonOverlapping )
		{
			return;
		}
		else
		{
			deepStateChange -= ImagePlug::NonOverlapping;
		}
	}

	if( deepStateChange & ImagePlug::SingleSample )
	{
		if( isZ )
		{
			h.append( tidyChannelDataHash( "Z", tileOrigin ) );
			h.append( tidyChannelDataHash( "ZBack", tileOrigin ) );
			h.append( tidyChannelDataHash( "A", tileOrigin ) );
		}
		else if( !isAlpha )
		{
			h.append( tidyChannelDataHash( associatedAlpha, tileOrigin ) );
		}

		if( deepStateChange == ImagePlug::SingleSample )
		{
			return;
		}
		else
		{
			deepStateChange -= ImagePlug::SingleSample;
		}
	}

	return;
}

IECore::ConstFloatVectorDataPtr ImageState::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const int deepState, const Gaffer::Context *context, const ImagePlug *parent, const bool useCached ) const
{
	ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
	const std::vector<std::string> &channelNames = channelNamesData->readable();

	const int inDeepState = inPlug()->deepStatePlug()->getValue();
	int deepStateChange = ( deepState | inDeepState ) - inDeepState;

	const std::string associatedAlpha = channelAlpha( channelName, channelNames );

	const bool isAlpha = associatedAlpha == "" && channelName[0] == 'A';
	const bool isZ = associatedAlpha == "" && channelName[0] == 'Z';

	ConstCompoundObjectPtr sampleMergingData = sampleMerging( tileOrigin );

	ConstFloatVectorDataPtr inData = inPlug()->channelData( channelName, tileOrigin );


	if( deepStateChange & ImagePlug::Sorted )
	{
		ConstFloatVectorDataPtr sortedData;

		if( isAlpha && useCached )
		{
			sortedData = sortedChannelData( channelName, tileOrigin );
		}
		else
		{
			sortedData = sortedChannelData( inData, tileOrigin );
		}

		if( deepStateChange == ImagePlug::Sorted )
		{
			return sortedData;
		}
		else
		{
			deepStateChange -= ImagePlug::Sorted;
			inData = sortedData;
		}
	}

	if( deepStateChange & ImagePlug::NonOverlapping )
	{
		ConstFloatVectorDataPtr tidyData;

		if( isZ )
		{
			tidyData = sampleMerging( tileOrigin )->member<FloatVectorData>( channelName, false );
		}
		else if( isAlpha && useCached )
		{
			tidyData = tidyChannelData( channelName, tileOrigin );
		}
		else
		{
			ConstFloatVectorDataPtr alphaData;
			if( associatedAlpha != "" )
			{
				alphaData = sortedChannelData( associatedAlpha, tileOrigin );
			}
			else
			{
				alphaData = inData;
			}


			tidyData = tidyChannelData( inData, alphaData, tileOrigin );

		}

		if( deepStateChange == ImagePlug::NonOverlapping )
		{
			return tidyData;
		}
		else
		{
			deepStateChange -= ImagePlug::NonOverlapping;
			inData = tidyData;
		}
	}

	if( deepStateChange & ImagePlug::SingleSample )
	{
		ConstFloatVectorDataPtr flatData;

		if( isZ )
		{
			ConstFloatVectorDataPtr zData = tidyChannelData( "Z", tileOrigin );

			ConstFloatVectorDataPtr zBackData;
			if( std::find( channelNames.begin(), channelNames.end(), "ZBack" ) != channelNames.end() )
			{
				zBackData = tidyChannelData( "ZBack", tileOrigin );
			}
			else
			{
				zBackData = zData;
			}

			ConstFloatVectorDataPtr alphaData;
			if( std::find( channelNames.begin(), channelNames.end(), "A" ) != channelNames.end() )
			{
				alphaData = tidyChannelData( "A", tileOrigin );
			}
			else
			{
				alphaData = new FloatVectorData;
			}

			flatData = flatZData( zData, zBackData, alphaData, channelName, tileOrigin );
		}
		else if( isAlpha )
		{
			flatData = flatChannelData( inData, inData, tileOrigin );
		}
		else
		{
			ConstFloatVectorDataPtr alphaData;

			if( associatedAlpha != "" )
			{
				alphaData = tidyChannelData( associatedAlpha, tileOrigin );
			}
			else
			{
				alphaData = inData;
			}

			flatData = flatChannelData( inData, alphaData, tileOrigin );
		}

		if( deepStateChange == ImagePlug::SingleSample )
		{
			return flatData;
		}
		else
		{
			deepStateChange -= ImagePlug::SingleSample;
			inData = flatData;
		}
	}

	return inData;
}

void ImageState::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const int inDeepState = inPlug()->deepStatePlug()->getValue();
	const int outDeepState = outPlug()->deepStatePlug()->getValue();

	if( inDeepState == outDeepState || outDeepState == ImagePlug::Sorted )
	{
		// If we aren't going to be changing the state, pass through the hash
		h = inPlug()->sampleOffsetsPlug()->hash();
		return;
	}

	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );

	ImageProcessor::hashSampleOffsets( parent, context, h );

	deepStatePlug()->hash( h );

	inPlug()->sampleOffsetsPlug()->hash( h );

	h.append( inPlug()->channelDataHash( "Z", tileOrigin ) );
	h.append( inPlug()->channelDataHash( "ZBack", tileOrigin ) );
}

IECore::ConstIntVectorDataPtr ImageState::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const int inDeepState = inPlug()->deepStatePlug()->getValue();
	const int outDeepState = outPlug()->deepStatePlug()->getValue();

	if( inDeepState == outDeepState || outDeepState == ImagePlug::Sorted )
	{
		return inPlug()->sampleOffsets( tileOrigin );
	}
	else if( outDeepState == ImagePlug::Tidy )
	{
		return sampleMerging( tileOrigin )->member<IntVectorData>( ImageState::sampleMergingSampleOffsetsName, false );
	}
	else
	{
		return ImagePlug::flatTileSampleOffsets();
	}
}

void ImageState::hashDeepState( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const int inDeepState = inPlug()->deepStatePlug()->getValue();
	const int requestedDeepState = deepStatePlug()->getValue();
	const int deepState = inDeepState | requestedDeepState;

	if( deepState == inDeepState )
	{
		// If we aren't going to be changing the state, pass through the hash
		h = inPlug()->deepStatePlug()->hash();
		return;
	}

	ImageProcessor::hashDeepState( parent, context, h );

	deepStatePlug()->hash( h );
}

int ImageState::computeDeepState( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const int inDeepState = inPlug()->deepStatePlug()->getValue();
	const int requestedDeepState = deepStatePlug()->getValue();
	const int deepState = inDeepState | requestedDeepState;

	if( deepState & ImagePlug::SingleSample )
	{
		return ImagePlug::Flat;
	}
	else if( deepState & ImagePlug::NonOverlapping )
	{
		return ImagePlug::Tidy;
	}
	else
	{
		return ImagePlug::Sorted;
	}
}

IECore::ConstFloatVectorDataPtr ImageState::sortedChannelData( ConstFloatVectorDataPtr data, const Imath::V2i &tileOrigin ) const
{
	FloatVectorDataPtr sortedData = new FloatVectorData;
	std::vector<float> &sorted = sortedData->writable();

	const std::vector<float> &in = data->readable();
	sorted.resize( in.size() );

	ConstIntVectorDataPtr sampleSortingData = sampleSorting( tileOrigin );
	const std::vector<int> &sampleSortingVec = sampleSortingData->readable();

	std::vector<int>::const_iterator sampleSortingIt;
	std::vector<float>::iterator sortedIt;

	for( sampleSortingIt = sampleSortingVec.begin(), sortedIt = sorted.begin(); sortedIt != sorted.end(); ++sampleSortingIt, ++sortedIt )
	{
		*sortedIt = in[*sampleSortingIt];
	}

	return sortedData;
}

IECore::ConstFloatVectorDataPtr ImageState::tidyChannelData( ConstFloatVectorDataPtr data, ConstFloatVectorDataPtr alphaData, const Imath::V2i &tileOrigin ) const
{
	static const float MAX = numeric_limits<float>::max();

	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();

	const vector<float> &dataVec = data->readable();
	const vector<float> &alphaVec = alphaData->readable();

	ConstCompoundObjectPtr sampleMergingData = sampleMerging( tileOrigin );

	ConstIntVectorDataPtr mergedSampleContributionIdsData = sampleMergingData->member<IntVectorData>( ImageState::sampleMergingSampleContributionIdsName, false );
	ConstFloatVectorDataPtr mergedSampleContributionAmountsData = sampleMergingData->member<FloatVectorData>( ImageState::sampleMergingSampleContributionAmountsName, false );
	ConstIntVectorDataPtr mergedSampleContributionOffsetsData = sampleMergingData->member<IntVectorData>( ImageState::sampleMergingSampleContributionOffsetsName, false );

	const vector<int> &mergedSampleContributionIds = mergedSampleContributionIdsData->readable();
	const vector<float> &mergedSampleContributionAmounts = mergedSampleContributionAmountsData->readable();
	const vector<int> &mergedSampleContributionOffsets = mergedSampleContributionOffsetsData->readable();

	vector<int>::const_iterator mergedSampleContributionOffsetsIt = mergedSampleContributionOffsets.begin();

	for( ; mergedSampleContributionOffsetsIt != mergedSampleContributionOffsets.end() ; ++mergedSampleContributionOffsetsIt )
	{
		ConstFloatSampleRange sampleContributionAmountsRange = sampleRange( mergedSampleContributionAmounts, mergedSampleContributionOffsetsIt, mergedSampleContributionOffsets.begin() );
		ConstIntSampleRange sampleContributionIdsRange = sampleRange( mergedSampleContributionIds, mergedSampleContributionOffsetsIt, mergedSampleContributionOffsets.begin() );

		if( sampleContributionIdsRange.begin() == sampleContributionIdsRange.end() )
		{
			continue;
		}

		float newSampleValue = 0.0;
		float newSampleAlpha = 0.0;

		vector<int>::const_iterator idsIt = sampleContributionIdsRange.begin();
		vector<float>::const_iterator amountsIt = sampleContributionAmountsRange.begin();

		int averagedSamples = 1;

		for( ; idsIt != sampleContributionIdsRange.end(); ++idsIt, ++amountsIt )
		{
			const float sampleValue = dataVec[*idsIt];
			const float sampleAlpha = max( 0.0f, min( alphaVec[*idsIt], 1.0f ) );
			const float sampleAmount = *amountsIt;

			float splitAlpha;
			float splitValue;

			if( sampleAlpha == 0.0f )
			{
				splitAlpha = 0.0f;
				splitValue = sampleValue * sampleAmount;
			}
			else
			{
				splitAlpha = -expm1( sampleAmount * log1p( -sampleAlpha ) );
				splitValue = (splitAlpha / sampleAlpha ) * sampleValue;
			}

			float mergedAlpha = newSampleAlpha + splitAlpha - ( newSampleAlpha * splitAlpha );
			float mergedValue;

			if( newSampleAlpha == 1.0f && splitAlpha == 1.0f )
			{
				mergedValue = ( ( newSampleValue * averagedSamples ) + splitValue ) / ( averagedSamples + 1 );
				mergedAlpha = 1.0f;
				averagedSamples++;
			}
			else if( splitAlpha == 1.0f )
			{
				mergedValue = splitValue;
				mergedAlpha = splitAlpha;
			}
			else if( newSampleAlpha == 1.0f )
			{
				mergedValue = newSampleValue;
				mergedAlpha = newSampleAlpha;
			}
			else
			{
				float newSampleU = -log1p( -newSampleAlpha );
				float newSampleV = ( newSampleU < newSampleAlpha * MAX ) ? newSampleU / newSampleAlpha : 1.0f;
				float splitU = -log1p( -splitAlpha );
				float splitV = ( splitU < splitAlpha * MAX ) ? splitU / splitAlpha : 1.0f;

				float u = newSampleU + splitU;
				float w = ( u > 1 || mergedAlpha < u * MAX ) ? mergedAlpha / u : 1.0f;

				mergedValue = ( newSampleValue * newSampleV + splitValue * splitV ) * w;
			}

			newSampleAlpha = mergedAlpha;
			newSampleValue = mergedValue;
		}

		result.push_back( newSampleValue );
	}

	return resultData;
}

IECore::ConstFloatVectorDataPtr ImageState::flatChannelData( ConstFloatVectorDataPtr valueData, ConstFloatVectorDataPtr alphaData, const Imath::V2i &tileOrigin ) const
{
	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();

	ConstCompoundObjectPtr sampleMergingData = sampleMerging( tileOrigin );

	ConstIntVectorDataPtr sampleOffsetsData = sampleMergingData->member<IntVectorData>( ImageState::sampleMergingSampleOffsetsName, false );
	const vector<int> &sampleOffsets = sampleOffsetsData->readable();

	const vector<float> &valueVec = valueData->readable();
	const vector<float> &alphaVec = alphaData->readable();

	for( vector<int>::const_iterator sampleOffsetsIt = sampleOffsets.begin(); sampleOffsetsIt != sampleOffsets.end(); ++sampleOffsetsIt )
	{
		float value = 0.0;
		float alpha = 0.0;

		ConstFloatSampleRange valueRange = sampleRange( valueVec, sampleOffsetsIt, sampleOffsets.begin() );
		ConstFloatSampleRange alphaRange = sampleRange( alphaVec, sampleOffsetsIt, sampleOffsets.begin() );

		vector<float>::const_iterator valueIt = valueRange.begin();
		vector<float>::const_iterator alphaIt = alphaRange.begin();

		for( ; valueIt != valueRange.end(); ++valueIt, ++alphaIt )
		{
			value = value + ( (*valueIt) * ( 1 - alpha ) );
			alpha = alpha + (*alphaIt) - ( alpha * (*alphaIt) );
		}

		result.push_back( value );
	}

	return resultData;
}

IECore::ConstFloatVectorDataPtr ImageState::flatZData( ConstFloatVectorDataPtr zData, ConstFloatVectorDataPtr zBackData, ConstFloatVectorDataPtr alphaData, const std::string &channelName, const Imath::V2i &tileOrigin ) const
{
	FloatVectorDataPtr resultData = new FloatVectorData;
	vector<float> &result = resultData->writable();

	ConstCompoundObjectPtr sampleMergingData = sampleMerging( tileOrigin );

	ConstIntVectorDataPtr sampleOffsetsData = sampleMergingData->member<IntVectorData>( ImageState::sampleMergingSampleOffsetsName, false );
	const vector<int> &sampleOffsets = sampleOffsetsData->readable();

	const vector<float> &z = zData->readable();
	const vector<float> &zBack = zBackData->readable();
	const vector<float> &alpha = alphaData->readable();

	const bool hasAlpha = !alpha.empty();

	for( vector<int>::const_iterator sampleOffsetsIt = sampleOffsets.begin(); sampleOffsetsIt != sampleOffsets.end(); ++sampleOffsetsIt )
	{
		ConstFloatSampleRange zRange = sampleRange( z, sampleOffsetsIt, sampleOffsets.begin() );
		float value = 0.0f;

		if( zRange.begin() == zRange.end() )
		{
			value = numeric_limits<float>::max();
		}
		else
		{
			if( channelName == "Z" )
			{
				value = zRange.front();
			}
			else if( channelName == "ZBack" )
			{
				bool hasValue = false;

				if( hasAlpha )
				{
					ConstFloatSampleRange alphaRange = sampleRange( alpha, sampleOffsetsIt, sampleOffsets.begin() );

					vector<float>::const_iterator zIt = zRange.begin();
					vector<float>::const_iterator alphaIt = alphaRange.begin();

					// Look for a sample with an alpha of 1.0f. If found, set ZBack to
					// the front of this sample
					for( ; zIt != zRange.end(); ++zIt, ++alphaIt )
					{
						if( *alphaIt >= 1.0f )
						{
							value = *zIt;
							hasValue = true;
							break;
						}
					}
				}

				// If the alpha never hits 1.0f, then use the back of the last sample as zBack
				if( !hasValue )
				{
					value = sampleRange( zBack, sampleOffsetsIt, sampleOffsets.begin() ).back();
				}
			}
		}

		result.push_back( value );
	}

	return resultData;
}