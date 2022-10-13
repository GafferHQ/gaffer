//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2017, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/BoxIO.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Box.h"
#include "Gaffer/BoxIn.h"
#include "Gaffer/BoxOut.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/Switch.h"

#include "boost/algorithm/string/replace.hpp"
#include "boost/bind/bind.hpp"

using namespace std;
using namespace boost::placeholders;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal constants
//////////////////////////////////////////////////////////////////////////

namespace
{

InternedString g_inName( "in" );
InternedString g_inNamePrivate( "__in" );
InternedString g_outName( "out" );
InternedString g_outNamePrivate( "__out" );
InternedString g_passThroughName( "passThrough" );
InternedString g_enabledName( "enabled" );
InternedString g_switchName( "__switch" );
InternedString g_sectionName( "noduleLayout:section" );

std::string oppositeSection( const std::string &section )
{
	if( section == "left" )
	{
		return "right";
	}
	else if( section == "right" )
	{
		return "left";
	}
	else if( section == "bottom" )
	{
		return "top";
	}
	else
	{
		return "bottom";
	}
}

void setupNoduleSectionMetadata( Plug *dst, const Plug *src )
{
	ConstStringDataPtr sectionData;
	for( const Plug *metadataPlug = src; metadataPlug; metadataPlug = metadataPlug->parent<Plug>() )
	{
		if( ( sectionData = Metadata::value<StringData>( metadataPlug, g_sectionName ) ) )
		{
			break;
		}
	}

	if( !sectionData )
	{
		return;
	}

	std::string section = sectionData->readable();
	if( src->direction() != dst->direction() )
	{
		section = oppositeSection( section );
	}

	Metadata::registerValue( dst, g_sectionName, new StringData( section ) );

}

// See equivalent function in PlugAlgo.cpp for an explanation of
// why this nonsense is necessary.
// \todo Abolish the Dynamic flag and instead make the serialisers
// smart enough to always do the right thing.
void applyDynamicFlag( Plug *plug )
{
	plug->setFlags( Plug::Dynamic, true );

	auto compoundTypes = { PlugTypeId, ValuePlugTypeId, ArrayPlugTypeId };
	if( find( begin( compoundTypes ), end( compoundTypes ), (Gaffer::TypeId)plug->typeId() ) != end( compoundTypes ) )
	{
		for( Plug::RecursiveIterator it( plug ); !it.done(); ++it )
		{
			(*it)->setFlags( Plug::Dynamic, true );
			if( find( begin( compoundTypes ), end( compoundTypes ), (Gaffer::TypeId)(*it)->typeId() ) == end( compoundTypes ) )
			{
				it.prune();
			}
		}
	}
}

// \todo This also exists in PlugAlgo.cpp. Should it be a public method,
// and if so, what should happen when the plugs don't match (the asserts
// wouldn't be appropriate). Or, more radically, should the `setFrom()`
// virtual method be moved from ValuePlug to Plug?
void setFrom( Plug *dst, const Plug *src )
{
	assert( dst->typeId() == src->typeId() );
	if( ValuePlug *dstValuePlug = IECore::runTimeCast<ValuePlug>( dst ) )
	{
		dstValuePlug->setFrom( static_cast<const ValuePlug *>( src ) );
	}
	else
	{
		for( Plug::Iterator it( dst ); !it.done(); ++it )
		{
			Plug *dstChild = it->get();
			const Plug *srcChild = src->getChild<Plug>( dstChild->getName() );
			assert( srcChild );
			setFrom( dstChild, srcChild );
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// BoxIO
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( BoxIO );

size_t BoxIO::g_firstPlugIndex = 0;

BoxIO::BoxIO( Plug::Direction direction, const std::string &name )
	:	Node( name ), m_direction( direction )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	// Must not accept inputs because the name is syncronised with the promoted
	// plug name and must therefore not be context-varying.
	addChild( new StringPlug( "name", Plug::In, direction == Plug::In ? "in" : "out", Plug::Default & ~Plug::AcceptsInputs ) );

	// Connect to the signals we need to syncronise the namePlug() value
	// with the name of the promotedPlug().
	plugSetSignal().connect( boost::bind( &BoxIO::plugSet, this, ::_1 ) );
	plugInputChangedSignal().connect( boost::bind( &BoxIO::plugInputChanged, this, ::_1 ) );
}

BoxIO::~BoxIO()
{
}

StringPlug *BoxIO::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *BoxIO::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

void BoxIO::setup( const Plug *plug )
{
	if( inPlugInternal() )
	{
		throw IECore::Exception( "Plugs already set up" );
	}
	addChild( plug->createCounterpart( inPlugName(), Plug::In ) );
	addChild( plug->createCounterpart( outPlugName(), Plug::Out ) );

	inPlugInternal()->setFlags( Plug::Serialisable, true );
	outPlugInternal()->setFlags( Plug::Serialisable, true );
	applyDynamicFlag( inPlugInternal() );
	applyDynamicFlag( outPlugInternal() );

	MetadataAlgo::copyIf(
		plug,
		m_direction == Plug::In ? inPlugInternal() : outPlugInternal(),
		[]( const GraphComponent *from, const GraphComponent *to, InternedString name )
		{
			if( StringAlgo::matchMultiple( name.string(), "layout:*" ) )
			{
				/// \todo Remove this condition and rely on registered exclusions only. An obstacle
				/// to doing this is making it easy to exclude `layout:*` without lots and lots of
				/// individual exclusions.
				return false;
			}
			return MetadataAlgo::isPromotable( from, to, name );
		}
	);

	setupNoduleSectionMetadata(
		m_direction == Plug::In ? outPlugInternal() : inPlugInternal(),
		plug
	);

	if( m_direction == Plug::Out )
	{
		setupPassThrough();
	}
	else
	{
		outPlugInternal()->setInput( inPlugInternal() );
	}

	// We also want to set up our promoted plug.  But if we're
	// being created from a script execution, we don't need to
	// do that ourselves because it'll have been serialised into
	// the script.
	ScriptNode *script = scriptNode();
	if( !script || !script->isExecuting() )
	{
		setupPromotedPlug();
	}
}

void BoxIO::setupPassThrough()
{
	addChild( inPlugInternal()->createCounterpart( g_passThroughName, Plug::In ) );
	addChild( new BoolPlug( g_enabledName, Plug::In, true ) );
	addChild( new Switch( g_switchName ) );
	switchInternal()->setup( inPlugInternal() );
	switchInternal()->enabledPlug()->setInput( enabledPlugInternal() );
	switchInternal()->inPlugs()->getChild<Plug>( 0 )->setInput( passThroughPlugInternal() );
	switchInternal()->inPlugs()->getChild<Plug>( 1 )->setInput( inPlugInternal() );
	switchInternal()->indexPlug()->setValue( 1 );
	outPlugInternal()->setInput( switchInternal()->outPlug() );
}

void BoxIO::setupPromotedPlug()
{
	Plug *toPromote = m_direction == Plug::In ? inPlugInternal() : outPlugInternal();
	if( toPromote && parent<Box>() )
	{
		Plug *promoted = PlugAlgo::promoteWithName( toPromote, namePlug()->getValue() );
		namePlug()->setValue( promoted->getName() );
	}
}

void BoxIO::setupBoxEnabledPlug()
{
	if( m_direction != Plug::Out )
	{
		return;
	}

	Box *box = parent<Box>();
	if( !box )
	{
		return;
	}

	BoolPlug *boxEnabledPlug = box->enabledPlug();
	if( !boxEnabledPlug )
	{
		BoolPlugPtr p = new BoolPlug( g_enabledName, Plug::In, true, Plug::Default | Plug::Dynamic );
		box->addChild( p );
		boxEnabledPlug = p.get();
	}
	enabledPlugInternal()->setInput( boxEnabledPlug );
}

Plug::Direction BoxIO::direction() const
{
	return m_direction;
}

Gaffer::Plug *BoxIO::inPlugInternal()
{
	return getChild<Plug>( inPlugName() );
}

const Gaffer::Plug *BoxIO::inPlugInternal() const
{
	return getChild<Plug>( inPlugName() );
}

Gaffer::Plug *BoxIO::outPlugInternal()
{
	return getChild<Plug>( outPlugName() );
}

const Gaffer::Plug *BoxIO::outPlugInternal() const
{
	return getChild<Plug>( outPlugName() );
}

Gaffer::Plug *BoxIO::passThroughPlugInternal()
{
	return getChild<Plug>( g_passThroughName );
}

const Gaffer::Plug *BoxIO::passThroughPlugInternal() const
{
	return getChild<Plug>( g_passThroughName );
}

Gaffer::Switch *BoxIO::switchInternal()
{
	return getChild<Switch>( g_switchName );
}

const Gaffer::Switch *BoxIO::switchInternal() const
{
	return getChild<Switch>( g_switchName );
}

BoolPlug *BoxIO::enabledPlugInternal()
{
	return getChild<BoolPlug>( g_enabledName );
}

const BoolPlug *BoxIO::enabledPlugInternal() const
{
	return getChild<BoolPlug>( g_enabledName );
}

void BoxIO::parentChanging( Gaffer::GraphComponent *newParent )
{
	// We're being deleted or moved to another parent. Delete
	// the promoted versions of our input and output plugs.
	// This allows the user to remove all trace of us by simply
	// deleting the BoxInOut node. We must do this in parentChanging()
	// rather than parentChanged() because we need a current parent
	// in order for the operations below to be undoable.

	Box *box = parent<Box>();
	if( box && !MetadataAlgo::getChildNodesAreReadOnly( box ) )
	{
		m_promotedPlugNameChangedConnection.disconnect();
		m_promotedPlugParentChangedConnection.disconnect();
		if( Plug *i = inPlugInternal() )
		{
			if( PlugAlgo::isPromoted( i ) )
			{
				PlugAlgo::unpromote( i );
			}
		}
		if( Plug *o = outPlugInternal() )
		{
			if( PlugAlgo::isPromoted( o ) )
			{
				PlugAlgo::unpromote( o );
			}
		}
	}

	Node::parentChanging( newParent );
}

IECore::InternedString BoxIO::inPlugName() const
{
	return m_direction == Plug::In ? g_inNamePrivate : g_inName;
}

IECore::InternedString BoxIO::outPlugName() const
{
	return m_direction == Plug::Out ? g_outNamePrivate : g_outName;
}

void BoxIO::plugSet( Plug *plug )
{
	if( plug == namePlug() )
	{
		if( Plug *p = promotedPlug() )
		{
			const InternedString newName = p->setName( namePlug()->getValue() );
			// Name may have been adjusted due to
			// not being unique. Update the plug to
			// use the adjusted name.
			namePlug()->setValue( newName );
		}
	}
}

void BoxIO::parentChanged( GraphComponent *oldParent )
{
	Node::parentChanged( oldParent );

	// Manage inputChanged connections on our parent box,
	// so we can discover our promoted plug when an output
	// connection is made to it.

	m_boxPlugInputChangedConnection.disconnect();
	if( Box *box = parent<Box>() )
	{
		m_boxPlugInputChangedConnection = box->plugInputChangedSignal().connect(
			boost::bind( &BoxIO::plugInputChanged, this, ::_1 )
		);
	}
}

void BoxIO::plugInputChanged( Plug *plug )
{
	// An input has changed either on this node or on
	// the parent box node. This gives us the opportunity
	// to discover our promoted plug and connect to its
	// signals.
	Plug *promoted = nullptr;
	if( m_direction == Plug::In && plug == inPlugInternal() )
	{
		promoted = promotedPlug();
	}
	else if( m_direction == Plug::Out && plug == promotedPlug() )
	{
		promoted = plug;
	}

	if( promoted )
	{
		m_promotedPlugNameChangedConnection = promoted->nameChangedSignal().connect(
			boost::bind( &BoxIO::promotedPlugNameChanged, this, ::_1 )
		);
		m_promotedPlugParentChangedConnection = promoted->parentChangedSignal().connect(
			boost::bind( &BoxIO::promotedPlugParentChanged, this, ::_1 )
		);
	}

	// Detect manual setups created by legacy scripts from before
	// we added the pass-through, and fix them to include a pass-through.

	if(
		m_direction == Plug::Out &&
		plug == outPlugInternal() &&
		plug->getInput() == inPlugInternal() &&
		!passThroughPlugInternal()
	)
	{
		setupPassThrough();
	}

	// If a connection has been made to our passThrough plug
	// for the first time, then we also want to create an enabled
	// plug for the Box and connect to it.
	if( plug == passThroughPlugInternal() && passThroughPlugInternal()->getInput() )
	{
		setupBoxEnabledPlug();
	}
}

void BoxIO::promotedPlugNameChanged( GraphComponent *graphComponent )
{
	if( graphComponent == promotedPlug() )
	{
		namePlug()->setValue( graphComponent->getName() );
	}
}

void BoxIO::promotedPlugParentChanged( GraphComponent *graphComponent )
{
	// Promoted plug is being deleted. Since we exist only
	// to represent it as a node inside the box, delete
	// ourselves too.
	if( const ScriptNode *script = scriptNode() )
	{
		if(
			script->currentActionStage() == Action::Undo ||
			script->currentActionStage() == Action::Redo
		)
		{
			// We don't need to do anything during undo/redo
			// since in those cases our previous actions are
			// already recorded.
			return;
		}
	}

	if( !graphComponent->parent() )
	{
		if( GraphComponent *p = parent() )
		{
			p->removeChild( this );
		}
	}
}

//////////////////////////////////////////////////////////////////////////
// Static utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Perhaps this could be moved to PlugAlgo and
/// (along with a matching canConnect()) be used to
/// address the todo in GraphBookmarksUI.__connection?
void connect( Plug *plug1, Plug *plug2 )
{
	if( plug1->direction() == plug2->direction() )
	{
		throw IECore::Exception( "Ambiguous connection" );
	}

	if( plug1->direction() == Plug::In )
	{
		plug1->setInput( plug2 );
	}
	else
	{
		plug2->setInput( plug1 );
	}
}

InternedString g_noduleTypeName( "nodule:type" );

bool hasNodule( const Plug *plug )
{
	for( const Plug *p = plug; p; p = p->parent<Plug>() )
	{
		ConstStringDataPtr d = Metadata::value<StringData>( p, g_noduleTypeName );
		if( d && d->readable() == "" )
		{
			return false;
		}
		if( p != plug )
		{
			if( !d || d->readable() == "GafferUI::StandardNodule" )
			{
				return false;
			}
		}
	}

	return true;
}

Box *enclosingBox( Plug *plug )
{
	Node *node = plug->node();
	if( !node )
	{
		return nullptr;
	}
	return node->parent<Box>();
}

std::string promotedName( const Plug *plug )
{
	std::string result = plug->relativeName( plug->node() );
	boost::replace_all( result, ".", "_" );
	return result;
}

} // namespace

Plug *BoxIO::promote( Plug *plug )
{
	Box *box = enclosingBox( plug );
	if( !box || !hasNodule( plug ) )
	{
		return PlugAlgo::promote( plug );
	}

	BoxIOPtr boxIO;
	if( plug->direction() == Plug::In )
	{
		boxIO = new BoxIn;
	}
	else
	{
		boxIO = new BoxOut;
	}

	box->addChild( boxIO );
	boxIO->namePlug()->setValue( promotedName( plug ) );
	boxIO->setup( plug );

	if( plug->direction() == Plug::In )
	{
		setFrom( boxIO->promotedPlug(), plug );
	}

	connect( plug, boxIO->plug() );

	if( runTimeCast<ArrayPlug>( plug ) )
	{
		// If we allowed the user to edit the connections
		// for individual elements, they could break the
		// promotion of the parent plug, so hide the
		// individual elements.
		Metadata::registerValue( plug, g_noduleTypeName, new StringData( "GafferUI::StandardNodule" ) );
		Metadata::registerValue( boxIO->plug(), g_noduleTypeName, new StringData( "GafferUI::StandardNodule" ) );
	}

	return boxIO->promotedPlug();
}

bool BoxIO::canInsert( const Box *box )
{
	for( Plug::Iterator it( box ); !it.done(); ++it )
	{
		const Plug *plug = it->get();
		if( plug->direction() == Plug::In )
		{
			const Plug::OutputContainer &outputs = plug->outputs();
			for( Plug::OutputContainer::const_iterator oIt = outputs.begin(), oeIt = outputs.end(); oIt != oeIt; ++oIt )
			{
				if( hasNodule( *oIt ) && !runTimeCast<BoxIO>( (*oIt)->node() ) )
				{
					return true;
				}
			}
		}
		else
		{
			const Plug *input = plug->getInput();
			if( input && hasNodule( input ) && !runTimeCast<const BoxIO>( input->node() ) )
			{
				return true;
			}
		}
	}

	return false;
}

void BoxIO::insert( Box *box )
{
	// Must take a copy of children because adding a child
	// would invalidate our Plug::Iterator.
	GraphComponent::ChildContainer children = box->children();
	for( Plug::Iterator it( children ); !it.done(); ++it )
	{
		Plug *plug = it->get();
		if( plug->direction() == Plug::In )
		{
			std::vector<Plug *> outputsNeedingBoxIn;
			const Plug::OutputContainer &outputs = plug->outputs();
			for( Plug::OutputContainer::const_iterator oIt = outputs.begin(), oeIt = outputs.end(); oIt != oeIt; ++oIt )
			{
				if( hasNodule( *oIt ) && !runTimeCast<BoxIO>( (*oIt)->node() ) )
				{
					outputsNeedingBoxIn.push_back( *oIt );
				}
			}

			if( outputsNeedingBoxIn.empty() )
			{
				continue;
			}

			BoxInPtr boxIn = new BoxIn;
			boxIn->namePlug()->setValue( plug->getName() );
			boxIn->setup( plug );
			box->addChild( boxIn );

			boxIn->inPlugInternal()->setInput( plug );
			for( std::vector<Plug *>::const_iterator oIt = outputsNeedingBoxIn.begin(), oeIt = outputsNeedingBoxIn.end(); oIt != oeIt; ++oIt )
			{
				(*oIt)->setInput( boxIn->plug() );
			}
		}
		else
		{
			// Output plug

			Plug *input = plug->getInput();
			if( !input || !hasNodule( input ) || runTimeCast<BoxIO>( input->node() ) )
			{
				continue;
			}

			BoxOutPtr boxOut = new BoxOut;
			boxOut->namePlug()->setValue( plug->getName() );
			boxOut->setup( plug );
			box->addChild( boxOut );

			boxOut->plug()->setInput( input );
			plug->setInput( boxOut->outPlugInternal() );
		}
	}

}
