//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/Path.h"

#include "Gaffer/PathFilter.h"

#include "IECore/SimpleTypedData.h"
#include "IECore/StringAlgo.h"

#include "boost/bind.hpp"

using namespace std;
using namespace IECore;
using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( Path );

static InternedString g_namePropertyName( "name" );
static InternedString g_fullNamePropertyName( "fullName" );

Path::Path( PathFilterPtr filter )
	:	m_pathChangedSignal( nullptr )
{
	setFilter( filter );
}

Path::Path( const std::string &path, PathFilterPtr filter )
	:	m_pathChangedSignal( nullptr )
{
	setFromString( path );
	setFilter( filter );
}

Path::Path( const Names &names, const IECore::InternedString &root, PathFilterPtr filter )
	:	m_root( root ), m_names( names ), m_pathChangedSignal( nullptr )
{
	for( Names::const_iterator it = m_names.begin(), eIt = m_names.end(); it != eIt; ++it )
	{
		checkName( *it );
	}
	setFilter( filter );
}

Path::~Path()
{
	if( havePathChangedSignal() && m_filter )
	{
		// In an ideal world, we'd derive from Signals::Trackable, and wouldn't
		// need to do this manual connection management. But we construct a lot of Path
		// instances and trackable has significant overhead so we must avoid it. We must
		// disconnect somehow though, otherwise when the filter changes, filterChanged()
		// will be called on a dead Path instance.
		/// \todo Review this decision - it was made when we were using `boost::signals::trackable`
		/// and may not longer be valid.
		m_filter->changedSignal().disconnect( boost::bind( &Path::filterChanged, this ) );
	}
	delete m_pathChangedSignal;
}

const IECore::InternedString &Path::root() const
{
	return m_root;
}

bool Path::isEmpty() const
{
	return m_names.empty() && m_root.string().empty();
}

bool Path::isValid( const IECore::Canceller *canceller ) const
{
	return !isEmpty();
}

bool Path::isLeaf( const IECore::Canceller *canceller ) const
{
	return false;
}

void Path::propertyNames( std::vector<IECore::InternedString> &names, const IECore::Canceller *canceller ) const
{
	names.push_back( g_namePropertyName );
	names.push_back( g_fullNamePropertyName );
}

IECore::ConstRunTimeTypedPtr Path::property( const IECore::InternedString &name, const IECore::Canceller *canceller ) const
{
	if( name == g_namePropertyName )
	{
		if( m_names.size() )
		{
			return new StringData( m_names.back().string() );
		}
		else
		{
			return new StringData( "" );
		}
	}
	else if( name == g_fullNamePropertyName )
	{
		return new StringData( this->string() );
	}
	return nullptr;
}

PathPtr Path::parent() const
{
	if( m_names.empty() )
	{
		return nullptr;
	}

	PathPtr result = copy();
	result->m_names.pop_back();

	return result;
}

size_t Path::children( std::vector<PathPtr> &children, const IECore::Canceller *canceller ) const
{
	doChildren( children, canceller );
	if( m_filter )
	{
		m_filter->filter( children, canceller );
	}
	return children.size();
}

void Path::setFilter( PathFilterPtr filter )
{
	if( filter == m_filter )
	{
		return;
	}

	// We may need to connect to Filter::changedSignal() so we can
	// emit pathChangedSignal() appropriately. But it's not worth making
	// the connection unless m_pathChangedSignal exists.
	if( havePathChangedSignal() )
	{
		if( m_filter )
		{
			m_filter->changedSignal().disconnect( boost::bind( &Path::filterChanged, this ) );
		}
		if( filter )
		{
			filter->changedSignal().connect( boost::bind( &Path::filterChanged, this ) );
		}
	}

	m_filter = filter;
	emitPathChanged();
}

PathFilter *Path::getFilter()
{
	return m_filter.get();
}

const PathFilter *Path::getFilter() const
{
	return m_filter.get();
}

Path::PathChangedSignal &Path::pathChangedSignal()
{
	if( !m_pathChangedSignal )
	{
		m_pathChangedSignal = new PathChangedSignal;
		pathChangedSignalCreated();
	}
	return *m_pathChangedSignal;
}

void Path::setFromPath( const Path *path )
{
	if( path->m_names == m_names && path->m_root == m_root )
	{
		return;
	}

	m_root = path->m_root;
	m_names = path->m_names;

	emitPathChanged();
}

