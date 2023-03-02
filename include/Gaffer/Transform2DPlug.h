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

#pragma once

#include "Gaffer/CompoundNumericPlug.h"

namespace Gaffer
{

class GAFFER_API Transform2DPlug : public ValuePlug
{

	public :

		Transform2DPlug(
			const std::string &name = defaultName<Transform2DPlug>(),
			Direction direction=In,
			const Imath::V2f &defaultTranslate = Imath::V2f( 0 ),
			float defaultRotate = 0,
			const Imath::V2f &defaultScale = Imath::V2f( 1 ),
			const Imath::V2f &defaultPivot = Imath::V2f( 0 ),
			unsigned flags = Default
		);
		~Transform2DPlug() override;

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::Transform2DPlug, Transform2DPlugTypeId, ValuePlug );

		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		V2fPlug *translatePlug();
		const V2fPlug *translatePlug() const;
		FloatPlug *rotatePlug();
		const FloatPlug *rotatePlug() const;
		V2fPlug *scalePlug();
		const V2fPlug *scalePlug() const;
		V2fPlug *pivotPlug();
		const V2fPlug *pivotPlug() const;

		Imath::M33f matrix() const;

	private :

		static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( Transform2DPlug );

} // namespace Gaffer
