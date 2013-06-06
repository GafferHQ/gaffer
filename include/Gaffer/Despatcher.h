//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
//  
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//  
//	  * Redistributions of source code must retain the above
//		copyright notice, this list of conditions and the following
//		disclaimer.
//  
//	  * Redistributions in binary form must reproduce the above
//		copyright notice, this list of conditions and the following
//		disclaimer in the documentation and/or other materials provided with
//		the distribution.
//  
//	  * Neither the name of John Haddon nor the names of
//		any other contributors to this software may be used to endorse or
//		promote products derived from this software without specific prior
//		written permission.
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

#ifndef GAFFER_DESPATCHER_H
#define GAFFER_DESPATCHER_H

#include <string>
#include <vector>
#include <map>
#include <set>
#include "boost/signals.hpp"
#include "IECore/RunTimeTyped.h"
#include "Gaffer/TypeIds.h"
#include "Gaffer/Executable.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( Node )
IE_CORE_FORWARDDECLARE( Despatcher )
IE_CORE_FORWARDDECLARE( CompoundPlug )

/// Pure virtual class that specifies the interface for objects that
/// know how to run Executable nodes. They are also used after
/// construction of Execution nodes to add custom plugs that 
/// can tweak how they operate, for example, farm parameters.
class Despatcher : public IECore::RunTimeTyped
{
	public :

		Despatcher();

		virtual ~Despatcher();

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::Despatcher, DespatcherTypeId, IECore::RunTimeTyped );

		typedef boost::signal<void (const Despatcher *, const std::vector< NodePtr > &)> DespatchSignal;

		/// @name Despatch signals
		/// These signals are emitted on despatch events for any registered
		/// Despatcher instance.
		//////////////////////////////////////////////////////////////
		//@{
		/// Called when any despatcher is about to despatch nodes.
		static DespatchSignal &preDespatchSignal();
		/// Called after any despatcher has finished despatching nodes.
		static DespatchSignal &postDespatchSignal();

		/// Triggers the preDespatch signal and calls doDespatch() function.
		void despatch( const std::vector< NodePtr > &nodes ) const;

		/// Registration function for despatchers.
		static void registerDespatcher( std::string name, DespatcherPtr despatcher );

		/// Function that returns the names of all the registered despatchers
		static void despatcherNames( std::vector<std::string> &names );

		/// Function that gives access to a registered despatcher
		static const Despatcher *despatcher( std::string name );

	protected :

		friend class Executable;

		/// Despatches the execution of the given array of Executable nodes (and possibly their requirements).
		virtual void doDespatch( const std::vector< NodePtr > &nodes ) const = 0;

		/// This function is called to add custom Despatcher plugs during Executable node construction.
		static void addAllPlugs( CompoundPlug *despatcherPlug );

		/// Function called by addAllPlugs. Despatchers have a chance to create custom plugs on Executable nodes.
		/// The function must accept situations where the node already has the plugs (nodes loaded from a scene).
		virtual void addPlugs( CompoundPlug *despatcherPlug ) const = 0;

		/// Representation of a Executable task plus it's requirements as other tasks.
		struct TaskDescription 
		{
			Executable::Task task;
			std::set<Executable::Task> requirements;
		};

		/// Utility function that recursivelly collects all nodes and their execution requirements and flattens into 
		/// a list of unique Tasks (with unique executionHash) and their requirements. For nodes that don't compute (executionHash  
		/// returns default hash), this function will consider a separate task for each unique set of requirements. For all the other nodes
		/// they will be grouped by executionHash and their final requirements will be the union of all the requirements under that same
		/// hash.
		static void uniqueTasks( const Executable::Tasks &tasks, std::vector< TaskDescription > &uniqueTasks );

	private :

		typedef std::map< std::string, DespatcherPtr > DespatcherMap;
		static DespatcherMap g_despatchers;

		typedef std::map< IECore::MurmurHash, std::vector< size_t > > TaskSet;
		static const Executable::Task &uniqueTask( const Executable::Task &task, std::vector< Despatcher::TaskDescription > &uniqueTasks, TaskSet &seenTasks );

		static DespatchSignal g_preDespatchSignal;
		static DespatchSignal g_postDespatchSignal;
};

} // namespace Gaffer

#endif // GAFFER_DESPATCHER_H
