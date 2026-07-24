//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/SubGraph.h"

#include "Gaffer/Action.h"
#include "Gaffer/BoxOut.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/RampPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/UndoScope.h"

#include "IECore/SearchPath.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"
#include "boost/regex.hpp"

using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

bool descendantHasInput( const Plug *plug )
{
	for( auto &d : Plug::RecursiveRange( *plug ) )
	{
		if( d->getInput() )
		{
			return true;
		}
	}
	return false;
}

bool conformRampPlugs( const Gaffer::Plug *srcPlug, Gaffer::Plug *dstPlug, bool ignoreDefaultValues )
{
	auto conform = [=] ( auto typedSrc, Gaffer::Plug *dst ) {

		using PlugType = std::remove_const_t<std::remove_pointer_t<decltype( typedSrc )>>;
		auto typedDest = runTimeCast<PlugType>( dst );
		if( !typedDest )
		{
			return false;
		}

		if( typedSrc->isSetToDefault() && ignoreDefaultValues && !descendantHasInput( typedSrc ) )
		{
			// We don't want to transfer any inputs or values, so must leave
			// `dstPlug` alone.
			return false;
		}

		typedDest->clearPoints();
		for( size_t i = 0, n = typedSrc->numPoints(); i < n; ++i )
		{
			const Plug *point = typedSrc->pointPlug( i );
			typedDest->addChild( point->createCounterpart( point->getName(), point->direction() ) );
		}
		return true;
	};

	switch( (Gaffer::TypeId)srcPlug->typeId() )
	{
		case RampffPlugTypeId :
			return conform( static_cast<const RampffPlug *>( srcPlug ), dstPlug );
		case RampfColor3fPlugTypeId :
			return conform( static_cast<const RampfColor3fPlug *>( srcPlug ), dstPlug );
		case RampfColor4fPlugTypeId :
			return conform( static_cast<const RampfColor4fPlug *>( srcPlug ), dstPlug );
		default :
			return false;
	}
}

/// \todo Consider moving to PlugAlgo.h
void copyInputsAndValues( Gaffer::Plug *srcPlug, Gaffer::Plug *dstPlug, bool ignoreDefaultValues )
{

	// From a user's perspective, we consider RampPlugs to have a single
	// atomic value. So _any_ edit to _any_ child plug should cause the entire
	// value to be matched. To do that, we first need to conform the destination
	// so that it has the same number of points as the source, and then we need
	// to set values for all plugs.

	if( conformRampPlugs( srcPlug, dstPlug, ignoreDefaultValues ) )
	{
		ignoreDefaultValues = false;
	}

	// If we have an input to copy, we can leave the
	// recursion to the `setInput()` call, which will
	// also set all descendant inputs.

	if( Plug *input = srcPlug->getInput() )
	{
		dstPlug->setInput( input );
		return;
	}

	// We have no input.
	// =================

	// If we're at a leaf plug, remove the destination
	// input and copy the value.

	if( !dstPlug->children().size() )
	{
		dstPlug->setInput( nullptr );
		if( ValuePlug *srcValuePlug = runTimeCast<ValuePlug>( srcPlug ) )
		{
			if( !ignoreDefaultValues || !srcValuePlug->isSetToDefault() )
			{
				if( ValuePlug *dstValuePlug = runTimeCast<ValuePlug>( dstPlug ) )
				{
					dstValuePlug->setFrom( srcValuePlug );
				}
			}
		}
		return;
	}

	// Otherwise, recurse to children. We recurse awkwardly
	// using indices rather than PlugIterator for compatibility
	// with ArrayPlug, which will add new children as inputs are
	// added.

	const Plug::ChildContainer &children = dstPlug->children();
	for( size_t i = 0; i < children.size(); ++i )
	{
		if( Plug *srcChildPlug = srcPlug->getChild<Plug>( children[i]->getName() ) )
		{
			copyInputsAndValues( srcChildPlug, static_cast<Plug *>( children[i].get() ), ignoreDefaultValues );
		}
	}

}

