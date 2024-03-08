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

#include "GafferUI/Pointer.h"

#include "IECore/CachedReader.h"

#include "fmt/format.h"

using namespace GafferUI;

namespace
{

static ConstPointerPtr g_current;

using Registry = std::map<std::string, ConstPointerPtr>;
static Registry &registry()
{
	static Registry r;
	if( !r.size() )
	{
		// register standard pointers
		r["move"] = new Pointer( "move.png", Imath::V2i( 10 ) );
		r["moveDiagonallyUp"] = new Pointer( "moveDiagonallyUp.png", Imath::V2i( 10 ) );
		r["moveDiagonallyDown"] = new Pointer( "moveDiagonallyDown.png", Imath::V2i( 10 ) );
		r["moveHorizontally"] = new Pointer( "moveHorizontally.png", Imath::V2i( 10 ) );
		r["moveVertically"] = new Pointer( "moveVertically.png", Imath::V2i( 10 ) );
		r["nodes"] = new Pointer( "nodes.png", Imath::V2i( 10, 5 ) );
		r["objects"] = new Pointer( "objects.png", Imath::V2i( 53, 14 ) );
		r["plug"] = new Pointer( "plug.png", Imath::V2i( 8, 7 ) );
		r["rgba"] = new Pointer( "rgba.png", Imath::V2i( 11, 5 ) );
		r["values"] = new Pointer( "values.png", Imath::V2i( 18, 11 ) );
		r["paths"] = new Pointer( "paths.png", Imath::V2i( 7, 6 ) );
		r["contextMenu"] = new Pointer( "pointerContextMenu.png", Imath::V2i( 1 ) );
		r["tab"] = new Pointer( "pointerTab.png", Imath::V2i( 12, 13 ) );
		r["detachedPanel"] = new Pointer( "pointerDetachedPanel.png", Imath::V2i( 12, 13 ) );
		r["target"] = new Pointer( "pointerTarget.png", Imath::V2i( 14 ) );
		r["crossHair"] = new Pointer( "pointerCrossHair.png", Imath::V2i( 14 ) );
		r["add"] = new Pointer( "pointerAdd.png", Imath::V2i( 18, 11 ) );
		r["remove"] = new Pointer( "pointerRemove.png", Imath::V2i( 18, 11 ) );
		r["rotate"] = new Pointer( "pointerRotate.png", Imath::V2i( 10 ) );
		r["pivot"] = new Pointer( "pointerPivot.png", Imath::V2i( 13, 0 ) );
		r["cut"] = new Pointer( "pointerCut.png", Imath::V2i( 11, 7 ) );
		r["notEditable"] = new Pointer( "pointerNotEditable.png", Imath::V2i( 10 ) );
	}
	return r;
}

} // namespace

Pointer::Pointer( const IECoreImage::ImagePrimitive *image, const Imath::V2i &hotspot )
	:	m_image( image->copy() ), m_hotspot( hotspot )
{
}

Pointer::Pointer( const std::string &fileName, const Imath::V2i &hotspot )
	:	m_image( nullptr ), m_hotspot( hotspot )
{
	static IECore::CachedReaderPtr g_reader;
	if( !g_reader )
	{
		const char *sp = getenv( "GAFFERUI_IMAGE_PATHS" );
		sp = sp ? sp : "";
		g_reader = new IECore::CachedReader( IECore::SearchPath( sp ) );
	}

	m_image = IECore::runTimeCast<const IECoreImage::ImagePrimitive>( g_reader->read( fileName ) );
	if( !m_image )
	{
		throw IECore::Exception(
			fmt::format( "File \"{}\" does not contain an image.", fileName )
		);
	}
}

const IECoreImage::ImagePrimitive *Pointer::image() const
{
	return m_image.get();
}

const Imath::V2i &Pointer::hotspot() const
{
	return m_hotspot;
}

void Pointer::setCurrent( ConstPointerPtr pointer )
{
	if( !pointer && !g_current )
	{
		return;
	}
	if(
		pointer && g_current &&
		pointer->image()->isEqualTo( g_current->image() ) &&
		pointer->hotspot() == g_current->hotspot()
	)
	{
		return;
	}

	g_current = pointer;
	changedSignal()();
}

void Pointer::setCurrent( const std::string &name )
{
	if( !name.size() )
	{
		Pointer::setCurrent( (Pointer *)nullptr );
		return;
	}

	const Registry &r = registry();
	Registry::const_iterator it = r.find( name );
	if( it == r.end() )
	{
		throw IECore::Exception( fmt::format( "Pointer \"{}\" does not exist", name ) );
	}

	setCurrent( it->second );
}

const Pointer *Pointer::getCurrent()
{
	return g_current.get();
}

void Pointer::registerPointer( const std::string &name, ConstPointerPtr pointer )
{
	registry()[name] = pointer;
}

Pointer::ChangedSignal &Pointer::changedSignal()
{
	static ChangedSignal s;
	return s;
}
