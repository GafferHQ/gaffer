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

#include "IECore/Exception.h"

#include "Gaffer/Reference.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/CompoundPlug.h"

using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Reference );

size_t Reference::g_firstPlugIndex = 0;

Reference::Reference( const std::string &name )
	:	Node( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "fileName", Plug::In, "", Plug::Default & ~Plug::AcceptsInputs ) );	
}

Reference::~Reference()
{
}


StringPlug *Reference::fileNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const StringPlug *Reference::fileNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

void Reference::load( const std::string &fileName )
{
	ScriptNode *script = scriptNode();
	if( !script )
	{
		throw IECore::Exception( "Reference::load called without ScriptNode" );
	}
	
	// if we're doing a reload, then we want to maintain any values and
	// connections that our external plugs might have. but we also need to
	// get those existing plugs out of the way during the load, so that the
	// incoming plugs don't get renamed.
	
	std::map<std::string, Plug *> previousPlugs;
	for( PlugIterator it( this ); it != it.end(); ++it )
	{
		Plug *plug = it->get();
		if( isReferencePlug( plug ) )
		{
			previousPlugs[plug->getName()] = plug;
			plug->setName( "__tmp__" + plug->getName().string() );
		}
	}

	for( PlugIterator it( userPlug() ); it != it.end(); ++it )
	{
		Plug *plug = it->get();
		previousPlugs[plug->relativeName( this )] = plug;
		plug->setName( "__tmp__" + plug->getName().string() );
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
	
	// load the reference
	
	script->executeFile( fileName, this );
	fileNamePlug()->setValue( fileName );

	// sort out any conflicts between the old and new plugs, preferring to reuse
	// the old ones wherever possible so that the node remains identical from the
	// outside and old connections and values are preserved.
	
	for( std::map<std::string, Plug *>::const_iterator it = previousPlugs.begin(), eIt = previousPlugs.end(); it != eIt; ++it )
	{
		Plug *oldPlug = it->second;
		Plug *newPlug = descendant<Plug>( it->first );
		if( newPlug )
		{
			if( oldPlug->direction() == newPlug->direction() && oldPlug->typeId() == newPlug->typeId() )
			{
				// assume plugs are compatible and we can reuse the old one in place of the new one.
				/// \todo really we need a better way of guaranteeing compatibility that takes into account
				/// default values and the like.
				if( newPlug->direction() == Plug::In )
				{
					for( Plug::OutputContainer::const_iterator oIt = newPlug->outputs().begin(), oeIt = newPlug->outputs().end(); oIt != oeIt;  )
					{
						Plug *outputPlug = *oIt;
						++oIt; // increment now because the setInput() call invalidates our iterator.
						outputPlug->setInput( oldPlug );
					}
				}
				else
				{
					Plug *newInput = newPlug->getInput<Plug>();
					if( newInput )
					{
						oldPlug->setInput( newInput );
					}
				}
				InternedString name = newPlug->getName();
				newPlug->parent<GraphComponent>()->removeChild( newPlug );
				oldPlug->setName( name );
			}
			else
			{
				// plugs are incompatible - erase the old one and keep the new one.
				it->second->parent<GraphComponent>()->removeChild( oldPlug );		
			}
		}
		else
		{
			// no corresponding new plug - remove the old one because it was
			// removed in the referenced file.
			it->second->parent<GraphComponent>()->removeChild( oldPlug );	
		}
		
	}
	
	// make the loaded plugs non-dynamic, because we don't want them
	// to be serialised in the script the reference is in - the whole
	// point is that they are referenced.
	
	for( RecursivePlugIterator it( this ); it != it.end(); ++it )
	{
		if( isReferencePlug( it->get() ) )
		{
			(*it)->setFlags( Plug::Dynamic, false );
		}
	}
	
}

bool Reference::isReferencePlug( const Plug *plug ) const
{
	// we consider a plug to be a reference plug if it has connections to nodes within the reference.
	if( plug->direction() == Plug::In )
	{
		for( Plug::OutputContainer::const_iterator it = plug->outputs().begin(), eIt = plug->outputs().end(); it != eIt; ++it )
		{
			if( this->isAncestorOf( *it ) )
			{
				return true;
			}
		}
	}
	else
	{
		const Plug *input = plug->getInput<Plug>();
		if( input && this->isAncestorOf( input ) )
		{
			return true;
		}
	}
	return false;
}
