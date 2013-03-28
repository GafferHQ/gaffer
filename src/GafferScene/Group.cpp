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

#include <set>

#include "boost/bind.hpp"
#include "boost/regex.hpp"
#include "boost/lexical_cast.hpp"

#include "OpenEXR/ImathBoxAlgo.h"

#include "IECore/CompoundObject.h"

#include "Gaffer/Context.h"
#include "Gaffer/BlockedConnection.h"

#include "GafferScene/Group.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Group );

size_t Group::g_firstPlugIndex = 0;

Group::Group( const std::string &name )
	:	SceneProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	
	addChild( new StringPlug( "name", Plug::In, "group" ) );
	addChild( new TransformPlug( "transform" ) );
	
	addChild( new Gaffer::ObjectPlug( "__mapping", Gaffer::Plug::Out, new CompoundObject() ) );
	addChild( new Gaffer::ObjectPlug( "__inputMapping", Gaffer::Plug::In, new CompoundObject(), Gaffer::Plug::Default & ~Gaffer::Plug::Serialisable ) );
	inputMappingPlug()->setInput( mappingPlug() );
	
	m_plugInputChangedConnection = plugInputChangedSignal().connect( boost::bind( &Group::plugInputChanged, this, ::_1 ) );
	childAddedSignal().connect( boost::bind( &Group::childAdded, this, ::_1, ::_2 ) );
}

Group::~Group()
{
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

void Group::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	if( input == namePlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
	else if( input == inputMappingPlug() )
	{
		for( ValuePlugIterator it( outPlug() ); it != it.end(); it++ )
		{
			outputs.push_back( it->get() );
		}
	}
	else if( const ScenePlug *s = input->parent<ScenePlug>() )
	{
		// all input scene plugs affect the output
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) )
		;		
		if( input == s->childNamesPlug() )
		{
			outputs.push_back( mappingPlug() );
		}
	}
	
}

void Group::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{	
	SceneProcessor::hash( output, context, h );

	if( output == mappingPlug() )
	{
		ContextPtr tmpContext = new Context( *Context::current() );
		tmpContext->set( ScenePlug::scenePathContextName, ScenePath() );
		Context::Scope scopedContext( tmpContext );
		for( vector<ScenePlug *>::const_iterator it = m_inPlugs.begin(), eIt = m_inPlugs.end(); it!=eIt; it++ )
		{
			(*it)->childNamesPlug()->hash( h );
		}
	}
}

void Group::hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 ) // "/"
	{
		SceneProcessor::hashBound( path, context, parent, h );
		for( vector<ScenePlug *>::const_iterator it = m_inPlugs.begin(), eIt = m_inPlugs.end(); it!=eIt; it++ )
		{
			(*it)->boundPlug()->hash( h );
		}
		transformPlug()->hash( h );
	}
	else if( path.size() == 1 ) // "/group"
	{
		SceneProcessor::hashBound( path, context, parent, h );
		ContextPtr tmpContext = new Context( *Context::current() );
		tmpContext->set( ScenePlug::scenePathContextName, ScenePath() );
		Context::Scope scopedContext( tmpContext );
		for( vector<ScenePlug *>::const_iterator it = m_inPlugs.begin(), eIt = m_inPlugs.end(); it!=eIt; it++ )
		{
			(*it)->boundPlug()->hash( h );
		}
	}
	else // "/group/..."
	{
		// pass through
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, namePlug()->getValue(), &sourcePlug );
		h = sourcePlug->boundHash( source );
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
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, namePlug()->getValue(), &sourcePlug );
		h = sourcePlug->transformHash( source );
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
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, namePlug()->getValue(), &sourcePlug );
		h = sourcePlug->attributesHash( source );
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
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, namePlug()->getValue(), &sourcePlug );
		h = sourcePlug->objectHash( source );
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
		inputMappingPlug()->hash( h );
	}
	else // "/group/..."
	{
		// pass through
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, namePlug()->getValue(), &sourcePlug );
		h = sourcePlug->childNamesHash( source );
	}
}