/// \todo Consider moving to PlugAlgo.h
void transferOutputs( Gaffer::Plug *srcPlug, Gaffer::Plug *dstPlug )
{
	// Transfer outputs

	for( Plug::OutputContainer::const_iterator oIt = srcPlug->outputs().begin(), oeIt = srcPlug->outputs().end(); oIt != oeIt;  )
	{
		Plug *outputPlug = *oIt;
		++oIt; // increment now because the setInput() call invalidates our iterator.
		outputPlug->setInput( dstPlug );
	}

	// Recurse

	for( Plug::Iterator it( srcPlug ); !it.done(); ++it )
	{
		if( Plug *dstChildPlug = dstPlug->getChild<Plug>( (*it)->getName() ) )
		{
			transferOutputs( it->get(), dstChildPlug );
		}
	}
}

const InternedString g_childNodesAreReadOnlyName( "childNodesAreReadOnly" );
const std::filesystem::path g_emptyPath;

} // namespace

//////////////////////////////////////////////////////////////////////////
// PlugEdits and ReferenceState
//////////////////////////////////////////////////////////////////////////

class SubGraph::PlugEdits : public Signals::Trackable
{

	public :

		PlugEdits( SubGraph *subGraph )
			:	m_subGraph( subGraph )
		{
			m_connection = Metadata::plugValueChangedSignal( subGraph ).connect( boost::bind( &PlugEdits::plugValueChanged, this, ::_1, ::_2, ::_3 ) );
			m_subGraph->childRemovedSignal().connect( boost::bind( &PlugEdits::childRemoved, this, ::_1, ::_2 ) );
		}

		bool hasMetadataEdit( const Plug *plug, const InternedString &key ) const
		{
			const PlugEdit *edit = plugEdit( plug );

			if( !edit )
			{
				return false;
			}

			return edit->metadataEdits.find( key ) != edit->metadataEdits.end();
		}

		bool isChildEdit( const Plug *plug ) const
		{
			const Plug *parent = plug->parent<Plug>();
			if( !parent )
			{
				return false;
			}

			const PlugEdit *edit = plugEdit( parent );
			if( !edit )
			{
				return false;
			}

			if( edit->sizeAfterLoad == -1 || parent->children().size() <= (size_t)edit->sizeAfterLoad )
			{
				return false;
			}

			// Conceptually we want to compare the index of `plug` against
			// `sizeAfterLoad`. But finding the index currently requires linear
			// search. We expect the UI to only allow creation of new plugs in
			// originally-empty containers (to avoid merge hell on reload),
			// meaning that `sizeAfterLoad` can be expected to be either 0 or 1
			// (the latter for RowsPlug with a default row). So it is quicker to
			// reverse the test and search for plug in the range `[0,
			// sizeAfterLoad)`.
			return !std::any_of(
				parent->children().begin(), parent->children().begin() + edit->sizeAfterLoad,
				[plug]( const GraphComponentPtr &child ) { return child == plug; }
			);
		}

		void transferEdits( Plug *oldPlug, Plug *newPlug ) const
		{
			transferEditedMetadata( oldPlug, newPlug );
			transferChildEdits( oldPlug, newPlug );
		}

		// Used to allow PlugEdits to track reference loading.
		struct LoadingScope : boost::noncopyable
		{
			LoadingScope( PlugEdits &plugEdits )
				:	m_plugEdits( plugEdits ), m_blockedConnection( plugEdits.m_connection )
			{
			}
			~LoadingScope()
			{
				m_plugEdits.loadingFinished();
			}
			private :
				PlugEdits &m_plugEdits;
				// Changes made during loading aren't user edits and mustn't be
				// tracked, so we block the connection.
				Signals::BlockedConnection m_blockedConnection;
		};

	private :

		SubGraph *m_subGraph;
		Signals::ScopedConnection m_connection;

		// Struct for tracking all edits to a plug, where an edit is conceptually
		// any change the user makes to the plug after it has been loaded by
		// `SubGraph::loadReference()`. In practice we currently only track metadata
		// edits and the addition of children to a subset of plug types.
		struct PlugEdit
		{
			boost::container::flat_set<InternedString> metadataEdits;
			int64_t sizeAfterLoad = -1; // Default value means size not tracked
		};

		std::unordered_map<const Plug*, PlugEdit> m_plugEdits;

		const PlugEdit *plugEdit( const Plug *plug ) const
		{
			// Cheeky cast better than maintaining two near-identical functions.
			return const_cast<PlugEdits *>( this )->plugEdit( plug, /* createIfMissing = */ false );
		}

