//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#pragma once

#include "Gaffer/PlugAlgo.h"

#include "IECore/TypeTraits.h"

#include "fmt/format.h"

namespace Gaffer
{

template<typename T>
T *TweakPlug::valuePlug()
{
	return IECore::runTimeCast<T>( valuePlugInternal() );
}

template<typename T>
const T *TweakPlug::valuePlug() const
{
	return IECore::runTimeCast<const T>( valuePlugInternal() );
}

template<class GetDataFunctor, class SetDataFunctor>
bool TweakPlug::applyTweak(
	GetDataFunctor &&getDataFunctor,
	SetDataFunctor &&setDataFunctor,
	MissingMode missingMode
) const
{
	if( !enabledPlug()->getValue() )
	{
		return false;
	}

	const std::string name = namePlug()->getValue();
	if( name.empty() )
	{
		return false;
	}

	const Mode mode = static_cast<Mode>( modePlug()->getValue() );

	if( mode == Gaffer::TweakPlug::Remove )
	{
		return setDataFunctor( name,  nullptr );
	}

	IECore::DataPtr newData = Gaffer::PlugAlgo::getValueAsData( valuePlug() );
	if( !newData )
	{
		throw IECore::Exception(
			fmt::format( "Cannot apply tweak to \"{}\" : Value plug has unsupported type \"{}\"", name, valuePlug()->typeName() )
		);
	}

	if( mode == Gaffer::TweakPlug::Create )
	{
		return setDataFunctor( name, newData );
	}

	const IECore::Data *currentValue = getDataFunctor( name, /* withFallback = */ mode != Gaffer::TweakPlug::CreateIfMissing );

	if( IECore::runTimeCast<const IECore::InternedStringData>( currentValue ) )
	{
		if( const IECore::StringData *s = IECore::runTimeCast<const IECore::StringData>( newData.get() ) )
		{
			newData = new IECore::InternedStringData( s->readable() );
		}
	}

	if( currentValue && currentValue->typeId() != newData->typeId() )
	{
		throw IECore::Exception(
			fmt::format( "Cannot apply tweak to \"{}\" : Value of type \"{}\" does not match parameter of type \"{}\"", name, currentValue->typeName(), newData->typeName() )
		);
	}

	if( !currentValue )
	{
		if(
			mode == Gaffer::TweakPlug::ListAppend ||
			mode == Gaffer::TweakPlug::ListPrepend ||
			mode == Gaffer::TweakPlug::CreateIfMissing
		)
		{
			setDataFunctor( name, newData );
			return true;
		}
		else if( missingMode == Gaffer::TweakPlug::MissingMode::Ignore || mode == Gaffer::TweakPlug::ListRemove )
		{
			return false;
		}
		throw IECore::Exception( fmt::format( "Cannot apply tweak with mode {} to \"{}\" : This parameter does not exist", modeToString( mode ), name ) );
	}

	if(
		mode == Gaffer::TweakPlug::Add ||
		mode == Gaffer::TweakPlug::Subtract ||
		mode == Gaffer::TweakPlug::Multiply ||
		mode == Gaffer::TweakPlug::Min ||
		mode == Gaffer::TweakPlug::Max
	)
	{
		applyNumericDataTweak( currentValue, newData.get(), newData.get(), mode, name );
	}
	else if(
		mode == TweakPlug::ListAppend ||
		mode == TweakPlug::ListPrepend ||
		mode == TweakPlug::ListRemove
	)
	{
		applyListTweak( currentValue, newData.get(), newData.get(), mode, name );
	}
	else if( mode == TweakPlug::Replace )
	{
		applyReplaceTweak( currentValue, newData.get() );
	}

	if( mode != Gaffer::TweakPlug::CreateIfMissing )
	{
		setDataFunctor( name, newData );
	}

	return true;
}

template<class GetDataFunctor, class SetDataFunctor>
bool TweaksPlug::applyTweaks(
	GetDataFunctor &&getDataFunctor,
	SetDataFunctor &&setDataFunctor,
	TweakPlug::MissingMode missingMode
) const
{
	bool tweakApplied = false;

	for( auto &tweakPlug : TweakPlug::Range( *this ) )
	{
		if( tweakPlug->applyTweak( getDataFunctor, setDataFunctor, missingMode ) )
		{
			tweakApplied = true;
		}
	}

	return tweakApplied;
}

template<typename T>
T TweakPlug::vectorAwareMin( const T &v1, const T &v2 )
{
	if constexpr( IECore::TypeTraits::IsVec<T>::value || IECore::TypeTraits::IsColor<T>::value )
	{
		T result;
		for( size_t i = 0; i < T::dimensions(); ++i )
		{
			result[i] = std::min( v1[i], v2[i] );
		}
		return result;
	}
	else
	{
		return std::min( v1, v2 );
	}
}

template<typename T>
T TweakPlug::vectorAwareMax( const T &v1, const T &v2 )
{
	if constexpr( IECore::TypeTraits::IsVec<T>::value || IECore::TypeTraits::IsColor<T>::value )
	{
		T result;
		for( size_t i = 0; i < T::dimensions(); ++i )
		{
			result[i] = std::max( v1[i], v2[i] );
		}
		return result;
	}
	else
	{
		return std::max( v1, v2 );
	}
}

template< typename T >
T TweakPlug::applyNumericTweak(
	const T &source,
	const T &tweak,
	TweakPlug::Mode mode,
	const std::string &tweakName
)
{
	if constexpr(
		( std::is_arithmetic_v<T> && !std::is_same_v< T, bool > ) ||
		IECore::TypeTraits::IsVec<T>::value ||
		IECore::TypeTraits::IsColor<T>::value
	)
	{
		switch( mode )
		{
			case TweakPlug::Add :
				return source + tweak;
			case TweakPlug::Subtract :
				return source - tweak;
			case TweakPlug::Multiply :
				return source * tweak;
			case TweakPlug::Min :
				return vectorAwareMin( source, tweak );
			case TweakPlug::Max :
				return vectorAwareMax( source, tweak );
			case TweakPlug::ListAppend :
			case TweakPlug::ListPrepend :
			case TweakPlug::ListRemove :
			case TweakPlug::Replace :
			case TweakPlug::Remove :
			case TweakPlug::Create :
			case TweakPlug::CreateIfMissing :
				throw IECore::Exception(
					fmt::format(
						"Cannot apply tweak with mode {} using applyNumericTweak.",
						modeToString( mode )
					)
				);
			default:
				throw IECore::Exception( fmt::format( "Not a valid tweak mode: {}.", mode ) );
		}
	}
	else
	{
		// NOTE: If we are operating on variables that aren't actually stored in a Data, then the
		// data type reported here may not be technically correct - for example, we might want to
		// call this on elements of a StringVectorData, in which case this would report a type of
		// "StringData", but there is nothing of actual type "StringData". This message still
		// communicates the actual problem though ( we don't support arithmetic on strings ).

		throw IECore::Exception(
			fmt::format(
				"Cannot apply tweak with mode {} to \"{}\" : Data type {} not supported.",
				modeToString( mode ), tweakName, IECore::TypedData<T>::staticTypeName()
			)
		);
	}
}

} // namespace Gaffer
