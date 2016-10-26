//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, John Haddon. All rights reserved.
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

#ifndef GAFFERIMAGE_BLUR_H
#define GAFFERIMAGE_BLUR_H

#include "Gaffer/CompoundNumericPlug.h"

#include "GafferImage/FlatImageProcessor.h"

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( Resample )

class Blur : public FlatImageProcessor
{
	public :

		Blur( const std::string &name=defaultName<Blur>() );
		virtual ~Blur();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Blur, BlurTypeId, FlatImageProcessor );

		Gaffer::V2fPlug *radiusPlug();
		const Gaffer::V2fPlug *radiusPlug() const;

		Gaffer::IntPlug *boundingModePlug();
		const Gaffer::IntPlug *boundingModePlug() const;

		Gaffer::BoolPlug *expandDataWindowPlug();
		const Gaffer::BoolPlug *expandDataWindowPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		// Output plug to compute the filter width for the internal Resample.
		Gaffer::V2fPlug *filterWidthPlug();
		const Gaffer::V2fPlug *filterWidthPlug() const;

		// Input plug to receive the expanded data window from the internal Resample.
		Gaffer::AtomicBox2iPlug *resampledDataWindowPlug();
		const Gaffer::AtomicBox2iPlug *resampledDataWindowPlug() const;

		// Input plug to receive the blurred channel data from the internal Resample.
		Gaffer::FloatVectorDataPlug *resampledChannelDataPlug();
		const Gaffer::FloatVectorDataPlug *resampledChannelDataPlug() const;

		// Internal resample node.
		Resample *resample();
		const Resample *resample() const;

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		virtual void hashFlatDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::Box2i computeFlatDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashFlatChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstFloatVectorDataPtr computeFlatChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Blur )

} // namespace GafferImage

#endif // GAFFERIMAGE_BLUR_H
