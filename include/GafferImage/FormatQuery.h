//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERIMAGE_FORMATQUERY_H
#define GAFFERIMAGE_FORMATQUERY_H

#include "GafferImage/Export.h"
#include "GafferImage/FormatPlug.h"
#include "GafferImage/ImagePlug.h"
#include "GafferImage/TypeIds.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/CompoundNumericPlug.h"
#include "Gaffer/StringPlug.h"

namespace GafferImage
{

struct GAFFERIMAGE_API FormatQuery : Gaffer::ComputeNode
{

	FormatQuery( std::string const& name = defaultName< FormatQuery >() );
	~FormatQuery() override;

	GAFFER_NODE_DECLARE_TYPE( GafferImage::FormatQuery, FormatQueryTypeId, Gaffer::ComputeNode );

	GafferImage::ImagePlug* imagePlug();
	GafferImage::ImagePlug const* imagePlug() const;

	Gaffer::StringPlug *viewPlug();
	const Gaffer::StringPlug *viewPlug() const;

	GafferImage::FormatPlug* formatPlug();
	GafferImage::FormatPlug const* formatPlug() const;

	Gaffer::V2fPlug* centerPlug();
	Gaffer::V2fPlug const* centerPlug() const;
	Gaffer::V2iPlug* sizePlug();
	Gaffer::V2iPlug const* sizePlug() const;

	void affects( Gaffer::Plug const* input, AffectedPlugsContainer& outputs ) const override;

protected:

	void hash( Gaffer::ValuePlug const* output, Gaffer::Context const* context, IECore::MurmurHash& hash ) const override;
	void compute( Gaffer::ValuePlug* output, Gaffer::Context const* context ) const override;

private:

	static size_t g_firstPlugIndex;
};

IE_CORE_DECLAREPTR( FormatQuery )

} // GafferImage

#endif // GAFFERIMAGE_FORMATQUERY_H
