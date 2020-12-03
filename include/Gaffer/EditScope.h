//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFER_EDITSCOPE_H
#define GAFFER_EDITSCOPE_H

#include "Gaffer/Box.h"

namespace Gaffer
{

class BoxOut;

/// A container node for interactive tools to make nodes in as necessary.
///
/// EditScopes and Tools
/// ====================
///
/// Tools that affect change by modifying nodes/plugs in the Node Graph
/// should use the following logic to determine their edit target:
///
///  - If no EditScope has been selected, use the last (closest) upstream
///    target.
///
///  - If an EditScope has been selected, prefer existing targets inside
///    the EditScope over using the EditScopeAlgo to acquire a new target.
///
///  - If an EditScope has been selected, but is upstream of another target
///    either error (if overrides preclude editing), or allow editing with
///    a suitable warning identifying the last downstream target.
///
///  - If an EditScope has been selected but is not in the scene history,
///    error.
///
class GAFFER_API EditScope : public Box
{

	public :

		EditScope( const std::string &name=defaultName<EditScope>() );
		~EditScope() override;

		GAFFER_NODE_DECLARE_TYPE( Gaffer::EditScope, EditScopeTypeId, Box );

		/// Setup and plugs
		/// ===============
		///
		/// EditScopes always have primary `in` and `out` plugs
		/// of the same type, created by the `setup()` method.
		/// Initially, `in` is connected directly to `out` (via
		/// BoxIn and BoxOut nodes).

		void setup( const Plug *plug );

		template<typename T=Plug>
		T *inPlug();
		template<typename T=Plug>
		const T *inPlug() const;

		template<typename T=Plug>
		T *outPlug();
		template<typename T=Plug>
		const T *outPlug() const;

		/// Processors
		/// ==========
		///
		/// Processors are child nodes that are inserted on the
		/// internal path between the `out` and the `in` plugs. They
		/// must have their own `in` and `out` plugs of the same
		/// type as the EditScope itself.

		/// Acquires a processor of the specified `type`. Throws if
		/// `type` has not been registered by `registerProcessor()`.
		template<typename T=DependencyNode>
		T *acquireProcessor( const std::string &type, bool createIfNecessary = true );

		/// Returns all the processors between the `out` and the `in` plugs.
		std::vector<Gaffer::DependencyNode*> processors();

		/// Processor Factory
		/// -----------------

		using ProcessorCreator = std::function<DependencyNodePtr()>;
		/// Registers a function that creates a processor of the specified type. This
		/// is used by `acquireProcessor()` when the desired processor has not
		/// been created yet.
		static void registerProcessor( const std::string &type, ProcessorCreator creator );
		static void deregisterProcessor( const std::string &type );
		/// Returns a list of all the currently registered processor types.
		static const std::vector<std::string> &registeredProcessors();

		/// Convenience class to allow static registrations of processors.
		/// e.g. `static ProcessorRegistration g_registration( "Type", creator )`.
		struct ProcessorRegistration
		{
			ProcessorRegistration( const std::string &type, ProcessorCreator creator )
			{
				registerProcessor( type, creator );
			}
		};

	private :

		BoxOut *boxOut();
		DependencyNode *acquireProcessorInternal( const std::string &type, bool createIfNecessary );

};

IE_CORE_DECLAREPTR( EditScope )

} // namespace Gaffer

#include "Gaffer/EditScope.inl"

#endif // GAFFER_EDITSCOPE_H