		PlugEdit *plugEdit( const Plug *plug, bool createIfMissing )
		{
			if( plug->node() != m_subGraph )
			{
				return nullptr;
			}

			auto it = m_plugEdits.find( plug );
			if( it != m_plugEdits.end() )
			{
				return &(it->second);
			}

			if( !m_subGraph->isReferenceable( plug ) )
			{
				// We'll allow retrieval of existing edits on this plug, but we
				// won't create new ones.
				return nullptr;
			}

			if( !createIfMissing )
			{
				return nullptr;
			}

			return &m_plugEdits[plug];
		}

		void plugValueChanged( const Gaffer::Plug *plug, IECore::InternedString key, Metadata::ValueChangedReason reason )
		{
			if(
				reason == Metadata::ValueChangedReason::StaticRegistration ||
				reason == Metadata::ValueChangedReason::StaticDeregistration
			)
			{
				return;
			}

			ScriptNode *scriptNode = m_subGraph->ancestor<ScriptNode>();
			if( scriptNode && ( scriptNode->currentActionStage() == Action::Undo || scriptNode->currentActionStage() == Action::Redo ) )
			{
				// Our edit tracking code below utilises the undo system, so we don't need
				// to do anything for an Undo or Redo - our action from the original Do will
				// be replayed automatically.
				return;
			}

			PlugEdit *edit = plugEdit( plug, /* createIfMissing = */ true );
			if( !edit )
			{
				// May get a null edit even with `createIfMissing = true`,
				// if the plug is not a reference plug node.
				return;
			}

			if( edit->metadataEdits.find( key ) != edit->metadataEdits.end() )
			{
				return;
			}

			Action::enact(
				m_subGraph,
				[edit, key](){ edit->metadataEdits.insert( key ); },
				[edit, key](){ edit->metadataEdits.erase( key ); }
			);
		}

		void childRemoved( GraphComponent *parent, GraphComponent *child )
		{
			const Plug *plug = runTimeCast<Plug>( child );
			if( !plug )
			{
				return;
			}

			for( Plug::RecursiveIterator it( plug ); !it.done(); ++it )
			{
				m_plugEdits.erase( it->get() );
			}

			m_plugEdits.erase( plug );
		}

		void loadingFinished()
		{
			for( auto &plug : Plug::RecursiveRange( *m_subGraph ) )
			{
				if( !m_subGraph->isReferenceable( plug.get() ) )
				{
					continue;
				}

				const IECore::TypeId plugType = plug->typeId();
				if(
					plugType != (IECore::TypeId)SpreadsheetRowsPlugTypeId &&
					plugType != (IECore::TypeId)CompoundDataPlugTypeId
				)
				{
					// We only support child edits for RowsPlugs and
					// CompoundDataPlugs at present. It would be trivial
					// to do the tracking for everything, but most types
					// don't have dynamic numbers of children, and we
					// probably don't want the overhead of a PlugEdit for
					// everything else.
					continue;
				}
				if( auto *edit = plugEdit( plug.get(), /* createIfMissing = */ true ) )
				{
					edit->sizeAfterLoad = plug->children().size();
				}
			}
		}

		void transferEditedMetadata( const Plug *srcPlug, Plug *dstPlug ) const
		{
			// Transfer metadata that was edited and won't be provided by a
			// load. Note: Adding the metadata to a new plug
			// automatically registers a PlugEdit for that plug.

			if( auto *edit = plugEdit( srcPlug ) )
			{
				for( const InternedString &key : edit->metadataEdits )
				{
					Gaffer::Metadata::registerValue( dstPlug, key, Gaffer::Metadata::value<IECore::Data>( srcPlug, key ), /* persistent =*/ true );
				}
			}

			// Recurse

			for( Plug::Iterator it( srcPlug ); !it.done(); ++it )
			{
				if( Plug *dstChildPlug = dstPlug->getChild<Plug>( (*it)->getName() ) )
				{
					transferEditedMetadata( it->get(), dstChildPlug );
				}
			}
		}

