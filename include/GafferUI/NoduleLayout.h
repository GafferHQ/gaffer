//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERUI_NODULELAYOUT_H
#define GAFFERUI_NODULELAYOUT_H

#include "Gaffer/StringAlgo.h"

#include "GafferUI/Gadget.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Plug )
IE_CORE_FORWARDDECLARE( Node )

} // namespace Gaffer

namespace GafferUI
{

IE_CORE_FORWARDDECLARE( LinearContainer )
IE_CORE_FORWARDDECLARE( Nodule )

/// Child plug metadata
/// ===================
///
/// noduleLayout:index, int, controls relative order of nodules
/// noduleLayout:section, string, "left"/"right"/"top"/"bottom"
/// noduleLayout:visible, bool
///
/// Parent metadata
/// ===============
///
/// - noduleLayout:section:<sectionName>:spacing, float
/// - noduleLayout:section:<sectionName>:direction, string, "increasing" or "decreasing"
class NoduleLayout : public Gadget
{

	public :

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferUI::NoduleLayout, NoduleLayoutTypeId, Gadget );

		NoduleLayout( Gaffer::GraphComponentPtr parent, IECore::InternedString section = IECore::InternedString() );
		virtual ~NoduleLayout();

		virtual Nodule *nodule( const Gaffer::Plug *plug );
		virtual const Nodule *nodule( const Gaffer::Plug *plug ) const;

	private :

		LinearContainer *noduleContainer();
		const LinearContainer *noduleContainer() const;

		struct TypeAndNodule
		{
			TypeAndNodule() {}
			TypeAndNodule( IECore::InternedString type, NodulePtr nodule ) : type( type ), nodule( nodule ) {}
			IECore::InternedString type;
			NodulePtr nodule;
		};
		typedef std::map<const Gaffer::Plug *, TypeAndNodule> NoduleMap;
		NoduleMap m_nodules;

		void childAdded( Gaffer::GraphComponent *child );
		void childRemoved( Gaffer::GraphComponent *child );

		void plugMetadataChanged( IECore::TypeId nodeTypeId, const Gaffer::MatchPattern &plugPath, IECore::InternedString key, const Gaffer::Plug *plug );
		void nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, const Gaffer::Node *node );

		void updateNodules( std::vector<Nodule *> &nodules, std::vector<Nodule *> &added, std::vector<NodulePtr> &removed );
		void updateNoduleLayout();
		void updateSpacing();
		void updateDirection();
		void updateOrientation();

		Gaffer::GraphComponentPtr m_parent;
		const IECore::InternedString m_section;

};

IE_CORE_DECLAREPTR( NoduleLayout )

typedef Gaffer::FilteredChildIterator<Gaffer::TypePredicate<NoduleLayout> > NoduleLayoutIterator;
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::TypePredicate<NoduleLayout> > RecursiveNoduleLayoutIterator;

} // namespace GafferUI

#endif // GAFFERUI_NODULELAYOUT_H