void Group::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneProcessor::hashGlobals( context, parent, h );
		
	// all input globals affect the output, as does the mapping, because we use it to compute the forwardDeclarations
	for( vector<ScenePlug *>::const_iterator it = m_inPlugs.begin(), eIt = m_inPlugs.end(); it!=eIt; it++ )
	{
		(*it)->globalsPlug()->hash( h );
	}
	inputMappingPlug()->hash( h );
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
	for( vector<ScenePlug *>::const_iterator it = m_inPlugs.begin(), eIt = m_inPlugs.end(); it!=eIt; it++ )
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
			entry->members()["i"] = new IntData( it - m_inPlugs.begin() );
			result->members()[name] = entry;
		}
	}
	
	return result;
}

Imath::Box3f Group::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	
	if( path.size() <= 1 )
	{
		// either / or /groupName
		Box3f combinedBound;
		for( vector<ScenePlug *>::const_iterator it = m_inPlugs.begin(), eIt = m_inPlugs.end(); it!=eIt; it++ )
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
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, groupName, &sourcePlug );
		return sourcePlug->bound( source );
	}
}

Imath::M44f Group::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	
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
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, groupName, &sourcePlug );
		return sourcePlug->transform( source );
	}
}

IECore::ConstCompoundObjectPtr Group::computeAttributes( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	
	if( path.size() <= 1 )
	{
		return parent->attributesPlug()->defaultValue();
	}
	else
	{
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, groupName, &sourcePlug );
		return sourcePlug->attributes( source );
	}
}

IECore::ConstObjectPtr Group::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	
	if( path.size() <= 1 )
	{
		return parent->objectPlug()->defaultValue();
	}
	else
	{
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, groupName, &sourcePlug );
		return sourcePlug->object( source );
	}
}

IECore::ConstInternedStringVectorDataPtr Group::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{		
	std::string groupName = namePlug()->getValue();
	
	if( path.size() == 0 )
	{
		InternedStringVectorDataPtr result = new InternedStringVectorData();
		result->writable().push_back( groupName );
		return result;
	}
	else if( path.size() == 1 )
	{
		ConstCompoundObjectPtr mapping = staticPointerCast<const CompoundObject>( inputMappingPlug()->getValue() );
		return mapping->member<InternedStringVectorData>( "__GroupChildNames" );
	}
	else
	{
		ScenePlug *sourcePlug = 0;
		ScenePath source = sourcePath( path, groupName, &sourcePlug );
		return sourcePlug->childNames( source );
	}
}

IECore::ConstCompoundObjectPtr Group::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::CompoundObjectPtr result = inPlug()->globalsPlug()->getValue()->copy();
	
	std::string groupName = namePlug()->getValue();

	ConstCompoundObjectPtr mapping = staticPointerCast<const CompoundObject>( inputMappingPlug()->getValue() );
	const ObjectVector *forwardMappings = mapping->member<ObjectVector>( "__GroupForwardMappings", true /* throw if missing */ );

	IECore::CompoundDataPtr forwardDeclarations = new IECore::CompoundData;
	for( size_t i = 0, e = m_inPlugs.size(); i < e; i++ )
	{
		const CompoundData *forwardMapping = static_cast<const IECore::CompoundData *>( forwardMappings->members()[i].get() );
		ConstCompoundObjectPtr inputGlobals = m_inPlugs[i]->globalsPlug()->getValue();
		const CompoundData *inputForwardDeclarations = inputGlobals->member<CompoundData>( "gaffer:forwardDeclarations" );
		if( inputForwardDeclarations )
		{
			for( CompoundDataMap::const_iterator it = inputForwardDeclarations->readable().begin(), eIt = inputForwardDeclarations->readable().end(); it != eIt; it++ )
			{
				/// \todo This would all be much nicer if the forward declarations data structure
				/// used ScenePlug::ScenePaths or something similar - then we could ditch all the
				/// string munging.
				const InternedString &inputPath = it->first;
				size_t secondSlashPos = inputPath.string().find( '/', 1 );
				const std::string inputName( inputPath.string(), 1, secondSlashPos - 1 );
				const InternedString &outputName = forwardMapping->member<InternedStringData>( inputName, true /* throw if missing */ )->readable();
				std::string outputPath = std::string( "/" ) + groupName + "/" + outputName.string();
				if( secondSlashPos != string::npos )
				{
					outputPath += inputPath.string().substr( secondSlashPos );
				}
				forwardDeclarations->writable()[outputPath] = it->second;
			}
		}
	}
	result->members()["gaffer:forwardDeclarations"] = forwardDeclarations;
	
	return result;
}

