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

#ifndef GAFFERIMAGE_LUT_H
#define GAFFERIMAGE_LUT_H

#include "GafferImage/OpenColorIOTransform.h"

#include "Gaffer/NumericPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )

} // namespace Gaffer

namespace GafferImage
{

class GAFFERIMAGE_API LUT : public OpenColorIOTransform
{

	public :

		LUT( const std::string &name=defaultName<LUT>() );
		~LUT() override;

		GAFFER_NODE_DECLARE_TYPE( GafferImage::LUT, LUTTypeId, OpenColorIOTransform );

		enum Interpolation
		{
			Best = 0,
			Nearest,
			Linear,
			Tetrahedral
		};

		Gaffer::StringPlug *fileNamePlug();
		const Gaffer::StringPlug *fileNamePlug() const;

		Gaffer::IntPlug *interpolationPlug();
		const Gaffer::IntPlug *interpolationPlug() const;

		Gaffer::IntPlug *directionPlug();
		const Gaffer::IntPlug *directionPlug() const;

		/// Fills the supplied vector with the supported
		/// file extensions for the LUT node.
		static size_t supportedExtensions( std::vector<std::string> &extensions );

	protected :

		bool affectsTransform( const Gaffer::Plug *input ) const override;
		void hashTransform( const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		OCIO_NAMESPACE::ConstTransformRcPtr transform() const override;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( LUT )

} // namespace GafferImage

#endif // GAFFERIMAGE_LUT_H
