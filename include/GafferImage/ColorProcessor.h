//////////////////////////////////////////////////////////////////////////
//  
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

#ifndef GAFFERIMAGE_COLORPROCESSOR_H
#define GAFFERIMAGE_COLORPROCESSOR_H

#include "GafferImage/ImageProcessor.h"

namespace GafferImage
{

/// Forms a useful base class for nodes which must process R,G and B channels at the same time
/// to perform some sort of channel mixing.
/// \todo This is currently hardcoded to operate on the "R", "G" and "B" channels - make it able
/// to work on alternative sets of channels. To do this well I think we need to introduce the
/// concept of layers which group channels together (e.g. beauty.R, beauty.G, beauty.B etc).
class ColorProcessor : public ImageProcessor
{

	public :

		ColorProcessor( const std::string &name=defaultName<ColorProcessor>() );
		virtual ~ColorProcessor();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ColorProcessor, ColorProcessorTypeId, ImageProcessor );

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
				
	protected :
	
		virtual bool channelEnabled( const std::string &channel ) const;
	
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		/// Implemented to pass through the hashes from the input plug.
		virtual void hashFormat( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindow( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelNames( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		
		/// Implemented to pass through the input values. Derived classes need only implement computeChannelData().
		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
		/// Implemented to in terms of processColorData().
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;
		
		/// Must be implemented by derived classes to return true if the specified input is used in processColorData().
		/// Must first call the base class implementation and return true if it does.
		virtual bool affectsColorData( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented by derived classes to compute the hash for the color processing - all implementations
		/// must call their base class implementation first.
		virtual void hashColorData( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented by derived classes to modify R, G and B in place.
		virtual void processColorData( const Gaffer::Context *context, IECore::FloatVectorData *r, IECore::FloatVectorData *g, IECore::FloatVectorData *b ) const = 0;

	private :
		
		// Used to store the result of processColorData(), so that it can be reused in computeChannelData().
		Gaffer::ObjectPlug *colorDataPlug();
		const Gaffer::ObjectPlug *colorDataPlug() const;
		
		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ColorProcessor )

} // namespace GafferImage

#endif // GAFFERIMAGE_CHANNELDATAPROCESSOR_H
