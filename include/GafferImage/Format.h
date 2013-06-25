//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012-2013 Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_FORMAT_H
#define GAFFER_FORMAT_H

#include "OpenEXR/ImathBox.h"
#include "GafferImage/TypeIds.h"
#include "IECore/TypedData.h"
#include "Gaffer/GraphComponent.h"
#include "Gaffer/ScriptNode.h"

namespace GafferImage
{

class Format
{
	public:
	
		typedef boost::signal<void (const std::string&)> UnaryFormatSignal;
		
		Format( int width, int height, double aspect = 1. ):
			m_aspect( aspect )
		{
			width = std::max( 0, width );
			height = std::max( 0, height );
			m_displayWindow = Imath::Box2i( Imath::V2i( 0, 0 ), Imath::V2i( width-1, height-1 ) );
		}
		
		Format( const Imath::Box2i &displayWindow, double aspect = 1. ):
			m_displayWindow( displayWindow ),
			m_aspect( aspect )
		{}
		
		Format():
			m_aspect( 1. )
		{
		}
		
		/// Accessors
		inline double getPixelAspect() const { return m_aspect; }
		inline void setPixelAspect( double aspect ){ m_aspect = aspect; }
		inline Imath::Box2i getDisplayWindow() const { return m_displayWindow; }
		inline void setDisplayWindow( const Imath::Box2i &window ){ m_displayWindow = window; }
		int width() const;
		int height() const;
		
		/// Overloaded OStream operator to write the formats name to the ostream.
		friend std::ostream& operator<<(std::ostream& os, GafferImage::Format const& format);
		
		/// Equality operators
		inline bool operator == ( const Format& rhs ) const
		{
			return m_displayWindow == rhs.m_displayWindow && m_aspect == rhs.m_aspect;
		}
		
		inline bool operator != ( const Format& rhs ) const
		{
			return m_displayWindow != rhs.m_displayWindow || m_aspect != rhs.m_aspect;
		}
		
		/// @name Default Format methods
		/// These functions are used to create, set and get the formatPlug
		/// which resides on the script node. When a GafferImage node is created
		/// addDefaultFormatPlug() is called from the "parentChanged" signal. This
		/// initializes the default format which is held as a plug on the script node.
		/// The Script Node's plugSetSignal() is connected to the addFormatToContext()
		/// slot which updates an entry on the context every time that the plug is changed.
		/// This causes the hash of the context to change which triggers the viewer to
		/// recalculate it's output image.
		////////////////////////////////////////////////////////////////////
		//@{
		static void setDefaultFormat( Gaffer::ScriptNode *scriptNode, const Format &format );
		static void setDefaultFormat( Gaffer::ScriptNode *scriptNode, const std::string &name );
		static const Format getDefaultFormat( Gaffer::ScriptNode *scriptNode );
		
		/// Accessors and creators for the format list.
		static const Format &registerFormat( const Format &format, const std::string &name );
		static const Format &registerFormat( const Format &format );
		
		static void removeFormat( const Format &format );
		static void removeFormat( const std::string &name );
		static void removeAllFormats();
		
		static int formatCount();
		static const Format &getFormat( const std::string &name );
		static std::string formatName( const Format &format );
		static void formatNames( std::vector< std::string > &names );
		static void addFormatToContext( Gaffer::Plug *defaultFormatPlug );
		
		static UnaryFormatSignal &formatAddedSignal();
		static UnaryFormatSignal &formatRemovedSignal();
		//@}
		
		/// Called by the Node class to setup the format plug on the script node.
		static void addDefaultFormatPlug( Gaffer::ScriptNode *scriptNode );
		
		static const IECore::InternedString defaultFormatContextName;
		static const IECore::InternedString defaultFormatPlugName;
		
	private:
		
		typedef std::pair< std::string, Format > FormatEntry;
		typedef std::map< std::string, Format > FormatMap;
		
		/// Method to return a static instance of the format mappings
		inline static FormatMap &formatMap();
		
		/// Generates a name for a given format. The result is returned in place.
		static void generateFormatName( std::string &name, const Format &format);
		
		Imath::Box2i m_displayWindow;
		double m_aspect;
};

std::ostream & operator << ( std::ostream &os, const GafferImage::Format &format );

} // namespace GafferImage

#endif // GAFFER_FORMAT_H
