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

#include "GafferImage/Text.h"

#include "GafferImage/BufferAlgo.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/Transform2DPlug.h"
#include "Gaffer/Private/IECorePreview/LRUCache.h"

#include "IECore/SearchPath.h"

#include "tbb/enumerable_thread_specific.h"
#ifdef SearchPath
#undef SearchPath
#endif

#include "boost/locale/encoding_utf.hpp"

#include "ft2build.h"

#include FT_FREETYPE_H

#include <memory>

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// FreeType recommends that for thread safety it is easiest to use
// a distinct FT_Library instance per thread. This function returns
// the appropriate library for the current thread.
FT_Library library()
{
	using ThreadSpecificLibrary = tbb::enumerable_thread_specific<FT_Library>;
	static ThreadSpecificLibrary g_threadLibraries( FT_Library( nullptr ) );

	FT_Library &l = g_threadLibraries.local();
	if( !l )
	{
		FT_Error e = FT_Init_FreeType( &l );
		if( e )
		{
			throw Exception( "Error initialising FreeType library." );
		}
	}
	return l;
}

// We want to maintain a cache of FT_Faces, because creating them
// is fairly costly. But since FT_Faces belong to FT_Libraries
// the cache must be maintained per-thread.
using FacePtr = std::shared_ptr<FT_FaceRec_>;
FacePtr faceLoader( const std::string &font, size_t &cost, const IECore::Canceller *canceller )
{
	const char *e = getenv( "IECORE_FONT_PATHS" );
	IECore::SearchPath sp( e ? e : "" );

	std::string file = sp.find( font ).generic_string();
	if( !file.size() )
	{
		throw Exception( boost::str( boost::format( "Unable to find font \"%s\"." ) % font ) );
	}

	FT_Face face = nullptr;
	FT_Error error = FT_New_Face( library(), file.c_str(), 0, &face );
	// We use a smart pointer now to make sure we call FT_Done_Face no matter what.
	FacePtr result( face, FT_Done_Face );

	if( error )
	{
		throw Exception( boost::str( boost::format( "Error loading font \"%s\"." ) % font ) );
	}

	cost = 1;
	return result;
}

using FaceCache = IECorePreview::LRUCache<string, FacePtr>;
using FaceCachePtr = std::unique_ptr<FaceCache>;
FaceCachePtr createFaceCache()
{
	return FaceCachePtr( new FaceCache( faceLoader, 500 ) );
}

FacePtr face( const string &font, const V2i &size )
{
	using ThreadSpecificFaceCache = tbb::enumerable_thread_specific<FaceCachePtr>;
	static ThreadSpecificFaceCache g_faceCaches( createFaceCache );

	FacePtr face = g_faceCaches.local()->get( font );

	FT_Set_Transform( face.get(), nullptr, nullptr );
	FT_Error error = FT_Set_Pixel_Sizes( face.get(), size.x, size.y );
	if( error )
	{
		throw Exception( boost::str( boost::format( "Error setting size for font \"%s\"." ) % font ) );
	}

	return face;
}

FT_Matrix transform( const M33f &transform, FT_Vector &delta )
{
	FT_Matrix matrix;

	matrix.xx = (FT_Fixed)( transform[0][0] * 0x10000L );
	matrix.xy = (FT_Fixed)( transform[1][0] * 0x10000L );
	matrix.yx = (FT_Fixed)( transform[0][1] * 0x10000L );
	matrix.yy = (FT_Fixed)( transform[1][1] * 0x10000L );

	delta.x = (FT_Pos)(transform.translation()[0] * 64); // FT_Set_Transform expects delta
	delta.y = (FT_Pos)(transform.translation()[1] * 64); // to be in 1/64ths of a pixel.

	return matrix;
}

u32string fromUTF8( const string &utf8 )
{
	return boost::locale::conv::utf_to_utf<char32_t>( utf8 );
}

int width( const u32string &word, FT_FaceRec *face )
{
	int result = 0;
	for( auto c : word )
	{
		FT_Error e = FT_Load_Char( face, c, FT_LOAD_DEFAULT );
		if( e )
		{
			continue;
		}
		result += face->glyph->advance.x;
	}

	return result;
}

struct Word
{
	Word( const u32string &text, int x )
		:	text( text ), x( x )
	{
	}

	u32string text;
	int x;
};

struct Line
{
	Line( int y )
		: y( y ), width( 0 )
	{
	}

	vector<Word> words;
	int y;
	int width;
};

} // namespace

