//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_IMAGEPROCESSOR_H
#define GAFFERIMAGE_IMAGEPROCESSOR_H

#include "GafferImage/ImageNode.h"

namespace GafferImage
{

/// The ImageProcessor class provides a base class for nodes which will take an image input
/// and modify it in some way.
class ImageProcessor : public ImageNode
{

	public :

		ImageProcessor( const std::string &name=defaultName<ImageProcessor>() );
		virtual ~ImageProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ImageProcessor, ImageProcessorTypeId, ImageNode );

		/// Images enter the node through inPlug() and are output in processed form on ImageNode::outPlug()
		ImagePlug *inPlug();
		const ImagePlug *inPlug() const;

		virtual Gaffer::Plug *correspondingInput( const Gaffer::Plug *output );
		virtual const Gaffer::Plug *correspondingInput( const Gaffer::Plug *output ) const;

	protected :

		/// Reimplemented to pass through the hashes of the inPlug() when the node is disabled.
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// Reimplemented from ImageNode to pass through the inPlug() computations when the node is disabled.
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ImageProcessor )

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEPROCESSOR_H
