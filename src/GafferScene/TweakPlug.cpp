//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/TweakPlug.h"

#include "Gaffer/PlugAlgo.h"
#include "Gaffer/SplinePlug.h"

#include "IECore/DataAlgo.h"
#include "IECore/TypeTraits.h"
#include "IECore/SimpleTypedData.h"
#include "IECore/SplineData.h"
#include "IECore/StringAlgo.h"

using namespace std;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

//////////////////////////////////////////////////////////////////////////
// TweakPlug
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( TweakPlug );

TweakPlug::TweakPlug( const std::string &tweakName, Gaffer::ValuePlugPtr valuePlug, bool enabled )
	:	TweakPlug( "tweak", In, Default | Dynamic )
{
	valuePlug->setName( "value" );
	valuePlug->setFlags( Dynamic, true );
	addChild( valuePlug );

	namePlug()->setValue( tweakName );
	enabledPlug()->setValue( enabled );
}

TweakPlug::TweakPlug( const std::string &tweakName, const IECore::Data *value, bool enabled )
	:	TweakPlug( tweakName, PlugAlgo::createPlugFromData( "value", In, Default | Dynamic, value ), enabled )
{
}

TweakPlug::TweakPlug( const std::string &name, Direction direction, unsigned flags )
	:	Plug( name, direction, flags )
{
	addChild( new StringPlug( "name" ) );
	addChild( new BoolPlug( "enabled", Plug::In, true ) );
	addChild( new IntPlug( "mode", Plug::In, Replace, Replace, Remove ) );
}

Gaffer::StringPlug *TweakPlug::namePlug()
{
	return getChild<StringPlug>( 0 );
}

const Gaffer::StringPlug *TweakPlug::namePlug() const
{
	return getChild<StringPlug>( 0 );
}

Gaffer::BoolPlug *TweakPlug::enabledPlug()
{
	return getChild<BoolPlug>( 1 );
}

const Gaffer::BoolPlug *TweakPlug::enabledPlug() const
{
	return getChild<BoolPlug>( 1 );
}

Gaffer::IntPlug *TweakPlug::modePlug()
{
	return getChild<IntPlug>( 2 );
}

const Gaffer::IntPlug *TweakPlug::modePlug() const
{
	return getChild<IntPlug>( 2 );
}

template<typename T>
T *TweakPlug::valuePlug()
{
	return getChild<T>( 3 );
}

template<typename T>
const T *TweakPlug::valuePlug() const
{
	return getChild<T>( 3 );
}

bool TweakPlug::acceptsChild( const Gaffer::GraphComponent *potentialChild ) const
{
	if( !Plug::acceptsChild( potentialChild ) )
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
		potentialChild->isInstanceOf( BoolPlug::staticTypeId() ) &&
		potentialChild->getName() == "enabled" &&
		!getChild<Plug>( "enabled" )
	)
	{
		return true;
	}
	else if(
		potentialChild->isInstanceOf( IntPlug::staticTypeId() ) &&
		potentialChild->getName() == "mode" &&
		!getChild<Plug>( "mode" )
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

	return false;
}

Gaffer::PlugPtr TweakPlug::createCounterpart( const std::string &name, Direction direction ) const
{
	PlugPtr result = new TweakPlug( name, direction, getFlags() );
	if( const Plug *p = valuePlug<ValuePlug>() )
	{
		result->addChild( p->createCounterpart( p->getName(), direction ) );
	}
	return result;
}

// Utility methods need by applyTweak
namespace
{

const char *modeToString( TweakPlug::Mode mode )
{
	switch( mode )
	{
		case TweakPlug::Replace :
			return "Replace";
		case TweakPlug::Add :
			return "Add";
		case TweakPlug::Subtract :
			return "Subtract";
		case TweakPlug::Multiply :
			return "Multiply";
		case TweakPlug::Remove :
			return "Remove";
		default :
			return "Invalid";
	}
}

// TODO - if these make sense, I guess they should be pushed back to cortex

// IsColorTypedData
template< typename T > struct IsColorTypedData : boost::mpl::and_< TypeTraits::IsTypedData<T>, TypeTraits::IsColor< typename TypeTraits::ValueType<T>::type > > {};

// SupportsArithmeticData
template< typename T > struct SupportsArithData : boost::mpl::or_<  TypeTraits::IsNumericSimpleTypedData<T>, TypeTraits::IsVecTypedData<T>, IsColorTypedData<T>> {};

class NumericTweak
{
public:
	NumericTweak( IECore::Data *sourceData, TweakPlug::Mode mode, const std::string &parameterName )
		: m_sourceData( sourceData ), m_mode( mode ), m_parameterName( parameterName )
	{
	}

	template<typename T>
	void operator()( T * data, typename std::enable_if<SupportsArithData<T>::value>::type *enabler = nullptr ) const
	{
		T *sourceDataCast = runTimeCast<T>( m_sourceData );
		switch( m_mode )
		{
			case TweakPlug::Add :
				data->writable() += sourceDataCast->readable();
				break;
			case TweakPlug::Subtract :
				data->writable() -= sourceDataCast->readable();
				break;
			case TweakPlug::Multiply :
				data->writable() *= sourceDataCast->readable();
				break;
			case TweakPlug::Replace :
			case TweakPlug::Remove :
				// These cases are unused - we handle replace and remove mode outside of numericTweak.
				// But the compiler gets unhappy if we don't handle some cases
				break;
		}
	}

	void operator()( Data * data ) const
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak with mode %s to \"%s\" : Data type %s not supported." ) % modeToString( m_mode ) % m_parameterName % m_sourceData->typeName() ) );
	}

private:
	
	IECore::Data *m_sourceData;
	TweakPlug::Mode m_mode;
	const std::string &m_parameterName;
};

} // namespace

void TweakPlug::applyTweak( IECore::CompoundData *parameters, bool requireExists )
{
	if( !enabledPlug()->getValue() )
	{
		return;
	}
	const std::string name = namePlug()->getValue();
	if( name.empty() )
	{
		return;
	}

	Mode mode = static_cast<Mode>( modePlug()->getValue() );
	if( mode == Remove )
	{
		parameters->writable().erase( name );
		return;
	}


	Data *parameterValue = parameters->member<Data>( name );
	DataPtr newData = PlugAlgo::extractDataFromPlug( valuePlug<ValuePlug>() );
	if( !newData )
	{
		throw IECore::Exception(
			boost::str( boost::format( "Cannot apply to tweak to \"%s\" : Value plug has unsupported type \"%s\"" ) % name % valuePlug<ValuePlug>()->typeName() )
		);
	}
	if( parameterValue && parameterValue->typeId() != newData->typeId() )
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak to \"%s\" : Value of type \"%s\" does not match parameter of type \"%s\"" ) % name % parameterValue->typeName() % newData->typeName() ) );
	}

	if( mode == Replace )
	{
		if( !parameterValue && requireExists )
		{
			throw IECore::Exception( boost::str( boost::format( "Cannot replace parameter \"%s\" which does not exist" ) % name ) );
		}
		
		parameters->writable()[name] = newData;
		return;
	}

	if( !parameterValue )
	{
		throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak with mode %s to \"%s\" : This parameter does not exist" ) % modeToString( mode ) % name ) );
	}

	NumericTweak t( newData.get(), mode, name );
	dispatch( parameterValue, t );


}

