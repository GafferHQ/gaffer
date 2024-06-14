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

#include "GafferUI/Gadget.h"

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

		void graphGadgetChildAdded( GraphComponent *child );
		void graphGadgetChildRemoved( const GraphComponent *child );
		Annotations *annotations( const Gaffer::Node *node );
		const Annotations *annotations( const Gaffer::Node *node ) const;
		void nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, Gaffer::Node *node );
		void update() const;

		struct StandardAnnotation : public Gaffer::MetadataAlgo::Annotation
		{
			StandardAnnotation( const Gaffer::MetadataAlgo::Annotation &a, IECore::InternedString name ) : Annotation( a ), name( name ) {}
			IECore::InternedString name;
		};

		struct Annotations
		{
			bool dirty = true;
			std::vector<StandardAnnotation> standardAnnotations;
			bool bookmarked = false;
			IECore::InternedString numericBookmark;
			bool renderable = false;
		};

		Gaffer::Signals::ScopedConnection m_graphGadgetChildAddedConnection;
		Gaffer::Signals::ScopedConnection m_graphGadgetChildRemovedConnection;

		using AnnotationsContainer = std::unordered_map<const NodeGadget *, Annotations>;
		mutable AnnotationsContainer m_annotations;
		mutable bool m_dirty;

		IECore::StringAlgo::MatchPattern m_visibleAnnotations;

};

} // namespace GafferUI
