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

#ifndef GAFFERSCENE_FILTER_H
#define GAFFERSCENE_FILTER_H

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"

#include "GafferScene/TypeIds.h"
#include "GafferScene/FilterPlug.h"

namespace GafferScene
{

IE_CORE_FORWARDDECLARE( ScenePlug )

/// A base class for nodes which are used to limit the scope
/// of an operation to specific parts of the scene. Used in
/// conjunction with the FilteredSceneProcessor class.
class Filter : public Gaffer::ComputeNode
{

	public :

		enum Result
		{
			NoMatch = 0,
			DescendantMatch = 1,
			ExactMatch = 2,
			AncestorMatch = 4,
			EveryMatch = DescendantMatch | ExactMatch | AncestorMatch
		};

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( GafferScene::Filter, FilterTypeId, Gaffer::ComputeNode );

		Filter( const std::string &name=defaultName<Filter>() );
		virtual ~Filter();

		virtual Gaffer::BoolPlug *enabledPlug();
		virtual const Gaffer::BoolPlug *enabledPlug() const;

		FilterPlug *outPlug();
		const FilterPlug *outPlug() const;

		virtual void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const;
		virtual bool sceneAffectsMatch( const ScenePlug *scene, const Gaffer::ValuePlug *child ) const;

		/// \deprecated Use FilterPlug::SceneScope instead.
		static void setInputScene( Gaffer::Context *context, const ScenePlug *scenePlug );
		/// \deprecated
		static const ScenePlug *getInputScene( const Gaffer::Context *context );
		/// \deprecated Use FilterPlug::inputSceneContextName instead
		static const IECore::InternedString inputSceneContextName;

	protected :

		/// Implemented to call hashMatch() below when computing the hash for outPlug().
		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// Implemented to call computeMatch() below when computing the value of outPlug().
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const;

		/// Hash method for outPlug(). A derived class must either :
		///
		///    * Implement the method to call the base class implementation and then append to the hash.
		///
		/// or :
		///
		///    * Implement the method to assign directly to the hash from some input hash to signify that
		///      an input will be passed through unchanged by the corresponding computeMatch() method. Note
		///      that if you wish to pass through an input unconditionally, regardless of context, it is
		///      faster to use a connection as described below.
		///
		/// or :
		///
		///    * Make an input connection into outPlug(), so that the hash and compute methods
		///      are never called for it.
		virtual void hashMatch( const ScenePlug *scene, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// Must be implemented by derived classes to compute the result of the filter, or
		/// an input connection must be made into outPlug(), so that the method is not called.
		virtual unsigned computeMatch( const ScenePlug *scene, const Gaffer::Context *context ) const;

	private :

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Filter )

} // namespace GafferScene

#endif // GAFFERSCENE_FILTER_H
