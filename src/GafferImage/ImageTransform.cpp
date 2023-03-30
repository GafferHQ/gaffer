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

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathMatrixAlgo.h"
#else
#include "Imath/ImathMatrixAlgo.h"
#endif

#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

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

Imath::Box2i samplerWindow( const Imath::V2i &tileOrigin, const Imath::M33f &samplerMatrix )
{
	const Box2f tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );
	return box2fToBox2i( transform( tileBound, samplerMatrix ) );
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// ImageTransform::ChainingScope and ImageTransform::CleanScope
//////////////////////////////////////////////////////////////////////////

// Utility used in chaining a series of ImageTransform nodes so that the
// final node in the chain applies the concatenated transform in a single
// step. This avoids the expense and inaccuracy of performing repeated
// filtering.
class ImageTransform::ChainingScope : boost::noncopyable
{

	public :

		ChainingScope( const Gaffer::Context *context, const ImageTransform *imageTransform )
			:	m_chained( context->get<bool>( chainedContextName, false ) ), m_true( true )
		{
			if( !m_chained )
			{
				if( imageTransform->inTransformPlug()->getInput() && imageTransform->concatenatePlug()->getValue() )
				{
					// We're the bottom of a chain. Tell the upstream
					// nodes they've been chained.
					m_scope.emplace( context );
					m_scope->set( chainedContextName, &m_true );
				}
			}
			else
			{
				const bool concatenate = imageTransform->concatenatePlug()->getValue();
				m_chained = concatenate;
				if(
					!imageTransform->inTransformPlug()->getInput() ||
					!concatenate
				)
				{
					// Either we're at the top of a chain, in which case we
					// want to remove the context variable so it doesn't leak out
					// to unrelated nodes. Or we want to break concatenation,
					// in which case we need to do the same thing.
					m_scope.emplace( context );
					m_scope->remove( chainedContextName );
				}
			}
		}

		// Returns true if the current operation is part of a chain.
		// In this case, the operation should be implemented as a pass
		// through, as the bottom of the chain will do all the work
		// in a single operation.
		bool chained() const
		{
			return m_chained;
		}

		static InternedString chainedContextName;

	private :

		// We use `optional` here to avoid the expense of constructing
		// an EditableScope when we don't need one.
		std::optional<Context::EditableScope> m_scope;
		bool m_chained;
		bool m_true;

};

InternedString ImageTransform::ChainingScope::chainedContextName( "__imageTransform:chained" );

// Cleans up the `chainedContextName` variable created by ChainingScope.
class ImageTransform::CleanScope : boost::noncopyable
{

	public :

		CleanScope( const Gaffer::Context *context )
		{
			if( context->get<bool>( ChainingScope::chainedContextName, false ) )
			{
				m_scope.emplace( context );
				m_scope->remove( ChainingScope::chainedContextName );
				m_context = m_scope->context();
			}
			else
			{
				m_context = context;
			}
		}

		const Context *context() const
		{
			return m_context;
		}

	private :

		const Context *m_context;
		std::optional<Context::EditableScope> m_scope;

};

//////////////////////////////////////////////////////////////////////////
// ImageTransform
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( ImageTransform );

size_t ImageTransform::g_firstPlugIndex = 0;

ImageTransform::ImageTransform( const std::string &name )
	:	FlatImageProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new Gaffer::Transform2DPlug( "transform" ) );
	addChild( new StringPlug( "filter", Plug::In, "cubic" ) );
	addChild( new BoolPlug( "invert", Plug::In ) );
	addChild( new BoolPlug( "concatenate", Plug::In, true ) );

	// We use an internal Resample node to do filtered
	// sampling of the translate and scale in one. Then,
	// if we also have a rotation component we sample that
	// from the intermediate result in computeChannelData().

	addChild( new M33fPlug( "__resampleMatrix", Plug::Out ) );

	addChild( new M33fPlug( "__inTransform", Plug::In, M33f(), Plug::Default & ~Plug::Serialisable ) );
	addChild( new M33fPlug( "__outTransform", Plug::Out, M33f(), Plug::Default & ~Plug::Serialisable ) );

	addChild( new ImagePlug( "__resampledIn", Plug::In, Plug::Default & ~Plug::Serialisable ) );

	ResamplePtr resample = new Resample( "__resample" );
	addChild( resample );

	resample->inPlug()->setInput( inPlug() );
	resample->filterPlug()->setInput( filterPlug() );
	resample->matrixPlug()->setInput( resampleMatrixPlug() );
	resampledInPlug()->setInput( resample->outPlug() );

	// Pass through the things we don't change at all.
	outPlug()->viewNamesPlug()->setInput( inPlug()->viewNamesPlug() );
	outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
	outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
	outPlug()->channelNamesPlug()->setInput( inPlug()->channelNamesPlug() );

	plugInputChangedSignal().connect( boost::bind( &ImageTransform::plugInputChanged, this, ::_1 ) );
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

