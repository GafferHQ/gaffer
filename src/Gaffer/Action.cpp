//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011, John Haddon. All rights reserved.
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

#include "IECore/Exception.h"
#include "IECore/RunTimeTyped.h"

#include "Gaffer/Action.h"
#include "Gaffer/ScriptNode.h"

using namespace Gaffer;

//////////////////////////////////////////////////////////////////////////
// Action implementation
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( Action );

Action::Action()
	:	m_done( false )
{
}

Action::~Action()
{
}

void Action::enact( ActionPtr action )
{
	ScriptNodePtr s = IECore::runTimeCast<ScriptNode>( action->subject() );
	if( !s )
	{
		s = action->subject()->ancestor<ScriptNode>();
	}
	
	if( s )
	{
		s->addAction( action );
	}
	else
	{
		action->doAction();	
	}
		
}
	
void Action::doAction()
{
	if( m_done ) 
	{
		throw IECore::Exception( "Action cannot be done again without being undone first." );
	}
	m_done = true;
}

void Action::undoAction()
{
	if( !m_done ) 
	{
		throw IECore::Exception( "Action cannot be undone without being done first." );
	}
	m_done = false;
}

bool Action::canMerge( const Action *other ) const
{
	return true;
}

void Action::merge( const Action *other )
{
}

//////////////////////////////////////////////////////////////////////////
// SimpleAction implementation and Action::enact() convenience overload.
//////////////////////////////////////////////////////////////////////////

namespace Gaffer
{

class SimpleAction : public Action
{

	public :
	
		SimpleAction( const GraphComponentPtr subject, const Function &doFn, const Function &undoFn )
			:	m_subject( subject ), m_doFn( doFn ), m_undoFn( undoFn )
		{
		}

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::SimpleAction, SimpleActionTypeId, Action );

	protected :

		virtual GraphComponent *subject() const
		{
			return m_subject.get();
		}

		void doAction()
		{
			Action::doAction();
			m_doFn();
		}

		void undoAction()
		{
			Action::undoAction();
			m_undoFn();
		}

		bool canMerge( const Action *other ) const
		{
			return false;
		}

		void merge( const Action *other )
		{
		}
		
	private :
	
		GraphComponentPtr m_subject;
		Function m_doFn;
		Function m_undoFn;

};

IE_CORE_DEFINERUNTIMETYPED( SimpleAction );

void Action::enact( GraphComponentPtr subject, const Function &doFn, const Function &undoFn )
{
	/// \todo We might want to optimise away the construction of a SimpleAction
	/// when we know that enact() will just call doFn and throw it away (when undo
	/// is disabled). If we do that we should make it easy for other subclasses to do
	/// the same.
	enact( new SimpleAction( subject, doFn, undoFn ) );	
}

} // namespace Gaffer
