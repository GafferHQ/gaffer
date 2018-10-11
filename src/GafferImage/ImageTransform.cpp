//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#include "GafferImage/ImageTransform.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/Resample.h"
#include "GafferImage/Sampler.h"

#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Transform2DPlug.h"

#include "IECore/AngleConversion.h"

#include "OpenEXR/ImathMatrixAlgo.h"

#include "boost/bind.hpp"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

static InternedString g_transformChainContextName( "__imageTransform:trainsformChain" );

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Rounds min down, and max up, while converting from float to int.
Box2i box2fToBox2i( const Box2f &b )
{
	return Box2i(
		V2i( floor( b.min.x ), floor( b.min.y ) ),
		V2i( ceil( b.max.x ), ceil( b.max.y ) )
	);
}

Box2f transform( const Box2f &b, const M33f &m )
{
	if( b.isEmpty() )
	{
		return b;
	}

	Box2f r;
	r.extendBy( V2f( b.min.x, b.min.y ) * m );
	r.extendBy( V2f( b.max.x, b.min.y ) * m );
	r.extendBy( V2f( b.max.x, b.max.y ) * m );
	r.extendBy( V2f( b.min.x, b.max.y ) * m );
	return r;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageTransform
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( ImageTransform );

size_t ImageTransform::g_firstPlugIndex = 0;

ImageTransform::ImageTransform( const std::string &name )
	:	ImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Gaffer::Transform2DPlug( "transform" ) );
	addChild( new StringPlug( "filter", Plug::In, "cubic" ) );

	// We use an internal Resample node to do filtered
	// sampling of the translate and scale in one. Then,
	// if we also have a rotation component we sample that
	// from the intermediate result in computeChannelData().

	addChild( new M33fPlug( "__resampleMatrix", Plug::Out ) );

	addChild( new M33fPlug( "__inTransform", Plug::In ) );
	addChild( new M33fPlug( "__outTransform", Plug::Out ) );

	addChild( new ImagePlug( "__resampledIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	ResamplePtr resample = new Resample( "__resample" );
	addChild( resample );

	resample->inPlug()->setInput( inPlug() );
	resample->filterPlug()->setInput( filterPlug() );
	resample->matrixPlug()->setInput( resampleMatrixPlug() );
	resampledInPlug()->setInput( resample->outPlug() );

	// Pass through the things we don't change at all.
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );

	m_plugInputChangedConnection = plugInputChangedSignal().connect( boost::bind( &ImageTransform::plugInputChanged, this, ::_1 ) );


}

ImageTransform::~ImageTransform()
{
}

Gaffer::Transform2DPlug *ImageTransform::transformPlug()
{
	return getChild<Transform2DPlug>( g_firstPlugIndex );
}

const Gaffer::Transform2DPlug *ImageTransform::transformPlug() const
{
	return getChild<Transform2DPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ImageTransform::filterPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ImageTransform::filterPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::M33fPlug *ImageTransform::resampleMatrixPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::M33fPlug *ImageTransform::resampleMatrixPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex + 2 );
}

Gaffer::M33fPlug *ImageTransform::inTransformPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::M33fPlug *ImageTransform::inTransformPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex + 3 );
}

Gaffer::M33fPlug *ImageTransform::outTransformPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::M33fPlug *ImageTransform::outTransformPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex + 4 );
}

ImagePlug *ImageTransform::resampledInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 5 );
}

const ImagePlug *ImageTransform::resampledInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 5 );
}

Resample *ImageTransform::resample()
{
	return getChild<Resample>( g_firstPlugIndex + 6 );
}

const Resample *ImageTransform::resample() const
{
	return getChild<Resample>( g_firstPlugIndex + 6 );
}

