//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferImage/ImagePrimitiveSource.h"

#include "Gaffer/Context.h"

#include "IECore/BoxAlgo.h"
#include "IECore/BoxOps.h"
#include "IECore/NullObject.h"

namespace GafferImage
{

template<typename BaseType>
const IECore::RunTimeTyped::TypeDescription<ImagePrimitiveSource<BaseType> > ImagePrimitiveSource<BaseType>::g_typeDescription;

template<typename BaseType>
ImagePrimitiveSource<BaseType>::ImagePrimitiveSource( const std::string &name )
	:	BaseType( name )
{
	BaseType::addChild( new Gaffer::ObjectPlug( "__imagePrimitive", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
	BaseType::addChild( new Gaffer::ObjectPlug( "__inputImagePrimitive", Gaffer::Plug::In, IECore::NullObject::defaultNullObject(), Gaffer::Plug::Default & ~Gaffer::Plug::Serialisable ) );
	inputImagePrimitivePlug()->setInput( imagePrimitivePlug() );

	// disable caching on our outputs, as we're basically caching the entire
	// image ourselves in __inputImagePrimitive.
	for( Gaffer::OutputPlugIterator it( BaseType::outPlug() ); !it.done(); ++it )
	{
		(*it)->setFlags( Gaffer::Plug::Cacheable, false );
	}
}

template<typename BaseType>
ImagePrimitiveSource<BaseType>::~ImagePrimitiveSource()
{
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::affects( const Gaffer::Plug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const
{
	BaseType::affects( input, outputs );

	if( input == inputImagePrimitivePlug() )
	{
		for( Gaffer::ValuePlugIterator it( BaseType::outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BaseType::hash( output, context, h );

	if( output == imagePrimitivePlug() )
	{
		hashImagePrimitive( context, h );
	}
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == imagePrimitivePlug() )
	{
		IECoreImage::ConstImagePrimitivePtr image = computeImagePrimitive( context );
		Gaffer::ObjectPlug *plug = static_cast<Gaffer::ObjectPlug *>( output );
		if( image )
		{
			plug->setValue( image );
		}
		else
		{
			plug->setValue( plug->defaultValue() );
		}
		return;
	}

	return BaseType::compute( output, context );
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BaseType::hashFormat( output, context, h );
	inputImagePrimitivePlug()->hash( h );
}

template<typename BaseType>
GafferImage::Format ImagePrimitiveSource<BaseType>::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i result;
	IECoreImage::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECoreImage::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
	if( image )
	{
		return GafferImage::Format( image->getDisplayWindow(), 1.0f, /* fromEXRSpace = */ true );
	}
	return GafferImage::Format();
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BaseType::hashDataWindow( output, context, h );
	inputImagePrimitivePlug()->hash( h );
}

template<typename BaseType>
Imath::Box2i ImagePrimitiveSource<BaseType>::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECoreImage::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECoreImage::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
	if( image )
	{
		const Format format( image->getDisplayWindow(), 1.0f, /* fromEXRSpace = */ true );
		return format.fromEXRSpace( image->getDataWindow() );
	}
	return Imath::Box2i();
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BaseType::hashMetadata( parent, context, h );
	inputImagePrimitivePlug()->hash( h );
}

template<typename BaseType>
IECore::ConstCompoundDataPtr ImagePrimitiveSource<BaseType>::computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECoreImage::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECoreImage::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
	if( image )
	{
		return image->blindData();
	}
	else
	{
		return BaseType::outPlug()->metadataPlug()->defaultValue();
	}
}

template<typename BaseType>
bool ImagePrimitiveSource<BaseType>::computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return false;
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ImagePlug::flatTileSampleOffsets()->hash( h );
}

template<typename BaseType>
IECore::ConstIntVectorDataPtr ImagePrimitiveSource<BaseType>::computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	return ImagePlug::flatTileSampleOffsets();
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BaseType::hashChannelNames( output, context, h );
	inputImagePrimitivePlug()->hash( h );
}

template<typename BaseType>
IECore::ConstStringVectorDataPtr ImagePrimitiveSource<BaseType>::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::StringVectorDataPtr result = new IECore::StringVectorData();
	IECoreImage::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECoreImage::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
	if( image )
	{
		image->channelNames( result->writable() );
	}
	else
	{
		std::vector<std::string> &channelStrVector( result->writable() );
		channelStrVector.push_back("R");
		channelStrVector.push_back("G");
		channelStrVector.push_back("B");
	}

	return result;
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	BaseType::hashChannelData( output, context, h );
	h.append( context->get<Imath::V2i>( ImagePlug::tileOriginContextName ) );
	h.append( context->get<std::string>( ImagePlug::channelNameContextName ) );
	inputImagePrimitivePlug()->hash( h );
}

template<typename BaseType>
IECore::ConstFloatVectorDataPtr ImagePrimitiveSource<BaseType>::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECoreImage::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECoreImage::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
	if( !image )
	{
		return ImagePlug::blackTile();
	}

	IECore::ConstFloatVectorDataPtr channelData = image->getChannel<float>( channelName );
	if( !channelData )
	{
		return ImagePlug::blackTile();
	}
	const std::vector<float> &channel = channelData->readable();

	IECore::FloatVectorDataPtr resultData = new IECore::FloatVectorData;
	std::vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize(), 0.0f );

	const Format format( image->getDisplayWindow(), 1.0f, /* fromEXRSpace = */ true );
	const Imath::Box2i exrDataWindow = image->getDataWindow();
	const Imath::Box2i dataWindow = format.fromEXRSpace( exrDataWindow );

	Imath::Box2i tileBound( tileOrigin, tileOrigin + Imath::V2i( GafferImage::ImagePlug::tileSize() ) );
	Imath::Box2i bound = IECore::boxIntersection( tileBound, dataWindow );

	for( int y = bound.min.y; y<bound.max.y; y++ )
	{
		size_t srcIndex = ( format.toEXRSpace( y ) - exrDataWindow.min.y ) * dataWindow.size().x + bound.min.x - exrDataWindow.min.x;
		size_t dstIndex = ( y - tileBound.min.y ) * GafferImage::ImagePlug::tileSize() + bound.min.x - tileBound.min.x;
		const size_t srcEndIndex = srcIndex + bound.size().x;
		while( srcIndex < srcEndIndex )
		{
			result[dstIndex++] = channel[srcIndex++];
		}
	}

	return resultData;
}

template<typename BaseType>
Gaffer::ObjectPlug *ImagePrimitiveSource<BaseType>::imagePrimitivePlug()
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__imagePrimitive" );
}

template<typename BaseType>
const Gaffer::ObjectPlug *ImagePrimitiveSource<BaseType>::imagePrimitivePlug() const
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__imagePrimitive" );
}

template<typename BaseType>
Gaffer::ObjectPlug *ImagePrimitiveSource<BaseType>::inputImagePrimitivePlug()
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__inputImagePrimitive" );
}

template<typename BaseType>
const Gaffer::ObjectPlug *ImagePrimitiveSource<BaseType>::inputImagePrimitivePlug() const
{
	return BaseType::template getChild<Gaffer::ObjectPlug>( "__inputImagePrimitive" );
}

} // namespace GafferImage
