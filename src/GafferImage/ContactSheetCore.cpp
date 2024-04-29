//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, John Haddon. All rights reserved.
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

#include "GafferImage/ContactSheetCore.h"

#include "GafferImage/Crop.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/Resample.h"

#include "IECore/NullObject.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

// Note on terminology
// -------------------
//
// For the user, we refer to each image in the contact sheet as a "tile", since that
// seems the most intuitive term. But internally, GafferImage tiles to refer to the
// squares that an image is broken into to support multi-threading. To avoid overloading
// the terms in this file, we refer to ContactSheet tiles as "cells".

namespace
{

struct CoverageData : public IECore::Data
{

	CoverageData( const Format &format, const vector<Box2f> &cells )
		:	m_format( format ),
			m_tileWindow(
				ImagePlug::tileIndex( m_format.getDisplayWindow().min ),
				ImagePlug::tileIndex( m_format.getDisplayWindow().max ) + V2i( 1 )
			)
	{
		const size_t numTiles = ( m_tileWindow.size().x ) * ( m_tileWindow.size().y  );
		m_coverage.resize( numTiles );

		for( size_t cellIndex = 0; cellIndex < cells.size(); ++cellIndex )
		{
			Box2i cell(
				ImagePlug::tileIndex( cells[cellIndex].min ),
				ImagePlug::tileIndex( cells[cellIndex].max ) + V2i( 1 )
			);
			cell = BufferAlgo::intersection( cell, m_tileWindow );

			V2i tileIndex;
			for( tileIndex.y = cell.min.y; tileIndex.y < cell.max.y; ++tileIndex.y )
			{
				for( tileIndex.x = cell.min.x; tileIndex.x < cell.max.x; ++tileIndex.x )
				{
					if( !BufferAlgo::contains( m_tileWindow, tileIndex ) )
					{
						continue;
					}
					m_coverage[BufferAlgo::index( tileIndex, m_tileWindow )].push_back( cellIndex );
				}
			}
		}
	}

	const Format &format() const
	{
		return m_format;
	}

	const vector<int> &tileCells( const V2i &tileOrigin ) const
	{
		const V2i tileIndex = ImagePlug::tileIndex( tileOrigin );
		return m_coverage[BufferAlgo::index( tileIndex, m_tileWindow )];
	}

	private :

		const Format m_format;
		const Box2i m_tileWindow; // Tile indices, not pixel indices
		vector<vector<int>> m_coverage;

};

IE_CORE_DECLAREPTR( CoverageData );

} // namespace

GAFFER_NODE_DEFINE_TYPE( ContactSheetCore );

size_t ContactSheetCore::g_firstPlugIndex = 0;

ContactSheetCore::ContactSheetCore( const std::string &name )
	:	FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new FormatPlug( "format" ) );
	addChild( new Box2fVectorDataPlug( "tiles" ) );
	addChild( new StringPlug( "tileVariable", Plug::In, "contactSheet:tileIndex" ) );
	addChild( new StringPlug( "filter" ) );
	addChild( new ObjectPlug( "__coverage", Plug::Out, NullObject::defaultNullObject() ) );
	addChild( new M33fPlug( "__resampleMatrix", Plug::Out ) );
	addChild( new ImagePlug( "__resampledIn" ) );
	addChild( new Crop( "__crop" ) );
	addChild( new Resample( "__resample" ) );

	crop()->areaSourcePlug()->setValue( Crop::AreaSource::DisplayWindow );
	crop()->inPlug()->setInput( inPlug() );
	resample()->inPlug()->setInput( crop()->outPlug() );
	resample()->matrixPlug()->setInput( resampleMatrixPlug() );
	resample()->filterPlug()->setInput( filterPlug() );
	resampledInPlug()->setInput( resample()->outPlug() );
}

ContactSheetCore::~ContactSheetCore()
{
}

FormatPlug *ContactSheetCore::formatPlug()
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

const FormatPlug *ContactSheetCore::formatPlug() const
{
	return getChild<FormatPlug>( g_firstPlugIndex );
}

Gaffer::Box2fVectorDataPlug *ContactSheetCore::tilesPlug()
{
	return getChild<Box2fVectorDataPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::Box2fVectorDataPlug *ContactSheetCore::tilesPlug() const
{
	return getChild<Box2fVectorDataPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *ContactSheetCore::tileVariablePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *ContactSheetCore::tileVariablePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *ContactSheetCore::filterPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *ContactSheetCore::filterPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::ObjectPlug *ContactSheetCore::coveragePlug()
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::ObjectPlug *ContactSheetCore::coveragePlug() const
{
	return getChild<ObjectPlug>( g_firstPlugIndex + 4 );
}

Gaffer::M33fPlug *ContactSheetCore::resampleMatrixPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::M33fPlug *ContactSheetCore::resampleMatrixPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex + 5 );
}

