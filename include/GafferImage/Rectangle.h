//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, John Haddon. All rights reserved.
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

#include "GafferImage/Shape.h"

#include "Gaffer/BoxPlug.h"

namespace Gaffer
{

class Transform2DPlug;

} // namespace Gaffer

namespace GafferImage
{

class GAFFERIMAGE_API Rectangle : public Shape
{

	public :

		explicit Rectangle( const std::string &name=defaultName<Rectangle>() );
		~Rectangle() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::Rectangle, RectangleTypeId, Shape );

		Gaffer::Box2fPlug *areaPlug();
		const Gaffer::Box2fPlug *areaPlug() const;

		Gaffer::FloatPlug *lineWidthPlug();
		const Gaffer::FloatPlug *lineWidthPlug() const;

		Gaffer::FloatPlug *cornerRadiusPlug();
		const Gaffer::FloatPlug *cornerRadiusPlug() const;

		Gaffer::Transform2DPlug *transformPlug();
		const Gaffer::Transform2DPlug *transformPlug() const;

	protected :

		bool affectsShapeDataWindow( const Gaffer::Plug *input ) const override;
		void hashShapeDataWindow( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::Box2i computeShapeDataWindow( const Gaffer::Context *context ) const override;

		bool affectsShapeChannelData( const Gaffer::Plug *input ) const override;
		void hashShapeChannelData( const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstFloatVectorDataPtr computeShapeChannelData(  const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Rectangle )

} // namespace GafferImage
