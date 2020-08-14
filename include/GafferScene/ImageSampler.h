//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Hypothetical Inc. All rights reserved.
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

#ifndef GAFFERSCENE_IMAGESAMPLER_H
#define GAFFERSCENE_IMAGESAMPLER_H

#include "GafferImage/ImagePlug.h"

#include "GafferScene/Deformer.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/PrimitiveEvaluator.h"

namespace GafferScene
{

class GAFFERSCENE_API ImageSampler : public Deformer
{

	public :

		ImageSampler( const std::string &name = defaultName<ImageSampler>() );
		~ImageSampler() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferScene::ImageSampler, ImageSamplerTypeId, Deformer );

		enum UVBoundsMode
		{
			Clamp = 0,
			Tile = 1
		};

		GafferImage::ImagePlug *imagePlug();
		const GafferImage::ImagePlug *imagePlug() const;

		Gaffer::StringPlug *primVarNamePlug();
		const Gaffer::StringPlug *primVarNamePlug() const;

		Gaffer::StringPlug *uvVarNamePlug();
		const Gaffer::StringPlug *uvVarNamePlug() const;

		Gaffer::IntPlug *uvBoundsModePlug();
		const Gaffer::IntPlug *uvBoundsModePlug() const;

		Gaffer::StringPlug *channelsPlug();
		const Gaffer::StringPlug *channelsPlug() const;

	private :

		bool affectsProcessedObject( const Gaffer::Plug *input ) const final;
		void hashProcessedObject( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const final;
		IECore::ConstObjectPtr computeProcessedObject( const ScenePath &path, const Gaffer::Context *context, const IECore::Object *inputObject ) const final;

		bool adjustBounds() const final;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( ImageSampler )

} // namespace GafferScene

#endif // GAFFERSCENE_IMAGESAMPLER_H
