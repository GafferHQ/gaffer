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

#ifndef GAFFERIMAGE_IMAGEREADER_H
#define GAFFERIMAGE_IMAGEREADER_H

#include "Gaffer/CompoundNumericPlug.h"

#include "GafferImage/ImageNode.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( ColorSpace )
IE_CORE_FORWARDDECLARE( OpenImageIOReader )

class ImageReader : public ImageNode
{

	public :

		ImageReader( const std::string &name=defaultName<ImageReader>() );
		virtual ~ImageReader();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ImageReader, ImageReaderTypeId, ImageNode );

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

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

		static size_t supportedExtensions( std::vector<std::string> &extensions );

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

	private :

		// We use internal nodes to do all the hard work,
		// but we need to store intermediate results between
		// those nodes in order to affect the outcome.

		OpenImageIOReader *oiioReader();
		const OpenImageIOReader *oiioReader() const;

		Gaffer::CompoundObjectPlug *intermediateMetadataPlug();
		const Gaffer::CompoundObjectPlug *intermediateMetadataPlug() const;

		Gaffer::StringPlug *intermediateColorSpacePlug();
		const Gaffer::StringPlug *intermediateColorSpacePlug() const;

		ColorSpace *colorSpace();
		const ColorSpace *colorSpace() const;

		GafferImage::ImagePlug *intermediateImagePlug();
		const GafferImage::ImagePlug *intermediateImagePlug() const;

		void hashMaskedOutput( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h, bool alwaysClampToFrame = false ) const;
		void computeMaskedOutput( Gaffer::ValuePlug *output, const Gaffer::Context *context, bool alwaysClampToFrame = false ) const;

		bool computeFrameMask( const Gaffer::Context *context, Gaffer::ContextPtr &maskedContext ) const;

		static size_t g_firstChildIndex;

};

IE_CORE_DECLAREPTR( ImageReader )

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGEREADER_H
