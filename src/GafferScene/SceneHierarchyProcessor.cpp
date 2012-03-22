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

#include "GafferScene/SceneHierarchyProcessor.h"

#include "IECore/TypedDataInternals.h"
#include "IECore/Exception.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// Implementation of Mapping classes.
//////////////////////////////////////////////////////////////////////////

SceneHierarchyProcessor::Child::Child()
{
}

SceneHierarchyProcessor::Child::Child( const std::string &srcPlug, const std::string &srcPath )
	:	sourcePlug( srcPlug ), sourcePath( srcPath )
{
}

bool SceneHierarchyProcessor::Child::operator == ( const Child &other ) const
{
	return sourcePlug == other.sourcePlug && sourcePath == other.sourcePath;
}

// We use this class to allow the mapping types defined above to be stored on an ObjectPlug.
class SceneHierarchyProcessor::MappingData : public IECore::Data
{

	public :
	
		IE_CORE_DECLAREEXTENSIONOBJECT( SceneHierarchyProcessor::MappingData, SceneHierarchyProcessorMappingDataTypeId, Data )
		
		const Mapping &readable() const;
		Mapping &writable();
		
	private :
	
		IECore::SharedDataHolder<Mapping> m_data;
		
};

IE_CORE_DEFINEOBJECTTYPEDESCRIPTION( SceneHierarchyProcessor::MappingData );

bool SceneHierarchyProcessor::MappingData::isEqualTo( const IECore::Object *other ) const
{
	if( !Data::isEqualTo( other ) )
	{
		return false;
	}
	const MappingData *tOther = static_cast<const MappingData*>( other );
	return m_data == tOther->m_data;
}

void SceneHierarchyProcessor::MappingData::hash( IECore::MurmurHash &h ) const
{
	Data::hash( h );
	throw Exception( "MappingData::save not implemented yet." );
}

void SceneHierarchyProcessor::MappingData::copyFrom( const IECore::Object *other, IECore::Object::CopyContext *context )
{
	Data::copyFrom( other, context );
	const MappingData *tOther = static_cast<const MappingData*>( other );
	m_data = tOther->m_data;
}

void SceneHierarchyProcessor::MappingData::save( IECore::Object::SaveContext *context ) const
{
	Data::save( context );
	throw Exception( "MappingData::save not implemented yet." );
}

void SceneHierarchyProcessor::MappingData::load( IECore::Object::LoadContextPtr context )
{
	Data::load( context );
	throw Exception( "MappingData::load not implemented yet." );
}

void SceneHierarchyProcessor::MappingData::memoryUsage( IECore::Object::MemoryAccumulator &a ) const
{
	Data::memoryUsage( a );
	throw Exception( "MappingData::memoryUsage not implemented yet." );
}

const SceneHierarchyProcessor::Mapping &SceneHierarchyProcessor::MappingData::readable() const
{
	return m_data.readable();
}

SceneHierarchyProcessor::Mapping &SceneHierarchyProcessor::MappingData::writable()
{
	return m_data.writable();
}

//////////////////////////////////////////////////////////////////////////
// Implementation of SceneHierarchyProcessor
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( SceneHierarchyProcessor );

SceneHierarchyProcessor::SceneHierarchyProcessor( const std::string &name )
	:	SceneProcessor( name )
{
	addChild( 
		new ObjectPlug(
			"__mapping",
			Plug::Out,
			0,
			Plug::Default & ~Plug::Serialisable
		)
	);
}

SceneHierarchyProcessor::~SceneHierarchyProcessor()
{
}

void SceneHierarchyProcessor::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	SceneProcessor::affects( input, outputs );
	
	const ScenePlug *in = inPlug();
	if( input->parent<ScenePlug>() == in )
	{
		outputs.push_back( outPlug()->getChild<ValuePlug>( input->getName() ) );
	}
	else if( input == mappingPlug() )
	{
		outputs.push_back( outPlug() );
	}
}

const Gaffer::ObjectPlug *SceneHierarchyProcessor::mappingPlug() const
{
	return getChild<ObjectPlug>( "__mapping" );
}

