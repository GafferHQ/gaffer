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

#pragma once

#include "GafferImage/ChannelDataProcessor.h"

#include "Gaffer/CompoundNumericPlug.h"

namespace GafferImage
{

/// The clamp node implements a channel-wise clamping operation
/// with the option to have an override on the clamp-to value
/// The logic used is:
///
/// If the min/max clamp is enabled, if the channel value is outside the range,
/// either clamp to range or, if enabled, clamp to the provided value
//
class GAFFERIMAGE_API Clamp : public ChannelDataProcessor
{

	public :

		explicit Clamp( const std::string &name=defaultName<Clamp>() );
		~Clamp() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::Clamp, ClampTypeId, ChannelDataProcessor );

		//! @name Plug Accessors
		/// Returns a pointer to the node's plugs.
		//////////////////////////////////////////////////////////////
		//@{
		Gaffer::Color4fPlug *minPlug();
		const Gaffer::Color4fPlug *minPlug() const;
		Gaffer::Color4fPlug *maxPlug();
		const Gaffer::Color4fPlug *maxPlug() const;
		Gaffer::Color4fPlug *minClampToPlug();
		const Gaffer::Color4fPlug *minClampToPlug() const;
		Gaffer::Color4fPlug *maxClampToPlug();
		const Gaffer::Color4fPlug *maxClampToPlug() const;

		Gaffer::BoolPlug *minEnabledPlug();
		const Gaffer::BoolPlug *minEnabledPlug() const;
		Gaffer::BoolPlug *maxEnabledPlug();
		const Gaffer::BoolPlug *maxEnabledPlug() const;
		Gaffer::BoolPlug *minClampToEnabledPlug();
		const Gaffer::BoolPlug *minClampToEnabledPlug() const;
		Gaffer::BoolPlug *maxClampToEnabledPlug();
		const Gaffer::BoolPlug *maxClampToEnabledPlug() const;
		//@}

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		bool enabled() const override;

		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channelName, IECore::FloatVectorDataPtr outData ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Clamp )

} // namespace GafferImage
