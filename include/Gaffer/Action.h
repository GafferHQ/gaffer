//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
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

#ifndef GAFFER_ACTION_H
#define GAFFER_ACTION_H

#include "boost/function.hpp"

#include "IECore/RunTimeTyped.h"

#include "Gaffer/TypeIds.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( GraphComponent );
IE_CORE_FORWARDDECLARE( ScriptNode );
IE_CORE_FORWARDDECLARE( Action );

/// The Action class forms the basis of the undo system - all
/// methods which wish to support undo must be implemented by
/// calling Action::enact(). Note that client code never creates Actions
/// explicitly - instead they are created implicitly whenever an UndoContext
/// is active and an undoable method is called. Because Actions are
/// essentially an implementation detail of the undo system, subclasses
/// shouldn't be exposed in the public headers.
class Action : public IECore::RunTimeTyped
{

	public :
	
		/// The stages of the the do/undo/redo sequence.
		enum Stage
		{
			Invalid,
			Do,
			Undo,
			Redo
		};
	
		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Action, ActionTypeId, IECore::RunTimeTyped );

		typedef boost::function<void ()> Function;

		/// Enacts the specified action by calling doAction() and
		/// adding it to the undo queue in the appropriate ScriptNode.
		static void enact( ActionPtr action );
		/// Convenience function to enact a simple action without
		/// needing to create a new Action subclass. The callables
		/// passed will form the implementation of doAction() and
		/// undoAction(). Typically the callables would be constructed
		/// by using boost::bind with private member functions of the class
		/// implementing the undoable method.
		static void enact( GraphComponentPtr subject, const Function &doFn, const Function &undoFn );

	protected :

		Action();
		virtual ~Action();
		
		/// Must be implemented by derived classes to
		/// return the subject of the work they perform -
		/// this is used to find the ScriptNode in which
		/// to store the action.
		virtual GraphComponent *subject() const = 0;
		/// Must be implemented by derived classes to
		/// perform the action. Implementations should
		/// call the base class implementation before
		/// performing their own work.
		virtual void doAction() = 0;
		/// Must be implemented by derived classes to
		/// undo the effects of doAction(). Implementations should
		/// call the base class implementation before
		/// performing their own work.
		virtual void undoAction() = 0;

		/// May be reimplemented by derived classes to return
		/// true if it is valid to call merge( other ).
		/// Implementations must only return true if the base
		/// class implementation also returns true.
		virtual bool canMerge( const Action *other ) const = 0;
		/// May be implemented to merge another action into
		/// this one, so that doAction() now has the effect
		/// of having performed both actions (other second),
		/// and undoAction has the effect of undoing both.
		/// Implementations must call the base class
		/// implementation before performing their own merging.
		virtual void merge( const Action *other ) = 0;
		
	private :

		friend class ScriptNode;
		
		bool m_done;

};

IE_CORE_DECLAREPTR( Action );

} // namespace Gaffer

#endif // GAFFER_ACTION_H