void ImageTransform::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	ImageProcessor::affects( input, outputs );

	if(
		input->parent<Plug>() == transformPlug()->translatePlug() ||
		input->parent<Plug>() == transformPlug()->scalePlug() ||
		input->parent<Plug>() == transformPlug()->pivotPlug() ||
		input == inTransformPlug()
	)
	{
		outputs.push_back( resampleMatrixPlug() );
	}

	if(
		input == inPlug()->dataWindowPlug() ||
		input == resampledInPlug()->dataWindowPlug() ||
		transformPlug()->isAncestorOf( input ) ||
		input == inTransformPlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if(
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == resampledInPlug()->channelDataPlug() ||
		transformPlug()->isAncestorOf( input ) ||
		input == inTransformPlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if(
		transformPlug()->isAncestorOf( input ) ||
		input == inTransformPlug() ||
		input == enabledPlug()
	)
	{
		outputs.push_back( outTransformPlug() );
	}

}

void ImageTransform::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{

	if( output == resampleMatrixPlug() )
	{
		transformPlug()->translatePlug()->hash( h );
		transformPlug()->scalePlug()->hash( h );
		transformPlug()->pivotPlug()->hash( h );
		inTransformPlug()->hash( h );
	}

	if( output == outTransformPlug() )
	{
		enabledPlug()->hash( h );

		if( inTransformPlug()->getInput() )
		{
			inTransformPlug()->hash( h );
		}

		if( enabledPlug()->getValue() )
		{
			transformPlug()->translatePlug()->hash( h );
			transformPlug()->scalePlug()->hash( h );
			transformPlug()->pivotPlug()->hash( h );
			transformPlug()->rotatePlug()->hash( h );
		}
	}

	ImageProcessor::hash( output, context, h );
}

void ImageTransform::compute( ValuePlug *output, const Context *context ) const
{
	if( output == resampleMatrixPlug() )
	{
		M33f matrix, resampleMatrix;
		operation( matrix, resampleMatrix );
		static_cast<M33fPlug *>( output )->setValue( resampleMatrix );
		return;
	}

	if( output == outTransformPlug() )
	{
		M33f finalTransform;
		finalTransform.makeIdentity();

		if( inTransformPlug()->getInput() )
		{
			finalTransform *= inTransformPlug()->getValue();
		}

		if( enabledPlug()->getValue() )
		{
			finalTransform *= transformPlug()->matrix();

		}
		static_cast<M33fPlug *>( output )->setValue( finalTransform );
		return;
	}

	ImageProcessor::compute( output, context );
}

void ImageTransform::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	int transformChain = context->get<int>( g_transformChainContextName, 0 );
	h.append( transformChain );
	if( transformChain )
	{
		ImageProcessor::hashDataWindow( parent, context, h );
		inPlug()->dataWindowPlug()->hash( h );

	}
	else
	{
		M33f matrix, resampleMatrix;
		const unsigned op = operation( matrix, resampleMatrix );
		if( !(op & Rotate) )
		{
			h = resampledInPlug()->dataWindowPlug()->hash();
		}
		else
		{
			ImageProcessor::hashDataWindow( parent, context, h );
			inPlug()->dataWindowPlug()->hash( h );
			h.append( matrix );
		}
	}
}

Imath::Box2i ImageTransform::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// inside a transform chain just return the inPlug->channelData
	Context::EditableScope editableScope( context );
	if( context->get<int>( g_transformChainContextName, 0 ) )
	{
		if( !inTransformPlug()->getInput() )
		{
			editableScope.remove( g_transformChainContextName );		
		}
		return inPlug()->dataWindowPlug()->getValue();

	}
	else 
	{
		if( inTransformPlug()->getInput() )
		{
			editableScope.set<int>( g_transformChainContextName, 1 );
		}

		M33f matrix, resampleMatrix;
		const unsigned op = operation( matrix, resampleMatrix );
		if( !(op & Rotate) )
		{
			return resampledInPlug()->dataWindowPlug()->getValue();
		}
		else
		{
			const Box2i in = inPlug()->dataWindowPlug()->getValue();
			return box2fToBox2i( transform( Box2f( V2f( in.min ), V2f( in.max ) ), matrix ) );
		}
	}
}

void ImageTransform::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	// inside a transform chain just return the inPlug->channelDataPlug->hash
	Context::EditableScope editableScope( context );
	int transformChain = context->get<int>( g_transformChainContextName, 0 );
	h.append( transformChain );
	if( transformChain )
	{
		if( !inTransformPlug()->getInput() )
		{
			editableScope.remove( g_transformChainContextName );		
		}
		ImageProcessor::hashChannelData( parent, context, h );
		inPlug()->channelDataPlug()->hash( h );

	}
	else
	{
		if( inTransformPlug()->getInput() )
		{
			editableScope.set<int>( g_transformChainContextName, 1 );
		}
		M33f matrix, resampleMatrix;
		const unsigned op = operation( matrix, resampleMatrix );
		if( !(op & Rotate) )
		{
			h = resampledInPlug()->channelDataPlug()->hash();
		}
		else
		{
			// Rotation of either the input or the resampled input.
			{
				ImagePlug::GlobalScope c( context );
				ImageTransform::hashDataWindow( parent, context, h );
			}

			const ImagePlug *samplerImage; M33f samplerMatrix;
			const Box2i samplerRegion = sampler( op, matrix, resampleMatrix, context->get<V2i>( ImagePlug::tileOriginContextName ), samplerImage, samplerMatrix );

			Sampler sampler(
				samplerImage,
				context->get<std::string>( ImagePlug::channelNameContextName ),
				samplerRegion
			);
			sampler.hash( h );

			h.append( samplerMatrix );
		}
	}
}

