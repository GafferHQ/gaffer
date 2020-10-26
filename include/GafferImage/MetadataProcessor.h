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

#ifndef GAFFERIMAGE_METADATAPROCESSOR_H
#define GAFFERIMAGE_METADATAPROCESSOR_H

#include "GafferImage/ImageProcessor.h"

#include "Gaffer/CompoundDataPlug.h"

namespace GafferImage
{

/// The MetadataProcessor class provides a base class for modifying metadata
/// of an image while passing everything else through unchanged.
class GAFFERIMAGE_API MetadataProcessor : public ImageProcessor
{

	public :

		MetadataProcessor( const std::string &name=defaultName<MetadataProcessor>() );
		~MetadataProcessor() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::MetadataProcessor, MetadataProcessorTypeId, ImageProcessor );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		// Reimplemented to call hashProcessedMetadata()
		void hashMetadata( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		// Reimplemented to call computeProcessedMetadata()
		IECore::ConstCompoundDataPtr computeMetadata( const Gaffer::Context *context, const ImagePlug *parent ) const override;

		/// Must be implemented by derived classes to compute the hash for the work done in computeProcessedMetadata().
		virtual void hashProcessedMetadata( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented by derived classes to process the incoming metadata.
		virtual IECore::ConstCompoundDataPtr computeProcessedMetadata( const Gaffer::Context *context, const IECore::CompoundData *inputMetadata ) const = 0;

};

IE_CORE_DECLAREPTR( MetadataProcessor );

} // namespace GafferImage

#endif // GAFFERIMAGE_METADATAPROCESSOR_H
