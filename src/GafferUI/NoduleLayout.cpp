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

#include "boost/bind.hpp"
#include "boost/regex.hpp"
#include "boost/algorithm/string/predicate.hpp"
#include "boost/container/flat_set.hpp"

#include "IECore/SimpleTypedData.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/Plug.h"
#include "Gaffer/Node.h"

#include "GafferUI/Nodule.h"
#include "GafferUI/LinearContainer.h"
#include "GafferUI/CompoundNodule.h"
#include "GafferUI/NoduleLayout.h"
#include "GafferUI/NodeGadget.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferUI;

//////////////////////////////////////////////////////////////////////////
// Utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

// Section names

IECore::InternedString g_left( "left" );
IECore::InternedString g_right( "right" );
IECore::InternedString g_bottom( "bottom" );
IECore::InternedString g_top( "top" );

// Metadata keys

IECore::InternedString g_indexKey( "noduleLayout:index" );
IECore::InternedString g_sectionKey( "noduleLayout:section" );
IECore::InternedString g_visibleKey( "noduleLayout:visible" );
IECore::InternedString g_spacingKey( "noduleLayout:spacing" );
IECore::InternedString g_directionKey( "noduleLayout:direction" );
IECore::InternedString g_noduleTypeKey( "nodule:type" );

// Deprecated metadata keys
/// \todo Remove support for these

IECore::InternedString g_horizontalNoduleSpacingKey( "nodeGadget:horizontalNoduleSpacing"  );
IECore::InternedString g_verticalNoduleSpacingKey( "nodeGadget:verticalNoduleSpacing"  );
IECore::InternedString g_nodulePositionKey( "nodeGadget:nodulePosition" );
IECore::InternedString g_noduleIndexKey( "nodeGadget:noduleIndex" );

IECore::InternedString g_compoundNoduleSpacingKey( "compoundNodule:spacing"  );
IECore::InternedString g_compoundNoduleOrientationKey( "compoundNodule:orientation"  );
IECore::InternedString g_compoundNoduleDirectionKey( "compoundNodule:direction"  );

// Custom gadget factory

typedef map<string, NoduleLayout::CustomGadgetCreator> CustomGadgetCreatorMap;
CustomGadgetCreatorMap &customGadgetCreators()
{
	static CustomGadgetCreatorMap m;
	return m;
}

GadgetPtr createCustomGadget( const InternedString &gadgetType, GraphComponentPtr parent )
{
	const CustomGadgetCreatorMap &m = customGadgetCreators();
	const CustomGadgetCreatorMap::const_iterator it = m.find( gadgetType );
	if( it == m.end() )
	{
		return NULL;
	}
	return it->second( parent );
}

// Custom gadget metadata accessors. These affect the layout of custom gadgets

int index( const GraphComponent *parent, const InternedString &gadgetName, int defaultValue )
{
	ConstIntDataPtr i = Metadata::value<IntData>( parent, "noduleLayout:customGadget:" + gadgetName.string() + ":index" );
	return i ? i->readable() : defaultValue;
}

std::string section( const GraphComponent *parent, const InternedString &gadgetName )
{
	ConstStringDataPtr s = Metadata::value<StringData>( parent, "noduleLayout:customGadget:" + gadgetName.string() + ":section" );
	return s ? s->readable() : "top";
}

bool visible( const GraphComponent *parent, const InternedString &gadgetName, IECore::InternedString section )
{
	if( section != InternedString() && ::section( parent, gadgetName ) != section.string() )
	{
		return false;
	}

	if( ConstBoolDataPtr b = Metadata::value<BoolData>( parent, "noduleLayout:customGadget:" + gadgetName.string() + ":visible" ) )
	{
		return b->readable();
	}

	return true;
}

// Plug metadata accessors. These affect the layout of individual nodules.

typedef boost::variant<const Gaffer::Plug *, IECore::InternedString> GadgetKey;

int index( const Plug *plug, int defaultValue )
{
	ConstIntDataPtr i = Metadata::value<IntData>( plug, g_indexKey );
	if( !i )
	{
		i = Metadata::value<IntData>( plug, g_noduleIndexKey );
	}
	return i ? i->readable() : defaultValue;
}

