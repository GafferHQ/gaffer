//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2025, Cinesite VFX Ltd. All rights reserved.
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

#include "GafferDispatch/Export.h"
#include "GafferDispatch/TypeIds.h"

#include "Gaffer/ComputeNode.h"
#include "Gaffer/NumericPlug.h"
#include "Gaffer/StringPlug.h"
#include "Gaffer/TypedObjectPlug.h"

namespace GafferDispatch
{

class GAFFERDISPATCH_API FileList : public Gaffer::ComputeNode
{

	public :

		explicit FileList( const std::string &name=defaultName<FileList>() );
		~FileList() override;

		GAFFER_NODE_DECLARE_TYPE( GafferDispatch::FileList, FileListTypeId, Gaffer::ComputeNode );

		Gaffer::BoolPlug *enabledPlug() override;
		const Gaffer::BoolPlug *enabledPlug() const override;

		Gaffer::StringPlug *directoryPlug();
		const Gaffer::StringPlug *directoryPlug() const;

		Gaffer::IntPlug *refreshCountPlug();
		const Gaffer::IntPlug *refreshCountPlug() const;

		Gaffer::StringPlug *inclusionsPlug();
		const Gaffer::StringPlug *inclusionsPlug() const;

		Gaffer::StringPlug *exclusionsPlug();
		const Gaffer::StringPlug *exclusionsPlug() const;

		Gaffer::StringPlug *extensionsPlug();
		const Gaffer::StringPlug *extensionsPlug() const;

		Gaffer::BoolPlug *searchSubdirectoriesPlug();
		const Gaffer::BoolPlug *searchSubdirectoriesPlug() const;

		Gaffer::BoolPlug *absolutePlug();
		const Gaffer::BoolPlug *absolutePlug() const;

		enum class SequenceMode
		{
			// Lists all files individually, even if they belong to a sequence.
			Files,
			// Collects files into frame sequences, listing only the sequences.
			// Files not in a sequence are ommitted.
			Sequences,
			// Outputs sequences where possible, with non-sequence files listed
			// individually.
			FilesAndSequences,
		};

		Gaffer::IntPlug *sequenceModePlug();
		const Gaffer::IntPlug *sequenceModePlug() const;

		Gaffer::StringVectorDataPlug *outPlug();
		const Gaffer::StringVectorDataPlug *outPlug() const;

		void affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const override;

	protected :

		void hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const override;
		void compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const override;

		Gaffer::ValuePlug::CachePolicy computeCachePolicy( const Gaffer::ValuePlug *output ) const override;

	private :

		static size_t g_firstPlugIndex;

};

} // namespace GafferDispatch
