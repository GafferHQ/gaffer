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

#ifndef GAFFERIMAGE_IMAGEPRIMITIVESOURCE_H
#define GAFFERIMAGE_IMAGEPRIMITIVESOURCE_H

#include "Gaffer/TypedObjectPlug.h"

#include "GafferImage/ImageNode.h"

namespace GafferImage
{

template<typename BaseType>
class ImagePrimitiveSource : public BaseType
{

	public :

		IECORE_RUNTIMETYPED_DECLARETEMPLATE( ImagePrimitiveSource<BaseType>, BaseType );
		IE_CORE_DECLARERUNTIMETYPEDDESCRIPTION( ImagePrimitiveSource<BaseType> );

		virtual ~ImagePrimitiveSource();
				
		virtual void affects( const Gaffer::Plug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const;
		
	protected :

		ImagePrimitiveSource( const std::string &name );

		Gaffer::ObjectPlug *imagePrimitivePlug();
		const Gaffer::ObjectPlug *imagePrimitivePlug() const;

		virtual void hashImagePrimitive( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// It is ok to return 0 if no ImagePrimitive is available.
		virtual IECore::ConstImagePrimitivePtr computeImagePrimitive( const Gaffer::Context *context ) const = 0;		
		
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

	private :
	
		Gaffer::ObjectPlug *inputImagePrimitivePlug();
		const Gaffer::ObjectPlug *inputImagePrimitivePlug() const;
		
};

typedef ImagePrimitiveSource<ImageNode> ImagePrimitiveNode;
IE_CORE_DECLAREPTR( ImagePrimitiveNode );

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEPRIMITIVESOURCE_H
