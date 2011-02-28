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

#include "Gaffer/ApplicationRoot.h"

using namespace Gaffer;

IE_CORE_DEFINERUNTIMETYPED( ApplicationRoot );

ApplicationRoot::ApplicationRoot()
{
	ScriptContainerPtr s = new ScriptContainer;
	s->setName( "scripts" );
	addChild( s );
}

ApplicationRoot::~ApplicationRoot()
{
}
		
bool ApplicationRoot::acceptsChild( ConstGraphComponentPtr potentialChild ) const
{
	if( children().size()<1 )
	{
		return true;
	}
	return false;
}

bool ApplicationRoot::acceptsParent( const GraphComponent *potentialParent ) const
{
	return false;
}

ScriptContainerPtr ApplicationRoot::scripts()
{
	return getChild<ScriptContainer>( "scripts" );
}

ConstScriptContainerPtr ApplicationRoot::scripts() const
{
	return getChild<ScriptContainer>( "scripts" );
}

IECore::ConstObjectPtr ApplicationRoot::getClipboardContents() const
{
	return m_clipboardContents;
}

void ApplicationRoot::setClipboardContents( IECore::ConstObjectPtr clip )
{
	m_clipboardContents = clip->copy();
}