std::string section( const Plug *plug )
{
	ConstStringDataPtr s = Metadata::value<StringData>( plug, g_sectionKey );
	if( !s )
	{
		s = Metadata::value<StringData>( plug, g_nodulePositionKey );
	}

	if( s )
	{
		return s->readable();
	}
	return plug->direction() == Plug::In ? "top" : "bottom";
}

bool visible( const Plug *plug, IECore::InternedString section )
{
	if( section != InternedString() && ::section( plug ) != section.string() )
	{
		return false;
	}

	if( ConstBoolDataPtr b = Metadata::value<BoolData>( plug, g_visibleKey ) )
	{
		return b->readable();
	}

	return true;
}

// Metadata accessors common to custom gadgets and nodules

InternedString gadgetType( const GraphComponent *parent, const GadgetKey &gadgetKey )
{
	if( gadgetKey.which() == 0 )
	{
		const Plug *plug = boost::get<const Plug *>( gadgetKey );
		ConstStringDataPtr d = Metadata::value<IECore::StringData>( plug, g_noduleTypeKey );
		return d ? d->readable() : "GafferUI::StandardNodule";
	}
	else
	{
		const InternedString &name = boost::get<InternedString>( gadgetKey );
		ConstStringDataPtr d = Metadata::value<StringData>( parent, "noduleLayout:customGadget:" + name.string() + ":gadgetType" );
		return d ? d->readable() : "";
	}
}

// Parent metadata accessors. These affect the properties of the layout itself.

float spacing( const Gaffer::GraphComponent *parent, IECore::InternedString section )
{
	ConstFloatDataPtr f;
	if( section != "" )
	{
		f = Metadata::value<FloatData>( parent, "noduleLayout:section:" + section.string() + ":spacing" );
	}
	else
	{
		f = Metadata::value<FloatData>( parent, g_spacingKey );
	}

	if( !f )
	{
		// Backwards compatibility with old StandardNodeGadget and
		// CompoundNodule metadata.
		if( section == g_left || section == g_right )
		{
			f = Metadata::value<FloatData>( parent, g_verticalNoduleSpacingKey );
		}
		else if( section == g_top || section == g_bottom )
		{
			f = Metadata::value<FloatData>( parent, g_horizontalNoduleSpacingKey );
		}
		else
		{
			f = Metadata::value<FloatData>( parent, g_compoundNoduleSpacingKey );
		}
	}

	if( f )
	{
		return f->readable();
	}
	else if( section == g_left || section == g_right )
	{
		return 0.2f;
	}
	else if( section == g_top || section == g_bottom )
	{
		return 2.0f;
	}
	else
	{
		return 0.0f;
	}
}

bool affectsSpacing( IECore::InternedString key, IECore::InternedString section )
{
	if( section != "" )
	{
		if( key == "noduleLayout:section:" + section.string() + ":spacing" )
		{
			return true;
		}
	}
	else
	{
		if( key == g_spacingKey )
		{
			return true;
		}
	}

	if( section == g_left || section == g_right )
	{
		return key == g_verticalNoduleSpacingKey;
	}
	else if( section == g_top || section == g_bottom )
	{
		return key == g_horizontalNoduleSpacingKey;
	}
	else
	{
		return key == g_compoundNoduleSpacingKey;
	}
}

LinearContainer::Orientation orientation( const Gaffer::GraphComponent *parent, IECore::InternedString section )
{
	if( section == "" )
	{
		if( const Plug *parentPlug = runTimeCast<const Plug>( parent ) )
		{
			if( ConstStringDataPtr s = Metadata::value<StringData>( parentPlug, g_compoundNoduleOrientationKey ) )
			{
				// Backwards compatibility with old CompoundNodule metadata.
				return s->readable() == "x" ? LinearContainer::X : LinearContainer::Y;
			}
			section = ::section( parentPlug );
		}
	}

	if( section == g_left || section == g_right )
	{
		return LinearContainer::Y;
	}
	else
	{
		return LinearContainer::X;
	}
}

