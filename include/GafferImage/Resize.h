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

#ifndef GAFFERIMAGE_RESIZE_H
#define GAFFERIMAGE_RESIZE_H

#include "Gaffer/NumericPlug.h"

#include "GafferImage/FlatImageProcessor.h"
#include "GafferImage/FormatPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( Resample )

class Resize : public FlatImageProcessor
{
	public :

		Resize( const std::string &name=defaultName<Resize>() );
		virtual ~Resize();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Resize, ResizeTypeId, FlatImageProcessor );

		enum FitMode
		{
			Horizontal,
			Vertical,
			Fit,
			Fill,
			Distort
		};

		GafferImage::FormatPlug *formatPlug();
		const GafferImage::FormatPlug *formatPlug() const;

		Gaffer::IntPlug *fitModePlug();
		const Gaffer::IntPlug *fitModePlug() const;

		Gaffer::StringPlug *filterPlug();
		const Gaffer::StringPlug *filterPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		virtual void hashFlatFormat( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual GafferImage::Format computeFlatFormat( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashFlatDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::Box2i computeFlatDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashFlatChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstFloatVectorDataPtr computeFlatChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

	private :

		Gaffer::M33fPlug *matrixPlug();
		const Gaffer::M33fPlug *matrixPlug() const;

		// We use an internal Resample node to do all the hard
		// work of filtering the image into a new data window,
		// and receive the result of that through this plug.
		ImagePlug *resampledInPlug();
		const ImagePlug *resampledInPlug() const;

		// When we're actually changing the format, we get our
		// output from resampledInPlug(), but when the format
		// happens to be the same as the input, we simply pass
		// through inPlug(). This function just returns the
		// appropriate plug.
		const ImagePlug *source() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Resize )

} // namespace GafferImage

#endif // GAFFERIMAGE_RESIZE_H