void SceneHierarchyProcessor::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == mappingPlug() )
	{
		MappingDataPtr result = new MappingData;
		computeMapping( context, result->writable() );
		if( result->writable().size() )
		{
			static_cast<ObjectPlug *>( output )->setValue( result );
		}
		else
		{
			static_cast<ObjectPlug *>( output )->setValue( 0 );
		}
	}
	
	return SceneProcessor::compute( output, context );
}

Imath::Box3f SceneHierarchyProcessor::computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return Imath::Box3f( Imath::V3f( 0 ), Imath::V3f( 1 ) );
}

Imath::M44f SceneHierarchyProcessor::computeTransform( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{	
	Imath::M44f result;
	ConstMappingDataPtr mappingData = staticPointerCast<const MappingData>( mappingPlug()->getValue() );
	if( mappingData )
	{
		std::string remappedPath;
		const ScenePlug *remappedInput;
		remap( path, mappingData->readable(), remappedPath, remappedInput );
		if( remappedInput )
		{
			result = remappedInput->transform( remappedPath );
		}
	}
	else
	{
		result = inPlug()->transformPlug()->getValue();
	}
	
	return result;
}

IECore::PrimitivePtr SceneHierarchyProcessor::computeGeometry( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	ConstPrimitivePtr geometry = 0;
	ConstMappingDataPtr mappingData = staticPointerCast<const MappingData>( mappingPlug()->getValue() );
	if( mappingData )
	{
		std::string remappedPath;
		const ScenePlug *remappedInput;
		remap( path, mappingData->readable(), remappedPath, remappedInput );
		if( remappedInput )
		{
			geometry = remappedInput->geometry( remappedPath );
		}
	}
	else
	{
		geometry = inPlug()->geometryPlug()->getValue();
	}
	
	return geometry ? geometry->copy() : 0;
}

IECore::StringVectorDataPtr SceneHierarchyProcessor::computeChildNames( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{	
	// if no mapping has been computed by the subclass then we're just a pass through
	ConstMappingDataPtr mappingData = staticPointerCast<const MappingData>( mappingPlug()->getValue() );
	if( !mappingData )
	{
		ConstStringVectorDataPtr names = inPlug()->childNamesPlug()->getValue();
		return names ? names->copy() : 0;
	}
	
	// otherwise remap the path we're given
	const Mapping &mapping = mappingData->readable();
	std::string remappedPath;
	const ScenePlug *remappedInput;
	remap( path, mapping, remappedPath, remappedInput );
	
	// and then get the children from the remapped path
	StringVectorDataPtr result = 0;
	Mapping::const_iterator it = mapping.find( remappedPath );
	if( it != mapping.end() )
	{
		result = new StringVectorData;
		for( MappingChildContainer::const_iterator cIt = it->second.begin(), eIt = it->second.end(); cIt != eIt; cIt++ )
		{
			result->writable().push_back( cIt->first );
		}
	}
	else if( remappedInput )
	{
		ConstStringVectorDataPtr c = remappedInput->childNames( remappedPath );
		result = c ? c->copy() : 0;
	}
	
	return result;
}

void SceneHierarchyProcessor::remap( const std::string &scenePath, const Mapping &mapping, std::string &remappedPath, const ScenePlug *&remappedInput ) const
{	
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	Tokenizer tokens( scenePath, boost::char_separator<char>( "/" ) );

	remappedInput = inPlug();
	remappedPath = "/";
	for( Tokenizer::iterator tIt=tokens.begin(); tIt!=tokens.end(); tIt++ )
	{
		Mapping::const_iterator it = mapping.find( remappedPath );
		if( it != mapping.end() )
		{
			MappingChildContainer::const_iterator cIt = it->second.find( *tIt );
			if( cIt != it->second.end() )
			{
				if( cIt->second.sourcePath.size() && cIt->second.sourcePlug.size() )
				{
					remappedInput = getChild<ScenePlug>( cIt->second.sourcePlug );
					remappedPath = cIt->second.sourcePath;
					continue;
				}
				else
				{
					// this is an element being inserted in the scene out of nowhere
					// rather than being remapped from somewhere else. clear the remapped
					// input plug to denote this and fall through to the code to append
					// the current token.
					remappedInput = 0;
				}
			}
		}

		if( remappedPath.size() > 1 )
		{
			remappedPath += "/";
		}
		remappedPath += *tIt;
	}
}
