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

#include "GafferScene/ObjectSource.h"

#include "GafferScene/SceneAlgo.h"

#include "Gaffer/StringPlug.h"
#include "Gaffer/TransformPlug.h"

#include "IECore/NullObject.h"
#include "IECore/StringAlgo.h"

#include "OpenEXR/OpenEXRConfig.h"
#if OPENEXR_VERSION_MAJOR < 3
#include "OpenEXR/ImathBoxAlgo.h"
#else
#include "Imath/ImathBoxAlgo.h"
#endif

using namespace GafferScene;

static IECore::InternedString g_emptyString( "" );

GAFFER_NODE_DEFINE_TYPE( ObjectSource );

size_t ObjectSource::g_firstPlugIndex = 0;

ObjectSource::ObjectSource( const std::string &name, const std::string &namePlugDefaultValue )
	:	SceneNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new Gaffer::StringPlug( "name", Gaffer::Plug::In, namePlugDefaultValue ) );
	addChild( new Gaffer::StringPlug( "sets" ) );
	addChild( new Gaffer::TransformPlug( "transform" ) );
	addChild( new Gaffer::ObjectPlug( "__source", Gaffer::Plug::Out, IECore::NullObject::defaultNullObject() ) );
}

ObjectSource::~ObjectSource()
{
}

Gaffer::StringPlug *ObjectSource::namePlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *ObjectSource::namePlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *ObjectSource::setsPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *ObjectSource::setsPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex + 1 );
}

Gaffer::TransformPlug *ObjectSource::transformPlug()
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::TransformPlug *ObjectSource::transformPlug() const
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 2 );
}

void ObjectSource::affects( const Gaffer::Plug *input, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const
{
	SceneNode::affects( input, outputs );

	if( input == sourcePlug() )
	{
		outputs.push_back( outPlug()->boundPlug() );
		outputs.push_back( outPlug()->objectPlug() );
	}
	else if( input == namePlug() )
	{
		outputs.push_back( outPlug()->childNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}
	else if( transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
	else if( input == setsPlug() )
	{
		outputs.push_back( outPlug()->setNamesPlug() );
		outputs.push_back( outPlug()->setPlug() );
	}

}

Gaffer::ObjectPlug *ObjectSource::sourcePlug()
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::ObjectPlug *ObjectSource::sourcePlug() const
{
	return getChild<Gaffer::ObjectPlug>( g_firstPlugIndex + 3 );
}

void ObjectSource::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	SceneNode::hash( output, context, h );

	if( output == sourcePlug() )
	{
		hashSource( context, h );
	}
}

void ObjectSource::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == sourcePlug() )
	{
		static_cast<Gaffer::ObjectPlug *>( output )->setValue( computeSource( context ) );
		return;
	}

	return SceneNode::compute( output, context );
}

void ObjectSource::hashAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = parent->attributesPlug()->defaultValue()->Object::hash();
}

IECore::ConstCompoundObjectPtr ObjectSource::computeAttributes( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return parent->attributesPlug()->defaultValue();
}

void ObjectSource::hashBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashBound( path, context, parent, h );
	sourcePlug()->hash( h );
	if( path.size() == 0 )
	{
		transformPlug()->hash( h );
	}
}

Imath::Box3f ObjectSource::computeBound( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::ConstObjectPtr object = sourcePlug()->getValue();
	Imath::Box3f result = SceneAlgo::bound( object.get() );

	if( path.size() == 0 )
	{
		result = Imath::transform( result, transformPlug()->matrix() );
	}
	return result;
}

void ObjectSource::hashTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashTransform( path, context, parent, h );
	if( path.size() == 1 )
	{
		transformPlug()->hash( h );
	}
}

Imath::M44f ObjectSource::computeTransform( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 1 )
	{
		return transformPlug()->matrix();
	}
	return Imath::M44f();
}

void ObjectSource::hashObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() != 1 )
	{
		h = parent->objectPlug()->defaultValue()->hash();
		return;
	}

	SceneNode::hashObject( path, context, parent, h );
	sourcePlug()->hash( h );
}

IECore::ConstObjectPtr ObjectSource::computeObject( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() != 1 )
	{
		return parent->objectPlug()->defaultValue();
	}

	return sourcePlug()->getValue();
}

void ObjectSource::hashChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( path.size() == 0 )
	{
		SceneNode::hashChildNames( path, context, parent, h );
		namePlug()->hash( h );
		return;
	}
	h = parent->childNamesPlug()->defaultValue()->Object::hash();
}

void ObjectSource::hashStandardSetNames( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
}

IECore::ConstInternedStringVectorDataPtr ObjectSource::computeChildNames( const SceneNode::ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( path.size() == 0 )
	{
		IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
		result->writable().push_back( validatedName() );
		return result;
	}
	return parent->childNamesPlug()->defaultValue();
}

void ObjectSource::hashGlobals( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	h = parent->globalsPlug()->defaultValue()->Object::hash();
}

IECore::ConstCompoundObjectPtr ObjectSource::computeGlobals( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	return parent->globalsPlug()->defaultValue();
}

void ObjectSource::hashSetNames( const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	SceneNode::hashSetNames( context, parent, h );
	setsPlug()->hash( h );
	hashStandardSetNames( context, h );
}

IECore::ConstInternedStringVectorDataPtr ObjectSource::computeSetNames( const Gaffer::Context *context, const ScenePlug *parent ) const
{
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData;
	IECore::StringAlgo::tokenize( setsPlug()->getValue(), ' ', result->writable() );
	IECore::ConstInternedStringVectorDataPtr setNames = computeStandardSetNames();
	for(unsigned int i = 0; i < setNames->readable().size(); ++i)
	{
		result->writable().push_back( setNames->readable()[i] );
	}
	return result;
}

void ObjectSource::hashSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const
{
	if( setNameValid( setName ) )
	{
		SceneNode::hashSet( setName, context, parent, h );
		namePlug()->hash( h );
	}
	else
	{
		h = outPlug()->setPlug()->defaultValue()->Object::hash();
	}
}

IECore::ConstPathMatcherDataPtr ObjectSource::computeSet( const IECore::InternedString &setName, const Gaffer::Context *context, const ScenePlug *parent ) const
{
	if( setNameValid( setName ) )
	{
		IECore::PathMatcherDataPtr result = new IECore::PathMatcherData;
		result->writable().addPath( ScenePlug::ScenePath( { validatedName() } ) );
		return result;
	}
	else
	{
		return outPlug()->setPlug()->defaultValue();
	}
}

IECore::ConstInternedStringVectorDataPtr ObjectSource::computeStandardSetNames() const
{
	IECore::InternedStringVectorDataPtr result = new IECore::InternedStringVectorData();
	return result;
}

IECore::InternedString ObjectSource::validatedName() const
{
	const IECore::InternedString name = namePlug()->getValue();
	if( name.string().size() )
	{
		SceneAlgo::validateName( name );
		return name;
	}
	else
	{
		/// \todo Why don't we just let `validateName()` throw for us instead?
		return "unnamed";
	}
}

bool ObjectSource::setNameValid( const IECore::InternedString &setName ) const
{
	IECore::ConstInternedStringVectorDataPtr standardSets = computeStandardSetNames();
	if( std::find( standardSets->readable().begin(), standardSets->readable().end(), setName ) != standardSets->readable().end() )
	{
		return true;
	}

	std::vector<IECore::InternedString> setNames;
	IECore::StringAlgo::tokenize( setsPlug()->getValue(), ' ', setNames );
	return std::find( setNames.begin(), setNames.end(), setName ) != setNames.end();
}
