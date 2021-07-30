//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, John Haddon. All rights reserved.
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

#include "GafferUI/AnnotationsGadget.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/ImageGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/Style.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"
#include "boost/bind/placeholders.hpp"

using namespace GafferUI;
using namespace Gaffer;
using namespace IECore;
using namespace Imath;
using namespace std;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

Box2f nodeFrame( const NodeGadget *nodeGadget )
{
	const Box3f b = nodeGadget->transformedBound( nullptr );
	return Box2f(
		V2f( b.min.x, b.min.y ),
		V2f( b.max.x, b.max.y )
	);
}


IECoreGL::Texture *bookmarkTexture()
{
	static IECoreGL::TexturePtr bookmarkTexture;

	if( !bookmarkTexture )
	{
		bookmarkTexture = ImageGadget::textureLoader()->load( "bookmarkStar2.png" );

		IECoreGL::Texture::ScopedBinding binding( *bookmarkTexture );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER );
	}
	return bookmarkTexture.get();
}

IECoreGL::Texture *numericBookmarkTexture()
{
	static IECoreGL::TexturePtr numericBookmarkTexture;

	if( !numericBookmarkTexture )
	{
		numericBookmarkTexture = ImageGadget::textureLoader()->load( "bookmarkStar.png" );

		IECoreGL::Texture::ScopedBinding binding( *numericBookmarkTexture );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER );
	}
	return numericBookmarkTexture.get();
}

string wrap( const std::string &text, size_t maxLineLength )
{
	string result;

	using Tokenizer = boost::tokenizer<boost::char_separator<char>>;
	boost::char_separator<char> separator( "", " \n" );
	Tokenizer tokenizer( text, separator );

	size_t lineLength = 0;
	for( const auto &s : tokenizer )
	{
		if( s == "\n" )
		{
			result += s;
			lineLength = 0;
		}
		else if( lineLength == 0 || lineLength + s.size() < maxLineLength )
		{
			result += s;
			lineLength += s.size();
		}
		else
		{
			result += "\n" + s;
			lineLength = s.size();
		}
	}

	return result;
}
float g_offset = 0.5;

} // namespace

//////////////////////////////////////////////////////////////////////////
// AnnotationsGadget
//////////////////////////////////////////////////////////////////////////

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( AnnotationsGadget );

const std::string AnnotationsGadget::untemplatedAnnotations = "__untemplated__";

AnnotationsGadget::AnnotationsGadget()
	:	Gadget( "AnnotationsGadget" ), m_dirty( true ), m_visibleAnnotations( "*" )
{
	Metadata::nodeValueChangedSignal().connect(
		boost::bind( &AnnotationsGadget::nodeMetadataChanged, this, ::_1, ::_2, ::_3 )
	);
}

AnnotationsGadget::~AnnotationsGadget()
{
}

void AnnotationsGadget::setVisibleAnnotations( const IECore::StringAlgo::MatchPattern &patterns )
{
	if( patterns == m_visibleAnnotations )
	{
		return;
	}

	m_visibleAnnotations = patterns;
	for( auto &a : m_annotations )
	{
		a.second.dirty = true;
	}
	m_dirty = true;
	dirty( DirtyType::Render );
}

const IECore::StringAlgo::MatchPattern &AnnotationsGadget::getVisibleAnnotations() const
{
	return m_visibleAnnotations;
}

bool AnnotationsGadget::acceptsParent( const GraphComponent *potentialParent ) const
{
	return runTimeCast<const GraphGadget>( potentialParent );
}

void AnnotationsGadget::parentChanging( Gaffer::GraphComponent *newParent )
{
	m_annotations.clear();
	m_graphGadgetChildAddedConnection.disconnect();
	m_graphGadgetChildRemovedConnection.disconnect();
	if( newParent )
	{
		m_graphGadgetChildAddedConnection = newParent->childAddedSignal().connect(
			boost::bind( &AnnotationsGadget::graphGadgetChildAdded, this, ::_2 )
		);
		m_graphGadgetChildRemovedConnection = newParent->childRemovedSignal().connect(
			boost::bind( &AnnotationsGadget::graphGadgetChildRemoved, this, ::_2 )
		);
	}
}

