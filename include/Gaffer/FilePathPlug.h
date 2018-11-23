//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2022, Cinesite VFX Ltd. All rights reserved.
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

#ifndef GAFFER_FILEPATHPLUG_H
#define GAFFER_FILEPATHPLUG_H

#include "Gaffer/StringPlug.h"

#include "IECore/StringAlgo.h"

namespace Gaffer
{

/// Plug for providing file system path values.
///
/// Inherit from StringPlug for string substitution support and backwards
/// compatibility.

class GAFFER_API FilePathPlug : public StringPlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::FilePathPlug, FilePathPlugTypeId, StringPlug );

		FilePathPlug(
			const std::string &name = defaultName<FilePathPlug>(),
			Direction direction=In,
			const std::string &defaultValue = "",
			unsigned flags = Default,
			unsigned substitutions = IECore::StringAlgo::AllSubstitutions
		);
		~FilePathPlug() override;

		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		/// \undoable
		void setValue( const std::string &value ) override;
		/// Returns the value in OS-specific format. See comments in
		/// TypedObjectPlug::getValue() for details of the optional
		/// precomputedHash argument - and use with care!
		std::string getValue( const IECore::MurmurHash *precomputedHash = nullptr ) const override;
};

IE_CORE_DECLAREPTR( FilePathPlug );

} // namespace Gaffer

#endif // GAFFER_FILEPATHPLUGPLUG_H
