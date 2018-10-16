//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/CompoundDataPlug.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/StringPlug.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// CompoundData::MemberPlug implementation.
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( CompoundDataPlug::MemberPlug );

CompoundDataPlug::MemberPlug::MemberPlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
}

StringPlug *CompoundDataPlug::MemberPlug::namePlug()
{
	return getChild<StringPlug>( 0 );
}

const StringPlug *CompoundDataPlug::MemberPlug::namePlug() const
{
	return getChild<StringPlug>( 0 );
}

BoolPlug *CompoundDataPlug::MemberPlug::enabledPlug()
{
	return children().size() > 2 ? getChild<BoolPlug>( 2 ) : nullptr;
}

const BoolPlug *CompoundDataPlug::MemberPlug::enabledPlug() const
{
	return children().size() > 2 ? getChild<BoolPlug>( 2 ) : nullptr;
}

bool CompoundDataPlug::MemberPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	if(
		potentialChild->isInstanceOf( StringPlug::staticTypeId() ) &&
		potentialChild->getName() == "name" &&
		!getChild<Plug>( "name" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( ValuePlug::staticTypeId() ) &&
		potentialChild->getName() == "value" &&
		!getChild<Plug>( "value" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( BoolPlug::staticTypeId() ) &&
		potentialChild->getName() == "enabled" &&
		!getChild<Plug>( "enabled" )
	)
	{
		return true;
	}

	return false;
}

PlugPtr CompoundDataPlug::MemberPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new MemberPlug( name, direction, getFlags() );
	for( PlugIterator it( this ); !it.done(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

//////////////////////////////////////////////////////////////////////////
// CompoundDataPlug implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( CompoundDataPlug )

CompoundDataPlug::CompoundDataPlug( const std::string &name, Direction direction, unsigned flags )
	:	ValuePlug( name, direction, flags )
{
}

CompoundDataPlug::~CompoundDataPlug()
{
}

bool CompoundDataPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !ValuePlug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	return potentialChild->isInstanceOf( MemberPlug::staticTypeId() );
}

PlugPtr CompoundDataPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	CompoundDataPlugPtr result = new CompoundDataPlug( name, direction, getFlags() );
	for( PlugIterator it( this ); !it.done(); ++it )
	{
		result->addChild( (*it)->createCounterpart( (*it)->getName(), direction ) );
	}
	return result;
}

CompoundDataPlug::MemberPlug *CompoundDataPlug::addMember( const std::string &name, const IECore::Data *defaultValue, const std::string &plugName, unsigned plugFlags )
{
	return addMember( name, PlugAlgo::createPlugFromData( "value", direction(), plugFlags, defaultValue ).get(), plugName );
}

CompoundDataPlug::MemberPlug *CompoundDataPlug::addMember( const std::string &name, ValuePlug *valuePlug, const std::string &plugName )
{
	MemberPlugPtr plug = new MemberPlug( plugName, direction(), valuePlug->getFlags() );

	StringPlugPtr namePlug = new StringPlug( "name", direction(), name, valuePlug->getFlags() );
	plug->addChild( namePlug );

	valuePlug->setName( "value" );
	plug->addChild( valuePlug );

	addChild( plug );
	return plug.get();
}

CompoundDataPlug::MemberPlug *CompoundDataPlug::addOptionalMember( const std::string &name, const IECore::Data *defaultValue, const std::string &plugName, unsigned plugFlags, bool enabled )
{
	MemberPlug *plug = addMember( name, defaultValue, plugName, plugFlags );
	BoolPlugPtr e = new BoolPlug( "enabled", direction(), enabled, plugFlags );
	plug->addChild( e );
	return plug;
}

CompoundDataPlug::MemberPlug *CompoundDataPlug::addOptionalMember( const std::string &name, ValuePlug *valuePlug, const std::string &plugName, bool enabled )
{
	MemberPlug *plug = addMember( name, valuePlug, plugName );
	BoolPlugPtr e = new BoolPlug( "enabled", direction(), enabled, valuePlug->getFlags() );
	plug->addChild( e );
	return plug;
}

void CompoundDataPlug::addMembers( const IECore::CompoundData *parameters, bool useNameAsPlugName )
{
	std::string plugName = "member1";
	for( CompoundDataMap::const_iterator it = parameters->readable().begin(); it!=parameters->readable().end(); it++ )
	{
		if( useNameAsPlugName )
		{
			plugName = it->first;
			std::replace_if( plugName.begin(), plugName.end(), []( char c ) { return !::isalnum( c ); }, '_' );
		}
		addMember( it->first, it->second.get(), plugName );
	}
}

void CompoundDataPlug::fillCompoundData( IECore::CompoundDataMap &compoundDataMap ) const
{
	std::string name;
	for( MemberPlugIterator it( this ); !it.done(); ++it )
	{
		IECore::DataPtr data = memberDataAndName( it->get(), name );
		if( data )
		{
			compoundDataMap[name] = data;
		}
	}
}

IECore::MurmurHash CompoundDataPlug::hash() const
{
	IECore::MurmurHash h;
	for( MemberPlugIterator it( this ); !it.done(); ++it )
	{
		const MemberPlug *plug = it->get();
		bool active = true;
		if( plug->children().size() == 3 )
		{
			active = plug->getChild<BoolPlug>( 2 )->getValue();
		}
		if( active )
		{
			plug->getChild<ValuePlug>( 0 )->hash( h );
			plug->getChild<ValuePlug>( 1 )->hash( h );
		}
	}
	return h;
}

void CompoundDataPlug::hash( IECore::MurmurHash &h ) const
{
	h.append( hash() );
}

void CompoundDataPlug::fillCompoundObject( IECore::CompoundObject::ObjectMap &compoundObjectMap ) const
{
	std::string name;
	for( MemberPlugIterator it( this ); !it.done(); ++it )
	{
		IECore::DataPtr data = memberDataAndName( it->get(), name );
		if( data )
		{
			compoundObjectMap[name] = data;
		}
	}
}

IECore::DataPtr CompoundDataPlug::memberDataAndName( const MemberPlug *parameterPlug, std::string &name ) const
{
	if( parameterPlug->children().size() == 3 )
	{
		if( !parameterPlug->getChild<BoolPlug>( 2 )->getValue() )
		{
			return nullptr;
		}
	}

	if( parameterPlug->children().size() < 2 )
	{
		// we can end up here either if someone has very naughtily deleted
		// some plugs, or if we're being called during loading and the
		// child plugs haven't been fully constructed.
		return nullptr;
	}

	name = parameterPlug->getChild<StringPlug>( 0 )->getValue();
	if( !name.size() )
	{
		return nullptr;
	}

	const ValuePlug *valuePlug = parameterPlug->getChild<ValuePlug>( 1 );
	return PlugAlgo::extractDataFromPlug( valuePlug );
}

