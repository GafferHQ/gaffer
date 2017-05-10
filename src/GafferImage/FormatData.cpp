//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include "GafferImage/FormatData.h"

#include "GafferImage/Export.h"
#include "GafferImage/TypeIds.h"

#include "Gaffer/Context.h"

#include "IECore/TypedData.h"
#include "IECore/TypedData.inl"

using namespace Imath;

namespace
{

Gaffer::Context::TypeDescription<GafferImage::FormatData> g_formatDataTypeDescription;

} // namespace

namespace IECore
{

IECORE_RUNTIMETYPED_DEFINETEMPLATESPECIALISATION( GafferImage::FormatData, GafferImage::FormatDataTypeId )

template<> GAFFERIMAGE_API
void FormatData::save( SaveContext *context ) const
{
	Data::save( context );

	IndexedIO *container = context->rawContainer();
	container->write( "displayWindow", (const int*)&(readable().getDisplayWindow()), 4 );
	container->write( "pixelAspect", readable().getPixelAspect() );
}

template<> GAFFERIMAGE_API
void FormatData::load( LoadContextPtr context )
{
	Data::load( context );

	const IndexedIO *container = context->rawContainer();

	Box2i displayWindow;
	int *displayWindowPtr = (int *)&displayWindow;
	container->read( "displayWindow", displayWindowPtr, 4 );
	writable().setDisplayWindow( displayWindow );

	double pixelAspect = 1.0;
	container->read( "pixelAspect", pixelAspect );
	writable().setPixelAspect( pixelAspect );
}

template<> GAFFERIMAGE_API
void SimpleDataHolder<GafferImage::Format>::hash( MurmurHash &h ) const
{
	const GafferImage::Format &f = readable();
	h.append( f.getDisplayWindow() );
	h.append( f.getPixelAspect() );
}

template class TypedData<GafferImage::Format>;

} // namespace IECore
