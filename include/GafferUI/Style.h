//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012, Image Engine Design Inc. All rights reserved.
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

#include "OpenEXR/ImathBox.h"

#include "IECore/RunTimeTyped.h"
#include "IECore/LineSegment.h"
#include "IECoreGL/GL.h"

#include "GafferUI/TypeIds.h"

namespace IECoreGL
{

IE_CORE_FORWARDDECLARE( Texture );

} // namespace IECoreGL

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( Style );

class Style : public IECore::RunTimeTyped
{

	public :

		Style();
		virtual ~Style();

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
		virtual void bind( const Style *currentStyle=0 ) const = 0;

		enum ColorMask
		{
			None = 0,
			Red = 1,
			Green = 2,
			Blue = 4,
			Alpha = 8,
			All = 15
		};

		enum TextType
		{
			LabelText,
			LastText
		};

		virtual Imath::Box3f textBound( TextType textType, const std::string &text ) const = 0;
		virtual void renderText( TextType textType, const std::string &text, State state = NormalState ) const = 0;

		/// \todo Should all these be taking 3d arguments - no but 3d counterparts might be good.
		virtual void renderFrame( const Imath::Box2f &frame, float borderWidth, State state = NormalState ) const = 0;
		virtual void renderNodule( float radius, State state = NormalState ) const = 0;
		/// The tangents give an indication of which direction is "out" from a node.
		virtual void renderConnection( const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent, State state = NormalState ) const = 0;
		virtual void renderSelectionBox( const Imath::Box2f &box ) const = 0;
		virtual void renderImage( const Imath::Box2f &box, const IECoreGL::Texture *texture, int colorMask = All ) const = 0;
		virtual void renderLine( const IECore::LineSegment3f &line ) const = 0;
		virtual void renderSolidRectangle( const Imath::Box2f &box ) const = 0;
		virtual void renderRectangle( const Imath::Box2f &box ) const = 0;
				
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
	
		static StylePtr g_defaultStyle;
		
};

} // namespace GafferUI

#endif // GAFFERUI_STYLE_H
