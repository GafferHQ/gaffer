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

#include "boost/format.hpp"
#include "boost/algorithm/string/replace.hpp"
#include "boost/regex.hpp"

#include "Gaffer/Box.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/PlugIterator.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/CompoundPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Metadata.h"

using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Box );

Box::Box( const std::string &name )
	:	Node( name )
{
}

Box::~Box()
{
}

bool Box::canPromotePlug( const Plug *descendantPlug ) const
{
	return validatePromotability( descendantPlug, false );
}

Plug *Box::promotePlug( Plug *descendantPlug )
{
	validatePromotability( descendantPlug, true );

	std::string externalPlugName = descendantPlug->relativeName( this );
	boost::replace_all( externalPlugName, ".", "_" );

	PlugPtr externalPlug = descendantPlug->createCounterpart( externalPlugName, Plug::In );
	externalPlug->setFlags( Plug::Dynamic, true );
	// flags are not automatically propagated to the children of compound plugs,
	// so we need to do that ourselves.
	if( externalPlug->typeId() == Gaffer::CompoundPlug::staticTypeId() )
	{
		for( RecursivePlugIterator it( externalPlug ); it != it.end(); ++it )
		{
			(*it)->setFlags( Plug::Dynamic, true );
			if( (*it)->typeId() != Gaffer::CompoundPlug::staticTypeId() )
			{
				it.prune();
			}
		}
	}

	ValuePlug *externalValuePlug = IECore::runTimeCast<ValuePlug>( externalPlug );
	if( externalValuePlug )
	{
		externalValuePlug->setFrom( static_cast<ValuePlug *>( descendantPlug ) );
	}

	userPlug()->addChild( externalPlug );
	descendantPlug->setInput( externalPlug );

	return externalPlug.get();
}

bool Box::plugIsPromoted( const Plug *descendantPlug ) const
{
	if( !descendantPlug )
	{
		return false;
	}
	const Plug *input = descendantPlug->getInput<Plug>();
	return input && input->node() == this;
}

void Box::unpromotePlug( Plug *promotedDescendantPlug )
{
	if( !plugIsPromoted( promotedDescendantPlug ) )
	{
		if( promotedDescendantPlug )
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot unpromote plug \"%s\" as it has not been promoted." ) % promotedDescendantPlug->fullName()
				)
			);
		}
		else
		{
			throw IECore::Exception( "Cannot unpromote null plug" );
		}
	}
	
	Plug *inputPlug = promotedDescendantPlug->getInput<Plug>();
	promotedDescendantPlug->setInput( 0 );

	// remove the top level plug that provided the input, but only if
	// all the children are unused too in the case of a compound plug.
	bool remove = true;
	Plug *plugToRemove = inputPlug;
	while( plugToRemove->parent<Plug>() && plugToRemove->parent<Plug>() != userPlug() )
	{
		plugToRemove = plugToRemove->parent<Plug>();
		for( PlugIterator it( plugToRemove ); it != it.end(); ++it )
		{
			if( (*it)->outputs().size() )
			{
				remove = false;
				break;
			}
		}
	}
	if( remove )
	{
		plugToRemove->parent<GraphComponent>()->removeChild( plugToRemove );
	}
}

