//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferScene/Group.h"

#include "Gaffer/ArrayPlug.h"
#include "Gaffer/Context.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TransformPlug.h"

#include "IECore/CompoundData.h"
#include "IECore/CompoundObject.h"

#include "OpenEXR/ImathBoxAlgo.h"

#include "boost/lexical_cast.hpp"
#include "boost/regex.hpp"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( Group );

size_t Group::g_firstPlugIndex = 0;

Group::Group( const std::string &name )
	:	SceneProcessor( name, 1 )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "name", Plug::In, "group" ) );
	addChild( new TransformPlug( "transform" ) );

	addChild( new Gaffer::ObjectPlug( "__mapping", Gaffer::Plug::Out, new CompoundObject() ) );

	outPlug()->globalsPlug()->setInput( inPlug()->globalsPlug() );
}

Group::~Group()
{
}

ScenePlug *Group::nextInPlug()
{
	return runTimeCast<ScenePlug>( inPlugs()->children().back().get() );
}

const ScenePlug *Group::nextInPlug() const
{
	return runTimeCast<const ScenePlug>( inPlugs()->children().back().get() );
}

Gaffer::StringPlug *Group::namePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Group::namePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::TransformPlug *Group::transformPlug()
{
	return getChild<TransformPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::TransformPlug *Group::transformPlug() const
{
	return getChild<TransformPlug>( g_firstPlugIndex + 1 );
}

Gaffer::ObjectPlug *Group::mappingPlug()
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *Group::mappingPlug() const
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

void Group::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );

	if( input == namePlug() )
	{
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
	else if( const ScenePlug *s = input->parent<ScenePlug>() )
	{
		if( s->parent<ArrayPlug>() == inPlugs() )
		{
			// all input scene plugs children affect the corresponding output child
			outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
			// and the names also affect the mapping
			if( input == s->childNamesPlug() )
			{
				outputs.push_back( mappingPlug() );
			}
		}
	}
	else if( input == mappingPlug() )
	{
		// the mapping affects everything about the output
		for( ValuePlugIterator it( outPlug() ); !it.done(); ++it )
		{
			outputs.push_back( it->get() );
		}
	}

}

void Group::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneProcessor::hash( output, context, h );

	if( output == mappingPlug() )
	{
		ScenePlug::PathScope scope( context, ScenePath() );
		for( ScenePlugIterator it( inPlugs() ); !it.done(); ++it )
		{
			(*it)->childNamesPlug()->hash( h );
		}
	}
}

void Group::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == mappingPlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( computeMapping( context ) );
		return;
	}

	return SceneProcessor::compute( output, context );
}

void Group::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 ) // "/"
	{
		SceneProcessor::hashBound( path, context, parent, h );
		for( ScenePlugIterator it( inPlugs() ); !it.done(); ++it )
		{
			(*it)->boundPlug()->hash( h );
		}
		transformPlug()->hash( h );
	}
	else if( path.size() == 1 ) // "/group"
	{
		SceneProcessor::hashBound( path, context, parent, h );
		ScenePlug::PathScope scope( context, ScenePath() );
		for( ScenePlugIterator it( inPlugs() ); !it.done(); ++it )
		{
			(*it)->boundPlug()->hash( h );
		}
	}
	else // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->boundHash( source );
	}
}

Imath::Box3f Group::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() <= 1 )
	{
		// either / or /groupName
		Box3f combinedBound;
		for( ScenePlugIterator it( inPlugs() ); !it.done(); ++it )
		{
			// we don't need to transform these bounds, because the SceneNode
			// guarantees that the transform for root nodes is always identity.
			Box3f bound = (*it)->bound( ScenePath() );
			combinedBound.extendBy( bound );
		}
		if( path.size() == 0 )
		{
			combinedBound = transform( combinedBound, transformPlug()->matrix() );
		}
		return combinedBound;
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->bound( source );
	}
}

void Group::hashTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 ) // "/"
	{
		SceneProcessor::hashTransform( path, context, parent, h );
	}
	else if( path.size() == 1 ) // "/group"
	{
		SceneProcessor::hashTransform( path, context, parent, h );
		transformPlug()->hash( h );
	}
	else if( path.size() > 1 ) // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->transformHash( source );
	}
}

Imath::M44f Group::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		return Imath::M44f();
	}
	else if( path.size() == 1 )
	{
		return transformPlug()->matrix();
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->transform( source );
	}
}

