//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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
//      * Neither the name of Image Engine Design nor the names of
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

#ifndef GAFFERIMAGE_WARP_H
#define GAFFERIMAGE_WARP_H

#include "Gaffer/NumericPlug.h"

#include "GafferImage/FlatImageProcessor.h"

namespace GafferImage
{

/// Base class for nodes which warp the image in some way.
/// Derived classes must :
///
/// - Implement hashDataWindow()/computeDataWindow() to
///   to compute the output window for the warped image.
///   Alternatively they may make a pass-through connection
///   for the data window.
/// - Implement an Engine subclass to compute warped input
///   pixel positions from output pixel positions.
/// - Implement hashEngine() and computeEngine() to create
///   and return the Engine subclass.
class Warp : public FlatImageProcessor
{
	public :

		Warp( const std::string &name=defaultName<Warp>() );
		virtual ~Warp();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Warp, WarpTypeId, FlatImageProcessor );

		Gaffer::IntPlug *boundingModePlug();
		const Gaffer::IntPlug *boundingModePlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		virtual void hashFlatChannelData( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		virtual IECore::ConstFloatVectorDataPtr computeFlatChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const ImagePlug *parent ) const;

		/// Abstract base class for implementing the warp function.
		struct Engine
		{

			virtual ~Engine();

			/// Must be implemented to return a window bounding all input pixels
			/// for the specified tile.
			virtual Imath::Box2i inputWindow( const Imath::V2i &tileOrigin ) const = 0;
			/// Must be implemented to return the source pixel for the specified
			/// output pixel.
			virtual Imath::V2f inputPixel( const Imath::V2f &outputPixel ) const = 0;

			/// May be returned by inputPixel() to indicate that there is no
			/// suitable input position, and black should be output instead.
			static const Imath::V2f black;

		};

		/// Must be implemented to return true if the input is used
		/// in the implementation of engine().
		virtual bool affectsEngine( const Gaffer::Plug *input ) const = 0;
		/// Must be implemented to call the base class implementation then
		/// hash all the inputs used in creating an engine for the specified
		/// tile. If the tileOrigin is not included in the hash, then the
		/// same engine may be reused for all tiles.
		virtual void hashEngine( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const = 0;
		/// Must be implemented to return an Engine instance capable
		/// of answering all queries for the specified tile.
		virtual const Engine *computeEngine( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const = 0;

	private :

		IE_CORE_FORWARDDECLARE( EngineData );

		Gaffer::ObjectPlug *enginePlug();
		const Gaffer::ObjectPlug *enginePlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Warp )

} // namespace GafferImage

#endif // GAFFERIMAGE_WARP_H