		void transferChildEdits( Plug *oldPlug, Plug *newPlug ) const
		{
			if( newPlug->typeId() != oldPlug->typeId() )
			{
				return;
			}

			// Recurse

			for( Plug::Iterator it( oldPlug ); !it.done(); ++it )
			{
				if( Plug *dstChildPlug = newPlug->getChild<Plug>( (*it)->getName() ) )
				{
					transferChildEdits( it->get(), dstChildPlug );
				}
			}

			auto *edit = plugEdit( oldPlug );
			if( !edit || edit->sizeAfterLoad == -1 )
			{
				return;
			}

			auto *newRows = runTimeCast<Spreadsheet::RowsPlug>( newPlug );
			for( size_t i = edit->sizeAfterLoad; i < oldPlug->children().size(); ++i )
			{
				if( newRows )
				{
					// The only valid way to add children to a RowsPlug is to
					// call `addRow()`. If we don't use that, our new rows may
					// have the wrong number of columns if the columns in the
					// referenced file have been changed.
					Spreadsheet::RowPlug *newRow = newRows->addRow();
					newRow->setName( oldPlug->getChild( i )->getName() );
				}
				else
				{
					const Plug *oldChild = oldPlug->getChild<Plug>( i );
					newPlug->addChild( oldChild->createCounterpart( oldChild->getName(), oldChild->direction() ) );
				}
			}
		}

};

struct SubGraph::ReferenceState
{
	ReferenceState( SubGraph *subGraph ) : plugEdits( subGraph ) {}
	std::filesystem::path fileName;
	PlugEdits plugEdits;
};

//////////////////////////////////////////////////////////////////////////
// SubGraph
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( SubGraph );

static IECore::InternedString g_enabledName( "enabled" );

SubGraph::SubGraph( const std::string &name )
	:	DependencyNode( name )
{
}

SubGraph::~SubGraph()
{
}

void SubGraph::exportReference( const std::filesystem::path &fileName ) const
{
	const ScriptNode *script = scriptNode();
	if( !script )
	{
		throw IECore::Exception( "SubGraph::exportForReference called without ScriptNode" );
	}

	StandardSetPtr toExport = new StandardSet;
	for( const auto &child : GraphComponent::Range( *this ) )
	{
		if( isReferenceable( child.get() ) )
		{
			toExport->add( child.get() );
		}
	}

	ContextPtr context = new Context;
	context->set( "valuePlugSerialiser:omitParentNodePlugValues", true );
	context->set( "serialiser:includeParentMetadata", true );
	Context::Scope scopedContext( context.get() );

	script->serialiseToFile( fileName, this, toExport.get() );
}

void SubGraph::loadReference( const std::filesystem::path &fileName )
{
	const char *s = getenv( "GAFFER_REFERENCE_PATHS" );
	IECore::SearchPath sp( s ? s : "" );
	/// \todo Convert SearchPath to deal in `std::filesystem` rather than `boost::filesystem`.
	std::filesystem::path path = sp.find( fileName.string() ).string();
	if( path.empty() )
	{
		throw Exception( "Could not find file '" + fileName.generic_string() + "'" );
	}

	ScriptNode *script = scriptNode();
	if( !script )
	{
		throw IECore::Exception( "SubGraph::loadReference called without ScriptNode" );
	}

	Action::enact(
		this,
		boost::bind( &SubGraph::loadReferenceInternal, SubGraphPtr( this ), fileName ),
		boost::bind( &SubGraph::loadReferenceInternal, SubGraphPtr( this ), referenceFileName() )
	);
}

bool SubGraph::isReference() const
{
	return m_referenceState && !m_referenceState->fileName.empty();
}

const std::filesystem::path &SubGraph::referenceFileName() const
{
	return m_referenceState ? m_referenceState->fileName : g_emptyPath;
}

SubGraph::ReferenceChangedSignal &SubGraph::referenceChangedSignal()
{
	return m_referenceChangedSignal;
}

void SubGraph::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	DependencyNode::affects( input, outputs );
}

BoolPlug *SubGraph::enabledPlug()
{
	return getChild<BoolPlug>( g_enabledName );
}

const BoolPlug *SubGraph::enabledPlug() const
{
	return getChild<BoolPlug>( g_enabledName );
}

Plug *SubGraph::correspondingInput( const Plug *output )
{
	return const_cast<Plug *>( const_cast<const SubGraph *>( this )->SubGraph::correspondingInput( output ) );
}

