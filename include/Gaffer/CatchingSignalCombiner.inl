//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_CATCHINGSIGNALCOMBINER_INL
#define GAFFER_CATCHINGSIGNALCOMBINER_INL

#include "IECore/MessageHandler.h"

namespace Gaffer
{

template<typename T>
template<typename InputIterator>
typename CatchingSignalCombiner<T>::result_type CatchingSignalCombiner<T>::operator()( InputIterator first, InputIterator last ) const
{
	result_type r = result_type();
	while( first != last )
	{
		try
		{
			r = *first;
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Error, "Emitting signal", e.what() );
		}
		catch( ... )
		{
			IECore::msg( IECore::Msg::Error, "Emitting signal", "Unknown error" );
		}
		++first;
	}
	return r;
};

// Specialisation for void return type.
template<>
template<typename InputIterator>
typename CatchingSignalCombiner<void>::result_type CatchingSignalCombiner<void>::operator()( InputIterator first, InputIterator last ) const
{
	while( first != last )
	{
		try
		{
			*first;
		}
		catch( const std::exception &e )
		{
			IECore::msg( IECore::Msg::Error, "Emitting signal", e.what() );
		}
		catch( ... )
		{
			IECore::msg( IECore::Msg::Error, "Emitting signal", "Unknown error" );
		}
		++first;
	}
};

} // namespace Gaffer

#endif // GAFFER_CATCHINGSIGNALCOMBINER_INL
