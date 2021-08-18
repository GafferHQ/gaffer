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

#include "Gaffer/Reference.h"

#include "Gaffer/BlockedConnection.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/PlugAlgo.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/SplinePlug.h"
#include "Gaffer/Spreadsheet.h"
#include "Gaffer/StringPlug.h"

#include "IECore/Exception.h"
#include "IECore/MessageHandler.h"
#include "IECore/SearchPath.h"

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"
#include "boost/container/flat_set.hpp"

#include <unordered_map>


using namespace std;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Internal utilities
//////////////////////////////////////////////////////////////////////////

namespace
{

/// \todo Consider moving to PlugAlgo.h
void copyInputsAndValues( Gaffer::Plug *srcPlug, Gaffer::Plug *dstPlug, bool ignoreDefaultValues )
{

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

	for( PlugIterator it( srcPlug ); !it.done(); ++it )
	{
		if( Plug *dstChildPlug = dstPlug->getChild<Plug>( (*it)->getName() ) )
		{
			transferOutputs( it->get(), dstChildPlug );
		}
	}
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// PlugEdits. This internal utility class is used to track where edits have
// been applied to plugs following loading.
//////////////////////////////////////////////////////////////////////////

class Reference::PlugEdits : public boost::signals::trackable
{

	public :

		PlugEdits( Reference *reference )
			:	m_reference( reference )
		{
			m_connection = Metadata::plugValueChangedSignal( reference ).connect( boost::bind( &PlugEdits::plugValueChanged, this, ::_1, ::_2, ::_3 ) );
			m_reference->childRemovedSignal().connect( boost::bind( &PlugEdits::childRemoved, this, ::_1, ::_2 ) );
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
			LoadingScope( PlugEdits *plugEdits )
				:	m_plugEdits( plugEdits ), m_blockedConnection( plugEdits->m_connection )
			{
			}
			~LoadingScope()
			{
				m_plugEdits->loadingFinished();
			}
			private :
				PlugEdits *m_plugEdits;
				// Changes made during loading aren't user edits and mustn't be
				// tracked, so we block the connection.
				Gaffer::BlockedConnection m_blockedConnection;
		};

	private :

		Reference *m_reference;
		boost::signals::scoped_connection m_connection;

		// Struct for tracking all edits to a plug, where an edit is conceptually
		// any change the user makes to the plug after it has been loaded by
		// `Reference::load()`. In practice we currently only track metadata
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
			if( plug->node() != m_reference )
			{
				return nullptr;
			}

			auto it = m_plugEdits.find( plug );
			if( it != m_plugEdits.end() )
			{
				return &(it->second);
			}

			if( !m_reference->isReferencePlug( plug ) )
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

			ScriptNode *scriptNode = m_reference->ancestor<ScriptNode>();
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
				m_reference,
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

			m_plugEdits.erase( plug );
		}

		void loadingFinished()
		{
			for( auto &plug : Plug::RecursiveRange( *m_reference ) )
			{
				if( !m_reference->isReferencePlug( plug.get() ) )
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

			for( PlugIterator it( srcPlug ); !it.done(); ++it )
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

			for( PlugIterator it( oldPlug ); !it.done(); ++it )
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

//////////////////////////////////////////////////////////////////////////
// Reference
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( Reference );

Reference::Reference( const std::string &name )
	:	SubGraph( name ), m_plugEdits( new PlugEdits( this ) )
{
}

Reference::~Reference()
{
}

void Reference::load( const std::string &fileName )
{
	const char *s = getenv( "GAFFER_REFERENCE_PATHS" );
	IECore::SearchPath sp( s ? s : "" );
	boost::filesystem::path path = sp.find( fileName );
	if( path.empty() )
	{
		throw Exception( "Could not find file '" + fileName + "'" );
	}

	ScriptNode *script = scriptNode();
	if( !script )
	{
		throw IECore::Exception( "Reference::load called without ScriptNode" );
	}

	Action::enact(
		this,
		boost::bind( &Reference::loadInternal, ReferencePtr( this ), fileName ),
		boost::bind( &Reference::loadInternal, ReferencePtr( this ), m_fileName )
	);
}

const std::string &Reference::fileName() const
{
	return m_fileName;
}

Reference::ReferenceLoadedSignal &Reference::referenceLoadedSignal()
{
	return m_referenceLoadedSignal;
}

void Reference::loadInternal( const std::string &fileName )
{
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
	for( PlugIterator it( this ); !it.done(); ++it )
	{
		Plug *plug = it->get();
		if( isReferencePlug( plug ) )
		{
			previousPlugs[plug->getName()] = plug;
			plug->setName( "__tmp__" + plug->getName().string() );
		}
	}

	// We don't export user plugs to references, but old versions of
	// Gaffer did, so as above, we must get them out of the way during
	// the load.
	for( PlugIterator it( userPlug() ); !it.done(); ++it )
	{
		Plug *plug = it->get();
		if( isReferencePlug( plug ) )
		{
			previousPlugs[plug->relativeName( this )] = plug;
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
	userPlug()->childAddedSignal().connect( boost::bind( (bool (StandardSet::*)( IECore::RunTimeTypedPtr ) )&StandardSet::add, newChildren.get(), ::_2 ) );

	// load the reference. we use continueOnError=true to get everything possible
	// loaded, but if any errors do occur we throw an exception at the end of this
	// function. this means that the caller is still notified of errors via the
	// exception mechanism, but we leave ourselves in the best state possible for
	// the case where ScriptNode::load( continueOnError = true ) will ignore the
	// exception that we throw.

	bool errors = false;
	const char *s = getenv( "GAFFER_REFERENCE_PATHS" );
	IECore::SearchPath sp( s ? s : "" );
	boost::filesystem::path path = sp.find( fileName );
	if( !path.empty() )
	{
		PlugEdits::LoadingScope loadingScope( m_plugEdits.get() );
		errors = script->executeFile( path.string(), this, /* continueOnError = */ true );
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
				runTimeCast<const SplineffPlug>( plug ) ||
				runTimeCast<const SplinefColor3fPlug>( plug ) ||
				runTimeCast<const SplinefColor4fPlug>( plug )
			)
			{
				// Avoid recursion as it makes it impossible to serialise
				// the `x/y` children of spline points. See SplinePlugSerialiser
				// for further details of spline serialisation.
				continue;
			}

			for( RecursivePlugIterator it( plug ); !it.done(); ++it )
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
				m_plugEdits->transferEdits( oldPlug, newPlug );
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
					boost::str( boost::format( "Loading \"%s\" onto \"%s\"" ) % fileName % getName().c_str() ),
					e.what()
				);
			}

		}

		// remove the old plug now we're done with it.
		oldPlug->parent()->removeChild( oldPlug );
	}

	// Finish up.

	m_fileName = fileName;
	referenceLoadedSignal()( this );

	if( errors )
	{
		throw Exception( boost::str( boost::format( "Error loading reference \"%s\"" ) % fileName ) );
	}

}

bool Reference::hasMetadataEdit( const Plug *plug, const IECore::InternedString key ) const
{
	return m_plugEdits->hasMetadataEdit( plug, key );
}

bool Reference::isChildEdit( const Plug *plug ) const
{
	return m_plugEdits->isChildEdit( plug );
}

bool Reference::isReferencePlug( const Plug *plug ) const
{
	// If a plug is the descendant of a plug starting with
	// __, and that plug is a direct child of the reference,
	// assume that it is for gaffer's internal use, so would
	// never come directly from a reference. This lines up
	// with the export code in Box::exportForReference(), where
	// such plugs are excluded from the export.

	// find ancestor of p which is a direct child of this node:
	const Plug* ancestorPlug = plug;
	const GraphComponent* parent = plug->parent();
	while( parent != this )
	{
		ancestorPlug = runTimeCast< const Plug >( parent );
		if( !ancestorPlug )
		{
			// Looks like the plug we're looking for doesn't exist,
			// so we exit the loop.
			break;
		}
		parent = ancestorPlug->parent();
	}

	if( ancestorPlug && boost::starts_with( ancestorPlug->getName().c_str(), "__" ) )
	{
		return false;
	}

	// we know this doesn't come from a reference,
	// because it's made during construction.
	if( plug == userPlug() )
	{
		return false;
	}

	// User plugs are not meant to be referenced either. But old
	// versions of Gaffer did export them so we must be careful.
	// Since we make loaded plugs non-dynamic, we can assume that
	// if the plug is dynamic it was added locally by a user
	// rather than loaded from a reference.
	if( ancestorPlug == userPlug() && plug->getFlags( Plug::Dynamic ) )
	{
		return false;
	}
	// everything else must be from a reference then.
	return true;
}
