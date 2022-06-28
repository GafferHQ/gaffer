//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/SelectView.h"

#include "GafferImage/BufferAlgo.h"
#include "GafferImage/ImageAlgo.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/NameValuePlug.h"

#include "boost/bind/bind.hpp"
#include "boost/range/adaptor/reversed.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// SelectView
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( SelectView );

size_t SelectView::g_firstPlugIndex = 0;

SelectView::SelectView( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "view", Plug::In, "left" ) );
}

SelectView::~SelectView()
{
}

Gaffer::StringPlug *SelectView::viewPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringPlug *SelectView::viewPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 0 );
}

void SelectView::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == viewPlug() || input == inPlug()->viewNamesPlug() )
	{
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->metadataPlug() );
		outputs.push_back( outPlug()->deepPlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
	else if( input->parent() == inPlug() )
	{
		outputs.push_back( outPlug()->getChild< Plug >( input->getName() ) );
	}
}

std::string SelectView::selectViewName( const Gaffer::Context *context ) const
{
	ImagePlug::GlobalScope g( context  );
	g.remove( ImagePlug::viewNameContextName );
	return viewPlug()->getValue();
}

void SelectView::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );

	h = inPlug()->formatPlug()->hash();
}

void SelectView::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	h = inPlug()->dataWindowPlug()->hash();
}

void SelectView::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	h = inPlug()->metadataPlug()->hash();
}

void SelectView::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	h = inPlug()->deepPlug()->hash();
}

void SelectView::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	h = inPlug()->sampleOffsetsPlug()->hash();
}

void SelectView::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	h = inPlug()->channelNamesPlug()->hash();
}

void SelectView::hashViewNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashViewNames( output, context, h );
}

void SelectView::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	h = inPlug()->channelDataPlug()->hash();
}

GafferImage::Format SelectView::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	return inPlug()->formatPlug()->getValue();
}

Imath::Box2i SelectView::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	return inPlug()->dataWindowPlug()->getValue();
}

IECore::ConstCompoundDataPtr SelectView::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	return inPlug()->metadataPlug()->getValue();
}

bool SelectView::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	return inPlug()->deepPlug()->getValue();
}

IECore::ConstIntVectorDataPtr SelectView::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	return inPlug()->sampleOffsetsPlug()->getValue();
}

IECore::ConstStringVectorDataPtr SelectView::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	return inPlug()->channelNamesPlug()->getValue();
}

IECore::ConstStringVectorDataPtr SelectView::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::defaultViewNames();
}

IECore::ConstFloatVectorDataPtr SelectView::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	std::string v = selectViewName( context );
	ImagePlug::ViewScope s( context );
	s.setViewNameChecked( &v, inPlug()->viewNames().get() );
	return inPlug()->channelDataPlug()->getValue();
}
