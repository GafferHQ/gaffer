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

#include "GafferImage/DeepState.h"
#include "GafferImage/Export.h"
#include "GafferImage/TypeIds.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( ImagePlug )
IE_CORE_FORWARDDECLARE( FilterPlug )

class GAFFERIMAGE_API ImageSampler : public Gaffer::ComputeNode
{

	public :

		ImageSampler( const std::string &name=defaultName<ImageSampler>() );
		~ImageSampler() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferImage::ImageSampler, ImageSamplerTypeId, ComputeNode );

		ImagePlug *imagePlug();
		const ImagePlug *imagePlug() const;

		Gaffer::StringVectorDataPlug *channelsPlug();
		const Gaffer::StringVectorDataPlug *channelsPlug() const;

		Gaffer::V2fPlug *pixelPlug();
		const Gaffer::V2fPlug *pixelPlug() const;

		Gaffer::Color4fPlug *colorPlug();
		const Gaffer::Color4fPlug *colorPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

	private :

		// Returns the channel to be read for the specified child of colorPlug(),
		// returning the empty string if the channel doesn't exist.
		std::string channelName( const Gaffer::ValuePlug *output ) const;

		// Input plug to receive the flattened image from the internal
		// deepState plug.
		ImagePlug *flattenedInPlug();
		const ImagePlug *flattenedInPlug() const;

		// The internal DeepState node.
		GafferImage::DeepState *deepState();
		const GafferImage::DeepState *deepState() const;

		static size_t g_firstPlugIndex;

};

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGESAMPLER_H
