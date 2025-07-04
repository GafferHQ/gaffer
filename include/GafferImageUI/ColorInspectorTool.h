//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Image Engine Design Inc. All rights reserved.
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

#include "GafferImageUI/Export.h"
#include "GafferImageUI/ImageView.h"
#include "GafferImageUI/ImageGadget.h"
#include "GafferImageUI/TypeIds.h"

#include "GafferImage/ImageSampler.h"
#include "GafferImage/ImageStats.h"

#include "GafferUI/DragDropEvent.h"
#include "GafferUI/Tool.h"

#include "Gaffer/ContextQuery.h"
#include "Gaffer/DeleteContextVariables.h"


namespace GafferImageUI
{

class GAFFERIMAGEUI_API ColorInspectorTool : public GafferUI::Tool
{

	public :

		explicit ColorInspectorTool( GafferUI::View *view, const std::string &name = defaultName<ColorInspectorTool>() );

		~ColorInspectorTool() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImageUI::ColorInspectorTool, ColorInspectorToolTypeId, GafferUI::Tool );

		class GAFFERIMAGEUI_API ColorInspectorPlug : public Gaffer::ValuePlug
		{
			public :
				enum class GAFFERIMAGEUI_API Mode
				{
					Cursor,
					Pixel,
					Area
				};

				GAFFER_PLUG_DECLARE_TYPE( ColorInspectorPlug, ColorInspectorPlugTypeId, Gaffer::ValuePlug );
				ColorInspectorPlug( const std::string &name = defaultName<ColorInspectorPlug>(), Direction direction=In, unsigned flags=Default );

				Gaffer::IntPlug *modePlug();
				const Gaffer::IntPlug *modePlug() const;

				Gaffer::V2iPlug *pixelPlug();
				const Gaffer::V2iPlug *pixelPlug() const;

				Gaffer::Box2iPlug *areaPlug();
				const Gaffer::Box2iPlug *areaPlug() const;

				bool acceptsChild( const GraphComponent *potentialChild ) const override;
				Gaffer::PlugPtr createCounterpart( const std::string &name, Plug::Direction direction ) const override;
		};

		Gaffer::ArrayPlug *inspectorsPlug();
		const Gaffer::ArrayPlug *inspectorsPlug() const;

	private :

		void plugSet( Gaffer::Plug *plug );
		void colorInspectorAdded( GraphComponent *colorInspector );
		void colorInspectorRemoved( GraphComponent *colorInspector );
		void deleteClicked( Gaffer::Plug *plug );
		void channelsChanged();

		static size_t g_firstPlugIndex;
		static ToolDescription<ColorInspectorTool, GafferImageUI::ImageView> g_imageToolDescription;

		Gaffer::ContextQueryPtr m_contextQuery;
		Gaffer::DeleteContextVariablesPtr m_deleteContextVariables;
		GafferImage::ImageSamplerPtr m_sampler;
		GafferImage::ImageStatsPtr m_areaSampler;

		GafferUI::ContainerGadgetPtr m_gadgets;
};

IE_CORE_DECLAREPTR( ColorInspectorTool )

} // namespace GafferImageUI
