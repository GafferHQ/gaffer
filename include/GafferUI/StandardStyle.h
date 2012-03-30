//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( StandardStyle, StandardStyleTypeId, Style );

		virtual void bind( const Style *currentStyle=0 ) const;

		virtual Imath::Box3f textBound( TextType type, const std::string &text ) const;
		virtual void renderText( TextType type, const std::string &text, State state = NormalState ) const;

		virtual void renderFrame( const Imath::Box2f &frame, float borderWidth, State state = NormalState ) const;
		virtual void renderNodule( float radius, State state = NormalState ) const;
		virtual void renderConnection( const Imath::V3f &src, const Imath::V3f &dst, State state = NormalState ) const;
		virtual void renderSelectionBox( const Imath::Box2f &box ) const;
		virtual void renderImage( const Imath::Box2f &box, const IECoreGL::Texture *texture ) const;
		
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
	
		IECoreGL::Shader *shader() const;
		mutable IECoreGL::ShaderPtr m_shader;
		mutable int m_borderParameter;
		mutable int m_borderRadiusParameter;
		mutable int m_edgeAntiAliasingParameter;
		mutable int m_textureParameter;
		mutable int m_textureTypeParameter;
		mutable int m_bezierParameter;
		mutable int m_v0Parameter;
		mutable int m_v1Parameter;
		mutable int m_v2Parameter;
		mutable int m_v3Parameter;
		
		Imath::Color3f colorForState( Color c, State s ) const;
		boost::array<Imath::Color3f, LastColor> m_colors;
		
		boost::array<IECoreGL::FontPtr, LastText> m_fonts;

};

IE_CORE_DECLAREPTR( Style );

} // namespace GafferUI

#endif // GAFFERUI_STANDARDSTYLE_H
