//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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
#include "boost/lexical_cast.hpp"

#include "OpenEXR/ImathBoxAlgo.h"

#include "IECore/CompoundObject.h"

#include "Gaffer/Context.h"

#include "GafferScene/Group.h"

using namespace std;
using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Group );

Group::Group( const std::string &name )
	:	SceneProcessor( name )
{
	addChild( new StringPlug( "name", Plug::In, "group" ) );
	addChild( new TransformPlug( "transform" ) );
	
	addChild( new Gaffer::ObjectPlug( "__mapping", Gaffer::Plug::Out ) );
	addChild( new Gaffer::ObjectPlug( "__inputMapping", Gaffer::Plug::In, 0, Gaffer::Plug::Default & ~Gaffer::Plug::Serialisable ) );
	inputMappingPlug()->setInput( mappingPlug() );
	
	plugInputChangedSignal().connect( boost::bind( &Group::plugInputChanged, this, ::_1 ) );
	childAddedSignal().connect( boost::bind( &Group::childAdded, this, ::_1, ::_2 ) );
}

Group::~Group()
{
}

Gaffer::StringPlug *Group::namePlug()
{
	return getChild<StringPlug>( "name" );
}

const Gaffer::StringPlug *Group::namePlug() const
{
	return getChild<StringPlug>( "name" );
}

Gaffer::TransformPlug *Group::transformPlug()
{
	return getChild<TransformPlug>( "transform" );
}

const Gaffer::TransformPlug *Group::transformPlug() const
{
	return getChild<TransformPlug>( "transform" );
}

void Group::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	if( input == namePlug() || input == inPlug()->childNamesPlug() )
	{
		outputs.push_back( outPlug() );
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		/// \todo Strictly speaking I think we should just push outPlug()->transformPlug()
		/// here, but the dirty propagation doesn't work for that just now. Get it working.
		outputs.push_back( outPlug() );
	}
	else if( input == inputMappingPlug() )
	{
		outputs.push_back( outPlug() );	
	}
	else
	{
		const ScenePlug *s = input->ancestor<ScenePlug>();
		if( s && input == s->childNamesPlug() )
		{
			outputs.push_back( mappingPlug() );
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

static boost::regex g_namePrefixSuffixRegex( "^(.*[^0-9]+)([0-9]+)$" );
static boost::format g_namePrefixSuffixFormatter( "%s%d" );

IECore::ObjectPtr Group::computeMapping( const Gaffer::Context *context ) const
{
	/// \todo It might be more optimal to make our own Object subclass better tailored
	/// for passing the information we want.
	CompoundObjectPtr result = new CompoundObject();
	
	StringVectorDataPtr childNamesData = new StringVectorData();
	vector<string> &childNames = childNamesData->writable();
	result->members()["__GroupChildNames"] = childNamesData;
	
	set<string> allNames;
	for( vector<ScenePlug *>::const_iterator it = m_inPlugs.begin(), eIt = m_inPlugs.end(); it!=eIt; it++ )
	{
		ConstStringVectorDataPtr inChildNamesData = (*it)->childNames( "/" );
		if( !inChildNamesData )
		{
			continue;
		}
		
		const vector<string> &inChildNames = inChildNamesData->readable();
		for( vector<string>::const_iterator cIt = inChildNames.begin(), ceIt = inChildNames.end(); cIt!=ceIt; cIt++ )
		{
			string name = *cIt;
			if( allNames.find( name ) != allNames.end() )
			{
				// uniqueify the name
				/// \todo This code is almost identical to code in GraphComponent::setName(),
				/// is there a sensible place it can be shared? The primary obstacle is that
				/// each use has a different method of storing the existing names.
				string prefix = name;
				int suffix = 1;
				
				boost::cmatch match;
				if( regex_match( name.c_str(), match, g_namePrefixSuffixRegex ) )
				{
					prefix = match[1];
					suffix = boost::lexical_cast<int>( match[2] );
				}
				
				do
				{
					name = boost::str( g_namePrefixSuffixFormatter % prefix % suffix );
					suffix++;
				} while( allNames.find( name ) != allNames.end() );
			}
			
			allNames.insert( name );
			childNames.push_back( name );
			CompoundObjectPtr entry = new CompoundObject;
			entry->members()["n"] = new StringData( *cIt );
			entry->members()["i"] = new IntData( it - m_inPlugs.begin() );
			result->members()[name] = entry;
		}
	}
	
	return result;
}

Imath::Box3f Group::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	
	if( path.size() <= groupName.size() + 1 )
	{
		// either / or /groupName
		Box3f combinedBound;
		for( vector<ScenePlug *>::const_iterator it = m_inPlugs.begin(), eIt = m_inPlugs.end(); it!=eIt; it++ )
		{
			// we don't need to transform these bounds, because the SceneNode
			// guarantees that the transform for root nodes is always identity.
			Box3f bound = (*it)->bound( "/" );
			combinedBound.extendBy( bound );
		}
		if( path == "/" )
		{
			combinedBound = transform( combinedBound, transformPlug()->matrix() );
		}
		return combinedBound;
	}
	else
	{
		ScenePlug *sourcePlug = 0;
		std::string source = sourcePath( path, groupName, &sourcePlug );
		return sourcePlug->bound( source );
	}
}

Imath::M44f Group::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	
	if( path == "/" )
	{
		return Imath::M44f();
	}
	else if( path.size() == groupName.size() + 1 )
	{
		return transformPlug()->matrix();
	}
	else
	{
		ScenePlug *sourcePlug = 0;
		std::string source = sourcePath( path, groupName, &sourcePlug );
		return sourcePlug->transform( source );
	}
}

