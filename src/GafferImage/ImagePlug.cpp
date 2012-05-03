//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "IECore/Exception.h"
#include "IECore/BoxOps.h"
#include "IECore/BoxAlgo.h"

#include "Gaffer/Context.h"

#include "GafferImage/ImagePlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

IE_CORE_DEFINERUNTIMETYPED( ImagePlug );

ImagePlug::ImagePlug( const std::string &name, Direction direction, unsigned flags )
	:	CompoundPlug( name, direction, flags )
{
	
	addChild(
		new AtomicBox2iPlug(
			"displayWindow",
			direction,
			Imath::Box2i(),
			flags
		)
	);
	
	addChild(
		new AtomicBox2iPlug(
			"dataWindow",
			direction,
			Imath::Box2i(),
			flags
		)
	);
	
	addChild(
		new StringVectorDataPlug(
			"channelNames",
			direction,
			0,
			flags
		)
	);
	
	addChild(
		new FloatVectorDataPlug(
			"channelData",
			direction,
			0,
			flags
		)
	);
	
}

ImagePlug::~ImagePlug()
{
}

bool ImagePlug::acceptsChild( ConstGraphComponentPtr potentialChild ) const
{
	return children().size() != 4;
}

bool ImagePlug::acceptsInput( Gaffer::ConstPlugPtr input ) const
{
	if( !CompoundPlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return input->isInstanceOf( staticTypeId() );
	}
	return true;
}

Gaffer::AtomicBox2iPlug *ImagePlug::displayWindowPlug()
{
	return getChild<AtomicBox2iPlug>( "displayWindow" );
}

const Gaffer::AtomicBox2iPlug *ImagePlug::displayWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( "displayWindow" );
}

Gaffer::AtomicBox2iPlug *ImagePlug::dataWindowPlug()
{
	return getChild<AtomicBox2iPlug>( "dataWindow" );
}

const Gaffer::AtomicBox2iPlug *ImagePlug::dataWindowPlug() const
{
	return getChild<AtomicBox2iPlug>( "dataWindow" );
}

Gaffer::StringVectorDataPlug *ImagePlug::channelNamesPlug()
{
	return getChild<StringVectorDataPlug>( "channelNames" );
}

const Gaffer::StringVectorDataPlug *ImagePlug::channelNamesPlug() const
{
	return getChild<StringVectorDataPlug>( "channelNames" );
}

Gaffer::FloatVectorDataPlug *ImagePlug::channelDataPlug()
{
	return getChild<FloatVectorDataPlug>( "channelData" );
}

const Gaffer::FloatVectorDataPlug *ImagePlug::channelDataPlug() const
{
	return getChild<FloatVectorDataPlug>( "channelData" );
}

IECore::ConstFloatVectorDataPtr ImagePlug::channelData( const std::string &channelName, const Imath::V2i &tile ) const
{
	if( direction()==In && !getInput<Plug>() )
	{
		throw IECore::Exception( "ImagePlug::channelData called on unconnected input plug" );
	}
	ContextPtr tmpContext = new Context( *Context::current() );
	tmpContext->set( "image:channelName", channelName );
	tmpContext->set( "image:tileOrigin", tile );
	Context::Scope scopedContext( tmpContext );
	return channelDataPlug()->getValue();
}

IECore::ImagePrimitivePtr ImagePlug::image() const
{
	const Box2i displayWindow = displayWindowPlug()->getValue();
	if( displayWindow.isEmpty() )
	{
		return 0;
	}

	const Box2i dataWindow = dataWindowPlug()->getValue();

	ImagePrimitivePtr result = new ImagePrimitive( dataWindow, displayWindow );
	
	ConstStringVectorDataPtr channelNamesData = channelNamesPlug()->getValue();
	const vector<string> &channelNames = channelNamesData->readable();
	
	vector<float *> imageChannelData;
	for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it!=eIt; it++ )
	{
		FloatVectorDataPtr cd = new FloatVectorData;
		vector<float> &c = cd->writable();
		c.resize( result->variableSize( PrimitiveVariable::Vertex ), 0.0f );
		result->variables[*it] = PrimitiveVariable( PrimitiveVariable::Vertex, cd );
		imageChannelData.push_back( &(c[0]) );
	}
	
	V2i minTileOrigin = ( dataWindow.min / tileSize() ) * tileSize();
	V2i maxTileOrigin = ( dataWindow.max / tileSize() ) * tileSize();
	
	size_t imageStride = dataWindow.size().x + 1;
	
	ContextPtr context = new Context( *Context::current() );
	for( int tileOriginY = minTileOrigin.y; tileOriginY<=maxTileOrigin.y; tileOriginY += tileSize() )
	{
		for( int tileOriginX = minTileOrigin.x; tileOriginX<=maxTileOrigin.x; tileOriginX += tileSize() )
		{
			for( vector<string>::const_iterator it = channelNames.begin(), eIt = channelNames.end(); it!=eIt; it++ )
			{
				context->set( "image:channelName", *it );
				context->set( "image:tileOrigin", V2i( tileOriginX, tileOriginY ) );
				Context::Scope scope( context );
				
				Box2i tileBound( V2i( tileOriginX, tileOriginY ), V2i( tileOriginX + tileSize(), tileOriginY + tileSize() ) );
				Box2i b = boxIntersection( tileBound, dataWindow );
								
				ConstFloatVectorDataPtr tileData = channelDataPlug()->getValue();
				if( tileData )
				{
					for( int y = b.min.y; y<=b.max.y; y++ )
					{
						const float *tilePtr = &(tileData->readable()[0]) + (y - tileOriginY) * tileSize() + (b.min.x - tileOriginX);
						float *channelPtr = imageChannelData[it-channelNames.begin()] + ( y - dataWindow.min.y ) * imageStride + (b.min.x - dataWindow.min.x);
						for( int x = b.min.x; x <= b.max.x; x++ )
						{
							*channelPtr++ = *tilePtr++;
						}
					}
				}
			}
		}
	}
	
	return result;
}
