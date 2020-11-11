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

#ifndef GAFFER_NAMEVALUEPLUG_H
#define GAFFER_NAMEVALUEPLUG_H

#include "Gaffer/TypeIds.h"

#include "Gaffer/TypedPlug.h"
#include "Gaffer/StringPlug.h"

namespace Gaffer
{

class GAFFER_API NameValuePlug : public Gaffer::ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::NameValuePlug, NameValuePlugTypeId, Gaffer::ValuePlug );

		// Construct a NameValuePlug with the "name" and "value" children.  The value plug
		// can be constructed either based on a IECore::Data default value, or by supplying
		// a plug.  In the variant which takes a ValuePlug, NameValuePlug will take ownership
		// of this plug ( so be careful about using it afterwards ).
		NameValuePlug(
			const std::string &nameDefault,
			const IECore::Data *valueDefault,
			const std::string &name=defaultName<NameValuePlug>(),
			Direction direction=In,
			unsigned flags=Default
		);

		/// \deprecated Use the version below.
		/// \todo Remove, and add default arguments for `name` and `flags`
		/// in the version below.
		NameValuePlug(
			const std::string &nameDefault,
			Gaffer::PlugPtr valuePlug,
			const std::string &name=defaultName<NameValuePlug>()
		);

		NameValuePlug(
			const std::string &nameDefault,
			Gaffer::PlugPtr valuePlug,
			const std::string &name,
			unsigned flags
		);

		// Similar to above, construct a NameValuePlug with the "name" and "value" children,
		// and also an "enabled" child.
		NameValuePlug(
			const std::string &nameDefault,
			const IECore::Data *valueDefault,
			bool defaultEnabled,
			const std::string &name=defaultName<NameValuePlug>(),
			Direction direction=In,
			unsigned flags=Default
		);

		/// \deprecated Use the version below.
		/// \todo Remove, and add default arguments for `name` and `flags`
		/// in the version below.
		NameValuePlug(
			const std::string &nameDefault,
			Gaffer::PlugPtr valuePlug,
			bool defaultEnabled,
			const std::string &name=defaultName<NameValuePlug>()
		);

		NameValuePlug(
			const std::string &nameDefault,
			Gaffer::PlugPtr valuePlug,
			bool defaultEnabled,
			const std::string &name,
			unsigned flags
		);

		// Bare constructor required for compatibility with old CompoundDataPlug::MemberPlug constructor.
		// Deprecated, and dangerous, since if you don't manually construct child plugs in the expected order of
		// "name", "value", and optionally "enabled" then you will get a crash.
		NameValuePlug(
			const std::string &name=defaultName<NameValuePlug>(),
			Direction direction=In,
			unsigned flags=Default
		);

		Gaffer::StringPlug *namePlug();
		const Gaffer::StringPlug *namePlug() const;

		template<typename T = Gaffer::Plug>
		T *valuePlug();
		template<typename T = Gaffer::Plug>
		const T *valuePlug() const;

		Gaffer::BoolPlug *enabledPlug();
		const Gaffer::BoolPlug *enabledPlug() const;

		bool acceptsChild( const Gaffer::GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

};

[[deprecated("Use `NameValuePlug::Iterator` instead")]]
typedef FilteredChildIterator<PlugPredicate<Plug::Invalid, NameValuePlug> > NameValuePlugIterator;

IE_CORE_DECLAREPTR( NameValuePlug );

} // namespace Gaffer

#include "Gaffer/NameValuePlug.inl"

#endif // GAFFER_NAMEVALUEPLUG_H
