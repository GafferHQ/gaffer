//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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
#ifndef GAFFERIMAGE_SCALE_H
#define GAFFERIMAGE_SCALE_H

#include "GafferImage/ImageProcessor.h"
#include "GafferImage/FilterPlug.h"

#include "Gaffer/CompoundNumericPlug.h"

namespace GafferImage
{

/// Scales an image by a decimal factor.
class Scale : public ImageProcessor
{

	public :

		Scale( const std::string &name=defaultName<Scale>() );
		virtual ~Scale();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Scale, ScaleTypeId, ImageProcessor );
	
		/// Plug accessors.	
		GafferImage::FilterPlug *filterPlug();
		const GafferImage::FilterPlug *filterPlug() const;
		Gaffer::V2fPlug *scalePlug();
		const Gaffer::V2fPlug *scalePlug() const;
		Gaffer::V2fPlug *originPlug();
		const Gaffer::V2fPlug *originPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
		virtual bool enabled() const;
				
	protected :
		
		virtual void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;

		/// Scales the input plug with a filter by doing a 2-pass squash/stretch.
		/// We scale the image by doing two passes over the input in first the horizontal and then vertical directions.
		/// On each pass we use the chosen filter to create a (row or column) buffer of pixels their weighted contribution to each pixel on the row or column.
		/// Using this column/row buffer we iterate over the input and sum the contributing pixels. The result is normalized by the sum of weights.
		/// This process is repeated once for the vertical and horizontal passes and the final result is written into the output buffer.
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;
		
	private :

		static size_t g_firstPlugIndex;
		
};

IE_CORE_DECLAREPTR( Scale )

} // namespace GafferImage

#endif // GAFFERIMAGE_SCALE_H
