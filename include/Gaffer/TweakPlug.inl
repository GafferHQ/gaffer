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

#ifndef GAFFER_TWEAKPLUG_INL
#define GAFFER_TWEAKPLUG_INL

#include "Gaffer/PlugAlgo.h"

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
			boost::str( boost::format( "Cannot apply tweak to \"%s\" : Value plug has unsupported type \"%s\"" ) % name % valuePlug()->typeName() )
		);
	}

	if( mode == Gaffer::TweakPlug::Create )
	{
		return setDataFunctor( name, newData );
	}

	const IECore::Data *currentValue = getDataFunctor( name );

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
			boost::str( boost::format( "Cannot apply tweak to \"%s\" : Value of type \"%s\" does not match parameter of type \"%s\"" ) % name % currentValue->typeName() % newData->typeName() )
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
		else if( !( mode == Gaffer::TweakPlug::Replace && missingMode == Gaffer::TweakPlug::MissingMode::IgnoreOrReplace) )
		{
			throw IECore::Exception( boost::str( boost::format( "Cannot apply tweak with mode %s to \"%s\" : This parameter does not exist" ) % modeToString( mode ) % name ) );
		}
	}

	if(
		mode == Gaffer::TweakPlug::Add ||
		mode == Gaffer::TweakPlug::Subtract ||
		mode == Gaffer::TweakPlug::Multiply ||
		mode == Gaffer::TweakPlug::Min ||
		mode == Gaffer::TweakPlug::Max
	)
	{
		applyNumericTweak( currentValue, newData.get(), newData.get(), mode, name );
	}
	else if(
		mode == TweakPlug::ListAppend ||
		mode == TweakPlug::ListPrepend ||
		mode == TweakPlug::ListRemove
	)
	{
		applyListTweak( currentValue, newData.get(), newData.get(), mode, name );
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

} // namespace Gaffer

#endif // GAFFER_TWEAKPLUG_INL
