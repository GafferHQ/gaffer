//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2015, Image Engine Design Inc. All rights reserved.
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
#include "boost/algorithm/string/predicate.hpp"
#include "boost/regex.hpp"

#include "Gaffer/Box.h"
#include "Gaffer/StandardSet.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/ScriptNode.h"
#include "Gaffer/Metadata.h"
#include "Gaffer/Context.h"

using namespace std;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Box );

Box::Box( const std::string &name )
	:	SubGraph( name )
{
}

Box::~Box()
{
}

bool Box::canPromotePlug( const Plug *descendantPlug ) const
{
	return validatePromotability( descendantPlug, /* throwExceptions = */ false );
}

Plug *Box::promotePlug( Plug *descendantPlug )
{
	validatePromotability( descendantPlug, /* throwExceptions = */ true );

	PlugPtr externalPlug = descendantPlug->createCounterpart( promotedCounterpartName( descendantPlug ), descendantPlug->direction() );
	externalPlug->setFlags( Plug::Dynamic, true );
	// Flags are not automatically propagated to the children of compound plugs,
	// so we need to do that ourselves. We don't want to propagate them to the
	// children of plug types which create the children themselves during
	// construction though, hence the typeId checks for the base classes
	// which add no children during construction. I'm not sure this approach is
	// necessarily the best - the alternative would be to set everything dynamic
	// unconditionally and then implement Serialiser::childNeedsConstruction()
	// for types like CompoundNumericPlug that create children in their constructors.
	const Gaffer::TypeId compoundTypes[] = { PlugTypeId, ValuePlugTypeId, CompoundPlugTypeId, ArrayPlugTypeId };
	const Gaffer::TypeId *compoundTypesEnd = compoundTypes + 4;
	if( find( compoundTypes, compoundTypesEnd, (Gaffer::TypeId)externalPlug->typeId() ) != compoundTypesEnd )
	{
		for( RecursivePlugIterator it( externalPlug.get() ); !it.done(); ++it )
		{
			(*it)->setFlags( Plug::Dynamic, true );
			if( find( compoundTypes, compoundTypesEnd, (Gaffer::TypeId)(*it)->typeId() ) != compoundTypesEnd )
			{
				it.prune();
			}
		}
	}

	if( externalPlug->direction() == Plug::In )
	{
		if( ValuePlug *externalValuePlug = IECore::runTimeCast<ValuePlug>( externalPlug.get() ) )
		{
			externalValuePlug->setFrom( static_cast<ValuePlug *>( descendantPlug ) );
		}
	}

	// Copy over the metadata for nodule position, so the nodule appears in the expected spot.
	// This must be done before parenting the new plug, as the nodule is created from childAddedSignal().
	copyMetadata( descendantPlug, externalPlug.get() );

	addChild( externalPlug );

	if( externalPlug->direction() == Plug::In )
	{
		descendantPlug->setInput( externalPlug );
	}
	else
	{
		externalPlug->setInput( descendantPlug );
	}

	return externalPlug.get();
}