bool Box::validatePromotability( const Plug *descendantPlug, bool throwExceptions, bool checkNode ) const
{
	if( !descendantPlug )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(  "Cannot promote null plug" );
		}
	}
	
	if( descendantPlug->direction() != Plug::In )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot promote plug \"%s\" as it is not an input plug." ) % descendantPlug->fullName()
				)
			);
		}
	}

	if( descendantPlug->getFlags( Plug::ReadOnly ) )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot promote plug \"%s\" as it is read only." ) % descendantPlug->fullName()
				)
			);
		}
	}

	if( !descendantPlug->getFlags( Plug::Serialisable ) )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot promote plug \"%s\" as it is not serialisable." ) % descendantPlug->fullName()
				)
			);
		}
	}
	
	if( !descendantPlug->getFlags( Plug::AcceptsInputs ) )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot promote plug \"%s\" as it does not accept inputs." ) % descendantPlug->fullName()
				)
			);
		}
	}

	if( descendantPlug->getInput<Plug>() )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot promote plug \"%s\" as it already has an input." ) % descendantPlug->fullName()
				)
			);
		}
	}

	if( checkNode )
	{
		const Node *descendantNode = descendantPlug->node();
		if( !descendantNode || descendantNode->parent<Node>() != this )
		{
			if( !throwExceptions )
			{
				return false;
			}
			else
			{
				throw IECore::Exception(
					boost::str(
						boost::format( "Cannot promote plug \"%s\" as its node is not a child of \"%s\"." ) % descendantPlug->fullName() % fullName()
					)
				);
			}
		}
	}
	
	// check all the children of this plug too
	for( RecursivePlugIterator it( descendantPlug ); it != it.end(); ++it )
	{
		// no need to check the node, because we've already done that ourselves
		if( !validatePromotability( it->get(), throwExceptions, false ) )
		{
			return false;
		}
	}

	return true;
}

const IECore::Data *Box::getPlugMetadata( const Plug *plug, IECore::InternedString key ) const
{
	PlugMetadataMap::const_iterator it = m_plugMetadata.find( plug );
	if( it == m_plugMetadata.end() )
	{
		return NULL;
	}
	return it->second->member<IECore::Data>( key );
}

void Box::setPlugMetadata( const Plug *plug, IECore::InternedString key, IECore::ConstDataPtr value )
{
	IECore::CompoundDataPtr data;
	PlugMetadataMap::const_iterator it = m_plugMetadata.find( plug );
	if( it == m_plugMetadata.end() )
	{
		data = new IECore::CompoundData;
		m_plugMetadata[plug] = data;
	}
	else
	{
		data = it->second;
	}
	data->writable()[key] = IECore::constPointerCast<IECore::Data>( value );
}

void Box::exportForReference( const std::string &fileName ) const
{
	const ScriptNode *script = scriptNode();
	if( !script )
	{
		throw IECore::Exception( "Box::exportForReference called without ScriptNode" );
	}
	
	// we only want to save out our child nodes and plugs that are visible in the UI, so we build a filter
	// to specify just the things to export.
	
	boost::regex invisiblePlug( "^__.*$" );
	StandardSetPtr toExport = new StandardSet;
	for( ChildIterator it = children().begin(), eIt = children().end(); it != eIt; ++it )
	{
		if( (*it)->isInstanceOf( Node::staticTypeId() ) )
		{
			toExport->add( *it );
		}
		else if( const Plug *plug = IECore::runTimeCast<Plug>( it->get() ) )
		{
			if( !boost::regex_match( plug->getName().c_str(), invisiblePlug ) )
			{
				toExport->add( *it );	
			}
		}
	}
	
	script->serialiseToFile( fileName, this, toExport.get() );

}

