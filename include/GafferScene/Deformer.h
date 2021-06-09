//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2019, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_DEFORMER_H
#define GAFFERSCENE_DEFORMER_H

#include "GafferScene/ObjectProcessor.h"

namespace GafferScene
{

/// Base class for nodes which modify objects such that their bounding
/// box changes. The Deformer class takes care of propagating bounds
/// changes to parent locations.
///
/// > Note : Deformers are not limited to modifying vertex positions.
/// > They may change object topology or even type.
class GAFFERSCENE_API Deformer : public ObjectProcessor
{

	public :

		~Deformer() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::Deformer, DeformerTypeId, ObjectProcessor );

		Gaffer::BoolPlug *adjustBoundsPlug();
		const Gaffer::BoolPlug *adjustBoundsPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		/// Constructs with a single input ScenePlug named "in". Use inPlug()
		/// to access this plug.
		Deformer( const std::string &name );
		/// Constructs with an ArrayPlug called "in". Use inPlug() as a
		/// convenience for accessing the first child in the array, and use
		/// inPlugs() to access the array itself.
		Deformer( const std::string &name, size_t minInputs, size_t maxInputs = Imath::limits<size_t>::max() );

		/// Used to determine whether adjusted bounds need to be propagated up to
		/// all ancestor locations. Default implementation checks the value of `adjustBoundsPlug()`
		/// so that users may turn off bounds updates if they want. Derived classes may override
		/// to disable bounds propagation for configurations which do not create actual deformation.
		/// > Note : It is assumed that `affectsProcessedObject()` will return true for any plugs
		/// > accessed by `adjustBounds()`.
		virtual bool adjustBounds() const;

		/// If `computeProcessedObjectBound()` is overridden, this must be overriden
		/// to return true for any plugs it uses. Unlike other affects methods, overrides
		/// should _not_ call the base class implementation.
		virtual bool affectsProcessedObjectBound( const Gaffer::Plug *input ) const;
		/// If `computeProcessedObjectBound()` is overridden, this must be
		/// be overridden to match. Unlike other hash methods, overrides should
		/// _not_ call the base class implementation.
		virtual void hashProcessedObjectBound( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const;
		/// May be implemented by derived classes to return a bound for the
		/// result of `computeProcessedObject()`. This will only be called if
		/// `adjustBounds()` returns true. The default implementation uses
		/// the brute force approach of actually processing the object, so
		/// reimplementing to provide a cheaper approximate bound may improve
		/// performance considerably.
		/// > Note : Implementations are currently hampered by the fact that
		/// > `in.bound` provides the bound for the input object _and_ its
		/// > children. We could consider having separate `in.objectBound`
		/// > and `in.childBound` plugs instead.
		virtual Imath::Box3f computeProcessedObjectBound( const ScenePath &path, const Gaffer::Context *context ) const;

	private :

		void init();

		void hashBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent, IECore::MurmurHash &h ) const final;
		Imath::Box3f computeBound( const ScenePath &path, const Gaffer::Context *context, const ScenePlug *parent ) const final;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( Deformer )

} // namespace GafferScene

#endif // GAFFERSCENE_DEFORMER_H