IECore::ObjectVectorPtr Group::computeState( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	
	if( path.size() <= groupName.size() + 1 )
	{
		return 0;
	}
	else
	{
		ScenePlug *sourcePlug = 0;
		std::string source = sourcePath( path, groupName, &sourcePlug );
		ConstObjectVectorPtr s = sourcePlug->state( source );
		return s ? s->copy() : 0;
	}
	
	return 0;
}

IECore::ObjectPtr Group::computeObject( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	std::string groupName = namePlug()->getValue();
	
	if( path.size() <= groupName.size() + 1 )
	{
		return 0;
	}
	else
	{
		ScenePlug *sourcePlug = 0;
		std::string source = sourcePath( path, groupName, &sourcePlug );
		ConstObjectPtr o = sourcePlug->object( source );
		return o ? o->copy() : 0;
	}
}

IECore::StringVectorDataPtr Group::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{	
	std::string groupName = namePlug()->getValue();
	
	if( path == "/" )
	{
		StringVectorDataPtr result = new StringVectorData();
		result->writable().push_back( groupName );
		return result;
	}
	else if( path.size() == groupName.size() + 1 )
	{
		ConstCompoundObjectPtr mapping = staticPointerCast<const CompoundObject>( inputMappingPlug()->getValue() );
		ConstStringVectorDataPtr names = mapping->member<StringVectorData>( "__GroupChildNames" );
		return names ? names->copy() : 0;
	}
	else
	{
		ScenePlug *sourcePlug = 0;
		std::string source = sourcePath( path, groupName, &sourcePlug );
		ConstStringVectorDataPtr childNames = sourcePlug->childNames( source );
		return childNames ? childNames->copy() : 0;
	}
}

IECore::ObjectVectorPtr Group::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstObjectVectorPtr globals = inPlug()->globalsPlug()->getValue();
	return globals ? globals->copy() : 0;
}

std::string Group::sourcePath( const std::string &outputPath, const std::string &groupName, ScenePlug **source ) const
{	
	size_t slashPos = outputPath.find( "/", groupName.size() + 2 );
	std::string mappedChildName( outputPath, groupName.size() + 2, slashPos - groupName.size() - 2 );
	
	ConstCompoundObjectPtr mapping = staticPointerCast<const CompoundObject>( inputMappingPlug()->getValue() );
	const CompoundObject *entry = mapping->member<CompoundObject>( mappedChildName );
	if( !entry )
	{
		throw Exception( "Unable to find mapping" );
	}
		
	*source = m_inPlugs[entry->member<IntData>( "i" )->readable()];
	string result = "/" + entry->member<StringData>( "n" )->readable();
	if( slashPos != string::npos )
	{
		result += string( outputPath, slashPos );
	}
		
	return result;
}

Gaffer::ObjectPlug *Group::mappingPlug()
{
	return getChild<Gaffer::ObjectPlug>( "__mapping" );
}

const Gaffer::ObjectPlug *Group::mappingPlug() const
{
	return getChild<Gaffer::ObjectPlug>( "__mapping" );
}

Gaffer::ObjectPlug *Group::inputMappingPlug()
{
	return getChild<Gaffer::ObjectPlug>( "__inputMapping" );
}

const Gaffer::ObjectPlug *Group::inputMappingPlug() const
{
	return getChild<Gaffer::ObjectPlug>( "__inputMapping" );
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