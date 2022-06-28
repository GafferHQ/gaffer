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

#include "GafferImage/DeleteViews.h"

#include "Gaffer/Context.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// DeleteViews
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( DeleteViews );

size_t DeleteViews::g_firstPlugIndex = 0;

DeleteViews::DeleteViews( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new IntPlug( "mode", Plug::In, Delete, Delete, Keep ) );
	addChild( new StringPlug( "views", Plug::In, "" ) );

	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->deepPlug()->setInput( inPlug()->deepPlug() );
	outPlug()->sampleOffsetsPlug()->setInput( inPlug()->sampleOffsetsPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );
	outPlug()->channelDataPlug()->setInput( inPlug()->channelDataPlug() );
}

DeleteViews::~DeleteViews()
{
}

Gaffer::IntPlug *DeleteViews::modePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::IntPlug *DeleteViews::modePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 0 );
}

Gaffer::StringPlug *DeleteViews::viewsPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *DeleteViews::viewsPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

void DeleteViews::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if( input == inPlug()->viewNamesPlug() || input == modePlug() || input == viewsPlug() )
	{
		outputs.push_back( outPlug()->viewNamesPlug() );
	}
}

void DeleteViews::hashViewNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashViewNames( output, context, h );
	inPlug()->viewNamesPlug()->hash( h );
	modePlug()->hash( h );
	viewsPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr DeleteViews::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstStringVectorDataPtr inViewNamesData = inPlug()->viewNamesPlug()->getValue();

	const Mode mode = static_cast<Mode>( modePlug()->getValue() );
	const string views = viewsPlug()->getValue();


	StringVectorDataPtr resultData = new StringVectorData();
	vector<string> &result = resultData->writable();

	for( const std::string &i : inViewNamesData->readable() )
	{
		const bool match = StringAlgo::matchMultiple( i, views );
		if( match == ( mode == Keep ) )
		{
			result.push_back( i );
		}
	}

	return resultData;
}
