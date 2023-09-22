//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2023, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferImage/OpenColorIOContext.h"

#include "Gaffer/Context.h"
#include "Gaffer/OptionalValuePlug.h"

#include "OpenColorIO/OpenColorIO.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferImage;

GAFFER_NODE_DEFINE_TYPE( OpenColorIOContext );

size_t OpenColorIOContext::g_firstPlugIndex;

OpenColorIOContext::OpenColorIOContext( const std::string &name )
	:	ContextProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new OptionalValuePlug( "config", new StringPlug( "value" ) ) );
	addChild( new OptionalValuePlug( "workingSpace", new StringPlug( "value", Plug::In, OCIO_NAMESPACE::ROLE_SCENE_LINEAR ) ) );

	addChild( new ValuePlug( "variables" ) );
	addChild( new AtomicCompoundDataPlug( "extraVariables", Plug::In, new IECore::CompoundData ) );
	addChild( new AtomicCompoundDataPlug( "__combinedVariables", Plug::Out, new IECore::CompoundData ) );
}

OpenColorIOContext::~OpenColorIOContext()
{
}

Gaffer::OptionalValuePlug *OpenColorIOContext::configPlug()
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex );
}

const Gaffer::OptionalValuePlug *OpenColorIOContext::configPlug() const
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex );
}

Gaffer::OptionalValuePlug *OpenColorIOContext::workingSpacePlug()
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 1 );
}

const Gaffer::OptionalValuePlug *OpenColorIOContext::workingSpacePlug() const
{
	return getChild<OptionalValuePlug>( g_firstPlugIndex + 1 );
}

Gaffer::ValuePlug *OpenColorIOContext::variablesPlug()
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

const Gaffer::ValuePlug *OpenColorIOContext::variablesPlug() const
{
	return getChild<ValuePlug>( g_firstPlugIndex + 2 );
}

Gaffer::AtomicCompoundDataPlug *OpenColorIOContext::extraVariablesPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::AtomicCompoundDataPlug *OpenColorIOContext::extraVariablesPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 3 );
}

Gaffer::AtomicCompoundDataPlug *OpenColorIOContext::combinedVariablesPlug()
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::AtomicCompoundDataPlug *OpenColorIOContext::combinedVariablesPlug() const
{
	return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 4 );
}

void OpenColorIOContext::affects( const Gaffer::Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	ContextProcessor::affects( input, outputs );

	if(
		configPlug()->isAncestorOf( input ) ||
		workingSpacePlug()->isAncestorOf( input ) ||
		variablesPlug()->isAncestorOf( input ) ||
		input == extraVariablesPlug()
	)
	{
		outputs.push_back( combinedVariablesPlug() );
	}
}

bool OpenColorIOContext::affectsContext( const Gaffer::Plug *input ) const
{
	return input == combinedVariablesPlug();
}

void OpenColorIOContext::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	ContextProcessor::hash( output, context, h );

	if( output == combinedVariablesPlug() )
	{
		configPlug()->hash( h );
		workingSpacePlug()->hash( h );
		variablesPlug()->hash( h );
		extraVariablesPlug()->hash( h );
	}
}

void OpenColorIOContext::compute( ValuePlug *output, const Context *context ) const
{
	if( output == combinedVariablesPlug() )
	{
		IECore::CompoundDataPtr resultData = new IECore::CompoundData;
		IECore::CompoundDataMap &result = resultData->writable();

		if( configPlug()->enabledPlug()->getValue() )
		{
			result["ocio:config"] = new StringData( configPlug()->valuePlug<StringPlug>()->getValue() );
		}

		if( workingSpacePlug()->enabledPlug()->getValue() )
		{
			result["ocio:workingSpace"] = new StringData( workingSpacePlug()->valuePlug<StringPlug>()->getValue() );
		}

		ConstCompoundDataPtr extraVariables = extraVariablesPlug()->getValue();
		for( auto &[name, value] : extraVariables->readable() )
		{
			if( name.string().empty() )
			{
				continue;
			}
			if( auto stringData = runTimeCast<const StringData>( value ) )
			{
				result["ocio:stringVar:"+name.string()] = boost::const_pointer_cast<StringData>( stringData );
			}
			else
			{
				throw IECore::Exception( fmt::format( "Extra variable {} is {}, but must be StringData", name.string(), value->typeName() ) );
			}
		}

		for( const auto &plug : NameValuePlug::Range( *variablesPlug() ) )
		{
			if( auto enabledPlug = plug->enabledPlug() )
			{
				if( !enabledPlug->getValue() )
				{
					continue;
				}
			}

			const string name = plug->namePlug()->getValue();
			if( name.empty() )
			{
				continue;
			}
			if( auto stringPlug = plug->valuePlug<StringPlug>() )
			{
				result["ocio:stringVar:"+name] = new StringData( stringPlug->getValue() );
			}
			else
			{
				throw IECore::Exception( fmt::format( "Variable {} is {}, but must be StringPlug", name, plug->valuePlug()->typeName() ) );
			}
		}

		static_cast<AtomicCompoundDataPlug *>( output )->setValue( resultData );
		return;
	}

	return ContextProcessor::compute( output, context );
}

void OpenColorIOContext::processContext( Gaffer::Context::EditableScope &context, IECore::ConstRefCountedPtr &storage ) const
{
	IECore::ConstCompoundDataPtr combinedVariables = combinedVariablesPlug()->getValue();
	for( const auto &[name, value] : combinedVariables->readable() )
	{
		// Cast is safe because of type checks performed in `compute()`.
		// Note that we don't use `OpenColorIOAlgo::addVariable()` here because
		// it would need to construct an InternedString on the fly - we can do
		// better by caching that in `combinedVariablesPlug()`.
		context.set( name, &static_cast<const StringData *>( value.get() )->readable() );
	}
	storage = combinedVariables;
}
