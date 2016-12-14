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
#include "boost/algorithm/string/predicate.hpp"

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

// Used for sorting nodules for layout

struct IndexAndNodule
{

	IndexAndNodule()
		:	index( 0 ), nodule( NULL )
	{
	}

	IndexAndNodule( int index, Nodule *nodule )
		:	index( index ), nodule( nodule )
	{
	}

	bool operator < ( const IndexAndNodule &rhs ) const
	{
		return index < rhs.index;
	}

	int index;
	Nodule *nodule;

};

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

// Metadata accessors

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

	updateNoduleLayout();
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
		NoduleMap::iterator it = m_nodules.find( plug );
		if( it != m_nodules.end() )
		{
			return it->second.nodule.get();
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
		updateNoduleLayout();
	}
}

void NoduleLayout::childRemoved( Gaffer::GraphComponent *child )
{
	if( IECore::runTimeCast<Gaffer::Plug>( child ) )
	{
		updateNoduleLayout();
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
			updateNoduleLayout();
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
}

void NoduleLayout::updateNodules( std::vector<Nodule *> &nodules, std::vector<Nodule *> &added, std::vector<NodulePtr> &removed )
{
	// Update the nodules for all our plugs, and build a vector
	// of IndexAndNodule to sort ready for layout.
	vector<IndexAndNodule> sortedNodules;
	for( PlugIterator plugIt( m_parent.get() ); !plugIt.done(); ++plugIt )
	{
		Plug *plug = plugIt->get();
		if( boost::starts_with( plug->getName().string(), "__" ) )
		{
			continue;
		}

		Nodule *nodule = NULL;
		NoduleMap::iterator it = m_nodules.find( plug );

		if( ::visible( plug, m_section ) )
		{
			IECore::InternedString type;
			IECore::ConstStringDataPtr typeData = Metadata::value<IECore::StringData>( plug, g_noduleTypeKey );
			type = typeData ? typeData->readable() : "GafferUI::StandardNodule";

			if( it != m_nodules.end() && it->second.type == type )
			{
				// Reuse existing nodule
				nodule = it->second.nodule.get();
			}
			else
			{
				// Remove old nodule.
				if( it != m_nodules.end() && it->second.nodule )
				{
					removed.push_back( it->second.nodule );
				}
				// Add new one
				NodulePtr n = Nodule::create( plug );
				m_nodules[plug] = TypeAndNodule( type, n );
				if( n )
				{
					added.push_back( n.get() );
					nodule = n.get();
				}
			}
		}
		else if( it != m_nodules.end() )
		{
			// Not visible, but we have an old
			// record for it.
			if( it->second.nodule )
			{
				removed.push_back( it->second.nodule );
			}
			m_nodules.erase( it );
		}

		if( nodule )
		{
			sortedNodules.push_back( IndexAndNodule( index( plug, sortedNodules.size() ), nodule ) );
		}
	}

	// Remove any nodules for which a plug no longer exists.
	for( NoduleMap::iterator it = m_nodules.begin(); it != m_nodules.end(); )
	{
		NoduleMap::iterator next = it; next++;
		if( it->first->parent<GraphComponent>() != m_parent.get() )
		{
			if( it->second.nodule )
			{
				removed.push_back( it->second.nodule );
			}
			m_nodules.erase( it );
		}
		it = next;
	}

	// Sort ready for layout.
	sort( sortedNodules.begin(), sortedNodules.end() );
	for( vector<IndexAndNodule>::const_iterator it = sortedNodules.begin(), eIt = sortedNodules.end(); it != eIt; ++it )
	{
		nodules.push_back( it->nodule );
	}
}

void NoduleLayout::updateNoduleLayout()
{
	// Get an updated array of all our nodules,
	// remembering what was added and removed.
	vector<Nodule *> nodules;
	vector<Nodule *> added;
	vector<NodulePtr> removed;
	updateNodules( nodules, added, removed );

	// Clear the nodule container and refill it
	// in the right order.

	LinearContainer *c = noduleContainer();
	c->clearChildren();
	for( vector<Nodule *>::const_iterator it = nodules.begin(), eIt = nodules.end(); it != eIt; ++it )
	{
		c->addChild( *it );
	}

	// Let everyone know what we've done.
	/// \todo Maybe we shouldn't know about the NodeGadget?
	if( NodeGadget *nodeGadget = ancestor<NodeGadget>() )
	{
		for( vector<NodulePtr>::const_iterator it = removed.begin(), eIt = removed.end(); it != eIt; ++it )
		{
			nodeGadget->noduleRemovedSignal()( nodeGadget, it->get() );
		}

		for( vector<Nodule *>::const_iterator it = added.begin(), eIt = added.end(); it != eIt; ++it )
		{
			nodeGadget->noduleAddedSignal()( nodeGadget, *it );
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
