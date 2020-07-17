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

#include "GafferScene/ScenePlug.h"

#include "GafferScene/Filter.h"

#include "Gaffer/Context.h"
#include "Gaffer/ContextAlgo.h"

#include "IECore/NullObject.h"
#include "IECore/StringAlgo.h"

using namespace Gaffer;
using namespace GafferScene;

GAFFER_PLUG_DEFINE_TYPE( ScenePlug );

const IECore::InternedString ScenePlug::scenePathContextName( "scene:path" );
const IECore::InternedString ScenePlug::setNameContextName( "scene:setName" );

static ContextAlgo::GlobalScope::Registration g_globalScopeRegistration(
	ScenePlug::staticTypeId(),
	{ ScenePlug::scenePathContextName, ScenePlug::setNameContextName }
);

ScenePlug::ScenePlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
	// we don't want the children to be serialised in any way - we always create
	// them ourselves in this constructor so they aren't Dynamic, and we don't ever
	// want to store their values because they are meaningless without an input
	// connection, so they aren't Serialisable either.
	unsigned childFlags = flags & ~(Dynamic | Serialisable);

	addChild(
		new AtomicBox3fPlug(
			"bound",
			direction,
			Imath::Box3f(),
			childFlags
		)
	);

	addChild(
		new M44fPlug(
			"transform",
			direction,
			Imath::M44f(),
			childFlags
		)
	);

	addChild(
		new CompoundObjectPlug(
			"attributes",
			direction,
			new IECore::CompoundObject(),
			childFlags
		)
	);

	addChild(
		new ObjectPlug(
			"object",
			direction,
			new IECore::NullObject(),
			childFlags
		)
	);

	addChild(
		new InternedStringVectorDataPlug(
			"childNames",
			direction,
			new IECore::InternedStringVectorData(),
			childFlags
		)
	);

	addChild(
		new CompoundObjectPlug(
			"globals",
			direction,
			new IECore::CompoundObject(),
			childFlags
		)
	);

	addChild(
		new InternedStringVectorDataPlug(
			"setNames",
			direction,
			new IECore::InternedStringVectorData(),
			childFlags
		)
	);

	addChild(
		new PathMatcherDataPlug(
			"set",
			direction,
			new IECore::PathMatcherData(),
			childFlags
		)
	);

	addChild(
		new BoolPlug(
			"exists",
			direction,
			true,
			childFlags
		)
	);

	addChild(
		new AtomicBox3fPlug(
			"childBounds",
			direction,
			Imath::Box3f(),
			childFlags
		)
	);

	addChild(
		new InternedStringVectorDataPlug(
			"__sortedChildNames",
			direction,
			new IECore::InternedStringVectorData(),
			childFlags
		)
	);

}

ScenePlug::~ScenePlug()
{
}

bool ScenePlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}
	return children().size() != 11;
}

Gaffer::PlugPtr ScenePlug::createCounterpart( const std::string &name, Direction direction ) const
{
	return new ScenePlug( name, direction, getFlags() );
}

bool ScenePlug::acceptsInput( const Gaffer::Plug *input ) const
{
	if( !ValuePlug::acceptsInput( input ) )
	{
		return false;
	}
	if( input )
	{
		return input->isInstanceOf( staticTypeId() );
	}
	return true;
}

Gaffer::AtomicBox3fPlug *ScenePlug::boundPlug()
{
	return getChild<AtomicBox3fPlug>( 0 );
}

const Gaffer::AtomicBox3fPlug *ScenePlug::boundPlug() const
{
	return getChild<AtomicBox3fPlug>( 0 );
}

Gaffer::M44fPlug *ScenePlug::transformPlug()
{
	return getChild<M44fPlug>( 1 );
}

const Gaffer::M44fPlug *ScenePlug::transformPlug() const
{
	return getChild<M44fPlug>( 1 );
}

Gaffer::CompoundObjectPlug *ScenePlug::attributesPlug()
{
	return getChild<CompoundObjectPlug>( 2 );
}

const Gaffer::CompoundObjectPlug *ScenePlug::attributesPlug() const
{
	return getChild<CompoundObjectPlug>( 2 );
}

Gaffer::ObjectPlug *ScenePlug::objectPlug()
{
	return getChild<ObjectPlug>( 3 );
}

const Gaffer::ObjectPlug *ScenePlug::objectPlug() const
{
	return getChild<ObjectPlug>( 3 );
}

Gaffer::InternedStringVectorDataPlug *ScenePlug::childNamesPlug()
{
	return getChild<InternedStringVectorDataPlug>( 4 );
}

const Gaffer::InternedStringVectorDataPlug *ScenePlug::childNamesPlug() const
{
	return getChild<InternedStringVectorDataPlug>( 4 );
}

Gaffer::CompoundObjectPlug *ScenePlug::globalsPlug()
{
	return getChild<CompoundObjectPlug>( 5 );
}