//////////////////////////////////////////////////////////////////////////
// Text node
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Text );

size_t Text::g_firstPlugIndex = 0;

Text::Text( const std::string &name )
	:	Shape( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "text", Plug::In, "Hello World" ) );
	addChild( new StringPlug( "font", Plug::In, "Vera.ttf" ) );
	addChild( new V2iPlug( "size", Plug::In, V2i( 50 ), V2i( 0 ) ) );
	addChild( new Box2iPlug( "area" ) );
	addChild( new IntPlug( "horizontalAlignment", Plug::In, Left, Left, HorizontalCenter ) );
	addChild( new IntPlug( "verticalAlignment", Plug::In, Top, Bottom, VerticalCenter ) );
	addChild( new Transform2DPlug( "transform" ) );
	addChild( new CompoundObjectPlug( "__layout", Plug::Out, new CompoundObject ) );
}

Text::~Text()
{
}

Gaffer::StringPlug *Text::textPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Text::textPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *Text::fontPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *Text::fontPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::V2iPlug *Text::sizePlug()
{
	return getChild<V2iPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::V2iPlug *Text::sizePlug() const
{
	return getChild<V2iPlug>( g_firstPlugIndex + 2 );
}

Gaffer::Box2iPlug *Text::areaPlug()
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::Box2iPlug *Text::areaPlug() const
{
	return getChild<Box2iPlug>( g_firstPlugIndex + 3 );
}

Gaffer::IntPlug *Text::horizontalAlignmentPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::IntPlug *Text::horizontalAlignmentPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 4 );
}

Gaffer::IntPlug *Text::verticalAlignmentPlug()
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::IntPlug *Text::verticalAlignmentPlug() const
{
	return getChild<IntPlug>( g_firstPlugIndex + 5 );
}

Gaffer::Transform2DPlug *Text::transformPlug()
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::Transform2DPlug *Text::transformPlug() const
{
	return getChild<Transform2DPlug>( g_firstPlugIndex + 6 );
}

Gaffer::CompoundObjectPlug *Text::layoutPlug()
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::CompoundObjectPlug *Text::layoutPlug() const
{
	return getChild<CompoundObjectPlug>( g_firstPlugIndex + 7 );
}

void Text::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	Shape::affects( input, outputs );

	if( affectsLayout( input ) )
	{
		outputs.push_back( layoutPlug() );
	}
}

void Text::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Shape::hash( output, context, h );

	if( output == layoutPlug() )
	{
		hashLayout( context, h );
	}
}

void Text::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == layoutPlug() )
	{
		static_cast<CompoundObjectPlug *>( output )->setValue(
			computeLayout( context )
		);
		return;
	}
	else
	{
		Shape::compute( output, context );
	}
}

bool Text::affectsLayout( const Gaffer::Plug *input ) const
{
	return
		input == textPlug() ||
		input == fontPlug() ||
		input->parent<V2iPlug>() == sizePlug() ||
		areaPlug()->isAncestorOf( input ) ||
		input == inPlug()->formatPlug() ||
		input == horizontalAlignmentPlug() ||
		input == verticalAlignmentPlug() ||
		transformPlug()->isAncestorOf( input );
}

