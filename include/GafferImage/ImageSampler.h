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

#ifndef GAFFERIMAGE_IMAGESAMPLER_H
#define GAFFERIMAGE_IMAGESAMPLER_H

#include "Gaffer/ComputeNode.h"
#include "Gaffer/CompoundNumericPlug.h"

#include "GafferImage/TypeIds.h"

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( ImagePlug )
IE_CORE_FORWARDDECLARE( FilterPlug )

/// Samples colours at image locations.
/// \todo Support for choosing which channels to sample - ideally
/// we need ChannelMaskPlug to properly support layers to do that.
class ImageSampler : public Gaffer::ComputeNode
{

	public :

		ImageSampler( const std::string &name=defaultName<ImageSampler>() );
		virtual ~ImageSampler();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ImageSampler, ImageSamplerTypeId, ComputeNode );

		ImagePlug *imagePlug();
		const ImagePlug *imagePlug() const;

		Gaffer::V2fPlug *pixelPlug();
		const Gaffer::V2fPlug *pixelPlug() const;

		FilterPlug *filterPlug();
		const FilterPlug *filterPlug() const;

		Gaffer::Color4fPlug *colorPlug();
		const Gaffer::Color4fPlug *colorPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

	private :

		// Returns the channel to be read for the specified child of colorPlug(),
		// returning the empty string if the channel doesn't exist.
		std::string channelName( const Gaffer::ValuePlug *output ) const;

		static size_t g_firstPlugIndex;

};

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGESAMPLER_H
