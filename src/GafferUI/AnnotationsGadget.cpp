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

#include "GafferSceneUI/SceneGadget.h"

#include "GafferUI/GraphGadget.h"
#include "GafferUI/ImageGadget.h"
#include "GafferUI/NodeGadget.h"
#include "GafferUI/StandardNodeGadget.h"
#include "GafferUI/Style.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/Process.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"

#include "IECoreGL/Camera.h"
#include "IECoreGL/Selector.h"
#include "IECoreGL/ToGLCameraConverter.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind/bind.hpp"
#include "boost/bind/placeholders.hpp"

#include <regex>

using namespace GafferUI;
using namespace Gaffer;
using namespace IECore;
using namespace Imath;
using namespace boost::placeholders;
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


const IECoreGL::Texture *bookmarkTexture()
{
	static IECoreGL::ConstTexturePtr bookmarkTexture = ImageGadget::loadTexture( "bookmarkStar2.png" );
	return bookmarkTexture.get();
}

const IECoreGL::Texture *numericBookmarkTexture()
{
	static IECoreGL::ConstTexturePtr numericBookmarkTexture = ImageGadget::loadTexture( "bookmarkStar.png" );
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

const float g_offset = 0.5;
const string g_emptyString;
const int g_maxLineLength = 60;

template<typename PlugType>
string formatVectorDataPlugValue( const PlugType *plug )
{
	auto value = plug->getValue();

	string result;
	for( const auto &v : value->readable() )
	{
		if( !result.empty() )
		{
			result += ", ";
		}
		result += fmt::format( "{}", v );
	}

	return result;
}

/// \todo Should this be made public in PlugAlgo, and how does it relate
/// to `SpreadsheetUI.formatValue()`? It would be really nice if this could
/// support preset names too, but those are only available in Python at
/// present.
std::string formatPlugValue( const ValuePlug *plug )
{
	switch( (int)plug->typeId() )
	{
		case BoolPlugTypeId :
			return static_cast<const BoolPlug *>( plug )->getValue() ? "On" : "Off";
		case IntPlugTypeId :
			return std::to_string( static_cast<const IntPlug *>( plug )->getValue() );
		case FloatPlugTypeId :
			return fmt::format( "{}", static_cast<const FloatPlug *>( plug )->getValue() );
		case StringPlugTypeId :
			return static_cast<const StringPlug *>( plug )->getValue();
		case IntVectorDataPlugTypeId :
			return formatVectorDataPlugValue( static_cast<const IntVectorDataPlug *>( plug ) );
		case FloatVectorDataPlugTypeId :
			return formatVectorDataPlugValue( static_cast<const FloatVectorDataPlug *>( plug ) );
		case StringVectorDataPlugTypeId :
			return formatVectorDataPlugValue( static_cast<const StringVectorDataPlug *>( plug ) );
		default : {
			string result;
			for( const auto &child : ValuePlug::Range( *plug ) )
			{
				if( !result.empty() )
				{
					result += ", ";
				}
				result += formatPlugValue( child.get() );
			}
			return result;
		}
	}
}

const std::regex g_plugValueSubstitutionRegex( R"(\{([^}]*)\})" );

bool hasPlugValueSubstitutions( const string &text )
{
	return std::regex_search( text, g_plugValueSubstitutionRegex );
}

bool affectsPlugValueSubstitutions( const Plug *plug, const string &text )
{
	const string name = plug->relativeName( plug->node() );
	sregex_iterator matchIt( text.begin(), text.end(), g_plugValueSubstitutionRegex );
	sregex_iterator matchEnd;
	for( ; matchIt != matchEnd; ++matchIt )
	{
		if( matchIt->str( 1 ) == name )
		{
			return true;
		}
	}

	return false;
}

const Plug *plugValueSubstitutionsBackgroundTaskSubject( const std::string &text, const Node *node )
{
	sregex_iterator matchIt( text.begin(), text.end(), g_plugValueSubstitutionRegex );
	sregex_iterator matchEnd;
	for( ; matchIt != matchEnd; ++matchIt )
	{
		const string plugPath = matchIt->str( 1 );
		if( auto plug = node->descendant<ValuePlug>( plugPath ) )
		{
			if( PlugAlgo::dependsOnCompute( plug ) )
			{
				return plug;
			}
		}
	}
	return nullptr;
}

string substitutePlugValues( const string &text, const Node *node )
{
	sregex_iterator matchIt( text.begin(), text.end(), g_plugValueSubstitutionRegex );
	sregex_iterator matchEnd;

	if( matchIt == matchEnd )
	{
		// No matches
		return text;
	}

	string result;
	ssub_match suffix;
	for( ; matchIt != matchEnd; ++matchIt )
	{
		// Add any unmatched text from before this match.
		result.insert( result.end(), matchIt->prefix().first, matchIt->prefix().second );

		const string plugPath = matchIt->str( 1 );
		if( !node )
		{
			result += "---";
		}
		else if( auto plug = node->descendant<ValuePlug>( plugPath ) )
		{
			result += formatPlugValue( plug );
		}

		suffix = matchIt->suffix();
	}
	// The suffix for one match is the same as the prefix for the next
	// match. So we only need to add the suffix from the last match.
	result.insert( result.end(), suffix.first, suffix.second );
	return result;
}

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
	visibilityChangedSignal().connect(
		boost::bind( &AnnotationsGadget::visibilityChanged, this )
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

const std::string &AnnotationsGadget::annotationText( const Gaffer::Node *node, IECore::InternedString annotation ) const
{
	const_cast<AnnotationsGadget *>( this )->update();
	if( const Annotations *nodeAnnotations = annotations( node ) )
	{
		for( const auto &a : nodeAnnotations->standardAnnotations )
		{
			if( a.name == annotation )
			{
				return a.renderText;
			}
		}
	}

	return g_emptyString;
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

	renderAnnotations( style );
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

AnnotationsGadget::Annotations *AnnotationsGadget::annotations( const Gaffer::Node *node )
{
	return const_cast<Annotations *>( const_cast<const AnnotationsGadget *>( this )->annotations( node ) );
}

const AnnotationsGadget::Annotations *AnnotationsGadget::annotations( const Gaffer::Node *node ) const
{
	const GraphGadget *graphGadget = parent<GraphGadget>();
	if( !graphGadget )
	{
		return nullptr;
	}

	const NodeGadget *nodeGadget = graphGadget->nodeGadget( node );
	if( !nodeGadget )
	{
		return nullptr;
	}

	auto it = m_annotations.find( nodeGadget );
	if( it == m_annotations.end() )
	{
		return nullptr;
	}

	return &it->second;
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

	if( Annotations *a = annotations( node ) )
	{
		a->dirty = true;
		m_dirty = true;
		dirty( DirtyType::Render );
	}
}

void AnnotationsGadget::update()
{
	if( !m_dirty || !parent() )
	{
		return;
	}

	m_contextTracker = ContextTracker::acquireForFocus( parent<GraphGadget>()->getRoot()->scriptNode() );

	vector<string> templates;
	MetadataAlgo::annotationTemplates( templates );
	std::sort( templates.begin(), templates.end() );
	const bool untemplatedVisible = StringAlgo::matchMultiple( untemplatedAnnotations, m_visibleAnnotations );

	bool dependsOnContext = false;

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

		annotations.substitutionsTask.reset(); // Stop task before clearing the data it accesses.
		annotations.hasPlugValueSubstitutions = false;
		annotations.standardAnnotations.clear();

		vector<string> names = MetadataAlgo::annotations( node );
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

			StandardAnnotation a( MetadataAlgo::getAnnotation( node, name, /* inheritTemplate = */ true ), name );
			if( !hasPlugValueSubstitutions( a.text() ) )
			{
				a.renderText = wrap( a.text(), g_maxLineLength );
			}
			else
			{
				// We'll update `renderText` later in `schedulePlugValueSubstitutions()`.
				annotations.hasPlugValueSubstitutions = true;
				if( plugValueSubstitutionsBackgroundTaskSubject( a.text(), node ) )
				{
					annotations.hasContextSensitiveSubstitutions = true;
					dependsOnContext = true;
				}
			}
			annotations.standardAnnotations.push_back( a );
		}
		annotations.renderable |= (bool)annotations.standardAnnotations.size();

		if( annotations.hasPlugValueSubstitutions )
		{
			annotations.plugDirtiedConnection = const_cast<Node *>( node )->plugDirtiedSignal().connect(
				boost::bind( &AnnotationsGadget::plugDirtied, this, ::_1, &annotations )
			);
			schedulePlugValueSubstitutions( node, &annotations );
		}
		else
		{
			annotations.plugDirtiedConnection.disconnect();
		}

		annotations.dirty = false;
	}

	if( dependsOnContext )
	{
		m_contextTrackerChangedConnection = m_contextTracker->changedSignal().connect(
			boost::bind( &AnnotationsGadget::contextTrackerChanged, this )
		);
	}
	else
	{
		m_contextTrackerChangedConnection.disconnect();
	}

	m_dirty = false;
}

void AnnotationsGadget::plugDirtied( const Gaffer::Plug *plug, Annotations *annotations )
{
	assert( annotations->hasPlugValueSubstitutions );
	for( const auto &annotation : annotations->standardAnnotations )
	{
		if( affectsPlugValueSubstitutions( plug, annotation.text() ) )
		{
			annotations->dirty = true;
			m_dirty = true;
			dirty( DirtyType::Render );
			break;
		}
	}
}

void AnnotationsGadget::contextTrackerChanged()
{
	bool dirtied = false;
	for( auto &[nodeGadget, annotation] : m_annotations )
	{
		if( annotation.hasContextSensitiveSubstitutions )
		{
			annotation.dirty = true;
			dirtied = true;
		}
	}

	if( dirtied )
	{
		m_dirty = true;
		dirty( DirtyType::Render );
	}
}

void AnnotationsGadget::schedulePlugValueSubstitutions( const Gaffer::Node *node, Annotations *annotations )
{
	const Plug *backgroundTaskSubject = nullptr;
	for( const auto &annotation : annotations->standardAnnotations )
	{
		backgroundTaskSubject = plugValueSubstitutionsBackgroundTaskSubject( annotation.text(), node );
		if( backgroundTaskSubject )
		{
			break;
		}
	}

	if( !backgroundTaskSubject )
	{
		applySubstitutedRenderText( substitutedRenderText( node, *annotations ), *annotations );
		return;
	}

	// At least one annotation depends on a computed plug value. Evaluate all
	// substitutions in a background task, so that we don't lock up the UI if
	// the computation is slow. Before we launch background task, substitute
	// in `---` placeholders to give folks a hint as to what is happening.

	applySubstitutedRenderText( substitutedRenderText( /* node = */ nullptr, *annotations ), *annotations );

	Context::Scope scopedContext( m_contextTracker->context( node ).get() );

	annotations->substitutionsTask = ParallelAlgo::callOnBackgroundThread(

		// `this`, `node` and `annotations` are safe to capture because they are
		// guaranteed to outlive the BackgroundTask, due to `annotations` owning
		// the task, and waiting for it in its destructor.
		backgroundTaskSubject, [this, node, annotations] () {

			// Get new render text for each annotation. Note : We can not access
			// the Metatada API from a BackgroundTask, as it doesn't participate
			// in cancellation.

			bool cancelled = false;
			std::unordered_map<IECore::InternedString, std::string> renderText;
			try
			{
				renderText = substitutedRenderText( node, *annotations );
			}
			catch( const IECore::Cancelled & )
			{
				cancelled = true;
			}

			if( !cancelled && renderText.empty() )
			{
				return;
			}

			// Schedule an update on the UI thread.
			//
			// Note : As soon as the background task returns,  we have lost the
			// guarantee on the lifetime of `this`, `node` and `annotations` -
			// any could be destroyed before we get on to the UI thread. So
			// maintain ownership and look up `annotations` again.

			// Alias for `this` to work around MSVC bug that prevents capturing
			// `this` again in a nested lambda.
			AnnotationsGadget *that = this;

			ParallelAlgo::callOnUIThread(
				[gadget = Ptr( that ), node = ConstNodePtr( node ), renderText = std::move( renderText ), cancelled] {

					Annotations *annotations = gadget->annotations( node.get() );
					if( !annotations )
					{
						return;
					}

					gadget->applySubstitutedRenderText( renderText, *annotations );
					if( cancelled )
					{
						// Dirty, so that we relaunch background task on next redraw.
						annotations->dirty = true;
						gadget->m_dirty = true;
					}
					gadget->dirty( DirtyType::Render );
				}
			);

		}
	);
}

std::unordered_map<IECore::InternedString, std::string> AnnotationsGadget::substitutedRenderText( const Gaffer::Node *node, const Annotations &annotations )
{
	std::unordered_map<InternedString, string> result;

	for( auto &annotation : annotations.standardAnnotations )
	{
		try
		{
			const string newRenderText = wrap( substitutePlugValues( annotation.text(), node ), g_maxLineLength );
			if( newRenderText != annotation.renderText )
			{
				result[annotation.name] = newRenderText;
			}
		}
		catch( const ProcessException & )
		{
			// Computation error. Ignore, so we keep original `---` placeholder
			// text.
		}
	}

	return result;
}

void AnnotationsGadget::applySubstitutedRenderText( const std::unordered_map<IECore::InternedString, std::string> &renderText, Annotations &annotations )
{
	for( auto &annotation : annotations.standardAnnotations )
	{
		auto it = renderText.find( annotation.name );
		if( it != renderText.end() )
		{
			annotation.renderText = it->second;
		}
	}
}

void AnnotationsGadget::visibilityChanged()
{
	if( !visible() )
	{
		for( auto &[nodeGadget, annotation] : m_annotations )
		{
			// Cancel background task. If not yet complete, it will catch this
			// cancellation and dirty the annotation so that a new update starts
			// when we are next visible.
			annotation.substitutionsTask.reset();
		}
	}
}

void AnnotationsGadget::renderAnnotations( const Style *style, AnnotationBufferMap *selectionIds ) const
{
	const_cast<AnnotationsGadget *>( this )->update();

	IECoreGL::Selector *selector = IECoreGL::Selector::currentSelector();

	for( const auto &ga : m_annotations )
	{
		const Annotations &annotations = ga.second;
		assert( !annotations.dirty );
		if( !annotations.renderable )
		{
			continue;
		}

		const Box2f b = nodeFrame( ga.first );

		V2f bookmarkIconPos( b.min.x, b.max.y );
		V2f annotationOrigin( b.max.x + g_offset, b.max.y );
		if( ga.first->node() == ga.first->node()->ancestor<ScriptNode>()->getFocus() )
		{
			const StandardNodeGadget *standardNodeGadget = runTimeCast<const StandardNodeGadget>( ga.first );
			if( standardNodeGadget )
			{
				float fbw = standardNodeGadget->focusBorderWidth();
				bookmarkIconPos += V2f( -fbw, fbw );
				annotationOrigin += V2f( fbw, 0.0f );
			}
		}

		if( !selectionIds )
		{
			if( annotations.bookmarked )
			{
				style->renderImage( Box2f( bookmarkIconPos - V2f( 1.0 ), bookmarkIconPos + V2f( 1.0 ) ), bookmarkTexture() );
			}

			if( annotations.numericBookmark.string().size() )
			{
				if( !annotations.bookmarked )
				{
					style->renderImage( Box2f( bookmarkIconPos - V2f( 1.0 ), bookmarkIconPos + V2f( 1.0 ) ), numericBookmarkTexture() );
				}

				const Box3f textBounds = style->textBound( Style::LabelText, annotations.numericBookmark.string() );

				const Imath::Color4f textColor( 0.8f );
				glPushMatrix();
					IECoreGL::glTranslate( V2f( bookmarkIconPos.x - 0.9 - textBounds.size().x, bookmarkIconPos.y - textBounds.size().y * 0.5 - 0.2 ) );
					style->renderText( Style::LabelText, annotations.numericBookmark.string(), Style::NormalState, &textColor );
				glPopMatrix();
			}
		}

		for( const auto &a : annotations.standardAnnotations )
		{
			if( selectionIds && selector )
			{
				unsigned int id = selector->loadName();
				(*selectionIds)[id] = AnnotationIdentifier( ga.first->node(), a.name );
			}

			annotationOrigin = style->renderAnnotation( annotationOrigin, a.renderText, Style::NormalState, a.colorData ? &a.color() : nullptr );
		}
	}
}

std::optional<AnnotationsGadget::AnnotationIdentifier> AnnotationsGadget::annotationAt( const LineSegment3f &lineInGadgetSpace ) const
{
	std::vector<IECoreGL::HitRecord> selection;
	AnnotationBufferMap annotationBuffer;
	{
		ViewportGadget::SelectionScope selectionScope( lineInGadgetSpace, this, selection, IECoreGL::Selector::Mode::IDRender );

		const Style *currentStyle = style();
		currentStyle->bind();

		// See `ViewportGadget::renderInternal()` for reasoning behind disabling blending.
		glDisable( GL_BLEND );

		renderAnnotations( currentStyle, &annotationBuffer );
	}

	if( selection.empty() )
	{
		return std::optional<AnnotationIdentifier>( std::nullopt );
	}

	auto result = annotationBuffer.find( selection[0].name );
	if( result == annotationBuffer.end() )
	{
		return std::optional<AnnotationIdentifier>( std::nullopt );
	}
	return result->second;
}
