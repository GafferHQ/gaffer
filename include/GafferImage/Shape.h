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

#include "GafferImage/FlatImageProcessor.h"

#include "Gaffer/CompoundNumericPlug.h"

namespace GafferImage
{

IE_CORE_FORWARDDECLARE( Merge )
IE_CORE_FORWARDDECLARE( ImageTransform )

/// Base class for nodes which draw shapes on top of an input image.
/// Derived classes are responsible only for generating a mask for the
/// shape, and the base class takes care of colouring it and compositing
/// it over the input.
class GAFFERIMAGE_API Shape : public FlatImageProcessor
{

	public :

		Shape( const std::string &name=defaultName<Shape>() );
		~Shape() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::Shape, ShapeTypeId, FlatImageProcessor );

		Gaffer::Color4fPlug *colorPlug();
		const Gaffer::Color4fPlug *colorPlug() const;

		Gaffer::BoolPlug *shadowPlug();
		const Gaffer::BoolPlug *shadowPlug() const;

		Gaffer::Color4fPlug *shadowColorPlug();
		const Gaffer::Color4fPlug *shadowColorPlug() const;

		Gaffer::V2fPlug *shadowOffsetPlug();
		const Gaffer::V2fPlug *shadowOffsetPlug() const;

		Gaffer::FloatPlug *shadowBlurPlug();
		const Gaffer::FloatPlug *shadowBlurPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hashViewNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashDataWindow( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void hashChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;

		IECore::ConstStringVectorDataPtr computeViewNames( const Gaffer::Context *context, const ImagePlug *parent ) const override;
		Imath::Box2i computeDataWindow( const Gaffer::Context *context, const ImagePlug *parent ) const override;
		IECore::ConstStringVectorDataPtr computeChannelNames( const Gaffer::Context *context, const ImagePlug *parent ) const override;
		IECore::ConstFloatVectorDataPtr computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const override;

		/// Must be implemented to return true if the input plug affects the computation of the
		/// data window for the shape.
		virtual bool affectsShapeDataWindow( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented to call the base class implementation and then append any
		/// plugs that will be used in computing the data window.
		virtual void hashShapeDataWindow( const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented to return the data window for the shape.
		virtual Imath::Box2i computeShapeDataWindow( const Gaffer::Context *context ) const = 0;

		/// Must be implemented to return true if the input plug affects the computation of the
		/// channel data for the shape.
		virtual bool affectsShapeChannelData( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented to call the base class implementation and then append any
		/// plugs that will be used in computing the shape channel data.
		virtual void hashShapeChannelData( const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented to return the channel data for the shape.
		virtual IECore::ConstFloatVectorDataPtr computeShapeChannelData(  const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const = 0;

	private :

		ImagePlug *shapePlug();
		const ImagePlug *shapePlug() const;

		ImagePlug *shadowShapePlug();
		const ImagePlug *shadowShapePlug() const;

		float channelValue( const GafferImage::ImagePlug *parent, const std::string &channelName ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Shape )

} // namespace GafferImage
