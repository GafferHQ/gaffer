//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2020, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedPlug.h"

#include "IECore/CompoundObject.h"

namespace Gaffer
{

/// Represents a "shuffle" - an name change for an existing value,
/// with options to delete the original source name and an enable flag.
class GAFFER_API ShufflePlug : public ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::ShufflePlug, ShufflePlugTypeId, ValuePlug );

		ShufflePlug( const std::string &source, const std::string &destination, bool deleteSource=false, bool enabled=true, bool replaceDestination=true );
		/// Primarily used for serialisation.
		explicit ShufflePlug( const std::string &name = defaultName<ShufflePlug>(), Direction direction=In, unsigned flags = Default );

		StringPlug *sourcePlug();
		const StringPlug *sourcePlug() const;

		BoolPlug *enabledPlug();
		const BoolPlug *enabledPlug() const;

		StringPlug *destinationPlug();
		const StringPlug *destinationPlug() const;

		BoolPlug *deleteSourcePlug();
		const BoolPlug *deleteSourcePlug() const;

		BoolPlug *replaceDestinationPlug();
		const BoolPlug *replaceDestinationPlug() const;

		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		Gaffer::PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

};

IE_CORE_DECLAREPTR( ShufflePlug )

/// Represents a collection of shuffles, and provides methods for applying them
/// to the likely data structures.
class GAFFER_API ShufflesPlug : public ValuePlug
{

	public :

		GAFFER_PLUG_DECLARE_TYPE( Gaffer::ShufflesPlug, ShufflesPlugTypeId, ValuePlug );

		ShufflesPlug( const std::string &name=defaultName<ShufflesPlug>(), Direction direction=In, unsigned flags=Default );

		bool acceptsChild( const GraphComponent *potentialChild ) const override;
		bool acceptsInput( const Plug *input ) const override;
		PlugPtr createCounterpart( const std::string &name, Direction direction ) const override;

		/// Shuffles the sources into a destination container. The container type should have a map
		/// compatible interface with string-compatible keys (eg std::string, IECore::InternedString).
		/// If `ignoreMissingSource` is false, then an exception will be thrown if a source is not
		/// found.
		template<typename T>
		T shuffle( const T &sourceContainer, bool ignoreMissingSource = true ) const;
		/// As above, but using `extraSources` to provide fallback values for sources not
		/// found in `sourceContainer`. A special key, `*`, may be included to provide a fallback
		/// for _any_ source.
		/// > Note : The `additionalSources` container is only searched for exact matches, _not_
		/// > for wildcard matches.
		template<typename T>
		T shuffleWithExtraSources( const T &sourceContainer, const T &extraSources, bool ignoreMissingSource = true ) const;

	private :

		template<typename T>
		T shuffleInternal( const T &sourceContainer, const T *extraSources, bool ignoreMissingSource ) const;

};

} // namespace Gaffer

#include "Gaffer/ShufflePlug.inl"