ImagePlug *ContactSheetCore::resampledInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 6 );
}

const ImagePlug *ContactSheetCore::resampledInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 6 );
}

Crop *ContactSheetCore::crop()
{
	return getChild<Crop>( g_firstPlugIndex + 7 );
}

const Crop *ContactSheetCore::crop() const
{
	return getChild<Crop>( g_firstPlugIndex + 7 );
}

Resample *ContactSheetCore::resample()
{
	return getChild<Resample>( g_firstPlugIndex + 8 );
}

const Resample *ContactSheetCore::resample() const
{
	return getChild<Resample>( g_firstPlugIndex + 8 );
}

void ContactSheetCore::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if( formatPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->formatPlug() );
	}

	if( input == outPlug()->formatPlug() )
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if(
		input == inPlug()->viewNamesPlug() ||
		input == inPlug()->channelNamesPlug() ||
		input == tilesPlug() ||
		input == tileVariablePlug()
	)
	{
		outputs.push_back( outPlug()->channelNamesPlug() );
	}

	if( input == formatPlug() || input == tilesPlug() )
	{
		outputs.push_back( coveragePlug() );
	}

	if( input == tilesPlug() || input == tileVariablePlug() )
	{
		outputs.push_back( resampleMatrixPlug() );
	}

	if(
		input == coveragePlug() ||
		input == resampledInPlug()->viewNamesPlug() ||
		input == resampledInPlug()->channelNamesPlug() ||
		input == resampledInPlug()->channelDataPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void ContactSheetCore::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hash( output, context, h );

	if( output == coveragePlug() )
	{
		formatPlug()->hash( h );
		tilesPlug()->hash( h );
	}
	else if( output == resampleMatrixPlug() )
	{
		inPlug()->formatPlug()->hash( h );
		tilesPlug()->hash( h );
		h.append( context->variableHash( tileVariablePlug()->getValue() ) );
	}
}

void ContactSheetCore::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == coveragePlug() )
	{
		static_cast<ObjectPlug *>( output )->setValue(
			new CoverageData( formatPlug()->getValue(), tilesPlug()->getValue()->readable() )
		);
	}
	else if( output == resampleMatrixPlug() )
	{
		const Format inFormat = inPlug()->formatPlug()->getValue();
		ConstBox2fVectorDataPtr cellsData = tilesPlug()->getValue();
		const int cellIndex = context->get<int>( tileVariablePlug()->getValue() );
		const Box2f &cell = cellsData->readable()[cellIndex];

		// Scale that would fit image exactly to the content area, but not
		// preserving aspect ratio.
		const V2f inSize( inFormat.getDisplayWindow().size() );
		const V2f distortScale = cell.size() / inSize;
		const float pixelAspectScale = 1.0f / inFormat.getPixelAspect();
		// Scale that fits the whole image in the available space in the cell, while
		// preserving aspect ratio.
		V2f fitScale;
		if( distortScale.x * pixelAspectScale < distortScale.y )
		{
			fitScale = V2f( distortScale.x, distortScale.x * pixelAspectScale );
		}
		else
		{
			fitScale = V2f( distortScale.y / pixelAspectScale, distortScale.y );
		}

		const V2f fittedSize = inSize * fitScale;

		// Stick that into a matrix.

		M33f result;
		result.translate( cell.min + ( cell.size() - fittedSize ) / 2.0f );
		result.scale( fitScale );
		static_cast<M33fPlug *>( output )->setValue( result );
		return;
	}

	FlatImageProcessor::compute( output, context );
}

void ContactSheetCore::hashViewNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashViewNames( parent, context, h );
}

IECore::ConstStringVectorDataPtr ContactSheetCore::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::defaultViewNames();
}

void ContactSheetCore::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashFormat( parent, context, h );
	formatPlug()->hash( h );
}

GafferImage::Format ContactSheetCore::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return formatPlug()->getValue();
}

void ContactSheetCore::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashDataWindow( parent, context, h );
	outPlug()->formatPlug()->hash( h );
}

Imath::Box2i ContactSheetCore::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->formatPlug()->getValue().getDisplayWindow();
}

void ContactSheetCore::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = outPlug()->metadataPlug()->defaultHash();
}

IECore::ConstCompoundDataPtr ContactSheetCore::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return outPlug()->metadataPlug()->defaultValue();
}