bool affectsOrientation( IECore::InternedString key, IECore::InternedString section )
{
	return section == "" && key == g_compoundNoduleOrientationKey;
}

LinearContainer::Direction direction( const Gaffer::GraphComponent *parent, IECore::InternedString section )
{
	ConstStringDataPtr d;
	if( section != "" )
	{
		d = Metadata::value<StringData>( parent, "noduleLayout:section:" + section.string() + ":direction" );
	}
	else
	{
		d = Metadata::value<StringData>( parent, g_directionKey );
	}

	if( !d && section == "" )
	{
		// Backwards compatibility with old
		// CompoundNodule metadata.
		d = Metadata::value<StringData>( parent, g_compoundNoduleSpacingKey );
	}

	if( d )
	{
		return d->readable() == "increasing" ? LinearContainer::Increasing : LinearContainer::Decreasing;
	}

	if( section == "" )
	{
		if( const Plug *parentPlug = runTimeCast<const Plug>( parent ) )
		{
			section = ::section( parentPlug );
		}
	}

	if( section == g_left || section == g_right )
	{
		return LinearContainer::Decreasing;
	}
	else
	{
		return LinearContainer::Increasing;
	}
}

bool affectsDirection( IECore::InternedString key, IECore::InternedString section )
{
	if( key == "noduleLayout:section:" + section.string() + ":direction" )
	{
		return true;
	}
	if( section == "" && key == g_compoundNoduleDirectionKey )
	{
		return true;
	}
	return false;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// NoduleLayout implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( NoduleLayout );

NoduleLayout::NoduleLayout( Gaffer::GraphComponentPtr parent, IECore::InternedString section )
	:	Gadget(), m_parent( parent ), m_section( section )
{
	LinearContainerPtr noduleContainer = new LinearContainer(
		"__noduleContainer",
		orientation( m_parent.get(), m_section ),
		LinearContainer::Centre,
		spacing( m_parent.get(), m_section ),
		direction( m_parent.get(), m_section )
	);

	addChild( noduleContainer );

	m_parent->childAddedSignal().connect( boost::bind( &NoduleLayout::childAdded, this, ::_2 ) );
	m_parent->childRemovedSignal().connect( boost::bind( &NoduleLayout::childRemoved, this, ::_2 ) );

	Metadata::plugValueChangedSignal().connect( boost::bind( &NoduleLayout::plugMetadataChanged, this, ::_1, ::_2, ::_3, ::_4 ) );
	Metadata::nodeValueChangedSignal().connect( boost::bind( &NoduleLayout::nodeMetadataChanged, this, ::_1, ::_2, ::_3 ) );

	updateLayout();
}

NoduleLayout::~NoduleLayout()
{
}

Nodule *NoduleLayout::nodule( const Gaffer::Plug *plug )
{
	const GraphComponent *plugParent = plug->parent<GraphComponent>();
	if( !plugParent )
	{
		return NULL;
	}

	if( plugParent == m_parent.get() )
	{
		GadgetMap::iterator it = m_gadgets.find( plug );
		if( it != m_gadgets.end() )
		{
			// Cast is safe because we only ever store nodules
			// for plug keys.
			return static_cast<Nodule *>( it->second.gadget.get() );
		}
		return NULL;
	}
	else if( const Plug *parentPlug = IECore::runTimeCast<const Plug>( plugParent ) )
	{
		CompoundNodule *compoundNodule = IECore::runTimeCast<CompoundNodule>( nodule( parentPlug ) );
		if( compoundNodule )
		{
			return compoundNodule->nodule( plug );
		}
	}
	return NULL;
}

const Nodule *NoduleLayout::nodule( const Gaffer::Plug *plug ) const
{
	// naughty cast is better than repeating the above logic.
	return const_cast<NoduleLayout *>( this )->nodule( plug );
}

Gadget *NoduleLayout::customGadget( const std::string &name )
{
	GadgetMap::iterator it = m_gadgets.find( name );
	if( it != m_gadgets.end() )
	{
		return it->second.gadget.get();
	}
	return NULL;
}

const Gadget *NoduleLayout::customGadget( const std::string &name ) const
{
	// naughty cast is better than repeating the above logic.
	return const_cast<NoduleLayout *>( this )->customGadget( name );
}

void NoduleLayout::registerCustomGadget( const std::string &gadgetType, CustomGadgetCreator creator )
{
	customGadgetCreators()[gadgetType] = creator;
}

LinearContainer *NoduleLayout::noduleContainer()
{
	return getChild<LinearContainer>( 0 );
}

const LinearContainer *NoduleLayout::noduleContainer() const
{
	return getChild<LinearContainer>( 0 );
}

void NoduleLayout::childAdded( Gaffer::GraphComponent *child )
{
	if( IECore::runTimeCast<Gaffer::Plug>( child ) )
	{
		updateLayout();
	}
}

void NoduleLayout::childRemoved( Gaffer::GraphComponent *child )
{
	if( IECore::runTimeCast<Gaffer::Plug>( child ) )
	{
		updateLayout();
	}
}

void NoduleLayout::plugMetadataChanged( IECore::TypeId nodeTypeId, const Gaffer::MatchPattern &plugPath, IECore::InternedString key, const Gaffer::Plug *plug )
{
	if( childAffectedByChange( m_parent.get(), nodeTypeId, plugPath, plug ) )
	{
		if(
			key == g_sectionKey || key == g_indexKey || key == g_visibleKey ||
			key == g_noduleTypeKey ||
			key == g_nodulePositionKey || key == g_noduleIndexKey
		)
		{
			updateLayout();
		}
	}

	if( const Plug *typedParent = runTimeCast<const Plug>( m_parent.get() ) )
	{
		if( affectedByChange( typedParent, nodeTypeId, plugPath, plug ) )
		{
			if( affectsSpacing( key, m_section ) )
			{
				updateSpacing();
			}
			if( affectsDirection( key, m_section ) )
			{
				updateDirection();
			}
			if( affectsOrientation( key, m_section ) )
			{
				updateOrientation();
			}
			if( boost::starts_with( key.string(), "noduleLayout:customGadget" ) )
			{
				updateLayout();
			}
		}
	}
}

void NoduleLayout::nodeMetadataChanged( IECore::TypeId nodeTypeId, IECore::InternedString key, const Gaffer::Node *node )
{
	const Node *typedParent = runTimeCast<const Node>( m_parent.get() );
	if( !typedParent || !affectedByChange( typedParent, nodeTypeId, node ) )
	{
		return;
	}

	if( affectsSpacing( key, m_section ) )
	{
		updateSpacing();
	}
	if( affectsDirection( key, m_section ) )
	{
		updateDirection();
	}
	if( affectsOrientation( key, m_section ) )
	{
		updateOrientation();
	}
	if( boost::starts_with( key.string(), "noduleLayout:customGadget" ) )
	{
		updateLayout();
	}
}

std::vector<NoduleLayout::GadgetKey> NoduleLayout::layoutOrder()
{
	typedef pair<int, GadgetKey> SortItem;
	vector<SortItem> toSort;

	// Add any plugs which should be visible

	for( PlugIterator plugIt( m_parent.get() ); !plugIt.done(); ++plugIt )
	{
		Plug *plug = plugIt->get();
		if( boost::starts_with( plug->getName().string(), "__" ) )
		{
			continue;
		}
		if( !::visible( plug, m_section ) )
		{
			continue;
		}

		toSort.push_back( SortItem( index( plug, toSort.size() ), plug ) );
	}

	// Then any custom gadgets specified by the metadata

	vector<InternedString> metadata;
	Metadata::registeredValues( m_parent.get(), metadata );
	boost::regex customGadgetRegex( "noduleLayout:customGadget:(.+):gadgetType" );
	for( vector<InternedString>::const_iterator it = metadata.begin(), eIt = metadata.end(); it != eIt; ++it )
	{
		boost::cmatch match;
		if( !boost::regex_match( it->c_str(), match, customGadgetRegex ) )
		{
			continue;
		}
		const InternedString name = match[1].str();
		if( !::visible( m_parent.get(), name, m_section ) )
		{
			continue;
		}

		toSort.push_back( SortItem( index( m_parent.get(), name, toSort.size() ), name ) );
	}

	// Sort and return the result

	sort( toSort.begin(), toSort.end() );

	vector<GadgetKey> result;
	result.reserve( toSort.size() );
	for( vector<SortItem>::const_iterator it = toSort.begin(), eIt = toSort.end(); it != eIt; ++it )
	{
		result.push_back( it->second );
	}

	return result;
}

void NoduleLayout::updateLayout()
{
	// Figure out the order we want to display things in
	// and clear our main container ready for filling in
	// that order.
	vector<GadgetKey> items = layoutOrder();

	LinearContainer *gadgetContainer = noduleContainer();
	gadgetContainer->clearChildren();

	vector<Gadget *> added;
	vector<GadgetPtr> removed;

	// Iterate over the items we need to lay out, creating
	// or reusing gadgets and adding them to the layout.
	for( vector<GadgetKey>::const_iterator it = items.begin(), eIt = items.end(); it != eIt; ++it )
	{
		const GadgetKey &item = *it;
		const IECore::InternedString gadgetType = ::gadgetType( m_parent.get(), *it );

		GadgetPtr gadget;
		GadgetMap::iterator gadgetIt = m_gadgets.find( item );
		if( gadgetIt != m_gadgets.end() && gadgetIt->second.type == gadgetType )
		{
			gadget = gadgetIt->second.gadget;
		}
		else
		{
			// No gadget created yet, or it's the wrong type
			if( item.which() == 0 )
			{
				gadget = Nodule::create( const_cast<Plug *>( boost::get<const Plug *>( item ) ) ); /// \todo Fix cast
			}
			else
			{
				gadget = createCustomGadget( gadgetType, m_parent.get() );
			}

			added.push_back( gadget.get() );
			if( gadgetIt != m_gadgets.end() )
			{
				removed.push_back( gadgetIt->second.gadget );
			}
			m_gadgets[item] = TypeAndGadget( gadgetType, gadget );
		}

		if( gadget )
		{
			gadgetContainer->addChild( gadget );
		}
	}

	// Remove any gadgets we didn't use
	boost::container::flat_set<GadgetKey> itemsSet( items.begin(), items.end() );
	for( GadgetMap::const_iterator it = m_gadgets.begin(), eIt = m_gadgets.end(); it != eIt; )
	{
		GadgetMap::const_iterator next = it; ++next;
		if( itemsSet.find( it->first ) == itemsSet.end() )
		{
			removed.push_back( it->second.gadget );
			m_gadgets.erase( it );
		}
		it = next;
	}

	// Let everyone know what we've done.
	/// \todo Maybe we shouldn't know about the NodeGadget?
	if( NodeGadget *nodeGadget = ancestor<NodeGadget>() )
	{
		for( vector<GadgetPtr>::const_iterator it = removed.begin(), eIt = removed.end(); it != eIt; ++it )
		{
			if( Nodule *n = runTimeCast<Nodule>( it->get() ) )
			{
				nodeGadget->noduleRemovedSignal()( nodeGadget, n );
			}
		}

		for( vector<Gadget *>::const_iterator it = added.begin(), eIt = added.end(); it != eIt; ++it )
		{
			if( Nodule *n = runTimeCast<Nodule>( *it ) )
			{
				nodeGadget->noduleAddedSignal()( nodeGadget, n );
			}
		}
	}
}

void NoduleLayout::updateSpacing()
{
	noduleContainer()->setSpacing( spacing( m_parent.get(), m_section ) );
}

void NoduleLayout::updateDirection()
{
	noduleContainer()->setDirection( direction( m_parent.get(), m_section ) );
}

void NoduleLayout::updateOrientation()
{
	noduleContainer()->setOrientation( orientation( m_parent.get(), m_section ) );
}
