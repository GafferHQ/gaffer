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

#include "GafferImage/Shape.h"

#include "Gaffer/BoxPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )
IE_CORE_FORWARDDECLARE( Transform2DPlug )

} // namespace Gaffer

namespace GafferImage
{

class GAFFERIMAGE_API Text : public Shape
{

	public :

		Text( const std::string &name=defaultName<Text>() );
		~Text() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::Text, TextTypeId, Shape );

		enum HorizontalAlignment
		{
			Left,
			Right,
			HorizontalCenter
		};

		enum VerticalAlignment
		{
			Bottom,
			Top,
			VerticalCenter
		};

		Gaffer::StringPlug *textPlug();
		const Gaffer::StringPlug *textPlug() const;

		Gaffer::StringPlug *fontPlug();
		const Gaffer::StringPlug *fontPlug() const;

		Gaffer::V2iPlug *sizePlug();
		const Gaffer::V2iPlug *sizePlug() const;

		Gaffer::Box2iPlug *areaPlug();
		const Gaffer::Box2iPlug *areaPlug() const;

		Gaffer::IntPlug *horizontalAlignmentPlug();
		const Gaffer::IntPlug *horizontalAlignmentPlug() const;

		Gaffer::IntPlug *verticalAlignmentPlug();
		const Gaffer::IntPlug *verticalAlignmentPlug() const;

		Gaffer::Transform2DPlug *transformPlug();
		const Gaffer::Transform2DPlug *transformPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		bool affectsLayout( const Gaffer::Plug *input ) const;
		void hashLayout( const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		IECore::ConstCompoundObjectPtr computeLayout( const Gaffer::Context *context ) const;

		bool affectsShapeDataWindow( const Gaffer::Plug *input ) const override;
		void hashShapeDataWindow( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		Imath::Box2i computeShapeDataWindow( const Gaffer::Context *context ) const override;

		bool affectsShapeChannelData( const Gaffer::Plug *input ) const override;
		void hashShapeChannelData( const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstFloatVectorDataPtr computeShapeChannelData(  const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const override;

	private :

		// We compute out layout once and cache it on this plug,
		// for subsequent use in computing the data window and
		// channel data.
		Gaffer::CompoundObjectPlug *layoutPlug();
		const Gaffer::CompoundObjectPlug *layoutPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Text )

} // namespace GafferImage