void Group::hashAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() <= 1 ) // "/" or "/group"
	{
		SceneProcessor::hashAttributes( path, context, parent, h );
	}
	else // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->attributesHash( source );
	}
}

IECore::ConstCompoundObjectPtr Group::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() <= 1 )
	{
		return parent->attributesPlug()->defaultValue();
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->attributes( source );
	}
}

void Group::hashObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() <= 1 ) // "/" or "/group"
	{
		SceneProcessor::hashObject( path, context, parent, h );
	}
	else // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->objectHash( source );
	}
}

IECore::ConstObjectPtr Group::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() <= 1 )
	{
		return parent->objectPlug()->defaultValue();
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->object( source );
	}
}

void Group::hashChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 ) // "/"
	{
		SceneProcessor::hashChildNames( path, context, parent, h );
		namePlug()->hash( h );
	}
	else if( path.size() == 1 ) // "/group"
	{
		SceneProcessor::hashChildNames( path, context, parent, h );
		mappingPlug()->hash( h );
	}
	else // "/group/..."
	{
		// pass through
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		h = sourcePlug->childNamesHash( source );
	}
}

IECore::ConstInternedStringVectorDataPtr Group::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		InternedStringVectorDataPtr result = new InternedStringVectorData();
		result->writable().push_back( namePlug()->getValue() );
		return result;
	}
	else if( path.size() == 1 )
	{
		ScenePlug::GlobalScope s( context );
		ConstCompoundObjectPtr mapping = boost::static_pointer_cast<const CompoundObject>( mappingPlug()->getValue() );
		return mapping->member<InternedStringVectorData>( "__GroupChildNames" );
	}
	else
	{
		const ScenePlug *sourcePlug = nullptr;
		ScenePath source = sourcePath( path, &sourcePlug );
		return sourcePlug->childNames( source );
	}
}

void Group::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSetNames( context, parent, h );
	for( ScenePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		(*it)->setNamesPlug()->hash( h );
	}
}

IECore::ConstInternedStringVectorDataPtr Group::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	InternedStringVectorDataPtr resultData = new InternedStringVectorData;
	vector<InternedString> &result = resultData->writable();
	for( ScenePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		// This naive approach to merging set names preserves the order of the incoming names,
		// but at the expense of using linear search. We assume that the number of sets is small
		// enough and the InternedString comparison fast enough that this is OK.
		ConstInternedStringVectorDataPtr inputSetNamesData = (*it)->setNamesPlug()->getValue();
		const vector<InternedString> &inputSetNames = inputSetNamesData->readable();
		for( vector<InternedString>::const_iterator it = inputSetNames.begin(), eIt = inputSetNames.end(); it != eIt; ++it )
		{
			if( std::find( result.begin(), result.end(), *it ) == result.end() )
			{
				result.push_back( *it );
			}
		}
	}

	return resultData;
}

void Group::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashSet( setName, context, parent, h );
	for( ScenePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		(*it)->setPlug()->hash( h );
	}

	ScenePlug::GlobalScope s( context );
	mappingPlug()->hash( h );
	namePlug()->hash( h );
}

IECore::ConstPathMatcherDataPtr Group::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	InternedString groupName;
	ConstCompoundObjectPtr mapping;
	{
		ScenePlug::GlobalScope s( context );
		groupName = namePlug()->getValue();
		mapping = boost::static_pointer_cast<const CompoundObject>( mappingPlug()->getValue() );
	}
	const ObjectVector *forwardMappings = mapping->member<ObjectVector>( "__GroupForwardMappings", true /* throw if missing */ );

	PathMatcherDataPtr resultData = new PathMatcherData;
	PathMatcher &result = resultData->writable();
	for( size_t i = 0, e = inPlugs()->children().size(); i < e; i++ )
	{
		ConstPathMatcherDataPtr inputSetData = inPlugs()->getChild<ScenePlug>( i )->setPlug()->getValue();
		const PathMatcher &inputSet = inputSetData->readable();

		const CompoundData *forwardMapping = static_cast<const IECore::CompoundData *>( forwardMappings->members()[i].get() );

		// We want our outputSet to reference the data within inputSet rather
		// than do an expensive copy. This is complicated slightly by the fact
		// that we may need to rename the children of the root according to the
		// forwardMapping object. Here we do that by taking subtrees of the input
		// and adding them to our output under a renamed prefix.
		for( PathMatcher::RawIterator pIt = inputSet.begin(), peIt = inputSet.end(); pIt != peIt; ++pIt )
		{
			const vector<InternedString> &inputPath = *pIt;
			if( !inputPath.size() )
			{
				// Skip root.
				continue;
			}
			assert( inputPath.size() == 1 );

			const InternedStringData *outputName = forwardMapping->member<InternedStringData>( inputPath[0], /* throwExceptions = */ true );

			vector<InternedString> prefix;
			prefix.push_back( groupName );
			prefix.push_back( outputName->readable() );
			result.addPaths( inputSet.subTree( inputPath ), prefix );

			pIt.prune(); // We only want to visit the first level
		}
	}

	return resultData;
}

