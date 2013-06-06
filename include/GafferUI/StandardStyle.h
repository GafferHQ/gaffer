//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#include "boost/array.hpp"

#include "OpenEXR/ImathColor.h"

#include "GafferUI/Style.h"

namespace IECoreGL
{

IE_CORE_FORWARDDECLARE( Font )
IE_CORE_FORWARDDECLARE( Shader )

} // namespace IECoreGL

namespace GafferUI
{

class StandardStyle : public Style
{

	public :

		StandardStyle();
		virtual ~StandardStyle();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::StandardStyle, StandardStyleTypeId, Style );

		virtual void bind( const Style *currentStyle=0 ) const;

		virtual Imath::Box3f textBound( TextType type, const std::string &text ) const;
		virtual void renderText( TextType type, const std::string &text, State state = NormalState ) const;

		virtual void renderFrame( const Imath::Box2f &frame, float borderWidth, State state = NormalState ) const;
		virtual void renderNodule( float radius, State state = NormalState ) const;
		virtual void renderConnection( const Imath::V3f &srcPosition, const Imath::V3f &srcTangent, const Imath::V3f &dstPosition, const Imath::V3f &dstTangent, State state = NormalState ) const;
		virtual void renderSelectionBox( const Imath::Box2f &box ) const;
		virtual void renderImage( const Imath::Box2f &box, const IECoreGL::Texture *texture ) const;
		virtual void renderLine( const IECore::LineSegment3f &line ) const;
		virtual void renderSolidRectangle( const Imath::Box2f &box ) const;
		virtual void renderRectangle( const Imath::Box2f &box ) const;
		
		enum Color
		{
			BackgroundColor,
			SunkenColor,
			RaisedColor,
			ForegroundColor,
			HighlightColor,
			ConnectionColor,
			LastColor
		};
		
		void setColor( Color c, Imath::Color3f v );
		const Imath::Color3f &getColor( Color c ) const;
		
		void setFont( TextType textType, IECoreGL::FontPtr font );
		const IECoreGL::Font *getFont( TextType textType ) const;
		
	private :
	
		static unsigned int connectionDisplayList();
	
		static IECoreGL::Shader *shader();
		static int g_borderParameter;
		static int g_borderRadiusParameter;
		static int g_edgeAntiAliasingParameter;
		static int g_textureParameter;
		static int g_textureTypeParameter;
		static int g_bezierParameter;
		static int g_v0Parameter;
		static int g_v1Parameter;
		static int g_v2Parameter;
		static int g_v3Parameter;
		
		Imath::Color3f colorForState( Color c, State s ) const;
		boost::array<Imath::Color3f, LastColor> m_colors;
		
		boost::array<IECoreGL::FontPtr, LastText> m_fonts;

};

IE_CORE_DECLAREPTR( Style );

} // namespace GafferUI

#endif // GAFFERUI_STANDARDSTYLE_H
