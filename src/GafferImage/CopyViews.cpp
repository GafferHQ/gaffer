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

#include "GafferImage/CopyViews.h"

#include "Gaffer/Context.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// CopyViews
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( CopyViews );

size_t CopyViews::g_firstPlugIndex = 0;

CopyViews::CopyViews( const std::string &name )
	:	ImageProcessor( name, /* minInputs = */ 1 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "views", Plug::In, "*" ) );
	addChild( new CompoundObjectPlug( "__mapping", Plug::Out, new CompoundObject() ) );

}

CopyViews::~CopyViews()
{
}

Gaffer::StringPlug *CopyViews::viewsPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 0 );
}

const Gaffer::StringPlug *CopyViews::viewsPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 0 );
}

Gaffer::CompoundObjectPlug *CopyViews::mappingPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::CompoundObjectPlug *CopyViews::mappingPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 1 );
}

void CopyViews::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	const ImagePlug *imagePlug = input->parent<ImagePlug>();
	if( imagePlug && imagePlug->parent<Plug>() != inPlugs() )
	{
		imagePlug = nullptr;
	}

	if( input == viewsPlug() || ( imagePlug && input == imagePlug->viewNamesPlug() ) )
	{
		outputs.push_back( mappingPlug() );
	}
	else if( imagePlug )
	{
		outputs.push_back( outPlug()->getChild<Plug>( input->getName() ) );
	}

	// I know we try to have each output mentioned exactly once in affects(), but I can't think
	// of any easy way to achieve this logic without these outputs also appearing in the conditional
	// above
	else if( input == mappingPlug() )
	{
		outputs.push_back( outPlug()->viewNamesPlug() );
		outputs.push_back( outPlug()->formatPlug() );
		outputs.push_back( outPlug()->dataWindowPlug() );
		outputs.push_back( outPlug()->metadataPlug() );
		outputs.push_back( outPlug()->deepPlug() );
		outputs.push_back( outPlug()->sampleOffsetsPlug() );
		outputs.push_back( outPlug()->channelNamesPlug() );
		outputs.push_back( outPlug()->channelDataPlug() );
	}
}

void CopyViews::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hash( output, context, h );

	if( output == mappingPlug() )
	{
		for( auto &i : ImagePlug::Range( *inPlugs() ) )
		{
			if( !i->getInput() )
			{
				continue;
			}
			i->viewNamesPlug()->hash( h );
		}
		viewsPlug()->hash( h );
	}
}

void CopyViews::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == mappingPlug() )
	{
		const string viewMatchPatterns = viewsPlug()->getValue();

		CompoundObjectPtr result = new CompoundObject();
		StringVectorDataPtr viewNamesData = new StringVectorData;
		result->members()["__viewNames"] = viewNamesData;
		vector<string> &viewNames = viewNamesData->writable();
		size_t i = 0;
		for( ImagePlug::Iterator it( inPlugs() ); !it.done(); ++i, ++it )
		{
			// We don't want to add a "default" view coming from the default value of an
			// unconnected input
			if( !(*it)->getInput() )
			{
				continue;
			}

			ConstStringVectorDataPtr inputViewNamesData = (*it)->viewNamesPlug()->getValue();
			for( const std::string &v : inputViewNamesData->readable() )
			{
				if( i > 0 && !StringAlgo::matchMultiple( v, viewMatchPatterns ) )
				{
					continue;
				}
				if( find( viewNames.begin(), viewNames.end(), v ) == viewNames.end() )
				{
					viewNames.push_back( v );
				}
				result->members()[v] = new IntData( i );
			}
		}
		static_cast<CompoundObjectPlug *>( output )->setValue( result );
		return;
	}

	ImageProcessor::compute( output, context );
}

const ImagePlug *CopyViews::inputImage( const Gaffer::Context *context ) const
{
	// Fast shortcut when there is a single input
	if( inPlugs()->children().size() == 2 && !inPlugs()->getChild<ImagePlug>( 1 )->getInput() )
	{
		return inPlugs()->getChild<ImagePlug>( 0 );
	}

	const std::string &viewName = context->get<std::string>( ImagePlug::viewNameContextName );

	ConstCompoundObjectPtr mapping;
	{
		ImagePlug::GlobalScope c( context );
		c.remove( ImagePlug::viewNameContextName );
		mapping = mappingPlug()->getValue();
	}
	const IntData *i = mapping->member<const IntData>( viewName );
	if( !i )
	{
		i = mapping->member<const IntData>( ImagePlug::defaultViewName );
		if( !i )
		{
			throw IECore::Exception( "CopyViews : Incorrect request from downstream node, view \"" + viewName + "\" does not exist" );
		}
	}

	return inPlugs()->getChild<ImagePlug>( i->readable() );
}

void CopyViews::hashViewNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImageProcessor::hashViewNames( output, context, h );

	mappingPlug()->hash( h );
}

void CopyViews::hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inputImage( context )->formatPlug()->hash();
}

void CopyViews::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inputImage( context )->dataWindowPlug()->hash();
}

void CopyViews::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inputImage( context )->metadataPlug()->hash();
}

void CopyViews::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inputImage( context )->deepPlug()->hash();
}

void CopyViews::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inputImage( context )->sampleOffsetsPlug()->hash();
}

void CopyViews::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inputImage( context )->channelNamesPlug()->hash();
}

void CopyViews::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	h = inputImage( context )->channelDataPlug()->hash();
}

IECore::ConstStringVectorDataPtr CopyViews::computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ConstCompoundObjectPtr mapping = mappingPlug()->getValue();
	return mapping->member<StringVectorData>( "__viewNames" );
}

GafferImage::Format CopyViews::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inputImage( context )->formatPlug()->getValue();
}

Imath::Box2i CopyViews::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inputImage( context )->dataWindowPlug()->getValue();
}

IECore::ConstCompoundDataPtr CopyViews::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inputImage( context )->metadataPlug()->getValue();
}

bool CopyViews::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inputImage( context )->deepPlug()->getValue();
}

IECore::ConstIntVectorDataPtr CopyViews::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inputImage( context )->sampleOffsetsPlug()->getValue();
}

IECore::ConstStringVectorDataPtr CopyViews::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inputImage( context )->channelNamesPlug()->getValue();
}

IECore::ConstFloatVectorDataPtr CopyViews::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return inputImage( context )->channelDataPlug()->getValue();
}
