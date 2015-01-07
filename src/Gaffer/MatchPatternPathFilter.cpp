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

#include "boost/bind.hpp"

#include "IECore/SimpleTypedData.h"

#include "Gaffer/MatchPatternPathFilter.h"
#include "Gaffer/Path.h"

using namespace Gaffer;

static IECore::InternedString g_nameAttributeName( "name" );

IE_CORE_DEFINERUNTIMETYPED( MatchPatternPathFilter );

MatchPatternPathFilter::MatchPatternPathFilter( const std::vector<MatchPattern> &patterns, IECore::InternedString attributeName, bool leafOnly, IECore::CompoundDataPtr userData )
	:	PathFilter( userData ), m_patterns( patterns ), m_attributeName( attributeName ), m_leafOnly( leafOnly ), m_inverted( false )
{
}

MatchPatternPathFilter::~MatchPatternPathFilter()
{
}

void MatchPatternPathFilter::setMatchPatterns( const std::vector<MatchPattern> &patterns )
{
	if( patterns == m_patterns )
	{
		return;
	}
	m_patterns = patterns;
	changedSignal()( this );
}

const std::vector<MatchPattern> &MatchPatternPathFilter::getMatchPatterns() const
{
	return m_patterns;
}

void MatchPatternPathFilter::setAttributeName( IECore::InternedString attributeName )
{
	if( attributeName == m_attributeName )
	{
		return;
	}
	m_attributeName = attributeName;
	changedSignal()( this );
}

IECore::InternedString MatchPatternPathFilter::getAttributeName() const
{
	return m_attributeName;
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

void MatchPatternPathFilter::doFilter( std::vector<PathPtr> &paths ) const
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
	if( m_leafOnly && !path->isLeaf() )
	{
		return false;
	}

	IECore::ConstStringDataPtr attributeData;
	const std::string *attributeValue = NULL;
	if( m_attributeName == g_nameAttributeName )
	{
		if( !path->names().size() )
		{
			return invert( true );
		}
		// quicker to retrieve the value from the path than as an attribute
		attributeValue = &(path->names().back().string());
	}
	else
	{
		attributeData = IECore::runTimeCast<const IECore::StringData>( path->attribute( m_attributeName ) );
		if( !attributeData )
		{
			throw IECore::Exception( "Expected StringData" );
		}
		attributeValue = &attributeData->readable();
	}

	for( std::vector<MatchPattern>::const_iterator it = m_patterns.begin(), eIt = m_patterns.end(); it != eIt; ++it )
	{
		if( match( attributeValue->c_str(), *it ) )
		{
			return invert( false );
		}
	}
	return invert( true );
}
