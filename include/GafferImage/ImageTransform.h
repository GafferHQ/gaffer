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
//      * Neither the name of Image Engine Design nor the names of
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

#ifndef GAFFERSCENE_IMAGETRANSFORM_H
#define GAFFERSCENE_IMAGETRANSFORM_H

#include "GafferImage/FlatImageProcessor.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )
IE_CORE_FORWARDDECLARE( Transform2DPlug )

} // namespace Gaffer

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( Resample )

class ImageTransform : public FlatImageProcessor
{
	public :

		ImageTransform( const std::string &name=defaultName<ImageTransform>() );
		virtual ~ImageTransform();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::ImageTransform, ImageTransformTypeId, FlatImageProcessor );

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

		Gaffer::Transform2DPlug *transformPlug();
		const Gaffer::Transform2DPlug *transformPlug() const;

		Gaffer::StringPlug *filterPlug();
		const Gaffer::StringPlug *filterPlug() const;

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		virtual void hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const;

		virtual void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

	private :

		// Output plug to compute the matrix for the internal
		// Resample.
		Gaffer::M33fPlug *resampleMatrixPlug();
		const Gaffer::M33fPlug *resampleMatrixPlug() const;

		// Input plug to receive the scaled and translated image
		// from the internal Resample.
		ImagePlug *resampledInPlug();
		const ImagePlug *resampledInPlug() const;

		// The internal Resample node.
		Resample *resample();
		const Resample *resample() const;

		enum Operation
		{
			Identity = 0,
			Scale = 1,
			Translate = 2,
			Rotate = 4,
		};

		unsigned operation( Imath::M33f &matrix, Imath::M33f &resampleMatrix ) const;
		Imath::Box2i sampler( unsigned op, const Imath::M33f &matrix, const Imath::M33f &resampleMatrix, const Imath::V2i &tileOrigin, const ImagePlug *&samplerImage, Imath::M33f &samplerMatrix ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ImageTransform )

} // namespace GafferImage

#endif // GAFFERSCENE_IMAGETRANSFORM_H
