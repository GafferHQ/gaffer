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

#ifndef GAFFERIMAGE_FORMAT_H
#define GAFFERIMAGE_FORMAT_H

#include "boost/signals.hpp"

#include "OpenEXR/ImathBox.h"

#include "IECore/InternedString.h"

namespace Gaffer
{

class ScriptNode;
class Plug;

} // namespace Gaffer

namespace GafferImage
{

class Format
{

	public :

		typedef boost::signal<void (const std::string&)> UnaryFormatSignal;

		inline Format();
		inline explicit Format( const Imath::Box2i &displayWindow, double pixelAspect = 1. );
		inline Format( int width, int height, double pixelAspect = 1. );

		inline const Imath::Box2i &getDisplayWindow() const;
		inline void setDisplayWindow( const Imath::Box2i &window );

		inline int width() const;
		inline int height() const;

		inline double getPixelAspect() const;
		inline void setPixelAspect( double pixelAspect );

		inline bool operator == ( const Format &rhs ) const;
		inline bool operator != ( const Format &rhs ) const;

		/// @name Coordinate system conversions.
		/// The image coordinate system used by Gaffer has the origin at the
		/// bottom, with increasing Y coordinates going up. The Cortex and OpenEXR
		/// coordinate systems have the origin at the top with increasing Y
		/// coordinates going down. These methods assist in converting between
		/// the two coordinate systems. They assume that the format has been
		/// constructed using exactly the same display window as is being
		/// used in the corresponding Y-down space - note that this means it
		/// is not necessary to perform any conversion on the display window
		/// itself.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Converts from the Y-down coordinate space to the Y-up space of
		/// the Format.
		inline int yDownToFormatSpace( int yDown ) const;
		inline Imath::V2i yDownToFormatSpace( const Imath::V2i &yDown ) const;
		inline Imath::Box2i yDownToFormatSpace( const Imath::Box2i &yDown ) const;
		/// Converts from the Y-up space of the format to the Y-down
		/// coordinate space.
		inline int formatToYDownSpace( int yUp ) const;
		inline Imath::V2i formatToYDownSpace( const Imath::V2i &yUp ) const;
		inline Imath::Box2i formatToYDownSpace( const Imath::Box2i &yUp ) const;
		//@}

		/// @name Default Format methods
		/// These functions are used to create, set and get the formatPlug
		/// which resides on the script node. When a GafferImage node is created
		/// addDefaultFormatPlug() is called from the "parentChanged" signal. This
		/// initializes the default format which is held as a plug on the script node.
		/// The Script Node's plugSetSignal() is connected to the addFormatToContext()
		/// slot which updates an entry on the context every time that the plug is changed.
		/// This causes the hash of the context to change which triggers the viewer to
		/// recalculate it's output image.
		/// \todo The Format should just be a basic class like Box or Vec -
		/// keep the named format registry here but move all the stuff related
		/// to nodes and plugs and contexts into FormatPlug.
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

	private :

		typedef std::pair< std::string, Format > FormatEntry;
		typedef std::map< std::string, Format > FormatMap;

		/// Method to return a static instance of the format mappings
		inline static FormatMap &formatMap();

		/// Generates a name for a given format. The result is returned in place.
		static void generateFormatName( std::string &name, const Format &format);

		Imath::Box2i m_displayWindow;
		double m_pixelAspect;

};

std::ostream & operator << ( std::ostream &os, const GafferImage::Format &format );

} // namespace GafferImage

#include "GafferImage/Format.inl"

#endif // GAFFERIMAGE_FORMAT_H
