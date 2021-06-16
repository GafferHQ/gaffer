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

#include "GafferUI/Gadget.h"
#include "GafferUI/GraphGadget.h"

#include "IECore/StringAlgo.h"

#include "boost/variant.hpp"

#include <functional>

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
/// - noduleLayout:customGadget:<name>:gadgetType, string
/// - noduleLayout:customGadget:<name>:*, as for child plug metadata above
class GAFFERUI_API NoduleLayout : public Gadget
{

	public :

		GAFFER_GRAPHCOMPONENT_DECLARE_TYPE( GafferUI::NoduleLayout, NoduleLayoutTypeId, Gadget );

		NoduleLayout( Gaffer::GraphComponentPtr parent, IECore::InternedString section = IECore::InternedString() );
		~NoduleLayout() override;

		/// \todo These do not need to be virtual, since this is
		/// not intended to be used as a base class.
		virtual Nodule *nodule( const Gaffer::Plug *plug );
		virtual const Nodule *nodule( const Gaffer::Plug *plug ) const;

		Gadget *customGadget( const std::string &name );
		const Gadget *customGadget( const std::string &name ) const;

		typedef std::function<GadgetPtr ( Gaffer::GraphComponentPtr )> CustomGadgetCreator;
		/// Registers a custom gadget type that can be added to the layout using
		/// "noduleLayout:customGadget:*"" metadata entries.
		static void registerCustomGadget( const std::string &gadgetType, CustomGadgetCreator creator );


	protected :

		bool hasLayer( Layer layer ) const override;

	private :

		LinearContainer *noduleContainer();
		const LinearContainer *noduleContainer() const;

		struct TypeAndGadget
		{
			TypeAndGadget() {}
			TypeAndGadget( IECore::InternedString type, GadgetPtr gadget ) : type( type ), gadget( gadget ) {}
			// Nodule type or custom gadget type
			IECore::InternedString type;
			// Nodule or custom gadget
			GadgetPtr gadget;
		};
		// Either a plug or the name of a custom widget
		typedef boost::variant<const Gaffer::Plug *, IECore::InternedString> GadgetKey;
		// Map from plugs and custom gadget names to the gadgets
		// that represent them.
		typedef std::map<GadgetKey, TypeAndGadget> GadgetMap;
		GadgetMap m_gadgets;

		void childAdded( Gaffer::GraphComponent *child );
		void childRemoved( Gaffer::GraphComponent *child );

		void plugMetadataChanged( const Gaffer::Plug *plug, IECore::InternedString key );
		void nodeMetadataChanged( const Gaffer::Node *node, IECore::InternedString key );

		std::vector<GadgetKey> layoutOrder();
		void updateNoduleLayout();
		void updateSpacing();
		void updateDirection();
		void updateOrientation();

		Gaffer::GraphComponentPtr m_parent;
		const IECore::InternedString m_section;

};

IE_CORE_DECLAREPTR( NoduleLayout )

} // namespace GafferUI

#endif // GAFFERUI_NODULELAYOUT_H
