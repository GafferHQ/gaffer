//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
//  Copyright (c) 2015, Nvizible Ltd. All rights reserved.
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

#ifndef GAFFERIMAGE_IMAGESTATE_H
#define GAFFERIMAGE_IMAGESTATE_H

#include "Gaffer/NumericPlug.h"

#include "GafferImage/ImageProcessor.h"

namespace GafferImage
{

/// A node for changing the state of
class ImageState : public ImageProcessor
{

	public :

		ImageState( const std::string &name=defaultName<ImageState>() );
		virtual ~ImageState();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ImageState, ImageStateTypeId, ImageProcessor );

		Gaffer::IntPlug *deepStatePlug();
		const Gaffer::IntPlug *deepStatePlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

		static const IECore::InternedString sampleMergingZName;
		static const IECore::InternedString sampleMergingZBackName;
		static const IECore::InternedString sampleMergingSampleOffsetsName;
		static const IECore::InternedString sampleMergingSampleContributionIdsName;
		static const IECore::InternedString sampleMergingSampleContributionAmountsName;
		static const IECore::InternedString sampleMergingSampleContributionOffsetsName;

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		virtual void hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDeepState( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual IECore::ConstIntVectorDataPtr computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual int computeDeepState( const Gaffer::Context *context, const ImagePlug *parent ) const;

	private :

		Gaffer::IntVectorDataPlug *sampleSortingPlug();
		const Gaffer::IntVectorDataPlug *sampleSortingPlug() const;
		Gaffer::CompoundObjectPlug *sampleMergingPlug();
		const Gaffer::CompoundObjectPlug *sampleMergingPlug() const;

		Gaffer::FloatVectorDataPlug *sortedChannelDataPlug();
		const Gaffer::FloatVectorDataPlug *sortedChannelDataPlug() const;
		Gaffer::FloatVectorDataPlug *tidyChannelDataPlug();
		const Gaffer::FloatVectorDataPlug *tidyChannelDataPlug() const;

		virtual void hashChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const int deepState, const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h, const bool useCached ) const;
		virtual void hashSampleSorting( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashSampleMerging( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashSortedChannelData( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashTidyChannelData( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		IECore::MurmurHash sampleSortingHash( const Imath::V2i &tileOrigin ) const;
		IECore::MurmurHash sampleMergingHash( const Imath::V2i &tileOrigin ) const;
		IECore::MurmurHash sortedChannelDataHash( const std::string &channelName, const Imath::V2i &tileOrigin ) const;
		IECore::MurmurHash tidyChannelDataHash( const std::string &channelName, const Imath::V2i &tileOrigin ) const;

		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const int deepState, const Gaffer::Context *context, const ImagePlug *parent, const bool useCached ) const;
		virtual IECore::ConstIntVectorDataPtr computeSampleSorting( const Imath::V2i &tileOrigin ) const;
		virtual IECore::ConstCompoundObjectPtr computeSampleMerging( const Imath::V2i &tileOrigin ) const;
		virtual IECore::ConstFloatVectorDataPtr computeSortedChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const;
		virtual IECore::ConstFloatVectorDataPtr computeTidyChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const;

		IECore::ConstIntVectorDataPtr sampleSorting( const Imath::V2i &tileOrigin ) const;
		IECore::ConstCompoundObjectPtr sampleMerging( const Imath::V2i &tileOrigin ) const;
		IECore::ConstFloatVectorDataPtr sortedChannelData( const std::string &channelName, const Imath::V2i &tileOrigin ) const;
		IECore::ConstFloatVectorDataPtr tidyChannelData( const std::string &channelName, const Imath::V2i &tileOrigin ) const;

		IECore::ConstFloatVectorDataPtr sortedChannelData( IECore::ConstFloatVectorDataPtr data, const Imath::V2i &tileOrigin ) const;
		IECore::ConstFloatVectorDataPtr tidyChannelData( IECore::ConstFloatVectorDataPtr data, IECore::ConstFloatVectorDataPtr alphaData, const Imath::V2i &tileOrigin ) const;
		IECore::ConstFloatVectorDataPtr flatChannelData( IECore::ConstFloatVectorDataPtr data, IECore::ConstFloatVectorDataPtr alphaData, const Imath::V2i &tileOrigin ) const;
		IECore::ConstFloatVectorDataPtr flatZData( IECore::ConstFloatVectorDataPtr zData, IECore::ConstFloatVectorDataPtr zBackData, IECore::ConstFloatVectorDataPtr alphaData, const std::string &channelName, const Imath::V2i &tileOrigin ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ImageState )

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGESTATE_H
