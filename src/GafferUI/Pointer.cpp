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

#include "IECore/CachedReader.h"

#include "GafferUI/Pointer.h"

using namespace GafferUI;

static IECore::ConstImagePrimitivePtr g_image;

void Pointer::set( IECore::ConstImagePrimitivePtr image )
{
	if( !image && !g_image )
	{
		return;
	}
	if( image && g_image && image->isEqualTo( g_image ) )
	{
		return;
	}
	
	g_image = image;
	changedSignal()();
}

const IECore::ImagePrimitive *Pointer::get()
{
	return g_image.get();
}

void Pointer::setFromFile( const std::string &name )
{
	if( !name.size() )
	{
		set( NULL );
		return;
	}

	static IECore::CachedReaderPtr g_reader;
	if( !g_reader )
	{
		const char *sp = getenv( "GAFFERUI_IMAGE_PATHS" );
		sp = sp ? sp : "";
		g_reader = new IECore::CachedReader( IECore::SearchPath( sp, ":" ) );
	}

	IECore::ConstImagePrimitivePtr image = IECore::runTimeCast<const IECore::ImagePrimitive>( g_reader->read( name ) ); 
	if( !image )
	{
		throw IECore::Exception( 
			boost::str( boost::format( "File \"%s\" does not contain an image." ) % name )
		);
	}
	
	set( image );
}

Pointer::ChangedSignal &Pointer::changedSignal()
{
	static ChangedSignal s;
	return s;
}
