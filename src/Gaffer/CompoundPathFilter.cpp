//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012-2014, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/CompoundPathFilter.h"

#include "IECore/Exception.h"

#include "boost/bind.hpp"

using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( CompoundPathFilter );

CompoundPathFilter::CompoundPathFilter( IECore::CompoundDataPtr userData )
	:	PathFilter( userData )
{
}

CompoundPathFilter::~CompoundPathFilter()
{
}

void CompoundPathFilter::addFilter( PathFilterPtr filter )
{
	addFilterInternal( filter );
	if( getEnabled() )
	{
		changedSignal()( this );
	}
}

void CompoundPathFilter::removeFilter( PathFilter *filter )
{
	for( std::list<Filter>::iterator it = m_filters.begin(), eIt = m_filters.end(); it != eIt; ++it )
	{
		if( it->filter == filter )
		{
			m_filters.erase( it );
			if( getEnabled() )
			{
				changedSignal()( this );
			}
			return;
		}
	}
	throw IECore::Exception( "Filter not found" );
}

void CompoundPathFilter::setFilters( const Filters &filters )
{
	bool same = false;
	if( filters.size() == m_filters.size() )
	{
		same = true;
		std::list<Filter>::const_iterator it = m_filters.begin();
		for( size_t i = 0, e = filters.size(); i < e; ++i, ++it )
		{
			if( filters[i] != it->filter )
			{
				same = false;
				break;
			}
		}
	}
	if( same )
	{
		return;
	}

	m_filters.clear();
	for( Filters::const_iterator it = filters.begin(), eIt = filters.end(); it != eIt; ++it )
	{
		addFilterInternal( *it );
	}
	if( getEnabled() )
	{
		changedSignal()( this );
	}
}

void CompoundPathFilter::getFilters( Filters &filters ) const
{
	for( std::list<Filter>::const_iterator it = m_filters.begin(), eIt = m_filters.end(); it != eIt; ++it )
	{
		filters.push_back( it->filter );
	}
}

void CompoundPathFilter::doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const
{
	for( std::list<Filter>::const_iterator it = m_filters.begin(), eIt = m_filters.end(); it != eIt; ++it )
	{
		it->filter->filter( paths );
	}
}

void CompoundPathFilter::addFilterInternal( PathFilterPtr filter )
{
	for( std::list<Filter>::const_iterator it = m_filters.begin(), eIt = m_filters.end(); it != eIt; ++it )
	{
		if( it->filter == filter )
		{
			throw IECore::Exception( "Filter already added" );
		}
	}
	m_filters.push_back( Filter() );
	m_filters.back().filter = filter;
	m_filters.back().filterChangedConnection = filter->changedSignal().connect( boost::bind( &CompoundPathFilter::filterChanged, this ) );
}

void CompoundPathFilter::filterChanged()
{
	if( getEnabled() )
	{
		changedSignal()( this );
	}
}
