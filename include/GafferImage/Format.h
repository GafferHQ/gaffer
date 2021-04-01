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

#include "GafferImage/Export.h"

#include "IECore/Export.h"
#include "IECore/MurmurHash.h"

IECORE_PUSH_DEFAULT_VISIBILITY
#include "OpenEXR/ImathBox.h"
IECORE_POP_DEFAULT_VISIBILITY

#include <string>
#include <vector>

namespace GafferImage
{

/// Basic maths class to represent the format of an image -
/// its display window and pixel aspect ratio.
class GAFFERIMAGE_API Format
{

	public :

		inline Format();
		inline explicit Format( const Imath::Box2i &displayWindow, double pixelAspect = 1., bool fromEXRSpace = false );
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
		/// bottom, with increasing Y coordinates going up. It also considers
		/// image bounds to be exclusive at the max end.
		///
		/// The Cortex and OpenEXR coordinate systems have the origin at the
		/// top with increasing Y coordinates going down. They use inclusive
		/// image bounds.
		///
		/// These methods assist in converting between the two coordinate
		/// systems.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Converts from the EXR coordinate space to the internal space of
		/// the Format.
		inline int fromEXRSpace( int exrSpace ) const;
		inline Imath::V2i fromEXRSpace( const Imath::V2i &exrSpace ) const;
		inline Imath::Box2i fromEXRSpace( const Imath::Box2i &exrSpace ) const;
		/// Converts from the internal space of the format to the EXR
		/// coordinate space.
		inline int toEXRSpace( int internalSpace ) const;
		inline Imath::V2i toEXRSpace( const Imath::V2i &internalSpace ) const;
		inline Imath::Box2i toEXRSpace( const Imath::Box2i &internalSpace ) const;
		//@}

		/// @name Format registry
		/// Maintains a list of named formats which may be registered
		/// by config files, and made available to the user via the UI.
		////////////////////////////////////////////////////////////////////
		//@{
		/// Registers a format with the specified name.
		static void registerFormat( const std::string &name, const Format &format );
		/// Removes a previously registered format.
		static void deregisterFormat( const std::string &name );
		/// Lists all currently registered formats.
		static void registeredFormats( std::vector<std::string> &names );
		/// Returns the format registered with the specified name, or
		/// an empty format if the name is not registered.
		static Format format( const std::string &name );
		/// Returns a name registered for the specific format, or
		/// the empty string if the format has not been registered.
		/// Note that this is unrelated to the ostream operator.
		static std::string name( const Format &format );
		//@}

	private :

		Imath::Box2i m_displayWindow;
		double m_pixelAspect;

};

/// Outputs a numeric description of the format, omitting default information
/// where possible. Note that this is unrelated to Format::name().
GAFFERIMAGE_API std::ostream & operator << ( std::ostream &os, const GafferImage::Format &format );

inline void murmurHashAppend( IECore::MurmurHash &h, const GafferImage::Format &data );

} // namespace GafferImage

#include "GafferImage/Format.inl"

#endif // GAFFERIMAGE_FORMAT_H
