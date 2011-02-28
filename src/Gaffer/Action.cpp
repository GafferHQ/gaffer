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

#include "IECore/Exception.h"
#include "IECore/RunTimeTyped.h"

#include "Gaffer/Action.h"
#include "Gaffer/ScriptNode.h"

using namespace Gaffer;

Action::Action( const Function &doFn, const Function &undoFn )
	:	m_doFn( doFn ), m_undoFn( undoFn ), m_done( false )
{
}

Action::~Action()
{
}

void Action::enact( GraphComponentPtr subject, const Function &doFn, const Function &undoFn )
{
	ScriptNodePtr s = IECore::runTimeCast<ScriptNode>( subject );
	if( !s )
	{
		s = subject->ancestor<ScriptNode>();
	}
	
	if( s && s->m_actionAccumulator )
	{
		ActionPtr a = new Action( doFn, undoFn );
		a->doAction();
		s->m_actionAccumulator->push_back( a );
	}
	else
	{
		doFn();
	}
	
}
	
void Action::doAction()
{
	if( m_done ) 
	{
		throw IECore::Exception( "Action cannot be done again without being undone first." );
	}
	m_doFn();
	m_done = true;
}

void Action::undoAction()
{
	if( !m_done ) 
	{
		throw IECore::Exception( "Action cannot be undone without being done first." );
	}
	m_undoFn();
	m_done = false;
}

/*void Action::addToScript( GraphComponentPtr subject )
{
}*/