Gaffer::BoolPlug *ImageTransform::invertPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::BoolPlug *ImageTransform::invertPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 2 );
}

Gaffer::BoolPlug *ImageTransform::concatenatePlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::BoolPlug *ImageTransform::concatenatePlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex + 3 );
}

Gaffer::M33fPlug *ImageTransform::resampleMatrixPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::M33fPlug *ImageTransform::resampleMatrixPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex + 4 );
}

Gaffer::M33fPlug *ImageTransform::inTransformPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::M33fPlug *ImageTransform::inTransformPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex + 5 );
}

Gaffer::M33fPlug *ImageTransform::outTransformPlug()
{
	return getChild<M33fPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::M33fPlug *ImageTransform::outTransformPlug() const
{
	return getChild<M33fPlug>( g_firstPlugIndex + 6 );
}

ImagePlug *ImageTransform::resampledInPlug()
{
	return getChild<ImagePlug>( g_firstPlugIndex + 7 );
}

const ImagePlug *ImageTransform::resampledInPlug() const
{
	return getChild<ImagePlug>( g_firstPlugIndex + 7 );
}

Resample *ImageTransform::resample()
{
	return getChild<Resample>( g_firstPlugIndex + 8 );
}

const Resample *ImageTransform::resample() const
{
	return getChild<Resample>( g_firstPlugIndex + 8 );
}

void ImageTransform::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FlatImageProcessor::affects( input, outputs );

	if(
		transformPlug()->isAncestorOf( input ) ||
		input == invertPlug() ||
		input == inTransformPlug() ||
		input == concatenatePlug()
	)
	{
		outputs.push_back( resampleMatrixPlug() );
	}

	if(
		input == inPlug()->dataWindowPlug() ||
		input == resampledInPlug()->dataWindowPlug() ||
		transformPlug()->isAncestorOf( input ) ||
		input == invertPlug() ||
		input == inTransformPlug() ||
		input == concatenatePlug()
	)
	{
		outputs.push_back( outPlug()->dataWindowPlug() );
	}

	if(
		input == inPlug()->channelDataPlug() ||
		input == inPlug()->dataWindowPlug() ||
		input == resampledInPlug()->channelDataPlug() ||
		transformPlug()->isAncestorOf( input ) ||
		input == invertPlug() ||
		input == inTransformPlug() ||
		input == concatenatePlug()
	)
	{
		outputs.push_back( outPlug()->channelDataPlug() );
	}

	if(
		transformPlug()->isAncestorOf( input ) ||
		input == invertPlug() ||
		input == inTransformPlug() ||
		input == enabledPlug() ||
		input == concatenatePlug()
	)
	{
		outputs.push_back( outTransformPlug() );
	}

}

void ImageTransform::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	FlatImageProcessor::hash( output, context, h );

	if( output == resampleMatrixPlug() )
	{
		transformPlug()->hash( h );
		invertPlug()->hash( h );
		inTransformPlug()->hash( h );
		concatenatePlug()->hash( h );
	}
	else if( output == outTransformPlug() )
	{
		if( enabledPlug()->getValue() )
		{
			transformPlug()->hash( h );
			invertPlug()->hash( h );
			if( concatenatePlug()->getValue() )
			{
				inTransformPlug()->hash( h );
			}
		}
		else
		{
			inTransformPlug()->hash( h );
		}
	}
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
	else if( output == outTransformPlug() )
	{
		M33f result;
		if( enabledPlug()->getValue() )
		{
			if( concatenatePlug()->getValue() )
			{
				M33f transform = transformPlug()->matrix();
				if( invertPlug()->getValue() )
				{
					transform.invert();
				}
				result = inTransformPlug()->getValue() * transform;
			}
		}
		else
		{
			// When we're disabled, we can't break concatenation.
			result = inTransformPlug()->getValue();
		}
		static_cast<M33fPlug *>( output )->setValue( result );
		return;
	}

	FlatImageProcessor::compute( output, context );
}