IECore::ObjectPtr Group::computeMapping( const Gaffer::Context *context ) const
{
	/// \todo It might be more optimal to make our own Object subclass better tailored
	/// for passing the information we want.
	CompoundObjectPtr result = new CompoundObject();

	InternedStringVectorDataPtr childNamesData = new InternedStringVectorData();
	vector<InternedString> &childNames = childNamesData->writable();
	result->members()["__GroupChildNames"] = childNamesData;

	ObjectVectorPtr forwardMappings = new ObjectVector;
	result->members()["__GroupForwardMappings"] = forwardMappings;

	boost::regex namePrefixSuffixRegex( "^(.*[^0-9]+)([0-9]+)$" );
	boost::format namePrefixSuffixFormatter( "%s%d" );

	set<InternedString> allNames;
	for( ScenePlugIterator it( inPlugs() ); !it.done(); ++it )
	{
		ConstInternedStringVectorDataPtr inChildNamesData = (*it)->childNames( ScenePath() );
		CompoundDataPtr forwardMapping = new CompoundData;
		forwardMappings->members().push_back( forwardMapping );

		const vector<InternedString> &inChildNames = inChildNamesData->readable();
		for( vector<InternedString>::const_iterator cIt = inChildNames.begin(), ceIt = inChildNames.end(); cIt!=ceIt; cIt++ )
		{
			InternedString name = *cIt;
			if( allNames.find( name ) != allNames.end() )
			{
				// uniqueify the name
				/// \todo This code is almost identical to code in GraphComponent::setName(),
				/// is there a sensible place it can be shared? The primary obstacle is that
				/// each use has a different method of storing the existing names.
				string prefix = name;
				int suffix = 1;

				boost::cmatch match;
				if( regex_match( name.value().c_str(), match, namePrefixSuffixRegex ) )
				{
					prefix = match[1];
					suffix = boost::lexical_cast<int>( match[2] );
				}

				do
				{
					name = boost::str( namePrefixSuffixFormatter % prefix % suffix );
					suffix++;
				} while( allNames.find( name ) != allNames.end() );
			}

			allNames.insert( name );
			childNames.push_back( name );
			forwardMapping->writable()[*cIt] = new InternedStringData( name );

			CompoundObjectPtr entry = new CompoundObject;
			entry->members()["n"] = new InternedStringData( *cIt );
			entry->members()["i"] = new IntData( it.base() - inPlugs()->children().begin() );
			result->members()[name] = entry;
		}
	}

	return result;
}

SceneNode::ScenePath Group::sourcePath( const ScenePath &outputPath, const ScenePlug **source ) const
{
	const InternedString mappedChildName = outputPath[1];

	ConstCompoundObjectPtr mapping;
	{
		ScenePlug::GlobalScope s( Context::current() );
		mapping = boost::static_pointer_cast<const CompoundObject>( mappingPlug()->getValue() );
	}
	const CompoundObject *entry = mapping->member<CompoundObject>( mappedChildName );
	if( !entry )
	{
		string outputPathString;
		ScenePlug::pathToString( outputPath, outputPathString );
		throw Exception( boost::str( boost::format( "Unable to find mapping for output path \"%s\"" ) % outputPathString ) );
	}

	*source = inPlugs()->getChild<ScenePlug>( entry->member<IntData>( "i" )->readable() );

	ScenePath result;
	result.reserve( outputPath.size() - 1 );
	result.push_back( entry->member<InternedStringData>( "n" )->readable() );
	result.insert( result.end(), outputPath.begin() + 2, outputPath.end() );
	return result;
}
