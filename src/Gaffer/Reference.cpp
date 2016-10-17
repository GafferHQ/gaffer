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

#include "boost/algorithm/string/predicate.hpp"
#include "boost/bind.hpp"

#include "IECore/Exception.h"
#include "IECore/MessageHandler.h"

#include "Gaffer/Reference.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/StandardSet.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Reference );

Reference::Reference( const std::string &name )
	:	SubGraph( name )
{
}

Reference::~Reference()
{
}

void Reference::load( const std::string &fileName )
{
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
	UndoContext undoDisabler( script, UndoContext::Disabled );

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
	if( !fileName.empty() )
	{
		errors = script->executeFile( fileName, this, /* continueOnError = */ true );
	}

	// Do a little bit of post processing on everything that was loaded.

	for( size_t i = 0, e = newChildren->size(); i < e; ++i )
	{
		if( Plug *plug = runTimeCast<Plug>( newChildren->member( i ) ) )
		{
			// Make the loaded plugs non-dynamic, because we don't want them
			// to be serialised in the script the reference is in - the whole
			// point is that they are referenced. For the same reason, make
			// their instance metadata non-persistent.
			plug->setFlags( Plug::Dynamic, false );
			convertPersistentMetadata( plug );
			for( RecursivePlugIterator it( plug ); !it.done(); ++it )
			{
				(*it)->setFlags( Plug::Dynamic, false );
				convertPersistentMetadata( it->get() );
			}
		}
		else if( Node *node = runTimeCast<Node>( newChildren->member( i ) ) )
		{
			// Make the loaded nodes read-only as far as the UI is
			// concerned, because any changes the user did make
			// would be lost on save/reload. We use non-persistent
			// metadata for this so that they can copy/paste nodes
			// out of the reference and have the copies be editable.
			setReadOnly( node, true, /* persistent = */ false );
		}
	}

	// figure out what version of gaffer was used to save the reference. prior to
	// version 0.9.0.0, references could contain setValue() calls for promoted plugs,
	// and we must make sure they don't clobber the user-set values on the reference node.
	int milestoneVersion = 0;
	int majorVersion = 0;
	if( IECore::ConstIntDataPtr v = Metadata::value<IECore::IntData>( this, "serialiser:milestoneVersion" ) )
	{
		milestoneVersion = v->readable();
	}
	if( IECore::ConstIntDataPtr v = Metadata::value<IECore::IntData>( this, "serialiser:majorVersion" ) )
	{
		majorVersion = v->readable();
	}
	const bool versionPriorTo09 = milestoneVersion == 0 && majorVersion < 9;

	// Transfer connections, values and metadata from the old plugs onto the corresponding new ones.

	for( std::map<std::string, Plug *>::const_iterator it = previousPlugs.begin(), eIt = previousPlugs.end(); it != eIt; ++it )
	{
		Plug *oldPlug = it->second;
		Plug *newPlug = descendant<Plug>( it->first );
		if( newPlug )
		{
			try
			{
				if( newPlug->direction() == Plug::In && oldPlug->direction() == Plug::In )
				{
					if( Plug *oldInput = oldPlug->getInput<Plug>() )
					{
						newPlug->setInput( oldInput );
					}
					else
					{
						ValuePlug *oldValuePlug = runTimeCast<ValuePlug>( oldPlug );
						ValuePlug *newValuePlug = runTimeCast<ValuePlug>( newPlug );
						if( oldValuePlug && newValuePlug )
						{
							if( versionPriorTo09 || !oldValuePlug->isSetToDefault() )
							{
								newValuePlug->setFrom( oldValuePlug );
							}
						}
					}
				}
				else if( newPlug->direction() == Plug::Out && oldPlug->direction() == Plug::Out )
				{
					for( Plug::OutputContainer::const_iterator oIt = oldPlug->outputs().begin(), oeIt = oldPlug->outputs().end(); oIt != oeIt;  )
					{
						Plug *outputPlug = *oIt;
						++oIt; // increment now because the setInput() call invalidates our iterator.
						outputPlug->setInput( newPlug );
					}
				}
				transferPersistentMetadata( oldPlug, newPlug );
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
		oldPlug->parent<GraphComponent>()->removeChild( oldPlug );
	}

	// Finish up.

	m_fileName = fileName;
	referenceLoadedSignal()( this );

	if( errors )
	{
		throw Exception( boost::str( boost::format( "Error loading reference \"%s\"" ) % fileName ) );
	}

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
	const GraphComponent* parent = plug->parent<GraphComponent>();
	while( parent != this )
	{
		ancestorPlug = runTimeCast< const Plug >( parent );
		if( !ancestorPlug )
		{
			// Looks like the plug we're looking for doesn't exist,
			// so we exit the loop.
			break;
		}
		parent = ancestorPlug->parent<GraphComponent>();
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

void Reference::convertPersistentMetadata( Plug *plug ) const
{
	vector<InternedString> keys;
	Metadata::registeredValues( plug, keys, /* instanceOnly = */ true, /* persistentOnly = */ true );
	for( vector<InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		ConstDataPtr value = Metadata::value<Data>( plug, *it );
		Metadata::registerValue( plug, *it, value, /* persistent = */ false );
	}
}

void Reference::transferPersistentMetadata( const Plug *srcPlug, Plug *dstPlug ) const
{
	vector<InternedString> keys;
	Metadata::registeredValues( srcPlug, keys, /* instanceOnly = */ true, /* persistentOnly = */ true );
	for( vector<InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		ConstDataPtr value = Metadata::value<Data>( srcPlug, *it );
		Metadata::registerValue( dstPlug, *it, value );
	}

	for( PlugIterator it( srcPlug ); !it.done(); ++it )
	{
		if( Plug *dstChildPlug = dstPlug->getChild<Plug>( (*it)->getName() ) )
		{
			transferPersistentMetadata( it->get(), dstChildPlug );
		}
	}
}
