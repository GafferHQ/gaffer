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

#ifndef GAFFERIMAGE_COPYIMAGEMETADATA_H
#define GAFFERIMAGE_COPYIMAGEMETADATA_H

#include "GafferImage/MetadataProcessor.h"

namespace GafferImage
{

class GAFFERIMAGE_API CopyImageMetadata : public MetadataProcessor
{

	public :

		CopyImageMetadata( const std::string &name=defaultName<CopyImageMetadata>() );
		~CopyImageMetadata() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::CopyImageMetadata, CopyImageMetadataTypeId, MetadataProcessor );

		/// \todo: If ImageProcessor provides an ArrayPlug for "in" instead,
		/// we can remove this secondary image plug.
		ImagePlug *copyFromPlug();
		const ImagePlug *copyFromPlug() const;

		Gaffer::StringPlug *namesPlug();
		const Gaffer::StringPlug *namesPlug() const;

		Gaffer::BoolPlug *invertNamesPlug();
		const Gaffer::BoolPlug *invertNamesPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashProcessedMetadata( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundDataPtr computeProcessedMetadata( const Gaffer::Context *context, const IECore::CompoundData *inputMetadata ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( CopyImageMetadata );

} // namespace GafferImage

#endif // GAFFERIMAGE_COPYIMAGEMETADATA_H