void ImageTransform::hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	// We need the CleanScope here because `hash/computeChannelData()` both use a Sampler,
	// and the Sampler constructor pulls on the deep plug.
	CleanScope cleanScope( context );
	FlatImageProcessor::hashDeep( parent, cleanScope.context(), h );
}

bool ImageTransform::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	// We need the CleanScope here because `hash/computeChannelData()` both use a Sampler,
	// and the Sampler constructor pulls on the deep plug.
	CleanScope cleanScope( context );
	return FlatImageProcessor::computeDeep( cleanScope.context(), parent );
}

void ImageTransform::hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ChainingScope chainingScope( context, this );
	if( chainingScope.chained() )
	{
		h = inPlug()->dataWindowPlug()->hash();
		return;
	}

	M33f matrix, resampleMatrix;
	const unsigned op = operation( matrix, resampleMatrix );
	if( !(op & Rotate) )
	{
		h = resampledInPlug()->dataWindowPlug()->hash();
	}
	else
	{
		FlatImageProcessor::hashDataWindow( parent, context, h );
		inPlug()->dataWindowPlug()->hash( h );
		h.append( matrix );
	}
}

Imath::Box2i ImageTransform::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ChainingScope chainingScope( context, this );
	if( chainingScope.chained() )
	{
		return inPlug()->dataWindowPlug()->getValue();
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
		if( BufferAlgo::empty( in ) )
		{
			return in;
		}
		return box2fToBox2i( transform( Box2f( V2f( in.min ), V2f( in.max ) ), matrix ) );
	}
}

void ImageTransform::hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ChainingScope chainingScope( context, this );
	if( chainingScope.chained() )
	{
		h = inPlug()->channelDataPlug()->hash();
		return;
	}

	M33f matrix, resampleMatrix;
	const unsigned op = operation( matrix, resampleMatrix );
	if( !(op & Rotate) )
	{
		h = resampledInPlug()->channelDataPlug()->hash();
	}
	else
	{
		// Rotation of the resampled input.
		FlatImageProcessor::hashChannelData( parent, context, h );

		const M33f samplerMatrix = matrix.inverse() * resampleMatrix;

		Sampler sampler(
			resampledInPlug(),
			context->get<std::string>( ImagePlug::channelNameContextName ),
			samplerWindow( context->get<V2i>( ImagePlug::tileOriginContextName ), samplerMatrix )
		);
		sampler.hash( h );

		h.append( samplerMatrix );
	}
}

IECore::ConstFloatVectorDataPtr ImageTransform::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	ChainingScope chainingScope( context, this );
	if( chainingScope.chained() )
	{
		return inPlug()->channelDataPlug()->getValue();
	}

	M33f matrix, resampleMatrix;
	const unsigned op = operation( matrix, resampleMatrix );
	if( !(op & Rotate) )
	{
		return resampledInPlug()->channelDataPlug()->getValue();
	}
	else
	{
		// Rotation of the resampled input.

		const M33f samplerMatrix = matrix.inverse() * resampleMatrix;

		Sampler sampler(
			resampledInPlug(),
			channelName,
			samplerWindow( tileOrigin, samplerMatrix )
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

unsigned ImageTransform::operation( Imath::M33f &matrix, Imath::M33f &resampleMatrix ) const
{
	matrix = transformPlug()->matrix();
	if( invertPlug()->getValue() )
	{
		matrix.invert();
	}
	if( concatenatePlug()->getValue() )
	{
		matrix = inTransformPlug()->getValue() * matrix;
	}

	V2f scale, translate;
	float shear = 0, rotate = 0;
	extractSHRT( matrix, scale, shear, rotate, translate );

	resampleMatrix = M33f().setScale( scale ) * M33f().setTranslation( translate );

	unsigned op = 0;
	if( translate != V2f( 0 ) )
	{
		op |= Translate;
	}
	if( scale != V2f( 1 ) )
	{
		op |= Scale;
	}
	if( rotate != 0 )
	{
		op |= Rotate;
	}

	return op;
}

void ImageTransform::plugInputChanged( Gaffer::Plug *plug )
{
	if( plug != inPlug() )
	{
		return;
	}

	ImageTransform *upstreamImageTransform = nullptr;
	if( plug->getInput() )
	{
		upstreamImageTransform = runTimeCast<ImageTransform>( plug->source()->node() );
	}

	inTransformPlug()->setInput(
		upstreamImageTransform ? upstreamImageTransform->outTransformPlug() : nullptr
	);
}