const Plug *SubGraph::correspondingInput( const Plug *output ) const
{
	const Plug *internalOutput = output->getInput();
	if( !internalOutput )
	{
		return nullptr;
	}

	const Plug *internalInput = nullptr;
	if( const BoxOut *boxOut = internalOutput->parent<BoxOut>() )
	{
		if( boxOut->passThroughPlug()->getInput() )
		{
			internalInput = boxOut->passThroughPlug();
		}
		else
		{
			// Prepare for legacy branch below
			internalOutput = boxOut->plug()->getInput();
			if( !internalOutput )
			{
				return nullptr;
			}
		}
	}

	if( !internalInput )
	{
		// Legacy code path for networks made before BoxOut had pass-through support.
		// These used Switch nodes wired up manually - this is the `node` referred to
		// below.

		const DependencyNode *node = IECore::runTimeCast<const DependencyNode>( internalOutput->node() );
		if( !node )
		{
			return nullptr;
		}

		const BoolPlug *externalEnabledPlug = enabledPlug();
		if( !externalEnabledPlug )
		{
			return nullptr;
		}

		const BoolPlug *internalEnabledPlug = node->enabledPlug();
		if( !internalEnabledPlug )
		{
			return nullptr;
		}

		if( internalEnabledPlug->getInput() != externalEnabledPlug )
		{
			return nullptr;
		}

		internalInput = node->correspondingInput( internalOutput );
		if( !internalInput )
		{
			return nullptr;
		}
	}

	const Plug *input = internalInput->getInput();
	while( input )
	{
		if( input->node() == this )
		{
			return input;
		}
		input = input->getInput();
	}

	return nullptr;
 }

void SubGraph::loadReferenceInternal( const std::filesystem::path &fileName )
{
	if( !m_referenceState )
	{
		m_referenceState = std::make_unique<ReferenceState>( this );
	}

	ScriptNode *script = scriptNode();

	// Disable undo for the actions we perform, because we ourselves
	// are undoable anyway and will take care of everything as a whole
	// when we are undone.
	UndoScope undoDisabler( script, UndoScope::Disabled );

	// if we're doing a reload, then we want to maintain any values and
	// connections that our external plugs might have. but we also need to
	// get those existing plugs out of the way during the load, so that the
	// incoming plugs don't get renamed.

	std::map<std::string, Plug *> previousPlugs;
	for( Plug::Iterator it( this ); !it.done(); ++it )
	{
		Plug *plug = it->get();
		if( isReferenceable( plug ) )
		{
			previousPlugs[plug->getName()] = plug;
			plug->setName( "__tmp__" + plug->getName().string() );
		}
	}

	// if we're doing a reload, then we also need to delete all our child
	// nodes to make way for the incoming nodes.

	int i = (int)(children().size()) - 1;
	while( i >= 0 )
	{
		if( Node *node = getChild<Node>( i ) )
		{
			removeChild( node );
		}
		i--;
	}

	// Set up a container to catch all the children added during loading.
	StandardSetPtr newChildren = new StandardSet;
	childAddedSignal().connect( boost::bind( (bool (StandardSet::*)( IECore::RunTimeTypedPtr ) )&StandardSet::add, newChildren.get(), ::_2 ) );

	// load the reference. we use continueOnError=true to get everything possible
	// loaded, but if any errors do occur we throw an exception at the end of this
	// function. this means that the caller is still notified of errors via the
	// exception mechanism, but we leave ourselves in the best state possible for
	// the case where ScriptNode::load( continueOnError = true ) will ignore the
	// exception that we throw.

	bool errors = false;
	const char *s = getenv( "GAFFER_REFERENCE_PATHS" );
	IECore::SearchPath sp( s ? s : "" );
	/// \todo Convert SearchPath to deal in `std::filesystem` rather than `boost::filesystem`.
	std::filesystem::path path = sp.find( fileName.string() ).string();
	if( !path.empty() )
	{
		PlugEdits::LoadingScope loadingScope( m_referenceState->plugEdits );
		// We register our child nodes as read-only _before_ loading, to facilitate
		// a special case in `MetadataAlgo::setNumericBookmark()`. Coverage for this
		// is in `MetadataAlgoTest.testNumericBookmarksInReferences`.
		Metadata::registerValue( this, g_childNodesAreReadOnlyName, new BoolData( true ), /* persistent = */ false );
		errors = script->executeFile( path.string(), this, /* continueOnError = */ true );
		// Alas we have to register again _after_ loading for `SubGraphTest.testChildNodesAreReadOnlyMetadata`
		// to pass. That test appears to model a problem with an internal Image Engine node - ideally the issue
		// would be fixed there and we'd remove this. See #4320.
		Metadata::registerValue( this, g_childNodesAreReadOnlyName, new BoolData( true ), /* persistent = */ false );
	}
	else
	{
		Metadata::deregisterValue( this, g_childNodesAreReadOnlyName );
	}

	// Do a little bit of post processing on everything that was loaded.

	for( size_t i = 0, e = newChildren->size(); i < e; ++i )
	{
		if( Plug *plug = runTimeCast<Plug>( newChildren->member( i ) ) )
		{
			// Make the loaded plugs non-dynamic, because we don't want them
			// to be serialised in the script the reference is in - the whole
			// point is that they are referenced.
			/// \todo Plug flags are not working. We need to introduce an
			/// alternative mechanism based on querying parent nodes/plugs
			/// for serialisation requirements at the point of serialisation.
			plug->setFlags( Plug::Dynamic, false );

			if(
				runTimeCast<const RampffPlug>( plug ) ||
				runTimeCast<const RampfColor3fPlug>( plug ) ||
				runTimeCast<const RampfColor4fPlug>( plug )
			)
			{
				// Avoid recursion as it makes it impossible to serialise
				// the `x/y` children of ramp points. See RampPlugSerialiser
				// for further details of ramp serialisation.
				continue;
			}

			for( Plug::RecursiveIterator it( plug ); !it.done(); ++it )
			{
				(*it)->setFlags( Plug::Dynamic, false );
			}
		}
	}

	// Transfer connections, values and metadata from the old plugs onto the corresponding new ones.

	for( std::map<std::string, Plug *>::const_iterator it = previousPlugs.begin(), eIt = previousPlugs.end(); it != eIt; ++it )
	{
		Plug *oldPlug = it->second;
		Plug *newPlug = descendant<Plug>( it->first );
		if( newPlug )
		{
			try
			{
				m_referenceState->plugEdits.transferEdits( oldPlug, newPlug );
				if( newPlug->direction() == Plug::In && oldPlug->direction() == Plug::In )
				{
					copyInputsAndValues( oldPlug, newPlug, /* ignoreDefaultValues = */ true );
				}
				transferOutputs( oldPlug, newPlug );
			}
			catch( const std::exception &e )
			{
				msg(
					Msg::Warning,
					fmt::format( "Loading \"{}\" onto \"{}\"", fileName.generic_string(), getName().c_str() ),
					e.what()
				);
			}

		}

		// remove the old plug now we're done with it.
		oldPlug->parent()->removeChild( oldPlug );
	}

	// Finish up.

	m_referenceState->fileName = fileName;
	referenceChangedSignal()( this );

	if( errors )
	{
		throw Exception( fmt::format( "Error loading reference \"{}\"", fileName.generic_string() ) );
	}

}

