//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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
#include "boost/lexical_cast.hpp"

#include "Gaffer/Context.h"
#include "Gaffer/Plug.h"

#include "GafferUI/View.h"

using namespace Gaffer;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( View );

size_t View::g_firstPlugIndex = 0;

View::View( const std::string &name, Gaffer::PlugPtr inPlug )
	:	Node( name ),
		m_viewportGadget( new ViewportGadget )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	setChild( "in", inPlug );

	setContext( new Context() );
}

View::~View()
{
}

Gaffer::Context *View::getContext()
{
	return m_context.get();
}

const Gaffer::Context *View::getContext() const
{
	return m_context.get();
}

void View::setContext( Gaffer::ContextPtr context )
{
	if( context == m_context )
	{
		return;
	}
	m_context = context;
	m_contextChangedConnection = m_context->changedSignal().connect( boost::bind( &View::contextChanged, this, ::_2 ) );
	contextChangedSignal()( this );
}

View::UnarySignal &View::contextChangedSignal()
{
	return m_contextChangedSignal;
}

ViewportGadget *View::viewportGadget()
{
	return m_viewportGadget.get();
}

const ViewportGadget *View::viewportGadget() const
{
	return m_viewportGadget.get();
}

void View::setPreprocessor( Gaffer::NodePtr preprocessor )
{
	setChild( "__preprocessor", preprocessor );
	preprocessor->getChild<Plug>( "in" )->setInput( inPlug<Plug>() );
}

void View::contextChanged( const IECore::InternedString &name )
{
}

boost::signals::connection &View::contextChangedConnection()
{
	return m_contextChangedConnection;
}

Imath::Box3f View::framingBound() const
{
	return Imath::Box3f();
}

View::CreatorMap &View::creators()
{
	static CreatorMap m;
	return m;
}

View::NamedCreatorMap &View::namedCreators()
{
	static NamedCreatorMap m;
	return m;
}

ViewPtr View::create( Gaffer::PlugPtr plug )
{
	const Gaffer::Node *node = plug->node();
	if( node )
	{
		std::string plugPath = plug->relativeName( node );
		const NamedCreatorMap &m = namedCreators();
		IECore::TypeId t = node->typeId();
		while( t!=IECore::InvalidTypeId )
		{
			NamedCreatorMap::const_iterator it = m.find( t );
			if( it!=m.end() )
			{
				for( RegexAndCreatorVector::const_reverse_iterator nIt = it->second.rbegin(); nIt!=it->second.rend(); nIt++ )
				{
					if( boost::regex_match( plugPath, nIt->first ) )
					{
						return nIt->second( plug );
					}
				}
			}
			t = IECore::RunTimeTyped::baseTypeId( t );
		}
	}

	CreatorMap &m = creators();
	IECore::TypeId t = plug->typeId();
	while( t!=IECore::InvalidTypeId )
	{
		CreatorMap::const_iterator it = m.find( t );
		if( it!=m.end() )
		{
			return it->second( plug );
		}
		t = IECore::RunTimeTyped::baseTypeId( t );
	}

	return 0;
}

void View::registerView( IECore::TypeId plugType, ViewCreator creator )
{
	creators()[plugType] = creator;
}

void View::registerView( const IECore::TypeId nodeType, const std::string &plugPath, ViewCreator creator )
{
	namedCreators()[nodeType].push_back( RegexAndCreator( boost::regex( plugPath ), creator ) );
}
