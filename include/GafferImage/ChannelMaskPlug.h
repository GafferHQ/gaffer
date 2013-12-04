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

#ifndef GAFFERIMAGE_CHANNELMASKPLUG_H
#define GAFFERIMAGE_CHANNELMASKPLUG_H

#include "Gaffer/TypedObjectPlug.h"

#include "GafferImage/TypeIds.h"

namespace GafferImage
{

class ChannelMaskPlug : public Gaffer::StringVectorDataPlug
{
	public:

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ChannelMaskPlug, ChannelMaskPlugTypeId, Gaffer::StringVectorDataPlug );
		
		/// A copy of defaultValue is taken - it must not be null.
		ChannelMaskPlug(
			const std::string &name,
			Direction direction,
			IECore::ConstStringVectorDataPtr defaultValue,
			unsigned flags = Default
		);
		virtual ~ChannelMaskPlug();

		/// Performs an in-place intersection of inChannels and the channels held within the StringVectorDataPlug.
		void maskChannels( std::vector<std::string> &inChannels ) const;

		/// Returns the index of a channel within it's layer.
		static int channelIndex( std::string channel );

		/// Removes channels that have the same channelIndex as another so that the list only contains channels with a unique index.
		static void removeDuplicateIndices( std::vector<std::string> &inChannels );
};

IE_CORE_DECLAREPTR( ChannelMaskPlug );

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ChannelMaskPlug> > ChannelMaskPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, ChannelMaskPlug> > InputChannelMaskPlugIterator;
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, ChannelMaskPlug> > OutputChannelMaskPlugIterator;

typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, ChannelMaskPlug>, Gaffer::PlugPredicate<> > RecursiveChannelMaskPlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, ChannelMaskPlug>, Gaffer::PlugPredicate<> > RecursiveInputChannelMaskPlugIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, ChannelMaskPlug>, Gaffer::PlugPredicate<> > RecursiveOutputChannelMaskPlugIterator;

} // namespace GafferImage

#endif // GAFFERIMAGE_CHANNELMASKPLUG_H