void AnnotationsGadget::renderLayer( Layer layer, const Style *style, RenderReason reason ) const
{
	if( layer != GraphLayer::Overlay )
	{
		return;
	}

	update();

	for( auto &ga : m_annotations )
	{
		Annotations &annotations = ga.second;
		assert( !annotations.dirty );
		if( !annotations.renderable )
		{
			continue;
		}

		const Box2f b = nodeFrame( ga.first );
		if( annotations.bookmarked )
		{
			style->renderImage( Box2f( V2f( b.min.x - 1.0, b.max.y - 1.0 ), V2f( b.min.x + 1.0, b.max.y + 1.0 ) ), bookmarkTexture() );
		}

		if( annotations.numericBookmark.string().size() )
		{
			if( !annotations.bookmarked )
			{
				style->renderImage( Box2f( V2f( b.min.x - 1.0, b.max.y - 1.0 ), V2f( b.min.x + 1.0, b.max.y + 1.0 ) ), numericBookmarkTexture() );
			}

			const Box3f textBounds = style->textBound( Style::LabelText, annotations.numericBookmark.string() );

			const Imath::Color4f textColor( 1.0f );
			glPushMatrix();
				IECoreGL::glTranslate( V2f( b.min.x + 1.0 - textBounds.size().x * 0.5, b.max.y - textBounds.size().y * 0.5 - 0.7 ) );
				style->renderText( Style::BodyText, annotations.numericBookmark.string(), Style::NormalState, &textColor );
			glPopMatrix();
		}

		V2f origin( b.max.x + g_offset, b.max.y );
		for( const auto &a : annotations.standardAnnotations )
		{
			origin = style->renderAnnotation( origin, a.text(), Style::NormalState, a.colorData ? &a.color() : nullptr );
		}
	}
}

unsigned AnnotationsGadget::layerMask() const
{
	return (unsigned)GraphLayer::Overlay;
}

Imath::Box3f AnnotationsGadget::renderBound() const
{
	// This Gadget renders annotations for many nodes, so we can't give it a tight render bound
	Box3f b;
	b.makeInfinite();
	return b;
}

GraphGadget *AnnotationsGadget::graphGadget()
{
	return parent<GraphGadget>();
}

const GraphGadget *AnnotationsGadget::graphGadget() const
{
	return parent<GraphGadget>();
}

void AnnotationsGadget::graphGadgetChildAdded( GraphComponent *child )
{
	if( NodeGadget *nodeGadget = runTimeCast<NodeGadget>( child ) )
	{
		m_annotations[nodeGadget] = Annotations();
		m_dirty = true;
	}
}

void AnnotationsGadget::graphGadgetChildRemoved( const GraphComponent *child )
{
	if( const NodeGadget *nodeGadget = runTimeCast<const NodeGadget>( child ) )
	{
		m_annotations.erase( nodeGadget );
		m_dirty = true;
	}
}

void AnnotationsGadget::nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, Gaffer::Node *node )
{
	if( !node )
	{
		// We only expect annotations to be registered
		// as per-instance metadate.
		return;
	}

	if(
		!MetadataAlgo::bookmarkedAffectedByChange( key ) &&
		!MetadataAlgo::numericBookmarkAffectedByChange( key ) &&
		!MetadataAlgo::annotationsAffectedByChange( key )
	)
	{
		return;
	}

	if( auto gadget = graphGadget()->nodeGadget( node ) )
	{
		auto it = m_annotations.find( gadget );
		assert( it != m_annotations.end() );
		it->second.dirty = true;
		m_dirty = true;
		dirty( DirtyType::Render );
	}
}

void AnnotationsGadget::update() const
{
	if( !m_dirty )
	{
		return;
	}

	vector<string> templates;
	MetadataAlgo::annotationTemplates( templates );
	std::sort( templates.begin(), templates.end() );
	const bool untemplatedVisible = StringAlgo::matchMultiple( untemplatedAnnotations, m_visibleAnnotations );

	vector<string> names;
	for( auto &ga : m_annotations )
	{
		const Node *node = ga.first->node();
		Annotations &annotations = ga.second;
		if( !annotations.dirty )
		{
			continue;
		}

		annotations.renderable = false;

		annotations.bookmarked = Gaffer::MetadataAlgo::getBookmarked( node );
		annotations.renderable |= annotations.bookmarked;

		if( int bookmark = MetadataAlgo::numericBookmark( node ) )
		{
			annotations.numericBookmark = std::to_string( bookmark );
			annotations.renderable = true;
		}
		else
		{
			annotations.numericBookmark = InternedString();
		}

		annotations.standardAnnotations.clear();
		names.clear();
		MetadataAlgo::annotations( node, names );
		for( const auto &name : names )
		{
			if( !StringAlgo::matchMultiple( name, m_visibleAnnotations ) )
			{
				const bool templated = binary_search( templates.begin(), templates.end(), name ) || name == "user";
				if( templated || !untemplatedVisible )
				{
					continue;
				}
			}

			annotations.standardAnnotations.push_back(
				MetadataAlgo::getAnnotation( node, name, /* inheritTemplate = */ true )
			);
			// Word wrap. It might be preferable to do this during
			// rendering, but we have no way of querying the extent of
			// `Style::renderWrappedText()`.
			annotations.standardAnnotations.back().textData = new StringData(
				wrap( annotations.standardAnnotations.back().text(), 60 )
			);
		}
		annotations.renderable |= (bool)annotations.standardAnnotations.size();

		annotations.dirty = false;
	}

	m_dirty = false;
}
