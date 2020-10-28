//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_STRINGPLUG_H
#define GAFFER_STRINGPLUG_H

#include "IECore/StringAlgo.h"

#include "Gaffer/Context.h"
#include "Gaffer/ValuePlug.h"

namespace Gaffer
{

/// Plug for providing string values.
///
/// Substitutions
/// =============
///
/// Substitutions allow the user to enter values containing
/// frame numbers and the values of context variables, and
/// have the appropriate values substituted in automatically
/// during computation.
///
/// e.g. "~/images/${name}.####.exr" -> "/home/bob/beauty.0001.exr"
///
/// Substitutions are performed transparently when `getValue()`
/// is called for an input plug from within a current `Process`,
/// so no specific action is required on the part of the Node
/// developer to support them.
///
///	If a node needs to deal with sequences directly, or otherwise
/// access unsubstituted values, the `substitutions` constructor
/// argument may be used to disable specific substitutions.
///
/// > Note : This feature does not affect the values passed
///	> internally between string plugs - substitutions are only
/// > applied to the return value generated for `getValue()`.
/// > This is important, since it allows a downstream node to
/// > access an unsubstituted value from its input, even if
/// > an intermediate upstream plug has substitutions enabled
/// > for other purposes.
/// >
/// > In other words, substitutions could just as well be
/// > implemented using an explicit `getSubstitutedValue()`
/// > method or by performing a manual substitution after using
/// > `getValue()`. However, in practice, it was determined to
/// > be too error prone to remember to do this for every
/// > value access in every node.
class GAFFER_API StringPlug : public ValuePlug
{

	public :

		typedef std::string ValueType;

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::StringPlug, StringPlugTypeId, ValuePlug );

		StringPlug(
			const std::string &name = defaultName<StringPlug>(),
			Direction direction=In,
			const std::string &defaultValue = "",
			unsigned flags = Default,
			unsigned substitutions = IECore::StringAlgo::AllSubstitutions
		);
		~StringPlug() override;

		unsigned substitutions() const;

		/// Accepts only instances of StringPlug or derived classes.
		bool acceptsInput( const Plug *input ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		const std::string &defaultValue() const;

		/// \undoable
		void setValue( const std::string &value );
		/// Returns the value. See comments in TypedObjectPlug::getValue()
		/// for details of the optional precomputedHash argument - and use
		/// with care!
		std::string getValue( const IECore::MurmurHash *precomputedHash = nullptr ) const;

		void setFrom( const ValuePlug *other ) override;

		IECore::MurmurHash hash() const override;
		/// Ensures the method above doesn't mask
		/// ValuePlug::hash( h )
		using ValuePlug::hash;

	private :

		unsigned m_substitutions;

};

IE_CORE_DECLAREPTR( StringPlug );

/// \deprecated Use StringPlug::Iterator etc instead
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, StringPlug> > StringPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::In, StringPlug> > InputStringPlugIterator;
typedef FilteredChildIterator<PlugPredicate<Plug::Out, StringPlug> > OutputStringPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Invalid, StringPlug>, PlugPredicate<> > RecursiveStringPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::In, StringPlug>, PlugPredicate<> > RecursiveInputStringPlugIterator;
typedef FilteredRecursiveChildIterator<PlugPredicate<Plug::Out, StringPlug>, PlugPredicate<> > RecursiveOutputStringPlugIterator;

} // namespace Gaffer

#endif // GAFFER_STRINGPLUG_H
