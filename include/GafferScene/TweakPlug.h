//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2018, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFERSCENE_TWEAKPLUG_H
#define GAFFERSCENE_TWEAKPLUG_H

#include "GafferScene/Shader.h"

#include "Gaffer/StringPlug.h"

#include "IECoreScene/ShaderNetwork.h"

namespace GafferScene
{

/// Represents a "tweak" - an adjustment with a name, a mode, and a value,
/// and an enable flag.  Can be used to add/subtract/multiply/replace or
/// remove parameters, for example in the ShaderTweaks or CameraTweaks nodes.
class GAFFERSCENE_API TweakPlug : public Gaffer::ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( GafferScene::TweakPlug, TweakPlugTypeId, Gaffer::ValuePlug );

		enum Mode
		{
			Replace,
			Add,
			Subtract,
			Multiply,
			Remove
		};

		TweakPlug( const std::string &tweakName, Gaffer::ValuePlugPtr valuePlug, Mode mode = Replace, bool enabled = true );
		TweakPlug( const std::string &tweakName, const IECore::Data *value, Mode mode = Replace, bool enabled = true );
		/// Primarily used for serialisation.
		TweakPlug( Gaffer::ValuePlugPtr valuePlug, const std::string &name=defaultName<TweakPlug>(), Direction direction=In, unsigned flags=Default );

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		Gaffer::BoolPlug *enabledPlug();
		const Gaffer::BoolPlug *enabledPlug() const;

		Gaffer::IntPlug *modePlug();
		const Gaffer::IntPlug *modePlug() const;

		template<typename T=Gaffer::ValuePlug>
		T *valuePlug();
		template<typename T=Gaffer::ValuePlug>
		const T *valuePlug() const;

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;
		IECore::MurmurHash hash() const override;
		/// Ensures the method above doesn't mask
		/// ValuePlug::hash( h )
		using ValuePlug::hash;

		/// Controls behaviour when the parameter to be
		/// tweaked cannot be found.
		enum class MissingMode
		{
			Ignore,
			Error,
			/// Legacy mode used by CameraTweaks. Same as
			/// Ignore mode except when `Mode == Replace`, in
			/// which case a new parameter is created.
			/// \deprecated Do not use in new code. If you find
			/// yourself wanting to, add Mode::Create instead.
			IgnoreOrReplace,
		};

		/// \deprecated. Use `TweaksPlug::applyTweaks()` instead.
		bool applyTweak( IECore::CompoundData *parameters, MissingMode missingMode = MissingMode::Error ) const;
		/// \returns true if any tweaks were applied
		static bool applyTweaks( const Plug *tweaksPlug, IECoreScene::ShaderNetwork *shaderNetwork, MissingMode missingMode = MissingMode::Error );

	private :

		Gaffer::ValuePlug *valuePlugInternal();
		const Gaffer::ValuePlug *valuePlugInternal() const;

		std::pair<const Shader *, const Gaffer::Plug *> shaderOutput() const;

};

typedef Gaffer::FilteredChildIterator<Gaffer::PlugPredicate<Gaffer::Plug::Invalid, TweakPlug> > TweakPlugIterator;

IE_CORE_DECLAREPTR( TweakPlug )

/// Represents a collection of tweaks, and provides methods for applying them
/// to parameters lists and shader networks.
/// \todo Consider how TweaksPlug/TweakPlug relates to CompoundDataPlug/CompoundDataPlug::MemberPlug
/// and others. We should make these consistent with one another.
class GAFFERSCENE_API TweaksPlug : public Gaffer::ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( GafferScene::TweaksPlug, TweaksPlugTypeId, Gaffer::ValuePlug );

		TweaksPlug( const std::string &name=defaultName<TweaksPlug>(), Direction direction=In, unsigned flags=Default );

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		bool acceptsInput( const Plug *input ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		/// Tweak application
		/// =================
		/// Functions return true if any tweaks were applied.

		bool applyTweaks( IECore::CompoundData *parameters, TweakPlug::MissingMode missingMode = TweakPlug::MissingMode::Error ) const;
		bool applyTweaks( IECoreScene::ShaderNetwork *shaderNetwork, TweakPlug::MissingMode missingMode = TweakPlug::MissingMode::Error ) const;

};

} // namespace GafferScene

#include "GafferScene/TweakPlug.inl"

#endif // GAFFERSCENE_TWEAKPLUG_H
