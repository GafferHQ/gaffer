//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_CATALOGUE_H
#define GAFFERIMAGE_CATALOGUE_H

#include "IECore/DisplayDriver.h"
#include "IECore/DisplayDriverServer.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/NumericPlug.h"

#include "GafferImage/ImageNode.h"
#include "GafferImage/ImageSwitch.h"
#include "GafferImageBindings/CatalogueBinding.h" // To enable friend declaration for bindCatalogue()

namespace GafferImage
{

class Catalogue : public ImageNode
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Catalogue, CatalogueTypeId, ImageNode );

		Catalogue( const std::string &name = defaultName<Catalogue>() );
		virtual ~Catalogue();

		/// Plug type used to represent an image in the catalogue.
		class Image : public Gaffer::Plug
		{

			public :

				IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferImage::Catalogue::Image, CatalogueImageTypeId, Gaffer::Plug );

				Image( const std::string &name = defaultName<Image>() );

				Gaffer::StringPlug *fileNamePlug();
				const Gaffer::StringPlug *fileNamePlug() const;

				Gaffer::StringPlug *descriptionPlug();
				const Gaffer::StringPlug *descriptionPlug() const;

				static Ptr load( const std::string &fileName );
				void save( const std::string &fileName ) const;

		};

		typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, Image> > ImageIterator;

		Gaffer::Plug *imagesPlug();
		const Gaffer::Plug *imagesPlug() const;

		Gaffer::IntPlug *imageIndexPlug();
		const Gaffer::IntPlug *imageIndexPlug() const;

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		Gaffer::StringPlug *directoryPlug();
		const Gaffer::StringPlug *directoryPlug() const;

		/// All Catalogues share a single DisplayDriverServer instance
		/// to receive rendered images. To send an image to the catalogues,
		/// use an IECore::ClientDisplayDriver with the "displayPort" parameter
		/// set to match `Catalogue::displayDriverServer()->portNumber()`.
		static IECore::DisplayDriverServer *displayDriverServer();

		/// Generates a filename that could be used for storing
		/// a particular image locally in this Catalogue's directory.
		/// Primarily exists to be used in the UI.
		std::string generateFileName( const Image *image ) const;
		std::string generateFileName( const ImagePlug *image ) const;

	private :

		// In an ideal world, the Catalogue would connect these to the relevant
		// signals directly, but unfortunately the signals are not emitted on the
		// UI thread where it is permissible to modify the internal graph. We
		// therefore rely on CatalogueUI.py to connect to the signals and then
		// call these "slots" from the UI thread.
		static void driverCreated( IECore::DisplayDriver *driver, const IECore::CompoundData *parameters );
		static void imageReceived( Gaffer::Plug *plug );
		friend void GafferImageBindings::bindCatalogue();

		ImageSwitch *imageSwitch();
		const ImageSwitch *imageSwitch() const;

		IE_CORE_FORWARDDECLARE( InternalImage );
		InternalImage *imageNode( const Image *image ) const;

		void imageAdded( GraphComponent *graphComponent );
		void imageRemoved( GraphComponent *graphComponent );

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Catalogue );

} // namespace GafferImage

#endif // GAFFERIMAGE_CATALOGUE_H