const Gaffer::CompoundObjectPlug *ScenePlug::globalsPlug() const
{
	return getChild<CompoundObjectPlug>( 5 );
}

Gaffer::InternedStringVectorDataPlug *ScenePlug::setNamesPlug()
{
	return getChild<InternedStringVectorDataPlug>( 6 );
}

const Gaffer::InternedStringVectorDataPlug *ScenePlug::setNamesPlug() const
{
	return getChild<InternedStringVectorDataPlug>( 6 );
}

Gaffer::PathMatcherDataPlug *ScenePlug::setPlug()
{
	return getChild<PathMatcherDataPlug>( 7 );
}

const Gaffer::PathMatcherDataPlug *ScenePlug::setPlug() const
{
	return getChild<PathMatcherDataPlug>( 7 );
}

Gaffer::BoolPlug *ScenePlug::existsPlug()
{
	return getChild<BoolPlug>( 8 );
}

const Gaffer::BoolPlug *ScenePlug::existsPlug() const
{
	return getChild<BoolPlug>( 8 );
}

Gaffer::AtomicBox3fPlug *ScenePlug::childBoundsPlug()
{
	return getChild<AtomicBox3fPlug>( 9 );
}

const Gaffer::AtomicBox3fPlug *ScenePlug::childBoundsPlug() const
{
	return getChild<AtomicBox3fPlug>( 9 );
}


Gaffer::InternedStringVectorDataPlug *ScenePlug::sortedChildNamesPlug()
{
	return getChild<InternedStringVectorDataPlug>( 10 );
}

const Gaffer::InternedStringVectorDataPlug *ScenePlug::sortedChildNamesPlug() const
{
	return getChild<InternedStringVectorDataPlug>( 10 );
}

ScenePlug::PathScope::PathScope( const Gaffer::Context *context )
	:	EditableScope( context )
{
	remove( ScenePlug::setNameContextName );
}

ScenePlug::PathScope::PathScope( const Gaffer::Context *context, const ScenePath &scenePath )
	:	PathScope( context )
{
	setPath( scenePath );
}

ScenePlug::PathScope::PathScope( const Gaffer::ThreadState &threadState )
	:	EditableScope( threadState )
{
}

ScenePlug::PathScope::PathScope( const Gaffer::ThreadState &threadState, const ScenePath &scenePath )
	:	EditableScope( threadState )
{
	setPath( scenePath );
}

void ScenePlug::PathScope::setPath( const ScenePath &scenePath )
{
	set( scenePathContextName, scenePath );
}

ScenePlug::SetScope::SetScope( const Gaffer::Context *context )
	:	EditableScope( context )
{
	remove( Filter::inputSceneContextName );
	remove( ScenePlug::scenePathContextName );
}

ScenePlug::SetScope::SetScope( const Gaffer::Context *context, const IECore::InternedString &setName )
	:	EditableScope( context )
{
	remove( Filter::inputSceneContextName );
	remove( ScenePlug::scenePathContextName );
	setSetName( setName );
}

ScenePlug::SetScope::SetScope( const Gaffer::ThreadState &threadState )
	:	EditableScope( threadState )
{
	remove( Filter::inputSceneContextName );
	remove( ScenePlug::scenePathContextName );
}

ScenePlug::SetScope::SetScope( const Gaffer::ThreadState &threadState, const IECore::InternedString &setName )
	:	EditableScope( threadState )
{
	remove( Filter::inputSceneContextName );
	remove( ScenePlug::scenePathContextName );
	setSetName( setName );
}

void ScenePlug::SetScope::setSetName( const IECore::InternedString &setName )
{
	set( setNameContextName, setName );
}

ScenePlug::GlobalScope::GlobalScope( const Gaffer::Context *context )
	:	EditableScope( context )
{
	remove( Filter::inputSceneContextName );
	remove( scenePathContextName );
	remove( setNameContextName );
}

ScenePlug::GlobalScope::GlobalScope( const Gaffer::ThreadState &threadState )
	:	EditableScope( threadState )
{
	remove( Filter::inputSceneContextName );
	remove( scenePathContextName );
	remove( setNameContextName );
}

bool ScenePlug::exists() const
{
	return existsPlug()->getValue();
}

bool ScenePlug::exists( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return existsPlug()->getValue();
}

Imath::Box3f ScenePlug::bound( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return boundPlug()->getValue();
}

Imath::M44f ScenePlug::transform( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return transformPlug()->getValue();
}

Imath::M44f ScenePlug::fullTransform( const ScenePath &scenePath ) const
{
	PathScope pathScope( Context::current() );

	Imath::M44f result;
	ScenePath path( scenePath );
	while( path.size() )
	{
		pathScope.setPath( path );
		result = result * transformPlug()->getValue();
		path.pop_back();
	}

	return result;
}

