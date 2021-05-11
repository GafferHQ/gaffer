//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2014, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_STANDARDSTYLE_H
#define GAFFERUI_STANDARDSTYLE_H

#include "GafferUI/Style.h"

#include "IECore/Export.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathColor.h"
IECORE_POP_DEFAULT_VISIBILITY

#include <array>

namespace IECoreGL
{

IE_CORE_FORWARDDECLARE( Font )
IE_CORE_FORWARDDECLARE( Shader )
IE_CORE_FORWARDDECLARE( State )

} // namespace IECoreGL

namespace GafferUI
{

class GAFFERUI_API StandardStyle : public Style
{

	public :

		StandardStyle();
		~StandardStyle() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardStyle, StandardStyleTypeId, Style );

		void bind( const Style *currentStyle=nullptr ) const override;

		void renderImage( const Imath::Box2f &box, const IECoreGL::Texture *texture ) const override;
		void renderLine( const IECore::LineSegment3f &line, float width=0.5, const Imath::Color4f *userColor = nullptr ) const override;
		void renderSolidRectangle( const Imath::Box2f &box ) const override;
		void renderRectangle( const Imath::Box2f &box ) const override;

		Imath::Box3f characterBound( TextType textType ) const override;
		Imath::Box3f textBound( TextType type, const std::string &text ) const override;
		void renderText( TextType type, const std::string &text, State state = NormalState, const Imath::Color4f *userColor = nullptr ) const override;
		void renderWrappedText( TextType textType, const std::string &text, const Imath::Box2f &bound, State state = NormalState ) const override;

		void renderFrame( const Imath::Box2f &frame, float borderWidth, State state = NormalState ) const override;
		void renderSelectionBox( const Imath::Box2f &box ) const override;
		void renderHorizontalRule( const Imath::V2f &center, float length, State state = NormalState ) const override;

		void renderNodeFrame( const Imath::Box2f &contents, float borderWidth, State state = NormalState, const Imath::Color3f *userColor = nullptr ) const override;
		void renderNodule( float radius, State state = NormalState, const Imath::Color3f *userColor = nullptr ) const override;
		void renderConnection( const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent, State state = NormalState, const Imath::Color3f *userColor = nullptr ) const override;
		Imath::V3f closestPointOnConnection( const Imath::V3f &p, const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent ) const override;
		void renderAuxiliaryConnection( const Imath::Box2f &srcNodeFrame, const Imath::Box2f &dstNodeFrame, State state ) const override;
		void renderAuxiliaryConnection( const Imath::V2f &srcPosition, const Imath::V2f &srcTangent, const Imath::V2f &dstPosition, const Imath::V2f &dstTangent, State state ) const override;
		void renderBackdrop( const Imath::Box2f &box, State state = NormalState, const Imath::Color3f *userColor = nullptr ) const override;
		Imath::V2f renderAnnotation( const Imath::V2f &origin, const std::string &text, State state = NormalState, const Imath::Color3f *userColor = nullptr ) const override;

		void renderTranslateHandle( Axes axes, State state = NormalState ) const override;
		void renderRotateHandle( Axes axes, State state = NormalState, const Imath::V3f &highlightVector = Imath::V3f( 0 ) ) const override;
		void renderScaleHandle( Axes axes, State state = NormalState ) const override;

		void renderAnimationCurve( const Imath::V2f &start, const Imath::V2f &end, const Imath::V2f &startTangent, const Imath::V2f &endTangent, State state, const Imath::Color3f *userColor = nullptr ) const override;
		void renderAnimationKey( const Imath::V2f &position, State state, float size = 2.0, const Imath::Color3f *userColor = nullptr ) const override;

		enum Color
		{
			BackgroundColor,
			SunkenColor,
			RaisedColor,
			ForegroundColor,
			HighlightColor,
			ConnectionColor,
			AuxiliaryConnectionColor,
			AnimationCurveColor,
			LastColor
		};

		void setColor( Color c, Imath::Color3f v );
		const Imath::Color3f &getColor( Color c ) const;

		void setFont( TextType textType, IECoreGL::FontPtr font );
		const IECoreGL::Font *getFont( TextType textType ) const;

		/// \todo Perhaps this should be something on the IECore or
		/// IECoreGL Font classes?
		void setFontScale( TextType textType, float scale );
		float getFontScale( TextType textType ) const;

	private :

		void renderConnectionInternal( const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent ) const;
		static unsigned int connectionDisplayList();

		static IECoreGL::Shader *shader();
		static int g_borderParameter;
		static int g_borderRadiusParameter;
		static int g_borderWidthParameter;
		static int g_edgeAntiAliasingParameter;
		static int g_textureParameter;
		static int g_textureTypeParameter;
		static int g_isCurveParameter;
		static int g_endPointSizeParameter;
		static int g_v0Parameter;
		static int g_v1Parameter;
		static int g_t0Parameter;
		static int g_t1Parameter;
		static int g_lineWidthParameter;

		Imath::Color3f colorForState( Color c, State s, const Imath::Color3f *userColor = nullptr ) const;
		std::array<Imath::Color3f, LastColor> m_colors;

		IECoreGL::FontPtr m_fonts[LastText];
		float m_fontScales[LastText];

		IECoreGL::StatePtr m_highlightState;

};

IE_CORE_DECLAREPTR( Style );

} // namespace GafferUI

#endif // GAFFERUI_STANDARDSTYLE_H
