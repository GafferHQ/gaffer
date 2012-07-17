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

#include "IECore/Display.h"

#include "GafferScene/ParameterListPlug.h"
#include "GafferScene/Displays.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Displays );

Displays::Displays( const std::string &name )
	:	GlobalsProcessor( name )
{
	addChild(
		new CompoundPlug(
			"displays",
			Plug::In,
			Plug::Default | Plug::Dynamic
		)
	);
}

Displays::~Displays()
{
}

Gaffer::CompoundPlug *Displays::displaysPlug()
{
	return getChild<CompoundPlug>( "displays" );
}

const Gaffer::CompoundPlug *Displays::displaysPlug() const
{
	return getChild<CompoundPlug>( "displays" );
}

Gaffer::CompoundPlug *Displays::addDisplay( const std::string &name, const std::string &type, const std::string &data )
{
	CompoundPlugPtr displayPlug = new CompoundPlug( "display1" );
	displayPlug->setFlags( Plug::Dynamic, true );
	
	BoolPlugPtr activePlug = new BoolPlug( "active", Plug::In, true );
	activePlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( activePlug );
	
	StringPlugPtr namePlug = new StringPlug( "name" );
	namePlug->setValue( name );
	namePlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( namePlug );

	StringPlugPtr typePlug = new StringPlug( "type" );
	typePlug->setValue( type );
	typePlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( typePlug );
	
	StringPlugPtr dataPlug = new StringPlug( "data" );
	dataPlug->setValue( data );
	dataPlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( dataPlug );
	
	ParameterListPlugPtr parametersPlug = new ParameterListPlug( "parameters" );
	parametersPlug->setFlags( Plug::Dynamic, true );
	displayPlug->addChild( parametersPlug );
	
	displaysPlug()->addChild( displayPlug );
	
	return displayPlug;
}

void Displays::affects( const ValuePlug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );
	
	if( displaysPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

IECore::ObjectVectorPtr Displays::processGlobals( const Gaffer::Context *context, IECore::ConstObjectVectorPtr inputGlobals ) const
{
	ObjectVectorPtr result = new ObjectVector;
	
	// add our displays to the result
	set<string> displaysCreated;
	const CompoundPlug *dsp = displaysPlug(); 
	for( InputCompoundPlugIterator it( dsp ); it != it.end(); it++ )
	{
		const CompoundPlug *displayPlug = *it;
		if( displayPlug->getChild<BoolPlug>( "active" )->getValue() )
		{
			std::string name = displayPlug->getChild<StringPlug>( "name" )->getValue();
			std::string type = displayPlug->getChild<StringPlug>( "type" )->getValue();
			std::string data = displayPlug->getChild<StringPlug>( "data" )->getValue();
			if( name.size() && type.size() && data.size() )
			{
				DisplayPtr d = new Display( name, type, data );
				displayPlug->getChild<ParameterListPlug>( "parameters" )->fillParameterList( d->parameters() );
				result->members().push_back( d );
				displaysCreated.insert( name );
			}
		}
	}
	
	// copy over the input globals, unless they're a display with a name clashing with one
	// we made ourselves.
	if( inputGlobals )
	{
		for( vector<ObjectPtr>::const_iterator it = inputGlobals->members().begin(), eIt = inputGlobals->members().end(); it!=eIt; it++ )
		{
			bool transfer = true;
			if( const Display *d = runTimeCast<Display>( it->get() ) )
			{
				if( displaysCreated.find( d->getName() ) != displaysCreated.end() )
				{
					transfer = false;
				}
			}
			if( transfer )
			{
				result->members().push_back( *it );
			}
		}
	}
	
	return result;
}
