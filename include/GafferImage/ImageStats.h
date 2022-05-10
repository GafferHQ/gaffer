//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_IMAGESTATS_H
#define GAFFERIMAGE_IMAGESTATS_H

#include "GafferImage/ImagePlug.h"
#include "GafferImage/DeepState.h"

#include "Gaffer/BoxPlug.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/ComputeNode.h"

namespace GafferImage
{

/// \todo Add an areaSource plug with the same semantics
/// that the Crop node has.
class GAFFERIMAGE_API ImageStats : public Gaffer::ComputeNode
{

	public :

		ImageStats( const std::string &name=defaultName<ImageStats>() );
		~ImageStats() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::ImageStats, ImageStatsTypeId, Gaffer::ComputeNode );

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

		GafferImage::ImagePlug *inPlug();
		const GafferImage::ImagePlug *inPlug() const;

		Gaffer::StringVectorDataPlug *channelsPlug();
		const Gaffer::StringVectorDataPlug *channelsPlug() const;

		Gaffer::Box2iPlug *areaPlug();
		const Gaffer::Box2iPlug *areaPlug() const;

		Gaffer::Color4fPlug *averagePlug();
		const Gaffer::Color4fPlug *averagePlug() const;

		Gaffer::Color4fPlug *minPlug();
		const Gaffer::Color4fPlug *minPlug() const;

		Gaffer::Color4fPlug *maxPlug();
		const Gaffer::Color4fPlug *maxPlug() const;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;
		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;
		Gaffer::ValuePlug::CachePolicy hashCachePolicy( const Gaffer::ValuePlug *output ) const override;


	private :

		// Stats for individual tiles
		Gaffer::ObjectPlug *tileStatsPlug();
		const Gaffer::ObjectPlug *tileStatsPlug() const;

		// Combined stats, before they get broken out into 3 seperate plugs
		Gaffer::ObjectPlug *allStatsPlug();
		const Gaffer::ObjectPlug *allStatsPlug() const;

		// Input plug to receive the flattened image from the internal
		// DeepState plug.
		ImagePlug *flattenedInPlug();
		const ImagePlug *flattenedInPlug() const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ImageStats );

} // namespace GafferImage

#endif // GAFFERIMAGE_IMAGESTATS_H
