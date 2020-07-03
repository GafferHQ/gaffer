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

#include "GafferImage/Shape.h"

#include "GafferImage/Blur.h"
#include "GafferImage/ImageAlgo.h"
#include "GafferImage/ImageTransform.h"
#include "GafferImage/Merge.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/Switch.h"
#include "Gaffer/Transform2DPlug.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Shape );

size_t Shape::g_firstPlugIndex = 0;
static std::string g_shapeChannelName( "__shape" );

Shape::Shape( const std::string &name )
	:	FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Color4fPlug( "color", Gaffer::Plug::In, Color4f( 1 ) ) );
	addChild( new BoolPlug( "shadow" ) );
	addChild( new Color4fPlug( "shadowColor", Gaffer::Plug::In, Color4f( 0, 0, 0, 1 ) ) );
	addChild( new V2fPlug( "shadowOffset", Gaffer::Plug::In, V2f( 5, -5 ) ) );
	addChild( new FloatPlug( "shadowBlur", Gaffer::Plug::In, 0.0f, 0.0f ) );

	// We generate our shape and shadow on the __shape and __shadowShape output plugs
	// and then use an internal node network to merge them over the input.

	addChild( new ImagePlug( "__shape", Gaffer::Plug::Out, Plug::Default & ~Plug::Serialisable ) );
	addChild( new ImagePlug( "__shadowShape", Gaffer::Plug::Out, Plug::Default & ~Plug::Serialisable ) );

	shadowShapePlug()->setInput( shapePlug() );
	shadowShapePlug()->channelDataPlug()->setInput( nullptr );

	BlurPtr shadowBlur = new Blur( "__shadowBlur" );
	addChild( shadowBlur );
	shadowBlur->inPlug()->setInput( shadowShapePlug() );
	shadowBlur->radiusPlug()->getChild( 0 )->setInput( shadowBlurPlug() );
	shadowBlur->radiusPlug()->getChild( 1 )->setInput( shadowBlurPlug() );
	shadowBlur->expandDataWindowPlug()->setValue( true );

	ImageTransformPtr shadowTransform = new ImageTransform( "__shadowTransform" );
	addChild( shadowTransform );
	shadowTransform->inPlug()->setInput( shadowBlur->outPlug() );
	shadowTransform->transformPlug()->translatePlug()->setInput( shadowOffsetPlug() );

	MergePtr shadowMerge = new Merge( "__shadowMerge" );
	addChild( shadowMerge );
	shadowMerge->inPlugs()->getChild<ImagePlug>( 0 )->setInput( inPlug() );
	shadowMerge->inPlugs()->getChild<ImagePlug>( 1 )->setInput( shadowTransform->outPlug() );
	shadowMerge->operationPlug()->setValue( Merge::Over );

	SwitchPtr shadowSwitch = new Switch( "__shadowSwitch" );
	shadowSwitch->setup( outPlug() );
	addChild( shadowSwitch );
	shadowSwitch->inPlugs()->getChild<ImagePlug>( 0 )->setInput( inPlug() );
	shadowSwitch->inPlugs()->getChild<ImagePlug>( 1 )->setInput( shadowMerge->outPlug() );
	shadowSwitch->indexPlug()->setInput( shadowPlug() );
	shadowSwitch->enabledPlug()->setInput( enabledPlug() );

	MergePtr merge = new Merge( "__merge" );
	addChild( merge );

	merge->inPlugs()->getChild<ImagePlug>( 0 )->setInput( shadowSwitch->outPlug() );
	merge->inPlugs()->getChild<ImagePlug>( 1 )->setInput( shapePlug() );
	merge->enabledPlug()->setInput( enabledPlug() );
	merge->operationPlug()->setValue( Merge::Over );

	outPlug()->setInput( merge->outPlug() );
}

Shape::~Shape()
{
}

Gaffer::Color4fPlug *Shape::colorPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex );
}

const Gaffer::Color4fPlug *Shape::colorPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex );
}

Gaffer::BoolPlug *Shape::shadowPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::BoolPlug *Shape::shadowPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 1 );
}

Gaffer::Color4fPlug *Shape::shadowColorPlug()
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::Color4fPlug *Shape::shadowColorPlug() const
{
	return getChild<Color4fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::V2fPlug *Shape::shadowOffsetPlug()
{
	return getChild<V2fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::V2fPlug *Shape::shadowOffsetPlug() const
{
	return getChild<V2fPlug>( g_firstPlugIndex + 3 );
}

Gaffer::FloatPlug *Shape::shadowBlurPlug()
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::FloatPlug *Shape::shadowBlurPlug() const
{
	return getChild<FloatPlug>( g_firstPlugIndex + 4 );
}

ImagePlug *Shape::shapePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 5 );
}

