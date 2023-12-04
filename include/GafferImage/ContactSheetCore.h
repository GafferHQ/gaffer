//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, John Haddon. All rights reserved.
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

#include "GafferImage/FormatPlug.h"
#include "GafferImage/FlatImageProcessor.h"

#include "Gaffer/StringPlug.h"

namespace GafferImage
{

class Crop;
class Resample;

class GAFFERIMAGE_API ContactSheetCore : public FlatImageProcessor
{

	public :

		explicit ContactSheetCore( const std::string &name=defaultName<ContactSheetCore>() );
		~ContactSheetCore() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::ContactSheetCore, ContactSheetCoreTypeId, FlatImageProcessor );

		FormatPlug *formatPlug();
		const FormatPlug *formatPlug() const;

		Gaffer::Box2fVectorDataPlug *tilesPlug();
		const Gaffer::Box2fVectorDataPlug *tilesPlug() const;

		Gaffer::StringPlug *tileVariablePlug();
		const Gaffer::StringPlug *tileVariablePlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const final;

	private :

		Gaffer::ObjectPlug *coveragePlug();
		const Gaffer::ObjectPlug *coveragePlug() const;

		Gaffer::M33fPlug *resampleMatrixPlug();
		const Gaffer::M33fPlug *resampleMatrixPlug() const;

		ImagePlug *resampledInPlug();
		const ImagePlug *resampledInPlug() const;

		Crop *crop();
		const Crop *crop() const;

		Resample *resample();
		const Resample *resample() const;

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const final;

		void hashViewNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		IECore::ConstStringVectorDataPtr computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const final;

		void hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const final;

		void hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const final;

		void hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		IECore::ConstCompoundDataPtr computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const final;

		void hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const final;

		void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const final;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ContactSheetCore )

} // namespace GafferImage