IECore::ConstCompoundObjectPtr ScenePlug::attributes( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return attributesPlug()->getValue();
}

IECore::CompoundObjectPtr ScenePlug::fullAttributes( const ScenePath &scenePath ) const
{
	PathScope pathScope( Context::current() );

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	IECore::CompoundObject::ObjectMap &resultMembers = result->members();
	ScenePath path( scenePath );
	while( path.size() )
	{
		pathScope.setPath( path );
		IECore::ConstCompoundObjectPtr a = attributesPlug()->getValue();
		const IECore::CompoundObject::ObjectMap &aMembers = a->members();
		for( IECore::CompoundObject::ObjectMap::const_iterator it = aMembers.begin(), eIt = aMembers.end(); it != eIt; it++ )
		{
			if( resultMembers.find( it->first ) == resultMembers.end() )
			{
				resultMembers.insert( *it );
			}
		}
		path.pop_back();
	}

	return result;
}

IECore::ConstObjectPtr ScenePlug::object( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return objectPlug()->getValue();
}

IECore::ConstInternedStringVectorDataPtr ScenePlug::childNames( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return childNamesPlug()->getValue();
}

IECore::ConstCompoundObjectPtr ScenePlug::globals() const
{
	GlobalScope scope( Context::current() );
	return globalsPlug()->getValue();
}

IECore::ConstInternedStringVectorDataPtr ScenePlug::setNames() const
{
	GlobalScope scope( Context::current() );
	return setNamesPlug()->getValue();
}

IECore::ConstPathMatcherDataPtr ScenePlug::set( const IECore::InternedString &setName ) const
{
	SetScope scope( Context::current(), setName );
	return setPlug()->getValue();
}

IECore::MurmurHash ScenePlug::boundHash( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return boundPlug()->hash();
}

IECore::MurmurHash ScenePlug::transformHash( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return transformPlug()->hash();
}

IECore::MurmurHash ScenePlug::fullTransformHash( const ScenePath &scenePath ) const
{
	PathScope pathScope( Context::current() );

	IECore::MurmurHash result;
	ScenePath path( scenePath );
	while( path.size() )
	{
		pathScope.setPath( path );
		transformPlug()->hash( result );
		path.pop_back();
	}

	return result;
}

IECore::MurmurHash ScenePlug::attributesHash( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return attributesPlug()->hash();
}

IECore::MurmurHash ScenePlug::fullAttributesHash( const ScenePath &scenePath ) const
{
	PathScope pathScope( Context::current() );

	IECore::MurmurHash result;
	ScenePath path( scenePath );
	while( path.size() )
	{
		pathScope.setPath( path );
		attributesPlug()->hash( result );
		path.pop_back();
	}

	return result;
}

IECore::MurmurHash ScenePlug::objectHash( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return objectPlug()->hash();
}

IECore::MurmurHash ScenePlug::childNamesHash( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return childNamesPlug()->hash();
}

IECore::MurmurHash ScenePlug::globalsHash() const
{
	GlobalScope scope( Context::current() );
	return globalsPlug()->hash();
}

IECore::MurmurHash ScenePlug::setNamesHash() const
{
	GlobalScope scope( Context::current() );
	return setNamesPlug()->hash();
}

IECore::MurmurHash ScenePlug::setHash( const IECore::InternedString &setName ) const
{
	SetScope scope( Context::current(), setName );
	return setPlug()->hash();
}

Imath::Box3f ScenePlug::childBounds( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return childBoundsPlug()->getValue();
}

Imath::Box3f ScenePlug::childBounds() const
{
	return childBoundsPlug()->getValue();
}

IECore::MurmurHash ScenePlug::childBoundsHash( const ScenePath &scenePath ) const
{
	PathScope scope( Context::current(), scenePath );
	return childBoundsPlug()->hash();
}

IECore::MurmurHash ScenePlug::childBoundsHash() const
{
	return childBoundsPlug()->hash();
}

void ScenePlug::stringToPath( const std::string &s, ScenePlug::ScenePath &path )
{
	path.clear();
	IECore::StringAlgo::tokenize( s, '/', path );
}

void ScenePlug::pathToString( const ScenePlug::ScenePath &path, std::string &s )
{
	if( !path.size() )
	{
		s = "/";
	}
	else
	{
		s.clear();
		for( ScenePlug::ScenePath::const_iterator it = path.begin(), eIt = path.end(); it != eIt; it++ )
		{
			s += "/" + it->string();
		}
	}
}

std::ostream &operator << ( std::ostream &o, const ScenePlug::ScenePath &path )
{
	if( !path.size() )
	{
		o << "/";
	}
	else
	{
		for( ScenePlug::ScenePath::const_iterator it = path.begin(); it != path.end(); ++it )
		{
			o << "/" << *it;
		}
	}
	return o;
}