bool Box::plugIsPromoted( const Plug *descendantPlug ) const
{
	if( !descendantPlug )
	{
		return false;
	}

	if( descendantPlug->direction() == Plug::In )
	{
		const Plug *input = descendantPlug->getInput<Plug>();
		return input && input->node() == this;
	}
	else
	{
		for( Plug::OutputContainer::const_iterator it = descendantPlug->outputs().begin(), eIt = descendantPlug->outputs().end(); it != eIt; ++it )
		{
			if( (*it)->node() == this )
			{
				return true;
			}
		}
		return false;
	}
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

	Plug *externalPlug = NULL;
	if( promotedDescendantPlug->direction() == Plug::In )
	{
		externalPlug = promotedDescendantPlug->getInput<Plug>();
		promotedDescendantPlug->setInput( NULL );
	}
	else
	{
		for( Plug::OutputContainer::const_iterator it = promotedDescendantPlug->outputs().begin(), eIt = promotedDescendantPlug->outputs().end(); it != eIt; ++it )
		{
			if( (*it)->node() == this )
			{
				externalPlug = *it;
				break;
			}
		}
		assert( externalPlug ); // should be true because we checked plugIsPromoted()
		externalPlug->setInput( NULL );
	}

	// remove the top level external plug , but only if
	// all the children are unused too in the case of a compound plug.
	bool remove = true;
	Plug *plugToRemove = externalPlug;
	while( plugToRemove->parent<Plug>() && plugToRemove->parent<Plug>() != userPlug() )
	{
		plugToRemove = plugToRemove->parent<Plug>();
		for( PlugIterator it( plugToRemove ); !it.done(); ++it )
		{
			if(
				( (*it)->direction() == Plug::In && (*it)->outputs().size() ) ||
				( (*it)->direction() == Plug::Out && (*it)->getInput<Plug>() )
			)
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

bool Box::validatePromotability( const Plug *descendantPlug, bool throwExceptions, bool childPlug ) const
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

	if( plugIsPromoted( descendantPlug ) )
	{
		if( !throwExceptions )
		{
			return false;
		}
		else
		{
			throw IECore::Exception(
				boost::str(
					boost::format( "Cannot promote plug \"%s\" as it is already promoted." ) % descendantPlug->fullName()
				)
			);
		}
	}

	if( descendantPlug->direction() == Plug::In )
	{
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

		// The plug must be serialisable, as we need its input to be saved,
		// but we only need to check this for the topmost plug and not for
		// children, because a setInput() call for a parent plug will also
		// restore child inputs.
		if( !childPlug && !descendantPlug->getFlags( Plug::Serialisable ) )
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
	}

	if( !childPlug )
	{
		// check that the node holding the plug is actually in the box!
		// we only do this when childPlug==false, because when it is true,
		// we'll have already checked in an earlier call.
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
	for( RecursivePlugIterator it( descendantPlug ); !it.done(); ++it )
	{
		if( !validatePromotability( it->get(), throwExceptions, /* childPlug = */ true ) )
		{
			return false;
		}
	}

	return true;
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
			if(
				!boost::regex_match( plug->getName().c_str(), invisiblePlug )
				&& plug != userPlug()
			)
			{
				toExport->add( *it );
			}
		}
	}

	ContextPtr context = new Context;
	context->set( "valuePlugSerialiser:resetParentPlugDefaults", true );
	context->set( "serialiser:includeParentMetadata", true );
	Context::Scope scopedContext( context.get() );

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
	for( NodeIterator nodeIt( parent ); !nodeIt.done(); ++nodeIt )
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
		for( RecursivePlugIterator plugIt( childNode ); !plugIt.done(); ++plugIt )
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
						PlugPtr intermediateInput = plug->createCounterpart( result->promotedCounterpartName( plug ), Plug::In );
						// we want intermediate inputs to appear on the same side of the node as the
						// equivalent internal plug, so we copy the relevant metadata over.
						copyMetadata( plug, intermediateInput.get() );
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
								PlugPtr intermediateOutput = plug->createCounterpart( result->promotedCounterpartName( plug ), Plug::Out );
								copyMetadata( plug, intermediateOutput.get() );
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

std::string Box::promotedCounterpartName( const Plug *plug ) const
{
	std::string result = plug->relativeName( plug->node() );
	boost::replace_all( result, ".", "_" );
	return result;
}

void Box::copyMetadata( const Plug *from, Plug *to )
{
	/// \todo Perhaps we should have a more dynamic mechanism for mirroring all metadata?
	/// If we could register a dynamic metadata value for "*", then we could just answer
	/// all metadata queries on the fly - would that be a good idea? We'd need to figure
	/// out how to make it compatible with Metadata::registeredPlugValues(), which needs to
	/// know all valid names. We'd also need to put a lot of thought into how we allowed the
	/// user to delete values which were being mirrored dynamically.
	vector<IECore::InternedString> keys;
	Metadata::registeredValues( from, keys, /* instanceOnly = */ false, /* persistentOnly = */ true );
	for( vector<IECore::InternedString>::const_iterator it = keys.begin(), eIt = keys.end(); it != eIt; ++it )
	{
		if( boost::starts_with( it->string(), "layout:" ) )
		{
			// Don't want to copy layout metadata because the user will be making their own layout.
			continue;
		}
		Metadata::registerValue( to, *it, Metadata::value<IECore::Data>( from, *it ) );
	}

	for( PlugIterator it( from ); !it.done(); ++it )
	{
		if( Plug *childTo = to->getChild<Plug>( (*it)->getName() ) )
		{
			copyMetadata( it->get(), childTo );
		}
	}
}