void Path::setFromString( const std::string &string )
{
	Names newNames;
	StringAlgo::tokenize<InternedString>( string, '/', back_inserter( newNames ) );

	InternedString newRoot;
	if( string.size() && string[0] == '/' )
	{
		newRoot = "/";
	}

	if( newRoot == m_root && newNames == m_names )
	{
		return;
	}

	m_names = newNames;
	m_root = newRoot;

	emitPathChanged();
}

PathPtr Path::copy() const
{
	return new Path( m_names, m_root, m_filter );
}

void Path::append( const IECore::InternedString &name )
{
	checkName( name );
	m_names.push_back( name );
	emitPathChanged();
}

void Path::truncateUntilValid()
{
	bool changed = false;
	while( m_names.size() && !isValid() )
	{
		m_names.pop_back();
		changed = true;
	}

	if( changed )
	{
		emitPathChanged();
	}
}

const Path::Names &Path::names() const
{
	return m_names;
}

void Path::set( size_t index, const IECore::InternedString &name )
{
	if( index >= m_names.size() )
	{
		throw IECore::Exception( "Index out of range" );
	}

	if( name == m_names[index] )
	{
		return;
	}

	checkName( name );

	m_names[index] = name;
	emitPathChanged();
}

void Path::set( size_t begin, size_t end, const Names &names )
{
	if( begin > m_names.size() )
	{
		throw IECore::Exception( "Index out of range" );
	}

	if( end > m_names.size() )
	{
		throw IECore::Exception( "Index out of range" );
	}

	Names::difference_type sizeDifference = names.size() - (end - begin);

	if( sizeDifference == 0 )
	{
		if( equal( m_names.begin() + begin, m_names.begin() + end, names.begin() ) )
		{
			return;
		}
	}
	else if( sizeDifference > 0 )
	{
		m_names.resize( m_names.size() + sizeDifference );
		std::copy_backward( m_names.begin() + end, m_names.begin() + end + sizeDifference, m_names.end() );
	}
	else
	{
		std::copy( m_names.begin() + end, m_names.end(), m_names.begin() + end + sizeDifference );
		m_names.resize( m_names.size() + sizeDifference );
	}

	std::copy( names.begin(), names.end(), m_names.begin() + begin );
	emitPathChanged();
}

void Path::remove( size_t index )
{
	if( index >= m_names.size() )
	{
		throw IECore::Exception( "Index out of range" );
	}

	m_names.erase( m_names.begin() + index );
	emitPathChanged();
}

void Path::remove( size_t begin, size_t end )
{
	if( begin >= m_names.size() )
	{
		throw IECore::Exception( "Index out of range" );
	}

	if( end > m_names.size() )
	{
		throw IECore::Exception( "Index out of range" );
	}

	m_names.erase( m_names.begin() + begin, m_names.begin() + end );
	emitPathChanged();
}

std::string Path::string() const
{
	std::string result = m_root.string();
	for( size_t i = 0, s = m_names.size(); i < s; ++i )
	{
		if( i != 0 )
		{
			result += "/";
		}
		result += m_names[i].string();
	}
	return result;
}

bool Path::operator == ( const Path &other ) const
{
	return
		typeId() == other.typeId() &&
		m_root == other.m_root &&
		m_names == other.m_names;
}

bool Path::operator != ( const Path &other ) const
{
	return !(*this == other );
}

const Plug *Path::cancellationSubject() const
{
	return nullptr;
}

void Path::doChildren( std::vector<PathPtr> &children, const IECore::Canceller *canceller ) const
{
}

void Path::emitPathChanged()
{
	if( !m_pathChangedSignal )
	{
		return;
	}
	(*m_pathChangedSignal)( this );
}

void Path::pathChangedSignalCreated()
{
	if( m_filter )
	{
		m_filter->changedSignal().connect( boost::bind( &Path::filterChanged, this ) );
	}
}

bool Path::havePathChangedSignal() const
{
	return m_pathChangedSignal;
}

void Path::filterChanged()
{
	emitPathChanged();
}

void Path::checkName( const IECore::InternedString &name ) const
{
	if( name.string().find( '/' ) != string::npos )
	{
		throw IECore::Exception( "Path name contains '/'." );
	}

	if( name.string().empty() )
	{
		throw IECore::Exception( "Path name is empty." );
	}
}
