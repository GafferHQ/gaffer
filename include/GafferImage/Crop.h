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

#ifndef GAFFERIMAGE_CROP_H
#define GAFFERIMAGE_CROP_H

#include "Gaffer/BoxPlug.h"

#include "GafferImage/Export.h"
#include "GafferImage/ImageProcessor.h"

namespace GafferImage
{
	IE_CORE_FORWARDDECLARE( FormatPlug );

class GAFFERIMAGE_API Crop : public ImageProcessor
{
	public :

		Crop( const std::string &name=defaultName<Crop>() );
		virtual ~Crop();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Crop, CropTypeId, ImageProcessor );

		enum AreaSource
		{
			Area = 0,
			DataWindow = 1,
			DisplayWindow = 2,
			Format = 3
		};

		Gaffer::IntPlug *areaSourcePlug();
		const Gaffer::IntPlug *areaSourcePlug() const;

		Gaffer::Box2iPlug *areaPlug();
		const Gaffer::Box2iPlug *areaPlug() const;

		GafferImage::FormatPlug *formatPlug();
		const GafferImage::FormatPlug *formatPlug() const;

		Gaffer::BoolPlug *formatCenterPlug();
		const Gaffer::BoolPlug *formatCenterPlug() const;

		Gaffer::BoolPlug *affectDataWindowPlug();
		const Gaffer::BoolPlug *affectDataWindowPlug() const;

		Gaffer::BoolPlug *affectDisplayWindowPlug();
		const Gaffer::BoolPlug *affectDisplayWindowPlug() const;

		Gaffer::BoolPlug *resetOriginPlug();
		const Gaffer::BoolPlug *resetOriginPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hashFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;

		virtual GafferImage::Format computeFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

	private :

		Gaffer::AtomicBox2iPlug *cropWindowPlug();
		const Gaffer::AtomicBox2iPlug *cropWindowPlug() const;

		Gaffer::V2iPlug *offsetPlug();
		const Gaffer::V2iPlug *offsetPlug() const;

		static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( Crop )

} // namespace GafferImage

#endif // GAFFERIMAGE_CROP_H
