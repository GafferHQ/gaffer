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

#ifndef GAFFERSCENE_SETVISUALISER_H
#define GAFFERSCENE_SETVISUALISER_H

#include "GafferScene/AttributeProcessor.h"

#include "Gaffer/NumericPlug.h"

namespace Gaffer
{

IE_CORE_FORWARDDECLARE( StringPlug )
IE_CORE_FORWARDDECLARE( CompoundDataPlug )

} // namespace Gaffer

namespace GafferScene
{

/// The SetVisualiser follows the Gaffer 'Visualiser Node' pattern, allowing
/// users to see what sets an Object is a member of via flat-color shading in the
/// viewport.
///
/// It uses a private plug containing lists of set names and colors used for
/// display. This allows more efficient hashing/compute without the need for
/// any internal state management, as well as permitting informative UIs that
/// help the user understand the resultant color mappings.
class GAFFERSCENE_API SetVisualiser : public AttributeProcessor
{

	public :

		SetVisualiser( const std::string &name=defaultName<SetVisualiser>() );
		~SetVisualiser() override;

		GAFFER_NODE_DECLARE_TYPE( GafferScene::SetVisualiser, SetVisualiserTypeId, AttributeProcessor );

		Gaffer::StringPlug *setsPlug();
		const Gaffer::StringPlug *setsPlug() const;

		Gaffer::BoolPlug *includeInheritedPlug();
		const Gaffer::BoolPlug *includeInheritedPlug() const;

		Gaffer::FloatPlug *stripeWidthPlug();
		const Gaffer::FloatPlug *stripeWidthPlug() const;

		Gaffer::CompoundDataPlug *colorOverridesPlug();
		const Gaffer::CompoundDataPlug *colorOverridesPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		virtual void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		virtual void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		bool affectsProcessedAttributes( const Gaffer::Plug *input ) const override;
		void hashProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		IECore::ConstCompoundObjectPtr computeProcessedAttributes( const ScenePath &path, const Gaffer::Context *context, const IECore::CompoundObject *inputAttributes ) const override;

	private :

		Gaffer::AtomicCompoundDataPlug *outSetsPlug();
		const Gaffer::AtomicCompoundDataPlug *outSetsPlug() const;

		/// Computes a filtered list of sets from the input ScenePlug, taking
		/// into account filtering defined by the Node's plugs and masking of
		/// Gaffer-internal sets, etc.
		std::vector<IECore::InternedString> candidateSetNames() const;

		/// Produces a stable list of colors for the supplied set names
		std::vector<Imath::Color3f> colorsForSets( const std::vector<IECore::InternedString>& setNames ) const;

		static size_t g_firstPlugIndex;

};

IE_CORE_DECLAREPTR( SetVisualiser )

} // namespace GafferScene

#endif // GAFFERSCENE_SETVISUALISER_H
