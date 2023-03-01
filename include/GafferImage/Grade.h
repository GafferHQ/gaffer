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

/// The grade node implements the common grade operation to the RGB channels of the input.
/// The computation performed is:
/// A = multiply * (gain - lift) / (whitePoint - blackPoint)
/// B = offset + lift - A * blackPoint
/// output = pow( A * input + B, 1/gamma )
//
class GAFFERIMAGE_API Grade : public ChannelDataProcessor
{

	public :

		Grade( const std::string &name=defaultName<Grade>() );
		~Grade() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::Grade, GradeTypeId, ChannelDataProcessor );

		Gaffer::Color4fPlug *blackPointPlug();
		const Gaffer::Color4fPlug *blackPointPlug() const;
		Gaffer::Color4fPlug *whitePointPlug();
		const Gaffer::Color4fPlug *whitePointPlug() const;
		Gaffer::Color4fPlug *liftPlug();
		const Gaffer::Color4fPlug *liftPlug() const;
		Gaffer::Color4fPlug *gainPlug();
		const Gaffer::Color4fPlug *gainPlug() const;
		Gaffer::Color4fPlug *multiplyPlug();
		const Gaffer::Color4fPlug *multiplyPlug() const;
		Gaffer::Color4fPlug *offsetPlug();
		const Gaffer::Color4fPlug *offsetPlug() const;
		Gaffer::Color4fPlug *gammaPlug();
		const Gaffer::Color4fPlug *gammaPlug() const;
		Gaffer::BoolPlug *blackClampPlug();
		const Gaffer::BoolPlug *blackClampPlug() const;
		Gaffer::BoolPlug *whiteClampPlug();
		const Gaffer::BoolPlug *whiteClampPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		bool channelEnabled( const std::string &channel ) const override;

		void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void processChannelData( const Gaffer::Context *context, const ImagePlug *parent, const std::string &channelIndex, IECore::FloatVectorDataPtr outData ) const override;

	private :

		void parameters( size_t channelIndex, float &a, float &b, float &gamma ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Grade );

} // namespace GafferImage