const ImagePlug *Shape::shapePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 5 );
}

ImagePlug *Shape::shadowShapePlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 6 );
}

const ImagePlug *Shape::shadowShapePlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 6 );
}

void Shape::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	// TypeId comparison is necessary to avoid calling pure virtual
	// methods below if we're called before being fully constructed.
	if( typeId() == staticTypeId() )
	{
		return;
	}

	if( input == inPlug()->deepPlug() )
	{
		outputs.push_back( shapePlug()->deepPlug() );
	}

	if( affectsShapeDataWindow( input ) )
	{
		outputs.push_back( shapePlug()->dataWindowPlug() );
		outputs.push_back( shadowShapePlug()->dataWindowPlug() );
	}

	if( affectsShapeChannelData( input ) )
	{
		outputs.push_back( shapePlug()->channelDataPlug() );
		outputs.push_back( shadowShapePlug()->channelDataPlug() );
	}

	if( input->parent<Plug>() == colorPlug() )
	{
		outputs.push_back( shapePlug()->channelDataPlug() );
	}
	else if( input->parent<Plug>() == shadowColorPlug() )
	{
		outputs.push_back( shadowShapePlug()->channelDataPlug() );
	}

}

void Shape::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	assert( parent == shapePlug() );
	hashShapeDataWindow( context, h );
}

Imath::Box2i Shape::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	assert( parent == shapePlug() );
	return computeShapeDataWindow( context );
}

void Shape::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	assert( parent == shapePlug() );
	FlatImageProcessor::hashChannelNames( parent, context, h );
	// Because our channel names are constant, we don't need to add
	// anything else to the hash.
}

IECore::ConstStringVectorDataPtr Shape::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	assert( parent == shapePlug() );
	StringVectorDataPtr result = new StringVectorData();
	result->writable().push_back( "R" );
	result->writable().push_back( "G" );
	result->writable().push_back( "B" );
	result->writable().push_back( "A" );
	return result;
}

void Shape::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	assert( parent == shapePlug() || parent == shadowShapePlug()  );
	const std::string &channelName = context->get<std::string>( ImagePlug::channelNameContextName );
	if( channelName == g_shapeChannelName )
	{
		// Private channel we use for caching the shape but don't advertise via channelNames.
		hashShapeChannelData( context->get<V2i>( ImagePlug::tileOriginContextName ), context, h );
	}
	else
	{
		const MurmurHash shapeHash = parent->channelDataHash( g_shapeChannelName, context->get<V2i>( ImagePlug::tileOriginContextName ) );
		const float c = channelValue( parent, channelName );
		if( c == 1 )
		{
			h = shapeHash;
		}
		else
		{
			FlatImageProcessor::hashChannelData( parent, context, h );
			h.append( shapeHash );
			h.append( c );
		}
	}
}

IECore::ConstFloatVectorDataPtr Shape::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	assert( parent == shapePlug() || parent == shadowShapePlug()  );
	if( channelName == g_shapeChannelName )
	{
		// Private channel we use for caching the shape but don't advertise via channelNames.
		return computeShapeChannelData( tileOrigin, context );
	}
	else
	{
		ConstFloatVectorDataPtr shape = parent->channelData( g_shapeChannelName, context->get<V2i>( ImagePlug::tileOriginContextName ) );
		const float c = channelValue( parent, channelName );
		if( c == 1 )
		{
			return shape;
		}
		else
		{
			FloatVectorDataPtr resultData = shape->copy();
			vector<float> &result = resultData->writable();
			for( vector<float>::iterator it = result.begin(), eIt = result.end(); it != eIt; ++it )
			{
				*it *= c;
			}
			return resultData;
		}
	}
}

float Shape::channelValue( const GafferImage::ImagePlug *parent, const std::string &channelName ) const
{
	const Color4fPlug *p = parent == shadowShapePlug() ? shadowColorPlug() : colorPlug();
	const int i = ImageAlgo::colorIndex( channelName );
	float c = p->getChild( i )->getValue();
	if( i != 3 )
	{
		// Premultiply
		c *= p->getChild( 3 )->getValue();
	}

	return c;
}

bool Shape::affectsShapeDataWindow( const Gaffer::Plug *input ) const
{
	return false;
}

void Shape::hashShapeDataWindow( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashDataWindow( shapePlug(), context, h );
}

bool Shape::affectsShapeChannelData( const Gaffer::Plug *input ) const
{
	return false;
}

void Shape::hashShapeChannelData( const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hashChannelData( shapePlug(), context, h );
}