IECore::ConstFloatVectorDataPtr ImageTransform::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// inside a transform chain just return the inPlug->channelData
	Context::EditableScope editableScope( context );
	if( context->get<int>( g_transformChainContextName, 0 ) )
	{
		if( !inTransformPlug()->getInput() )
		{
			editableScope.remove( g_transformChainContextName );		
		}
		return inPlug()->channelDataPlug()->getValue();

	}
	else 
	{
		if( inTransformPlug()->getInput() )
		{
			editableScope.set<int>( g_transformChainContextName, 1 );
		}
	
		M33f matrix, resampleMatrix;
		const unsigned op = operation( matrix, resampleMatrix );
		if( !(op & Rotate) )
		{
			return resampledInPlug()->channelDataPlug()->getValue();
		}
		else
		{
			// Rotation of either the input or the resampled input.

			const ImagePlug *samplerImage; M33f samplerMatrix;
			const Box2i samplerRegion = sampler( op, matrix, resampleMatrix, context->get<V2i>( ImagePlug::tileOriginContextName ), samplerImage, samplerMatrix );

			Sampler sampler(
				samplerImage,
				channelName,
				samplerRegion
			);

			FloatVectorDataPtr resultData = new FloatVectorData;
			resultData->writable().resize( ImagePlug::tileSize() * ImagePlug::tileSize() );
			std::vector<float>::iterator pIt = resultData->writable().begin();

			const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
			V2i oP;
			for( oP.y = tileBound.min.y; oP.y < tileBound.max.y; ++oP.y )
			{
				for( oP.x = tileBound.min.x; oP.x < tileBound.max.x; ++oP.x )
				{
					V2f iP = V2f( oP.x + 0.5, oP.y + 0.5 ) * samplerMatrix;
					*pIt++ = sampler.sample( iP.x, iP.y );
				}
			}

			return resultData;
		}
	}
}

unsigned ImageTransform::operation( Imath::M33f &matrix, Imath::M33f &resampleMatrix ) const
{
	const Transform2DPlug *plug = transformPlug();

	const V2f pivot = plug->pivotPlug()->getValue();
	const V2f translate = plug->translatePlug()->getValue();
	const V2f scale = plug->scalePlug()->getValue();
	const float rotate = plug->rotatePlug()->getValue();

	M33f pivotMatrix; pivotMatrix.setTranslation( pivot );
	M33f pivotInverseMatrix; pivotInverseMatrix.setTranslation( -pivot );
	M33f translateMatrix; translateMatrix.setTranslation( translate );
	M33f scaleMatrix; scaleMatrix.setScale( scale );
	M33f rotateMatrix; rotateMatrix.setRotation( degreesToRadians( rotate ) );
	M33f inTransform; inTransform.makeIdentity();

	if( inTransformPlug()->getInput() )
	{
		 inTransform = inTransformPlug()->getValue();
	}

	matrix = inTransform * pivotInverseMatrix * scaleMatrix * rotateMatrix  * pivotMatrix * translateMatrix;

	M33f resampledScaleMatrix;
	M33f resampledTranslateMatrix;
	V2f s, t;
	float h, r = 0;
	extractSHRT( matrix, s, h, r, t, true );
	resampledTranslateMatrix.setTranslation( t );
	resampledScaleMatrix.setScale( s );

	resampleMatrix = resampledScaleMatrix * resampledTranslateMatrix; 	

	unsigned op = 0;
	if( t != V2f( 0 ) )
	{
		op |= Translate;
	}
	if( s != V2f( 1 ) )
	{
		op |= Scale;
	}
	if( r != 0 )
	{
		op |= Rotate;
	}

	return op;
}

Imath::Box2i ImageTransform::sampler( unsigned op, const Imath::M33f &matrix, const Imath::M33f &resampleMatrix, const Imath::V2i &tileOrigin, const ImagePlug *&samplerImage, Imath::M33f &samplerMatrix ) const
{
	assert( op & Rotate );

	if( op & ( Scale | Translate ) )
	{
		samplerImage = resampledInPlug();
		samplerMatrix = matrix.inverse() * resampleMatrix;
	}
	else
	{
		samplerImage = inPlug();
		samplerMatrix = matrix.inverse();
	}

	const Box2f tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	return box2fToBox2i( transform( tileBound, samplerMatrix ) );
}

void ImageTransform::plugInputChanged( Gaffer::Plug *plug )
{
	if( plug == inPlug() )
	{
		if ( plug->getInput() )
		{
			Node* source = plug->source()->node();
			if( ImageTransform* imageTransform = runTimeCast< ImageTransform >( source ) )
			{
				inTransformPlug()->setInput( imageTransform->outTransformPlug() );
			}
			// inPlug is connected but not to an imageTransform node.
			else
			{
				inTransformPlug()->setInput( NULL );
			}
		}
		// inPlug is not connected.
		else
		{
			inTransformPlug()->setInput( NULL );
		}
	}
}

