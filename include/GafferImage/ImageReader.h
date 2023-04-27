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

#pragma once

#include "GafferImage/ImageNode.h"

#include "Gaffer/CompoundNumericPlug.h"

#include <functional>

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( ColorSpace )
IE_CORE_FORWARDDECLARE( OpenImageIOReader )

class GAFFERIMAGE_API ImageReader : public ImageNode
{

	public :

		explicit ImageReader( const std::string &name=defaultName<ImageReader>() );
		~ImageReader() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::ImageReader, ImageReaderTypeId, ImageNode );

		/// The MissingFrameMode controls how to handle missing images.
		/// It is distinct from OpenImageIOReader::MissingFrameMode so
		/// that we can provide alternate modes using higher
		/// level approaches in the future (e.g interpolation).
		enum MissingFrameMode
		{
			Error = 0,
			Black,
			Hold,
		};

		/// The FrameMaskMode controls how to handle images
		/// outside of the values provided by the start
		/// and end frame masks.
		enum FrameMaskMode
		{
			None = 0,
			BlackOutside,
			ClampToFrame,
		};

		/// Defines how we get channel names from the information stored in a file.
		/// Because some software like Nuke fails to follow the spec, the Default
		/// mode employs heuristics to try and guess the intention.
		enum class ChannelInterpretation
		{
			Legacy,
			Default,
			Specification,
		};

		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		/// Number of times the node has been refreshed.
		Gaffer::IntPlug *refreshCountPlug();
		const Gaffer::IntPlug *refreshCountPlug() const;

		Gaffer::IntPlug *missingFrameModePlug();
		const Gaffer::IntPlug *missingFrameModePlug() const;

		Gaffer::IntPlug *startModePlug();
		const Gaffer::IntPlug *startModePlug() const;

		Gaffer::IntPlug *startFramePlug();
		const Gaffer::IntPlug *startFramePlug() const;

		Gaffer::IntPlug *endModePlug();
		const Gaffer::IntPlug *endModePlug() const;

		Gaffer::IntPlug *endFramePlug();
		const Gaffer::IntPlug *endFramePlug() const;

		Gaffer::StringPlug *colorSpacePlug();
		const Gaffer::StringPlug *colorSpacePlug() const;

		Gaffer::IntPlug *channelInterpretationPlug();
		const Gaffer::IntPlug *channelInterpretationPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		static size_t supportedExtensions( std::vector<std::string> &extensions );

		/// A function which can take information about a file being read, and return the colorspace
		/// of the data within the file. This is used whenever the colorSpace plug is at its default
		/// value.
		using DefaultColorSpaceFunction = std::function<const std::string ( const std::string &fileName, const std::string &fileFormat, const std::string &dataType, const IECore::CompoundData *metadata )>;
		static void setDefaultColorSpaceFunction( DefaultColorSpaceFunction f );
		static DefaultColorSpaceFunction getDefaultColorSpaceFunction();

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		void hashViewNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstStringVectorDataPtr computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundDataPtr computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashDeep( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		bool computeDeep( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashSampleOffsets( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstIntVectorDataPtr computeSampleOffsets( const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

	private :

		// We use internal nodes to do all the hard work,
		// but we need to store intermediate results between
		// those nodes in order to affect the outcome.

		OpenImageIOReader *oiioReader();
		const OpenImageIOReader *oiioReader() const;

		Gaffer::AtomicCompoundDataPlug *intermediateMetadataPlug();
		const Gaffer::AtomicCompoundDataPlug *intermediateMetadataPlug() const;

		Gaffer::StringPlug *intermediateColorSpacePlug();
		const Gaffer::StringPlug *intermediateColorSpacePlug() const;

		ColorSpace *colorSpace();
		const ColorSpace *colorSpace() const;

		GafferImage::ImagePlug *intermediateImagePlug();
		const GafferImage::ImagePlug *intermediateImagePlug() const;

		static DefaultColorSpaceFunction &defaultColorSpaceFunction();

		static size_t g_firstChildIndex;

};

IE_CORE_DECLAREPTR( ImageReader )

} // namespace GafferImage
