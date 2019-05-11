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
#include "Gaffer/Node.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// CompoundDataPlug implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( CompoundDataPlug )

CompoundDataPlug::CompoundDataPlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
}

CompoundDataPlug::~CompoundDataPlug()
{
}

bool CompoundDataPlug::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
	{
		return false;
	}

	return potentialChild->isInstanceOf( NameValuePlug::staticTypeId() );
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
		addChild( new NameValuePlug( it->first.string(), it->second.get(), plugName ) );
	}
}

void CompoundDataPlug::fillCompoundData( IECore::CompoundDataMap &compoundDataMap ) const
{
	std::string name;
	for( NameValuePlugIterator it( this ); !it.done(); ++it )
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
	for( NameValuePlugIterator it( this ); !it.done(); ++it )
	{
		const NameValuePlug *plug = it->get();
		bool active = true;
		if( plug->children().size() == 3 )
		{
			active = plug->enabledPlug()->getValue();
		}
		if( active )
		{
			plug->namePlug()->hash( h );
			const ValuePlug* valuePlug = plug->valuePlug<ValuePlug>();
			if( valuePlug )
			{
				valuePlug->hash( h );
			}
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
	for( NameValuePlugIterator it( this ); !it.done(); ++it )
	{
		IECore::DataPtr data = memberDataAndName( it->get(), name );
		if( data )
		{
			compoundObjectMap[name] = data;
		}
	}
}

IECore::DataPtr CompoundDataPlug::memberDataAndName( const NameValuePlug *parameterPlug, std::string &name ) const
{
	if( parameterPlug->enabledPlug() && !parameterPlug->enabledPlug()->getValue() )
	{
		return nullptr;
	}

	if( !parameterPlug->namePlug() || !parameterPlug->valuePlug() )
	{
		// we can end up here either if someone has very naughtily deleted
		// some plugs, or if we're being called during loading and the
		// child plugs haven't been fully constructed.
		return nullptr;
	}

	name = parameterPlug->namePlug()->getValue();
	if( !name.size() )
	{
		return nullptr;
	}

	const ValuePlug *valuePlug = parameterPlug->valuePlug<ValuePlug>();
	if( !valuePlug )
	{
		return nullptr;
	}

	return PlugAlgo::extractDataFromPlug( valuePlug );
}

void CompoundDataPlug::emitPlugSet()
{
    if( Node *n = node() )
    {
        Plug *p = this;
        while( p )
        {
            n->plugSetSignal()( p );
            p = p->parent<Plug>();
        }
    }

    // take a copy of the outputs, owning a reference - because who
    // knows what will be added and removed by the connected slots.
    std::vector<PlugPtr> o( outputs().begin(), outputs().end() );
    for( std::vector<PlugPtr>::const_iterator it=o.begin(), eIt=o.end(); it!=eIt; ++it )
    {
        if( CompoundDataPlug *output = IECore::runTimeCast<CompoundDataPlug>( it->get() ) )
        {
            output->emitPlugSet();
        }
    }
}