BoxPtr Box::create( Node *parent, const Set *childNodes )
{
	BoxPtr result = new Box;
	parent->addChild( result );

	// it's pretty natural to call this function passing childNodes == ScriptNode::selection().
	// unfortunately nodes will be removed from the selection as we reparent
	// them, so we have to make a copy of childNodes so our iteration isn't befuddled by
	// the changing contents. we can use this opportunity to weed out anything in childNodes
	// which isn't a direct child of parent though.
	StandardSetPtr verifiedChildNodes = new StandardSet();
	for( NodeIterator nodeIt( parent ); nodeIt != nodeIt.end(); nodeIt++ )
	{
		if( childNodes->contains( nodeIt->get() ) )
		{
			verifiedChildNodes->add( *nodeIt );
		}
	}
	
	// when a node we're putting in the box has connections to
	// a node remaining outside, we need to reroute the connection
	// via an intermediate plug on the box. this mapping maps input
	// plugs (be they internal or external) to intermediate input plugs.
	typedef std::pair<const Plug *, Plug *> PlugPair;
	typedef std::map<const Plug *, Plug *> PlugMap;
	PlugMap plugMap;

	for( size_t i = 0, e = verifiedChildNodes->size(); i < e; i++ )
	{		
		Node *childNode = static_cast<Node *>( verifiedChildNodes->member( i ) );
		// reroute any connections to external nodes
		for( RecursivePlugIterator plugIt( childNode ); plugIt != plugIt.end(); plugIt++ )
		{
			Plug *plug = plugIt->get();
			if( plug->direction() == Plug::In )
			{
				Plug *input = plug->getInput<Plug>();
				if( input && !verifiedChildNodes->contains( input->node() ) )
				{
					PlugMap::const_iterator mapIt = plugMap.find( input );
					if( mapIt == plugMap.end() )
					{
						PlugPtr intermediateInput = plug->createCounterpart( "in", Plug::In );
						// we want intermediate inputs to appear on the same side of the node as the
						// equivalent internal plug, so we copy the relevant metadata over.
						result->setPlugMetadata( intermediateInput, "nodeGadget:nodulePosition", Metadata::plugValue<IECore::Data>( plug, "nodeGadget:nodulePosition" ) );
						intermediateInput->setFlags( Plug::Dynamic, true );
						result->addChild( intermediateInput );
						intermediateInput->setInput( input );
						mapIt = plugMap.insert( PlugPair( input, intermediateInput.get() ) ).first;
					}
					plug->setInput( mapIt->second );
					plugIt.prune();
				}
			}
			else
			{
				// take a copy of the outputs, because we might be modifying the
				// original as we iterate.
				Plug::OutputContainer outputs = plug->outputs();
				if( !outputs.empty() )
				{
					typedef Plug::OutputContainer::const_iterator OutputIterator;
					for( OutputIterator oIt = outputs.begin(), eIt = outputs.end(); oIt != eIt; oIt++ )
					{
						Plug *output = *oIt;
						const Node *outputNode = output->node();
						if( outputNode->parent<Node>() == parent && !verifiedChildNodes->contains( outputNode ) )
						{
							PlugMap::const_iterator mapIt = plugMap.find( plug );
							if( mapIt == plugMap.end() )
							{
								PlugPtr intermediateOutput = plug->createCounterpart( "out", Plug::Out );
								result->setPlugMetadata( intermediateOutput, "nodeGadget:nodulePosition", Metadata::plugValue<IECore::Data>( plug, "nodeGadget:nodulePosition" ) );
								intermediateOutput->setFlags( Plug::Dynamic, true );
								result->addChild( intermediateOutput );
								intermediateOutput->setInput( plug );
								mapIt = plugMap.insert( PlugPair( plug, intermediateOutput.get() ) ).first;
							}
							output->setInput( mapIt->second );
						}
					}
					plugIt.prune();
				}
			}
		}
		// reparent the child under the Box. it's important that we do this after adding the intermediate
		// input plugs, so that when they are serialised and reloaded, the inputs to the box are set before
		// the inputs to the nodes inside the box - see GafferSceneTest.ShaderAssignmentTest.testAssignShaderFromOutsideBox
		// for a test case highlighting this necessity.
		result->addChild( childNode );
	}

	return result;
}

//////////////////////////////////////////////////////////////////////////
// Metadata registration
// We use this to make the per-instance Box metadata available through
// the standard Metadata query system.
//////////////////////////////////////////////////////////////////////////

namespace // anonymous
{

IECore::ConstDataPtr boxPlugMetadata( const Plug *plug, IECore::InternedString key )
{
	const Box *box = static_cast<const Box *>( plug->node() );
	IECore::ConstDataPtr value = box->getPlugMetadata( plug, key );
	if( value )
	{
		return value;
	}
	
	return NULL;
}

int registerMetadata()
{
	/// \todo Perhaps if Metadata::registerPlugValue() allowed match strings for keys
	/// as well as plugs, we wouldn't need to loop over an explicit list of keys.
	const char *keys[] = { "description", "nodeGadget:nodulePosition", NULL };
	for( const char **key = keys; *key; key++ )
	{
		Metadata::registerPlugValue( Box::staticTypeId(), boost::regex( ".*" ), *key, boost::bind( boxPlugMetadata, ::_1, *key ) );
	}
	return 0;
}

int registration = registerMetadata();

} // namespace anonymous
