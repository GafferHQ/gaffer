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
		return setDataFunctor( name, nullptr );
	}

	IECore::DataPtr tweakData = Gaffer::PlugAlgo::getValueAsData( valuePlug() );
	if( !tweakData )
	{
		throw IECore::Exception(
			fmt::format( "Cannot apply tweak to \"{}\" : Value plug has unsupported type \"{}\"", name, valuePlug()->typeName() )
		);
	}

	if( mode == Gaffer::TweakPlug::Create )
	{
		return setDataFunctor( name, tweakData );
	}

	const IECore::Data *currentValue = getDataFunctor( name, /* withFallback = */ mode != Gaffer::TweakPlug::CreateIfMissing );

	if( IECore::runTimeCast<const IECore::InternedStringData>( currentValue ) )
	{
		if( const IECore::StringData *s = IECore::runTimeCast<const IECore::StringData>( tweakData.get() ) )
		{
			tweakData = new IECore::InternedStringData( s->readable() );
		}
	}

	if( !currentValue )
	{
		if(
			mode == Gaffer::TweakPlug::ListAppend ||
			mode == Gaffer::TweakPlug::ListPrepend ||
			mode == Gaffer::TweakPlug::CreateIfMissing
		)
		{
			setDataFunctor( name, tweakData );
			return true;
		}
		else if( missingMode == Gaffer::TweakPlug::MissingMode::Ignore || mode == Gaffer::TweakPlug::ListRemove )
		{
			return false;
		}
		throw IECore::Exception( fmt::format( "Cannot apply tweak with mode {} to \"{}\" : This parameter does not exist", modeToString( mode ), name ) );
	}

	if( mode == Gaffer::TweakPlug::CreateIfMissing )
	{
		// \todo - It would make more sense if this returned false ( this tweak technically is applying, but it's
		// not doing anything ).  Fixing this now would technically be a compatibility break though. If we fixed
		//this, we could clarify the documentation of applyTweak:
		// instead of "returns true if any tweaks were applied" it could be "returns true if any changes were made".
		return true;
	}

	// valueTweakData
	IECore::DataPtr resultData = currentValue->copy();

	applyTweakInternal( resultData.get(), tweakData.get(), mode, name );
	setDataFunctor( name, resultData );


	return true;
}

template<class GetDataFunctor, class SetDataFunctor>
bool TweakPlug::applyElementwiseTweak(
	GetDataFunctor &&getDataFunctor,
	SetDataFunctor &&setDataFunctor,
	size_t createSize,
	const boost::dynamic_bitset<> *mask,
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
		return setDataFunctor( name, DataAndIndices() );
	}

	IECore::DataPtr tweakData = Gaffer::PlugAlgo::getValueAsData( valuePlug() );
	if( !tweakData )
	{
		throw IECore::Exception(
			fmt::format( "Cannot apply tweak to \"{}\" : Value plug has unsupported type \"{}\"", name, valuePlug()->typeName() )
		);
	}

	DataAndIndices current;
	if( mode != Gaffer::TweakPlug::Create )
	{
		current = getDataFunctor( name, /* withFallback = */ mode != Gaffer::TweakPlug::CreateIfMissing );
	}

	if(
		mode == Gaffer::TweakPlug::Create ||
		( !current.data && (
			mode == Gaffer::TweakPlug::CreateIfMissing ||
			mode == Gaffer::TweakPlug::ListAppend ||
			mode == Gaffer::TweakPlug::ListPrepend
		) )
	)
	{
		DataAndIndices result;
		if( mask )
		{
			result.data = createVectorDataFromElement( tweakData.get(), createSize, false, name );

			applyVectorElementTweak( result.data.get(), tweakData.get(), nullptr, TweakPlug::Replace, name, mask );
		}
		else
		{
			result.data = createVectorDataFromElement( tweakData.get(), createSize, true, name );
		}
		return setDataFunctor( name, result );
	}

	if( IECore::runTimeCast<const IECore::InternedStringData>( current.data ) )
	{
		if( const IECore::StringData *s = IECore::runTimeCast<const IECore::StringData>( tweakData.get() ) )
		{
			tweakData = new IECore::InternedStringData( s->readable() );
		}
	}

	if( !current.data )
	{
		if( missingMode == Gaffer::TweakPlug::MissingMode::Ignore || mode == Gaffer::TweakPlug::ListRemove )
		{
			return false;
		}
		throw IECore::Exception( fmt::format( "Cannot apply tweak with mode {} to \"{}\" : This parameter does not exist", modeToString( mode ), name ) );
	}

	if( mode == Gaffer::TweakPlug::CreateIfMissing )
	{
		// \todo - See \todo in applyTweak about this return value.
		return true;
	}

	DataAndIndices result;
	result.data = current.data->copy();
	if( current.indices )
	{
		result.indices = current.indices->copy();
	}
	applyVectorElementTweak( result.data.get(), tweakData.get(), result.indices.get(), mode, name, mask );
	setDataFunctor( name, result );

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
