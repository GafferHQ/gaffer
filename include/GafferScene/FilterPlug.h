//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_FILTERPLUG_H
#define GAFFERSCENE_FILTERPLUG_H

#include "GafferScene/Export.h"
#include "GafferScene/TypeIds.h"

#include "Gaffer/Context.h"
#include "Gaffer/DependencyNode.h"
#include "Gaffer/NumericPlug.h"

namespace GafferScene
{

class ScenePlug;

/// Plug type to provide the output from Filter nodes, and
/// an input for nodes which wish to use Filters.
/// \todo This derives from IntPlug for backwards compatibility
/// reasons, but it may be preferable to derive straight from
/// ValuePlug for version 1.0.0.0.
class GAFFERSCENE_API FilterPlug : public Gaffer::IntPlug
{

	public :

		FilterPlug(
			const std::string &name = defaultName<FilterPlug>(),
			Direction direction = In,
			unsigned flags = Default
		);

		/// \deprecated
		FilterPlug(
			const std::string &name,
			Direction direction ,
			int defaultValue,
			int minValue,
			int maxValue,
			unsigned flags
		);

		~FilterPlug() override;

		GAFFER_PLUG_DECLARE_TYPE( GafferScene::FilterPlug, FilterPlugTypeId, Gaffer::IntPlug );

		bool acceptsInput( const Gaffer::Plug *input ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		/// Must be called when a child of a ScenePlug is dirtied, and that ScenePlug will later
		/// be passed to the filter via SceneScope. This allows the filter to participate fully in
		/// dirty propagation, despite not having ScenePlug inputs of its own. For an example of
		/// usage, see `FilteredSceneProcessor::affects()`.
		void sceneAffects( const Gaffer::Plug *scenePlugChild, Gaffer::DependencyNode::AffectedPlugsContainer &outputs ) const;

		/// Evaluates the filter for the specified scene plug. Should be used in preference to
		/// singular calls to getValue(), as it ensures a suitable SceneScope before evaluating the filter.
		unsigned match( const ScenePlug *scene ) const;

		/// Name of a context variable used to provide the input
		/// scene to the filter
		static const IECore::InternedString inputSceneContextName;

		/// Provides the input scene for a filter evaluation
		struct SceneScope : public Gaffer::Context::EditableScope
		{
			SceneScope( const Gaffer::Context *context, const ScenePlug *scenePlug );
			private :
				const ScenePlug *m_scenePlug;
		};

};

IE_CORE_DECLAREPTR( FilterPlug );

[[deprecated("Use `FilterPlug::Iterator` instead")]]
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, FilterPlug> > FilterPlugIterator;
[[deprecated("Use `FilterPlug::InputIterator` instead")]]
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, FilterPlug> > InputFilterPlugIterator;
[[deprecated("Use `FilterPlug::OutputIterator` instead")]]
typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, FilterPlug> > OutputFilterPlugIterator;

[[deprecated("Use `FilterPlug::RecursiveIterator` instead")]]
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, FilterPlug>, Gaffer::PlugPredicate<> > RecursiveFilterPlugIterator;
[[deprecated("Use `FilterPlug::RecursiveInputIterator` instead")]]
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::In, FilterPlug>, Gaffer::PlugPredicate<> > RecursiveInputFilterPlugIterator;
[[deprecated("Use `FilterPlug::RecursiveOutputIterator` instead")]]
typedef Gaffer::FilteredRecursiveChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Out, FilterPlug>, Gaffer::PlugPredicate<> > RecursiveOutputFilterPlugIterator;

} // namespace GafferScene

#endif // GAFFERSCENE_FILTERPLUG_H
