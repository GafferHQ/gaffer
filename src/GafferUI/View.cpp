//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "GafferUI/View.h"

using namespace Gaffer;
using namespace GafferUI;

IE_CORE_DEFINERUNTIMETYPED( View );

size_t View::g_firstPlugIndex = 0;

View::View( const std::string &name, Gaffer::PlugPtr inPlug )
	:	Node( name ),
		m_viewportGadget( new ViewportGadget ),
		m_context( new Context() )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	setChild( "in", inPlug );
	
	viewportGadget()->keyPressSignal().connect( boost::bind( &View::keyPress, this, ::_1, ::_2 ) );	
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
	m_context = context;
}
		
ViewportGadget *View::viewportGadget()
{
	return m_viewportGadget;
}

bool View::keyPress( GadgetPtr gadget, const KeyEvent &keyEvent )
{
	if( keyEvent.key == "F" )
	{
		if( Gadget *c = viewportGadget()->getChild<Gadget>() )
		{
			viewportGadget()->frame( c->bound() );
			return true;
		}
	}
	
	return false;
}

View::CreatorMap &View::creators()
{
	static CreatorMap m;
	return m;
}

ViewPtr View::create( Gaffer::PlugPtr plug )
{	
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