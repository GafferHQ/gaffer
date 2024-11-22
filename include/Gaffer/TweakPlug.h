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

#pragma once

#include "Gaffer/Export.h"
#include "Gaffer/CompoundDataPlug.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"


namespace Gaffer
{

/// Represents a "tweak" - an adjustment with a name, a mode, and a value,
/// and an enable flag.  Can be used to add/subtract/multiply/replace or
/// remove parameters, for example in the ShaderTweaks or CameraTweaks nodes.
class GAFFER_API TweakPlug : public Gaffer::ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::TweakPlug, TweakPlugTypeId, Gaffer::ValuePlug );

		enum Mode
		{
			Replace,
			Add,
			Subtract,
			Multiply,
			Remove,
			Create,
			Min,
			Max,
			ListAppend,
			ListPrepend,
			ListRemove,
			CreateIfMissing,

			First = Replace,
			Last = CreateIfMissing,
		};

		TweakPlug( const std::string &tweakName, Gaffer::ValuePlugPtr valuePlug, Mode mode = Replace, bool enabled = true );
		TweakPlug( const std::string &tweakName, const IECore::Data *value, Mode mode = Replace, bool enabled = true );
		/// Primarily used for serialisation.
		explicit TweakPlug( Gaffer::ValuePlugPtr valuePlug, const std::string &name=defaultName<TweakPlug>(), Direction direction=In, unsigned flags=Default );

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

		/// Controls behaviour when the parameter to be
		/// tweaked cannot be found.
		enum class MissingMode
		{
			Ignore,
			Error
		};

		/// \deprecated. Use `TweaksPlug::applyTweaks()` instead.
		bool applyTweak( IECore::CompoundData *parameters, MissingMode missingMode = MissingMode::Error ) const;

		/// Applies the tweak using functors to get and set the data.
		/// \returns true if any tweaks were applied
		template<class GetDataFunctor, class SetDataFunctor>
		bool applyTweak(
			/// Signature : const IECore::Data *functor( const std::string &valueName, const bool withFallback ).
			/// Passing `withFallback=False` specifies that no fallback value should be returned in place of missing data.
			/// \returns `nullptr` if `valueName` is invalid.
			GetDataFunctor &&getDataFunctor,
			/// Signature : bool functor( const std::string &valueName, IECore::DataPtr newData).
			/// Passing `nullptr` in `newData` removes the entry for `valueName`.
			/// \returns true if the value was set or erased, false if erasure failed.
			SetDataFunctor &&setDataFunctor,
			MissingMode missingMode = MissingMode::Error
		) const;

		template< typename T >
		static T applyNumericTweak(
			const T &source,
			const T &tweak,
			TweakPlug::Mode mode,
			const std::string &tweakName
		);

	private :

		Gaffer::ValuePlug *valuePlugInternal();
		const Gaffer::ValuePlug *valuePlugInternal() const;

		void applyNumericDataTweak(
			const IECore::Data *sourceData,
			const IECore::Data *tweakData,
			IECore::Data *destData,
			TweakPlug::Mode mode,
			const std::string &tweakName
		) const;

		void applyListTweak(
			const IECore::Data *sourceData,
			const IECore::Data *tweakData,
			IECore::Data *destData,
			TweakPlug::Mode mode,
			const std::string &tweakName
		) const;

		template<typename T>
		static T vectorAwareMin( const T &v1, const T &v2 );

		template<typename T>
		static T vectorAwareMax( const T &v1, const T &v2 );

		void applyReplaceTweak( const IECore::Data *sourceData, IECore::Data *tweakData ) const;

		static const char *modeToString( Gaffer::TweakPlug::Mode mode );

};

IE_CORE_DECLAREPTR( TweakPlug )

/// Represents a collection of tweaks, and provides methods for applying them
/// to parameters lists and shader networks.
/// \todo Consider how TweaksPlug/TweakPlug relates to CompoundDataPlug/CompoundDataPlug::MemberPlug
/// and others. We should make these consistent with one another.
class GAFFER_API TweaksPlug : public Gaffer::ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::TweaksPlug, TweaksPlugTypeId, Gaffer::ValuePlug );

		TweaksPlug( const std::string &name=defaultName<TweaksPlug>(), Direction direction=In, unsigned flags=Default );

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		bool acceptsInput( const Plug *input ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		/// Tweak application
		/// =================
		/// Functions return true if any tweaks were applied.

		bool applyTweaks( IECore::CompoundData *parameters, TweakPlug::MissingMode missingMode = TweakPlug::MissingMode::Error ) const;

		/// Applies the tweak using functors to get and set the data.
		/// \returns true if any tweaks were applied
		template<class GetDataFunctor, class SetDataFunctor>
		bool applyTweaks(
			/// Signature : const IECore::Data *functor( const std::string &valueName ).
			/// \returns `nullptr` if `valueName` is invalid.
			GetDataFunctor &&getDataFunctor,
			/// Signature : bool functor( const std::string &valueName, IECore::DataPtr newData ).
			/// Passing `nullptr` in `newData` removes the entry for `valueName`.
			/// \returns true if the value was set or erased, false if erasure failed.
			SetDataFunctor &&setDataFunctor,
			TweakPlug::MissingMode missingMode = TweakPlug::MissingMode::Error
		) const;
};

} // namespace Gaffer

#include "Gaffer/TweakPlug.inl"