void Text::hashLayout( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	textPlug()->hash( h );
	fontPlug()->hash( h );
	sizePlug()->hash( h );
	areaPlug()->hash( h );
	inPlug()->formatPlug()->hash( h );
	horizontalAlignmentPlug()->hash( h );
	verticalAlignmentPlug()->hash( h );
	transformPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr Text::computeLayout( const Gaffer::Context *context ) const
{

	// Get the face.

	const V2i size = sizePlug()->getValue();
	const string font = fontPlug()->getValue();
	FacePtr face = ::face( font, size );

	// For simplicity we start by performing the word wrapping
	// and layout in the untransformed axis-aligned space specified by
	// the area plug. We use FreeType's 26.6 fixed integer format for
	// this stage, which measures in 64ths of a pixel. We store the layout
	// in a vector of Lines made up of Words.

	Box2i area = areaPlug()->getValue();
	if( BufferAlgo::empty( area ) )
	{
		area = inPlug()->formatPlug()->getValue().getDisplayWindow();
	}

	area.min *= 64; area.max *= 64;
	V2i pen = V2i( area.min.x, area.max.y - face->size->metrics.ascender );

	vector<Line> lines;
	lines.push_back( Line( pen.y ) );

	int penYCutoff = area.min.y - face->size->metrics.descender;

	const std::string text = textPlug()->getValue();
	/// \todo Does tokenization/wrapping need to be unicode aware?
	using Tokenizer = boost::tokenizer<boost::char_separator<char> >;
	boost::char_separator<char> separator( "", " \n\t" );
	Tokenizer tokenizer( text, separator );
	for( Tokenizer::iterator it = tokenizer.begin(), eIt = tokenizer.end(); it != eIt; ++it )
	{
		if( *it == "\n" )
		{
			pen.x = area.min.x;

			if( pen.y - face->size->metrics.height < penYCutoff )
			{
				// We ran out of vertical space.
				break;
			}

			pen.y -= face->size->metrics.height;
			lines.push_back( Line( pen.y ) );
		}
		else if( *it == " " || *it =="\t" )
		{
			pen.x += ::width( fromUTF8( *it ), face.get() );
		}
		else
		{
			const u32string word = fromUTF8( *it );
			int width = ::width( word, face.get() );
			if( pen.x + width > area.max.x && pen.x > area.min.x )
			{
				pen.x = area.min.x;

				if( pen.y - face->size->metrics.height < penYCutoff )
				{
					// We ran out of vertical space.
					break;
				}

				pen.y -= face->size->metrics.height;
				lines.push_back( Line( pen.y ) );
			}

			lines.back().words.push_back( Word( word, pen.x ) );
			pen.x += width;
			lines.back().width = pen.x - area.min.x;
		}
	}

	// Now we'll take that basic layout and apply the transform
	// to it, generating everything we'll need later in
	// computeShapeDataWindow() and computeShapeChannelData().
	// We start by generating the container which is used to store
	// the layout on layoutPlug().

	CompoundObjectPtr layout = new CompoundObject;

	layout->members()["font"] = new StringData( font );
	layout->members()["size"] = new V2iData( size );

	const IntVectorDataPtr characters = new IntVectorData;
	const M33fVectorDataPtr transforms = new M33fVectorData;
	const Box2iVectorDataPtr bounds = new Box2iVectorData;
	layout->members()["characters"] = characters;
	layout->members()["transforms"] = transforms;
	layout->members()["bounds"] = bounds;

	// Now we fill that container by transforming the laid out lines
	// we generated already. During this phase we use floating point
	// format to represent pixel coordinates, storing our transform in
	// an M33f. This is because we need our transform to be storable in a
	// CompoundObject. It is also during this phase that we apply the
	// justification.

	const HorizontalAlignment horizontalAlignment = (HorizontalAlignment)horizontalAlignmentPlug()->getValue();
	const VerticalAlignment verticalAlignment = (VerticalAlignment)verticalAlignmentPlug()->getValue();
	const M33f transform = transformPlug()->matrix();

	float yOffset = 0;
	if( verticalAlignment == Bottom )
	{
		yOffset = (float)(area.min.y - (pen.y + face->size->metrics.descender) ) / 64.0f;
	}
	else if( verticalAlignment == VerticalCenter )
	{
		yOffset = (float)(area.min.y - (pen.y + face->size->metrics.descender) ) / (64.0f * 2.0f);
	}

	FT_GlyphSlot slot = face->glyph;

	for( vector<Line>::const_iterator lIt = lines.begin(), leIt = lines.end(); lIt != leIt; ++lIt )
	{
		float xOffset = 0;
		if( horizontalAlignment == Right )
		{
			xOffset = (float)(area.size().x - lIt->width) / 64.0f;
		}
		else if( horizontalAlignment == HorizontalCenter )
		{
			xOffset = (float)(area.size().x - lIt->width) / (64.0f * 2.0f);
		}

		for( vector<Word>::const_iterator wIt = lIt->words.begin(), weIt = lIt->words.end(); wIt != weIt; ++wIt )
		{
			M33f characterTransform;
			characterTransform[2][0] = xOffset + (float)wIt->x / 64.0f;
			characterTransform[2][1] = yOffset + (float)lIt->y / 64.0f;
			characterTransform *= transform;

			for( auto c : wIt->text )
			{
				FT_Vector delta;
				FT_Matrix matrix = ::transform( characterTransform, delta );
				FT_Set_Transform( face.get(), &matrix, &delta );

				FT_Error e = FT_Load_Char( face.get(), c, FT_LOAD_RENDER );
				if( e )
				{
					continue;
				}

				const FT_Bitmap &bitmap = slot->bitmap;
				const Box2i bound(
					V2i( slot->bitmap_left, slot->bitmap_top - bitmap.rows ),
					V2i( slot->bitmap_left + bitmap.width, slot->bitmap_top )
				);

				characters->writable().push_back( c );
				transforms->writable().push_back( characterTransform );
				bounds->writable().push_back( bound );

				characterTransform[2][0] += (float)slot->advance.x / 64.0f;
				characterTransform[2][1] += (float)slot->advance.y / 64.0f;
			}
		}
	}

	return layout;
}

bool Text::affectsShapeDataWindow( const Gaffer::Plug *input ) const
{
	if( Shape::affectsShapeDataWindow( input ) )
	{
		return true;
	}

	return input == layoutPlug();
}

void Text::hashShapeDataWindow( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Shape::hashShapeDataWindow( context, h );
	layoutPlug()->hash( h );
}

Imath::Box2i Text::computeShapeDataWindow( const Gaffer::Context *context ) const
{
	ConstCompoundObjectPtr layout = layoutPlug()->getValue();
	const vector<Box2i> &bounds = layout->member<Box2iVectorData>( "bounds" )->readable();

	Box2i result;
	for( vector<Box2i>::const_iterator it = bounds.begin(), eIt = bounds.end(); it != eIt; ++it )
	{
		result.extendBy( *it );
	}

	return result;
}

bool Text::affectsShapeChannelData( const Gaffer::Plug *input ) const
{
	if( Shape::affectsShapeChannelData( input ) )
	{
		return true;
	}

	return input == layoutPlug();
}

void Text::hashShapeChannelData( const Imath::V2i &tileOrigin, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	Shape::hashShapeChannelData( tileOrigin, context, h );
	{
		ImagePlug::GlobalScope c( context );
		layoutPlug()->hash( h );
	}
	h.append( tileOrigin );
}

IECore::ConstFloatVectorDataPtr Text::computeShapeChannelData(  const Imath::V2i &tileOrigin, const Gaffer::Context *context ) const
{
	ConstCompoundObjectPtr layout;
	{
		ImagePlug::GlobalScope c( context );
		layout = layoutPlug()->getValue();
	}

	const vector<int> &characters = layout->member<IntVectorData>( "characters" )->readable();
	const vector<M33f> &transforms = layout->member<M33fVectorData>( "transforms" )->readable();
	const vector<Box2i> &bounds = layout->member<Box2iVectorData>( "bounds" )->readable();

	FacePtr face = ::face( layout->member<StringData>( "font" )->readable(), layout->member<V2iData>( "size" )->readable() );
	FT_GlyphSlot slot = face->glyph;

	FloatVectorDataPtr resultData = new FloatVectorData();
	vector<float> &result = resultData->writable();
	result.resize( ImagePlug::tileSize() * ImagePlug::tileSize(), 0.0f );

	const Box2i tileBound( tileOrigin, tileOrigin + V2i( ImagePlug::tileSize() ) );

	for( int i = 0, e = characters.size(); i < e; ++i )
	{
		const Box2i &bitmapBound = bounds[i];
		const Box2i validBound = BufferAlgo::intersection( tileBound, bitmapBound );
		if( BufferAlgo::empty( validBound ) )
		{
			continue;
		}

		FT_Vector delta;
		FT_Matrix matrix = transform( transforms[i], delta );
		FT_Set_Transform( face.get(), &matrix, &delta );

		FT_Error error = FT_Load_Char( face.get(), characters[i], FT_LOAD_RENDER );
		if( error )
		{
			continue;
		}

		const FT_Bitmap &bitmap = slot->bitmap;

		V2i p;
		for( p.y = validBound.min.y; p.y < validBound.max.y; ++p.y )
		{
			const unsigned char *src = bitmap.buffer + ( bitmapBound.max.y - 1 - p.y ) * bitmap.pitch + validBound.min.x - bitmapBound.min.x;
			vector<float>::iterator dst = result.begin() + ( p.y - tileBound.min.y ) * ImagePlug::tileSize() + validBound.min.x - tileBound.min.x;
			for( p.x = validBound.min.x; p.x < validBound.max.x; ++p.x )
			{
				// FreeType gives us linear coverage values suitable
				// for direct use as an alpha, so we don't need to do
				// any special colour transforms.
				float v = (float)*src / 255.0f;
				// But characters can overlap at small font sizes so
				// we're careful to screen the results so that we don't
				// create an alpha above 1.
				*dst += v - v * *dst;
				src++;
				dst++;
			}
		}
	}

	return resultData;
}