void ContactSheetCore::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelNames( parent, context, h );

	const int numTiles = tilesPlug()->getValue()->readable().size();
	const InternedString tileVariable = tileVariablePlug()->getValue();

	Context::EditableScope scope( context );
	for( int tileIndex = 0; tileIndex < numTiles; ++tileIndex )
	{
		scope.set( tileVariable, &tileIndex );
		if( !ImageAlgo::viewIsValid( context, inPlug()->viewNames()->readable() ) )
		{
			continue;
		}
		inPlug()->channelNamesPlug()->hash( h );
	}
}

IECore::ConstStringVectorDataPtr ContactSheetCore::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	const int numTiles = tilesPlug()->getValue()->readable().size();
	const InternedString tileVariable = tileVariablePlug()->getValue();

	StringVectorDataPtr resultData = new StringVectorData;
	vector<string> &result = resultData->writable();

	Context::EditableScope scope( context );
	for( int tileIndex = 0; tileIndex < numTiles; ++tileIndex )
	{
		scope.set( tileVariable, &tileIndex );
		if( !ImageAlgo::viewIsValid( context, inPlug()->viewNames()->readable() ) )
		{
			continue;
		}
		ConstStringVectorDataPtr channelNamesData = inPlug()->channelNamesPlug()->getValue();
		for( const std::string &c : channelNamesData->readable() )
		{
			if ( std::find( result.begin(), result.end(), c ) == result.end() )
			{
				result.push_back( c );
			}
		}
	}

	return resultData;
}

void ContactSheetCore::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelData( parent, context, h );

	ConstCoverageDataPtr coverage;
	{
		ImagePlug::GlobalScope globalScope( context );
		coverage = boost::static_pointer_cast<const CoverageData>( coveragePlug()->getValue() );
	}

	const InternedString cellVariable( tileVariablePlug()->getValue() );
	const V2i tileOrigin = context->get<V2i>( ImagePlug::tileOriginContextName );
	const string &channelName = context->get<string>( ImagePlug::channelNameContextName );

	const Box2i tileBound = Box2i( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i outTileBound = BufferAlgo::intersection( tileBound, coverage->format().getDisplayWindow() );

	Context::EditableScope scope( context );
	for( const auto &cellIndex : coverage->tileCells( tileOrigin ) )
	{
		scope.set( cellVariable, &cellIndex );

		Box2i inDataWindow;
		{
			ImagePlug::GlobalScope globalScope( scope.context() );
			if(
				!ImageAlgo::viewIsValid( context, resampledInPlug()->viewNames()->readable() ) ||
				!ImageAlgo::channelExists( resampledInPlug(), channelName )
			)
			{
				continue;
			}
			inDataWindow = resampledInPlug()->dataWindowPlug()->getValue();
		}

		const Box2i inTileBound = BufferAlgo::intersection( outTileBound, inDataWindow );
		if( BufferAlgo::empty( inTileBound ) )
		{
			continue;
		}

		resampledInPlug()->channelDataPlug()->hash( h );
	}
}

IECore::ConstFloatVectorDataPtr ContactSheetCore::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstCoverageDataPtr coverage;
	{
		ImagePlug::GlobalScope globalScope( context );
		coverage = boost::static_pointer_cast<const CoverageData>( coveragePlug()->getValue() );
	}

	const InternedString cellVariable( tileVariablePlug()->getValue() );

	const Box2i tileBound = Box2i( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	const Box2i outTileBound = BufferAlgo::intersection( tileBound, coverage->format().getDisplayWindow() );

	FloatVectorDataPtr resultData = new FloatVectorData();
	vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize() );

	Context::EditableScope scope( context );
	for( const auto &cellIndex : coverage->tileCells( tileOrigin ) )
	{
		scope.set( cellVariable, &cellIndex );

		Box2i inDataWindow;
		{
			ImagePlug::GlobalScope globalScope( scope.context() );
			if(
				!ImageAlgo::viewIsValid( context, resampledInPlug()->viewNames()->readable() ) ||
				!ImageAlgo::channelExists( resampledInPlug(), channelName )
			)
			{
				continue;
			}
			inDataWindow = resampledInPlug()->dataWindowPlug()->getValue();
		}

		const Box2i inTileBound = BufferAlgo::intersection( outTileBound, inDataWindow );
		if( BufferAlgo::empty( inTileBound ) )
		{
			continue;
		}

		ConstFloatVectorDataPtr cellChannelDataData = resampledInPlug()->channelDataPlug()->getValue();
		const auto &cellChannelData = cellChannelDataData->readable();

		const int width = inTileBound.size().x;
		for( int y = inTileBound.min.y; y < inTileBound.max.y; ++y )
		{
			const int index = BufferAlgo::index( V2i( inTileBound.min.x, y ), tileBound );
			const float *from = cellChannelData.data() + index;
			float *to = result.data() + index;
			for( int i = 0; i < width; ++i )
			{
				*to++ += *from++;
			}
		}
	}

	return resultData;
}
