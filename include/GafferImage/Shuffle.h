//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_SHUFFLE_H
#define GAFFERIMAGE_SHUFFLE_H

#include "Gaffer/StringPlug.h"

#include "GafferImage/ImageProcessor.h"

namespace GafferImage
{

class Shuffle : public ImageProcessor
{

	public :

		Shuffle( const std::string &name=defaultName<Shuffle>() );
		virtual ~Shuffle();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Shuffle, ShuffleTypeId, ImageProcessor );

		/// A custom plug to hold the name of an output channel and the
		/// name of an input channel to shuffle into it. Add instances
		/// of these to the Shuffle::channelsPlug() to define the shuffle.
		class ChannelPlug : public Gaffer::ValuePlug
		{

			public :

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Shuffle::ChannelPlug, ShuffleChannelPlugTypeId, Gaffer::ValuePlug );

				// Standard constructor. This is needed for serialisation.
				ChannelPlug(
					const std::string &name = defaultName<ChannelPlug>(),
					Direction direction=In,
					unsigned flags = Default
				);
				// Convenience constructor defining a shuffle of the specified
				// in channel to the specified out channel.
				ChannelPlug( const std::string &out, const std::string &in );

				Gaffer::StringPlug *outPlug();
				const Gaffer::StringPlug *outPlug() const;

				Gaffer::StringPlug *inPlug();
				const Gaffer::StringPlug *inPlug() const;

				virtual bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const;
				virtual Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const;

		};

		IE_CORE_DECLAREPTR( ChannelPlug )

		typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ChannelPlug> > ChannelPlugIterator;

		Gaffer::ValuePlug *channelsPlug();
		const Gaffer::ValuePlug *channelsPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		virtual IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

	private :

		std::string inChannelName( const std::string &outChannelName ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Shuffle )

} // namespace GafferImage

#endif // GAFFERIMAGE_SHUFFLE_H
