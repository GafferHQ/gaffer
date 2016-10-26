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

#ifndef GAFFERIMAGE_IMAGESTATS_H
#define GAFFERIMAGE_IMAGESTATS_H

#include "Gaffer/ComputeNode.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/BoxPlug.h"

#include "GafferImage/ImagePlug.h"
#include "GafferImage/ChannelMaskPlug.h"
#include "GafferImage/ImageState.h"

namespace GafferImage
{

/// Provides statistics on an image's colour profile.
/// The ImageStats node outputs the minimum, maximum and average values of the pixel values within a region of interest in the image.
class ImageStats : public Gaffer::ComputeNode
{

	public :

		ImageStats( const std::string &name=staticTypeName() );
		virtual ~ImageStats();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ImageStats, ImageStatsTypeId, Gaffer::ComputeNode );

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

		GafferImage::ImagePlug *inPlug();
		const GafferImage::ImagePlug *inPlug() const;
		ChannelMaskPlug *channelsPlug();
		const ChannelMaskPlug *channelsPlug() const;
		Gaffer::Box2iPlug *regionOfInterestPlug();
		const Gaffer::Box2iPlug *regionOfInterestPlug() const;
		Gaffer::Color4fPlug *averagePlug();
		const Gaffer::Color4fPlug *averagePlug() const;
		Gaffer::Color4fPlug *minPlug();
		const Gaffer::Color4fPlug *minPlug() const;
		Gaffer::Color4fPlug *maxPlug();
		const Gaffer::Color4fPlug *maxPlug() const;

	protected :

		/// Implemented to hash the area we are sampling along with the channel context and regionOfInterest.
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		/// Computes the min, max and average plugs by analyzing the input ImagePlug.
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

	private :

		// Input plug to receive the flattened image from the internal
		// ImageState plug.
		ImagePlug *flattenedInPlug();
		const ImagePlug *flattenedInPlug() const;

		// The internal ImageState node.
		GafferImage::ImageState *imageState();
		const GafferImage::ImageState *imageState() const;

		/// Sets channelName to the channel which corresponds to the output plug. The channel name is
		/// computed from the intersection of the "in" plug's channels and the "channels" plug's channels.
		/// If multiple channels are found to have the same channel index, the first is used.
		/// For more information on this, please see ChannelMaskPlug::removeDuplicateIndices().
		void channelNameFromOutput( const Gaffer::ValuePlug *output, std::string &channelName ) const;

		/// A convenience function to just set the plug to 0 or 1 depending on what it's index is.
		void setOutputToDefault( Gaffer::FloatPlug *output ) const;

		/// Implemented to initialize the default format settings if they don't exist already.
		void parentChanging( Gaffer::GraphComponent *newParent );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ImageStats );

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGESTATS_H
