//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "Gaffer/MatchPatternPathFilter.h"

#include "Gaffer/Path.h"

#include "IECore/MessageHandler.h"
#include "IECore/SimpleTypedData.h"

#include "boost/bind/bind.hpp"

using namespace boost::placeholders;
using namespace Gaffer;

static IECore::InternedString g_namePropertyName( "name" );

IE_CORE_DEFINERUNTIMETYPED( MatchPatternPathFilter );

MatchPatternPathFilter::MatchPatternPathFilter( const std::vector<IECore::StringAlgo::MatchPattern> &patterns, IECore::InternedString propertyName, bool leafOnly, IECore::CompoundDataPtr userData )
	:	PathFilter( userData ), m_patterns( patterns ), m_propertyName( propertyName ), m_leafOnly( leafOnly ), m_inverted( false )
{
}

MatchPatternPathFilter::~MatchPatternPathFilter()
{
}

void MatchPatternPathFilter::setMatchPatterns( const std::vector<IECore::StringAlgo::MatchPattern> &patterns )
{
	if( patterns == m_patterns )
	{
		return;
	}
	m_patterns = patterns;
	changedSignal()( this );
}

const std::vector<IECore::StringAlgo::MatchPattern> &MatchPatternPathFilter::getMatchPatterns() const
{
	return m_patterns;
}

void MatchPatternPathFilter::setPropertyName( IECore::InternedString propertyName )
{
	if( propertyName == m_propertyName )
	{
		return;
	}
	m_propertyName = propertyName;
	changedSignal()( this );
}

IECore::InternedString MatchPatternPathFilter::getPropertyName() const
{
	return m_propertyName;
}

void MatchPatternPathFilter::setInverted( bool inverted )
{
	if( inverted == m_inverted )
	{
		return;
	}
	m_inverted = inverted;
	changedSignal()( this );
}

bool MatchPatternPathFilter::getInverted() const
{
	return m_inverted;
}

void MatchPatternPathFilter::doFilter( std::vector<PathPtr> &paths, const IECore::Canceller *canceller ) const
{
	paths.erase(
		std::remove_if(
			paths.begin(),
			paths.end(),
			boost::bind( &MatchPatternPathFilter::remove, this, ::_1 )
		),
		paths.end()
	);
}

bool MatchPatternPathFilter::invert( bool b ) const
{
	return b != m_inverted;
}

bool MatchPatternPathFilter::remove( PathPtr path ) const
{
	try
	{
		if( m_leafOnly && !path->isLeaf() )
		{
			return false;
		}

		IECore::ConstStringDataPtr propertyData;
		const std::string *propertyValue = nullptr;
		if( m_propertyName == g_namePropertyName )
		{
			if( !path->names().size() )
			{
				return invert( true );
			}
			// quicker to retrieve the value from the path than as a property
			propertyValue = &(path->names().back().string());
		}
		else
		{
			propertyData = IECore::runTimeCast<const IECore::StringData>( path->property( m_propertyName ) );
			if( !propertyData )
			{
				throw IECore::Exception( "Expected StringData" );
			}
			propertyValue = &propertyData->readable();
		}

		for( std::vector<IECore::StringAlgo::MatchPattern>::const_iterator it = m_patterns.begin(), eIt = m_patterns.end(); it != eIt; ++it )
		{
			if( IECore::StringAlgo::match( propertyValue->c_str(), *it ) )
			{
				return invert( false );
			}
		}
		return invert( true );
	}
	catch( const std::exception &e )
	{
		IECore::msg( IECore::Msg::Error, "MatchPatternPathFilter", e.what() );
		return true;
	}
}
