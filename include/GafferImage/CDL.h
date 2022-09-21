//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_CDL_H
#define GAFFERIMAGE_CDL_H

#include "GafferImage/OpenColorIOTransform.h"

#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/NumericPlug.h"

namespace GafferImage
{

class GAFFERIMAGE_API CDL : public OpenColorIOTransform
{

	public :

		CDL( const std::string &name=defaultName<CDL>() );
		~CDL() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::CDL, CDLTypeId, OpenColorIOTransform );

		// Direction enum is inline with the other OCIO nodes and will work
		// with OCIO 1.x and 2.x now. Compatibility will be maintained except
		// where expressions may have been used to set the direction plug.
		enum Direction
		{
			Forward = 0,
			Inverse = 1
		};

		Gaffer::Color3fPlug *slopePlug();
		const Gaffer::Color3fPlug *slopePlug() const;

		Gaffer::Color3fPlug *offsetPlug();
		const Gaffer::Color3fPlug *offsetPlug() const;

		Gaffer::Color3fPlug *powerPlug();
		const Gaffer::Color3fPlug *powerPlug() const;

		Gaffer::FloatPlug *saturationPlug();
		const Gaffer::FloatPlug *saturationPlug() const;

		Gaffer::IntPlug *directionPlug();
		const Gaffer::IntPlug *directionPlug() const;

	protected :

		bool affectsTransform( const Gaffer::Plug *input ) const override;
		void hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		OCIO_NAMESPACE::ConstTransformRcPtr transform() const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( CDL )

} // namespace GafferImage

#endif // GAFFERIMAGE_CDL_H
