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

#ifndef GAFFERUI_STYLE_H
#define GAFFERUI_STYLE_H

#include "GafferUI/Export.h"
#include "GafferUI/TypeIds.h"

#include "IECoreGL/GL.h"

#include "IECore/Export.h"
#include "IECore/LineSegment.h"
#include "IECore/RunTimeTyped.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathBox.h"
IECORE_POP_DEFAULT_VISIBILITY

#include "boost/signal.hpp"

namespace IECoreGL
{

IE_CORE_FORWARDDECLARE( Texture );

} // namespace IECoreGL

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Style );

class GAFFERUI_API Style : public IECore::RunTimeTyped
{

	public :

		Style();
		~Style() override;

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::Style, StyleTypeId, IECore::RunTimeTyped );

		enum State
		{
			NormalState,
			DisabledState,
			HighlightedState
		};

		/// Must be called once to allow the Style to set up any necessary state before calling
		/// any of the render* methods below. The currently bound style is passed as it may
		/// be possible to use it to optimise the binding of a new style of the same type.
		virtual void bind( const Style *currentStyle=nullptr ) const = 0;

		enum TextType
		{
			LabelText,
			BodyText,
			HeadingText,
			LastText
		};

		/// @name General drawing.
		/// I'm not sure this really belongs in the Style class - perhaps
		/// it would be better to have some utility drawing methods in IECoreGL?
		//////////////////////////////////////////////////////////////////////////
		//@{
		virtual void renderImage( const Imath::Box2f &box, const IECoreGL::Texture *texture ) const = 0;
		virtual void renderLine( const IECore::LineSegment3f &line, float width=0.5, const Imath::Color4f *userColor = nullptr ) const = 0;
		virtual void renderSolidRectangle( const Imath::Box2f &box ) const = 0;
		virtual void renderRectangle( const Imath::Box2f &box ) const = 0;
		//@}

		/// @name Text drawing
		//////////////////////////////////////////////////////////////////////////
		//@{
		virtual Imath::Box3f characterBound( TextType textType ) const = 0;
		virtual Imath::Box3f textBound( TextType textType, const std::string &text ) const = 0;
		virtual void renderText( TextType textType, const std::string &text, State state = NormalState, const Imath::Color4f *userColor = nullptr ) const = 0;
		virtual void renderWrappedText( TextType textType, const std::string &text, const Imath::Box2f &bound, State state = NormalState ) const = 0;
		//@}

		/// @name Generic UI elements
		//////////////////////////////////////////////////////////////////////////
		//@{
		virtual void renderFrame( const Imath::Box2f &frame, float borderWidth, State state = NormalState ) const = 0;
		virtual void renderSelectionBox( const Imath::Box2f &box ) const = 0;
		virtual void renderHorizontalRule( const Imath::V2f &center, float length, State state = NormalState ) const = 0;
		//@}

		/// @name GraphEditor UI elements
		//////////////////////////////////////////////////////////////////////////
		//@{
		virtual void renderNodeFrame( const Imath::Box2f &contents, float borderWidth, State state = NormalState, const Imath::Color3f *userColor = nullptr, const float borderThicknessMultiplier = 1.0f ) const = 0;
		virtual void renderNodule( float radius, State state = NormalState, const Imath::Color3f *userColor = nullptr ) const = 0;
		/// The tangents give an indication of which direction is "out" from a node.
		virtual void renderConnection( const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent, State state = NormalState, const Imath::Color3f *userColor = nullptr ) const = 0;
		virtual Imath::V3f closestPointOnConnection( const Imath::V3f &p, const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent ) const = 0;
		virtual void renderAuxiliaryConnection( const Imath::Box2f &srcNodeFrame, const Imath::Box2f &dstNodeFrame, State state ) const = 0;
		virtual void renderAuxiliaryConnection( const Imath::V2f &srcPosition, const Imath::V2f &srcTangent, const Imath::V2f &dstPosition, const Imath::V2f &dstTangent, State state ) const = 0;

		virtual void renderBackdrop( const Imath::Box2f &box, State state = NormalState, const Imath::Color3f *userColor = nullptr ) const = 0;
		//@}

		/// @name 3D UI elements
		//////////////////////////////////////////////////////////////////////////
		//@{
		enum Axes
		{
			X,
			Y,
			Z,
			XY,
			XZ,
			YZ,
			XYZ
		};
		virtual void renderTranslateHandle( Axes axes, State state = NormalState ) const = 0;
		virtual void renderRotateHandle( Axes axes, State state = NormalState, const Imath::V3f &highlightVector = Imath::V3f( 0 ) ) const = 0;
		virtual void renderScaleHandle( Axes axes, State state = NormalState ) const = 0;
		//@}

		/// @name Animation UI elements
		//////////////////////////////////////////////////////////////////////////
		//@{
		virtual void renderAnimationCurve( const Imath::V2f &start, const Imath::V2f &end, const Imath::V2f &startTangent, const Imath::V2f &endTangent, State state, const Imath::Color3f *userColor = nullptr ) const = 0;
		virtual void renderAnimationKey( const Imath::V2f &position, State state, float size = 2.0, const Imath::Color3f *userColor = nullptr ) const = 0;
		//@}

		typedef boost::signal<void (Style *)> UnarySignal;
		/// Emitted when the style has changed in a way which
		/// would necessitate a redraw.
		UnarySignal &changedSignal();

		//! @name Default style
		/// There always exists a default style which is
		/// applied to all Gadgets where the style has not
		/// been explicitly set. Typically you would set this
		/// once when an application starts and then leave it
		/// alone - if not set it defaults to an instance of
		/// StandardStyle.
		/// \see GafferUI::Gadget::setStyle()
		////////////////////////////////////////////////
		//@{
		static StylePtr getDefaultStyle();
		static void setDefaultStyle( StylePtr style );
		//@}

	private :

		UnarySignal m_changedSignal;

		static StylePtr g_defaultStyle;

};

} // namespace GafferUI

#endif // GAFFERUI_STYLE_H
