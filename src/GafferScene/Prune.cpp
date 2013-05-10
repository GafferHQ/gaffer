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

#include "boost/tokenizer.hpp"

#include "Gaffer/Context.h"

#include "GafferScene/Prune.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Prune );

size_t Prune::g_firstPlugIndex = 0;

Prune::Prune( const std::string &name )
	:	FilteredSceneProcessor( name, Filter::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "adjustBounds", Plug::In, false ) );
}

Prune::~Prune()
{
}

Gaffer::BoolPlug *Prune::adjustBoundsPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const Gaffer::BoolPlug *Prune::adjustBoundsPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

void Prune::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	FilteredSceneProcessor::affects( input, outputs );

	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == filterPlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->globalsPlug() );
	}
	else if( input == adjustBoundsPlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
	}
}

void Prune::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( adjustBoundsPlug()->getValue() )
	{
		Filter::Result match = (Filter::Result)filterPlug()->getValue();
		if( match == Filter::DescendantMatch )
		{
			h = hashOfTransformedChildBounds( path, outPlug() );
			return;
		}
	}

	// pass through
	h = inPlug()->boundPlug()->hash();
}

void Prune::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->transformPlug()->hash();
}

void Prune::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->attributesPlug()->hash();
}

void Prune::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = inPlug()->objectPlug()->hash();
}

void Prune::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	Filter::Result match = (Filter::Result)filterPlug()->getValue();
	if( match == Filter::DescendantMatch )
	{
		// we might be computing new childnames for this level.
		FilteredSceneProcessor::hashChildNames( path, context, parent, h );
		inPlug()->childNamesPlug()->hash( h );
		filterPlug()->hash( h );
	}
	else
	{
		// pass through
		h = inPlug()->childNamesPlug()->hash();
	}
}

void Prune::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	FilteredSceneProcessor::hashGlobals( context, parent, h );
	inPlug()->globalsPlug()->hash( h );
	filterPlug()->hash( h );
}

Imath::Box3f Prune::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( adjustBoundsPlug()->getValue() )
	{
		Filter::Result match = (Filter::Result)filterPlug()->getValue();
		if( match == Filter::DescendantMatch )
		{
			return unionOfTransformedChildBounds( path, outPlug() );
		}
	}
	
	return inPlug()->boundPlug()->getValue();
}

Imath::M44f Prune::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->transformPlug()->getValue();
}

IECore::ConstCompoundObjectPtr Prune::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->attributesPlug()->getValue();
}

IECore::ConstObjectPtr Prune::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return inPlug()->objectPlug()->getValue();
}

IECore::ConstInternedStringVectorDataPtr Prune::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	Filter::Result match = (Filter::Result)filterPlug()->getValue();
	if( match == Filter::DescendantMatch )
	{
		// we may need to delete one or more of our children
		ConstInternedStringVectorDataPtr inputChildNamesData = inPlug()->childNamesPlug()->getValue();
		const vector<InternedString> &inputChildNames = inputChildNamesData->readable();
		
		InternedStringVectorDataPtr outputChildNamesData = new InternedStringVectorData;
		vector<InternedString> &outputChildNames = outputChildNamesData->writable();
		
		ContextPtr tmpContext = new Context( *Context::current() );
		Context::Scope scopedContext( tmpContext );

		ScenePath childPath = path;
		childPath.push_back( InternedString() ); // for the child name
		for( vector<InternedString>::const_iterator it = inputChildNames.begin(), eIt = inputChildNames.end(); it != eIt; it++ )
		{
			childPath[path.size()] = *it;
			tmpContext->set( ScenePlug::scenePathContextName, childPath );
			if( filterPlug()->getValue() != Filter::Match )
			{
				outputChildNames.push_back( *it );
			}
		}
		
		return outputChildNamesData;
	}
	else
	{
		// pass through
		return inPlug()->childNamesPlug()->getValue();
	}
}

IECore::ConstCompoundObjectPtr Prune::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;

	ConstCompoundObjectPtr inputGlobals = inPlug()->globalsPlug()->getValue();
	const CompoundData *inputForwardDeclarations = inputGlobals->member<CompoundData>( "gaffer:forwardDeclarations" );
	if( !inputForwardDeclarations )
	{
		return inputGlobals;
	}
	
	ContextPtr tmpContext = new Context( *Context::current() );
	Context::Scope scopedContext( tmpContext );

	CompoundDataPtr outputForwardDeclarations = new CompoundData;
	ScenePath path;
	for( CompoundDataMap::const_iterator it = inputForwardDeclarations->readable().begin(), eIt = inputForwardDeclarations->readable().end(); it != eIt; it++ )
	{
		path.clear();
		Tokenizer pathTokenizer( it->first.string(), boost::char_separator<char>( "/" ) );	
		for( Tokenizer::const_iterator tIt = pathTokenizer.begin(), etIt = pathTokenizer.end(); tIt != etIt; tIt++ )
		{
			path.push_back( *tIt );
		}
		tmpContext->set( ScenePlug::scenePathContextName, path );
		/// \todo We really need to take into account ancestor matches here too, to remove
		/// items whose ancestor has been pruned, but the Filter classes don't provide that
		/// information yet.
		if( filterPlug()->getValue() != Filter::Match )
		{
			outputForwardDeclarations->writable()[it->first] = it->second;
		}
	}
	
	CompoundObjectPtr outputGlobals = inputGlobals->copy();
	outputGlobals->members()["gaffer:forwardDeclarations"] = outputForwardDeclarations;
	return outputGlobals;
}
