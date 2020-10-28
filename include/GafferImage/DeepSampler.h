//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_DEEPSAMPLER_H
#define GAFFERIMAGE_DEEPSAMPLER_H

#include "GafferImage/DeepState.h"
#include "GafferImage/Export.h"
#include "GafferImage/TypeIds.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/ComputeNode.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferImage
{

class GAFFERIMAGE_API DeepSampler : public Gaffer::ComputeNode
{

	public :

		DeepSampler( const std::string &name=defaultName<DeepSampler>() );
		~DeepSampler() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::DeepSampler, DeepSamplerTypeId, ComputeNode );

		ImagePlug *imagePlug();
		const ImagePlug *imagePlug() const;

		Gaffer::V2iPlug *pixelPlug();
		const Gaffer::V2iPlug *pixelPlug() const;

		Gaffer::AtomicCompoundDataPlug *pixelDataPlug();
		const Gaffer::AtomicCompoundDataPlug *pixelDataPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

	private :

		static size_t g_firstPlugIndex;

};

} // namespace GafferImage

#endif // GAFFERIMAGE_DEEPSAMPLER_H