bool SubGraph::hasMetadataEdit( const Plug *plug, const IECore::InternedString key ) const
{
	return m_referenceState && m_referenceState->plugEdits.hasMetadataEdit( plug, key );
}

bool SubGraph::isChildEdit( const Plug *plug ) const
{
	return m_referenceState && m_referenceState->plugEdits.isChildEdit( plug );
}

bool SubGraph::isReferenceable( const GraphComponent *descendant ) const
{
	// Walk up until `descendant` is immediately parented to us.
	const GraphComponent *parent = descendant->parent();
	while( parent && parent != this )
	{
		descendant = parent;
		parent = descendant->parent();
	}

	if( !parent )
	{
		// We weren't an ancestor of `descendant`.
		return false;
	}

	if( runTimeCast<const Node>( descendant ) )
	{
		return true;
	}
	else if( auto plug = runTimeCast<const Plug>( descendant ) )
	{
		// There are two classes of plug that we don't want to include
		// in exported references :
		//
		// 1. The `user` plug and its children. We want the `user` namespace
		//    to be available to users of the reference, so it must be empty
		//    when exported.
		// 2. Plugs prefixed with `__`. These are hidden plugs created by
		//    various UI components, for example to store the node's position
		//    in the GraphEditor. Arguably these should be metadata instead,
		//    but until they are, we need to ignore them.
		return plug != userPlug() && !boost::starts_with( plug->getName().c_str(), "__" );
	}

	return false;
}
