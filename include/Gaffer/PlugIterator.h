//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#ifndef GAFFER_PLUGITERATOR_H
#define GAFFER_PLUGITERATOR_H

#include "Gaffer/Plug.h"
#include "Gaffer/FilteredChildIterator.h"
#include "Gaffer/FilteredRecursiveChildIterator.h"

#include "boost/iterator/filter_iterator.hpp"

namespace Gaffer
{

template<Plug::Direction D=Plug::Invalid, typename T=Plug>
struct PlugPredicate
{
	typedef T ChildType;

	bool operator()( GraphComponentPtr g )
	{
		typename T::Ptr p = IECore::runTimeCast<T>( g );
		if( !p )
		{
			return false;
		}
		if( D==Plug::Invalid )
		{
			return true;
		}
		return D==p->direction();
	}
};

typedef FilteredChildIterator<PlugPredicate<> > PlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, Plug> > InputPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, Plug> > OutputPlugIterator;

typedef FilteredRecursiveChildIterator<PlugPredicate<> > RecursivePlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, Plug> > RecursiveInputPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, Plug> > RecursiveOutputPlugIterator;

} // namespace Gaffer

#endif // GAFFER_PLUGITERATOR_H
