//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//	  * Redistributions of source code must retain the above
//		copyright notice, this list of conditions and the following
//		disclaimer.
//
//	  * Redistributions in binary form must reproduce the above
//		copyright notice, this list of conditions and the following
//		disclaimer in the documentation and/or other materials provided with
//		the distribution.
//
//	  * Neither the name of John Haddon nor the names of
//		any other contributors to this software may be used to endorse or
//		promote products derived from this software without specific prior
//		written permission.
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

#ifndef GAFFERIMAGE_LOOKTRANSFORM_H
#define GAFFERIMAGE_LOOKTRANSFORM_H

#include "GafferImage/OpenColorIOTransform.h"

namespace GafferImage
{

class GAFFERIMAGE_API LookTransform : public OpenColorIOTransform
{

	public :

		LookTransform( const std::string &name=defaultName<LookTransform>() );
		~LookTransform() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::LookTransform, LookTransformTypeId, OpenColorIOTransform );

		Gaffer::StringPlug *lookPlug();
		const Gaffer::StringPlug *lookPlug() const;
		Gaffer::IntPlug *directionPlug();
		const Gaffer::IntPlug *directionPlug() const;

	protected :

		bool affectsTransform( const Gaffer::Plug *input ) const override;
		void hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		OCIO_NAMESPACE::ConstTransformRcPtr transform() const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( LookTransform )

} // namespace GafferImage

#endif // GAFFERIMAGE_LOOKTRANSFORM_H
