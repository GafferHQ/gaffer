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

#pragma once

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ParallelAlgo.h"

#include "GafferUI/Gadget.h"

#include "IECoreGL/Selector.h"

#include "IECore/StringAlgo.h"

#include <unordered_map>

namespace Gaffer
{

class Plug;
class Node;

} // namespace Gaffer

namespace GafferUI
{

class GraphGadget;
class NodeGadget;
IE_CORE_FORWARDDECLARE( ContextTracker );

class GAFFERUI_API AnnotationsGadget : public Gadget
{

	public :

		~AnnotationsGadget() override;

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::AnnotationsGadget, AnnotationsGadgetTypeId, Gadget );

		/// Special value that may be used with `setVisibleAnnotations()`, to match
		/// all annotations not registered with `MetadataAlgo::registerAnnotationTemplate()`.
		static const std::string untemplatedAnnotations;

		void setVisibleAnnotations( const IECore::StringAlgo::MatchPattern &patterns );
		const IECore::StringAlgo::MatchPattern &getVisibleAnnotations() const;

		/// Returns the text currently being rendered for the specified
		/// annotation. Only really intended for use in the unit tests.
		const std::string &annotationText( const Gaffer::Node *node, IECore::InternedString annotation = "user" ) const;

		bool acceptsParent( const GraphComponent *potentialParent ) const override;

		// Identifies an annotation by the node and it's name.
		using AnnotationIdentifier = std::pair<const Gaffer::Node *, std::string>;
		// Returns the node and annotation name under the specified line.
		std::optional<AnnotationIdentifier> annotationAt( const IECore::LineSegment3f &lineInGadgetSpace ) const;

	protected :

		// Protected constructor and friend status so only GraphGadget can
		// construct us.
		AnnotationsGadget();
		friend class GraphGadget;

		void parentChanging( Gaffer::GraphComponent *newParent ) override;
		void renderLayer( Layer layer, const Style *style, RenderReason reason ) const override;
		unsigned layerMask() const override;
		Imath::Box3f renderBound() const override;

	private :

		struct Annotations;

		// Update process
		// ==============
		//
		// We query annotation metadata and store it ready for rendering in our
		// `m_annotations` data structure. This occurs in synchronous, lazy and
		// asynchronous phases as performance requirements dictate.
		//
		// In the first phase, these two methods ensure that `m_annotations`
		// always has an entry for each NodeGadget being drawn by the
		// GraphGadget. This is done synchronously with the addition and removal
		// of children.
		void graphGadgetChildAdded( GraphComponent *child );
		void graphGadgetChildRemoved( const GraphComponent *child );
		// These accessors can then be used to find the annotations (if any)
		// for a node.
		Annotations *annotations( const Gaffer::Node *node );
		const Annotations *annotations( const Gaffer::Node *node ) const;
		// We then use `nodeMetadataChanged()` to dirty individual annotations
		// when the metadata has changed. We don't query the metadata at this
		// point, as it's fairly typical to receive many metadata edits at once
		// and we want to batch the updates. We might not even be visible when
		// the edits are made.
		void nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, Gaffer::Node *node );
		// We lazily call `update()` from `renderLayer()` to query all dirty
		// metadata just in time for rendering. Such update are fairly
		// infrequent because annotations are edited infrequently.
		void update();
		// Some annotations use `{}` syntax to substitute in the values of
		// plugs. For these we use `plugDirtied()` to check if the substitutions
		// are affected and dirty them when necessary. Plugs are dirtied
		// frequently and many don't affect the substitutions at all, so this is
		// performed at a finer level of granularity than `update()`.
		void plugDirtied( const Gaffer::Plug *plug, Annotations *annotations );
		// If the substitutions are from computed plugs, then we also need to
		// update when the context changes.
		void contextTrackerChanged();
		// Some plug substitutions may depend on computes, in which case we must
		// perform the substitutions in a BackgroundTask to avoid blocking the
		// UI. This function schedules such a task, or if the values are not
		// computes, does the substitutions directly on the UI thread. This is
		// done on a per-node basis, so that slow updates for one node do not
		// prevent other nodes updating rapidly.
		void schedulePlugValueSubstitutions( const Gaffer::Node *node, Annotations *annotations );
		// These two functions do the actual work of calculating and applying
		// substitutions.
		std::unordered_map<IECore::InternedString, std::string> substitutedRenderText( const Gaffer::Node *node, const Annotations &annotations );
		void applySubstitutedRenderText( const std::unordered_map<IECore::InternedString, std::string> &renderText, Annotations &annotations );
		// When we are hidden, we want to cancel all background tasks.
		void visibilityChanged();

		// Map associating an `IECoreGL::Selector::IDRender` entry with a `AnnotationIndex`.
		using AnnotationBufferMap = std::unordered_map<unsigned int, AnnotationIdentifier>;

		// If given an `AnnotationBufferMap` and `Selector`, draws all annotations
		// with a unique `IDRender` index per annotation and fills `selectionIds`.
		// If they are not given, no modification to the selection buffer IDs are
		// made (all annotations have the ID for this widget).
		void renderAnnotations( const Style *style, AnnotationBufferMap *selectionIds = nullptr ) const;

		struct StandardAnnotation : public Gaffer::MetadataAlgo::Annotation
		{
			StandardAnnotation( const Gaffer::MetadataAlgo::Annotation &a, IECore::InternedString name ) : Annotation( a ), name( name ) {}
			IECore::InternedString name;
			std::string renderText;
		};

		struct Annotations
		{
			bool dirty = true;
			std::vector<StandardAnnotation> standardAnnotations;
			bool bookmarked = false;
			IECore::InternedString numericBookmark;
			bool renderable = false;
			bool hasPlugValueSubstitutions = false;
			bool hasContextSensitiveSubstitutions = false;
			Gaffer::Signals::ScopedConnection plugDirtiedConnection;
			std::unique_ptr<Gaffer::BackgroundTask> substitutionsTask;
		};

		Gaffer::Signals::ScopedConnection m_graphGadgetChildAddedConnection;
		Gaffer::Signals::ScopedConnection m_graphGadgetChildRemovedConnection;
		ContextTrackerPtr m_contextTracker;
		Gaffer::Signals::ScopedConnection m_contextTrackerChangedConnection;

		using AnnotationsContainer = std::unordered_map<const NodeGadget *, Annotations>;
		AnnotationsContainer m_annotations;
		bool m_dirty;

		IECore::StringAlgo::MatchPattern m_visibleAnnotations;

};

} // namespace GafferUI
