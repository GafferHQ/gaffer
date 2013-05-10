//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "IECore/BoxOps.h"
#include "IECore/BoxAlgo.h"
#include "IECore/NullObject.h"

#include "GafferImage/ImagePrimitiveSource.h"

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
	for( Gaffer::OutputPlugIterator it( BaseType::outPlug() ); it!=it.end(); it++ )
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
		for( Gaffer::ValuePlugIterator it( BaseType::outPlug() ); it != it.end(); it++ )
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
void ImagePrimitiveSource<BaseType>::hashFormatPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inputImagePrimitivePlug()->hash( h );
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashChannelNamesPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inputImagePrimitivePlug()->hash( h );
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashDataWindowPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inputImagePrimitivePlug()->hash( h );
}

template<typename BaseType>
void ImagePrimitiveSource<BaseType>::hashChannelDataPlug( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	inputImagePrimitivePlug()->hash( h );
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
		
template<typename BaseType>
void ImagePrimitiveSource<BaseType>::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == imagePrimitivePlug() )
	{
		IECore::ConstImagePrimitivePtr image = computeImagePrimitive( context );
		Gaffer::ObjectPlug *plug = static_cast<Gaffer::ObjectPlug *>( output );
		plug->setValue( image ? image : plug->defaultValue() );
		return;
	}
	
	return BaseType::compute( output, context );
}

template<typename BaseType>
GafferImage::Format ImagePrimitiveSource<BaseType>::computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i result;
	IECore::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECore::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
	if( image )
	{
		result = image->getDisplayWindow();
	}
	return GafferImage::Format( result.max[0]-result.min[0]+1, result.max[1]-result.min[1]+1 );
}

template<typename BaseType>
Imath::Box2i ImagePrimitiveSource<BaseType>::computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	Imath::Box2i result;
	IECore::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECore::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
	if( image )
	{
		result = image->getDataWindow();
	}
	return result;
}

template<typename BaseType>
IECore::ConstStringVectorDataPtr ImagePrimitiveSource<BaseType>::computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::StringVectorDataPtr result = new IECore::StringVectorData();
	IECore::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECore::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
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
IECore::ConstFloatVectorDataPtr ImagePrimitiveSource<BaseType>::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const
{
	IECore::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECore::ImagePrimitive>( inputImagePrimitivePlug()->getValue() );
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
	
	Imath::Box2i dataWindow = image->getDataWindow();
	Imath::Box2i tileBound( tileOrigin, tileOrigin + Imath::V2i( GafferImage::ImagePlug::tileSize() - 1 ) );
	Imath::Box2i bound = IECore::boxIntersection( tileBound, dataWindow );
	
	for( int y = bound.min.y; y<=bound.max.y; y++ )
	{
		size_t srcIndex = (y - dataWindow.min.y ) * ( dataWindow.size().x + 1 ) + bound.min.x - dataWindow.min.x;
		size_t dstIndex = (y - tileBound.min.y) * GafferImage::ImagePlug::tileSize() + bound.min.x - tileBound.min.x;
		const size_t srcEndIndex = srcIndex + bound.size().x;
		while( srcIndex <= srcEndIndex )
		{
			result[dstIndex++] = channel[srcIndex++];
		}
	}
	
	return resultData;
}

} // namespace GafferImage
