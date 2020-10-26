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

#include "GafferImage/ImageNode.h"

#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Switch.h"

#include "IECoreImage/DisplayDriver.h"
#include "IECoreImage/DisplayDriverServer.h"

namespace GafferImageModule
{

// Forward declaration to enable friend declaration.
void bindCatalogue();

} // namespace GafferImageModule

namespace GafferImage
{

class GAFFERIMAGE_API Catalogue : public ImageNode
{

	public :

		GAFFER_NODE_DECLARE_TYPE( GafferImage::Catalogue, CatalogueTypeId, ImageNode );

		Catalogue( const std::string &name = defaultName<Catalogue>() );
		~Catalogue() override;

		/// Plug type used to represent an image in the catalogue.
		class Image : public Gaffer::Plug
		{

			public :

				GAFFER_PLUG_DECLARE_TYPE( GafferImage::Catalogue::Image, CatalogueImageTypeId, Gaffer::Plug );

				Image( const std::string &name = defaultName<Image>(), Direction direction = In, unsigned flags = Default );

				Gaffer::StringPlug *fileNamePlug();
				const Gaffer::StringPlug *fileNamePlug() const;

				Gaffer::StringPlug *descriptionPlug();
				const Gaffer::StringPlug *descriptionPlug() const;

				/// Primarily used to take a snapshot of a live render.
				/// This image must have have been added to a Catalogue
				/// before calling. The snapshot will be saved to disk
				/// asynchronously.
				void copyFrom( const Image *other );

				static Ptr load( const std::string &fileName );
				void save( const std::string &fileName ) const;

				Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

			private :

				// The Catalogue needs to know the name of each image
				// so it can support the `catalogue:imageName` context
				// variable. But computes can only depend on plugs,
				// so we transfer the name into this private plug
				// each time it changes.
				void nameChanged();
				Gaffer::StringPlug *namePlug();
				const Gaffer::StringPlug *namePlug() const;
				friend class Catalogue;

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
		/// use an IECoreImage::ClientDisplayDriver with the "displayPort" parameter
		/// set to match `Catalogue::displayDriverServer()->portNumber()`.
		static IECoreImage::DisplayDriverServer *displayDriverServer();

		/// Generates a filename that could be used for storing
		/// a particular image locally in this Catalogue's directory.
		/// Primarily exists to be used in the UI.
		std::string generateFileName( const Image *image ) const;
		std::string generateFileName( const ImagePlug *image ) const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	private :

		Gaffer::IntPlug *internalImageIndexPlug();
		const Gaffer::IntPlug *internalImageIndexPlug() const;

		Gaffer::Switch *imageSwitch();
		const Gaffer::Switch *imageSwitch() const;

		IE_CORE_FORWARDDECLARE( InternalImage );
		static InternalImage *imageNode( Image *image );
		static const InternalImage *imageNode( const Image *image );

		void imageAdded( GraphComponent *graphComponent );
		void imageRemoved( GraphComponent *graphComponent );

		void driverCreated( IECoreImage::DisplayDriver *driver, const IECore::CompoundData *parameters );
		void imageReceived( Gaffer::Plug *plug );

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		static size_t g_firstPlugIndex;

		// For bindings
		friend void GafferImageModule::bindCatalogue();
		static const std::type_info &internalImageTypeInfo();

};

IE_CORE_DECLAREPTR( Catalogue );

} // namespace GafferImage

#endif // GAFFERIMAGE_CATALOGUE_H