SceneNode::ScenePath Group::sourcePath( const ScenePath &outputPath, const std::string &groupName, ScenePlug **source ) const
{		
	const InternedString mappedChildName = outputPath[1];
	
	ConstCompoundObjectPtr mapping = staticPointerCast<const CompoundObject>( inputMappingPlug()->getValue() );
	const CompoundObject *entry = mapping->member<CompoundObject>( mappedChildName );
	if( !entry )
	{
		throw Exception( boost::str( boost::format( "Unable to find mapping for output path" ) ) );
	}
		
	*source = m_inPlugs[entry->member<IntData>( "i" )->readable()];
	
	ScenePath result;
	result.reserve( outputPath.size() - 1 );
	result.push_back( entry->member<InternedStringData>( "n" )->readable() );
	result.insert( result.end(), outputPath.begin() + 2, outputPath.end() );
	return result;
}

Gaffer::ObjectPlug *Group::mappingPlug()
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ObjectPlug *Group::mappingPlug() const
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 2 );
}

Gaffer::ObjectPlug *Group::inputMappingPlug()
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ObjectPlug *Group::inputMappingPlug() const
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 3 );
}

void Group::childAdded( GraphComponent *parent, GraphComponent *child )
{
	if( child->isInstanceOf( ScenePlug::staticTypeId() ) )
	{
		m_inPlugs.clear();
		for( InputScenePlugIterator it( this ); it != it.end(); it++ )
		{
			m_inPlugs.push_back( it->get() );
		}
	}
}

void Group::plugInputChanged( Gaffer::Plug *plug )
{
	if( plug->isInstanceOf( ScenePlug::staticTypeId() ) )
	{
		addAndRemoveInputs();
	}
}

void Group::addAndRemoveInputs()
{
	int lastConnected = -1;
	std::vector<ScenePlug *> inputs;
	for( InputScenePlugIterator it( this ); it != it.end(); ++it )
	{
		if( (*it)->getInput<Plug>() )
		{
			lastConnected = inputs.size();
		}
		inputs.push_back( it->get() );
	}
	
	if( lastConnected == (int)inputs.size() - 1 )
	{
		addChild( new ScenePlug( "in1", Plug::In, Plug::Default | Plug::Dynamic ) );
	}
	else
	{
		for( int i = lastConnected + 2; i < (int)inputs.size(); i++ )
		{
			removeChild( inputs[i] );
		}
	}
}

void Group::parentChanging( Gaffer::GraphComponent *newParent )
{
	// we block m_plugInputChangedConnection when we're being unparented, as the
	// calls to addAndRemoveInputs() it triggers would result in crashes in Node::parentChanging(),
	// because it iterates over all the plugs and the iterators aren't stable in the face
	// of plugs being removed mid-iteration.
	/// \todo I think the whole concept of Group adding and removing plugs on the fly based
	/// purely on connections/disconnections is flawed. I think we should have a method to
	/// explicitly request a new input, and a ui which uses that. We could also wrap up the
	/// multiple inputs behaviour into something we could reuse elsewhere - Plug::createCounterpart()
	/// might be useful for automatically making new plugs of the appropriate type.
	BlockedConnection block( m_plugInputChangedConnection, newParent == 0 );
	SceneProcessor::parentChanging( newParent );
}
