//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2012-2015, Image Engine Design Inc. All rights reserved.
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

#ifndef GAFFER_FILESYSTEMPATH_H
#define GAFFER_FILESYSTEMPATH_H

#include "IECore/FileSequence.h"

#include "Gaffer/Export.h"
#include "Gaffer/Path.h"

namespace Gaffer
{

class GAFFER_API FileSystemPath : public Path
{

	public :

		FileSystemPath( PathFilterPtr filter = NULL, bool includeSequences = false );
		FileSystemPath( const std::string &path, PathFilterPtr filter = NULL, bool includeSequences = false );
		FileSystemPath( const Names &names, const IECore::InternedString &root = "/", PathFilterPtr filter = NULL, bool includeSequences = false );

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::FileSystemPath, FileSystemPathTypeId, Path );

		virtual ~FileSystemPath();

		virtual bool isValid() const;
		virtual bool isLeaf() const;
		virtual void propertyNames( std::vector<IECore::InternedString> &names ) const;
		/// Supported properties :
		///
		/// "fileSystem:owner" -> StringData
		/// "fileSystem:group" -> StringData
		/// "fileSystem:modificationTime" -> DateTimeData, in UTC time
		/// "fileSystem:size" -> UInt64Data, in bytes
		/// "fileSystem:frameRange" -> StringData
		virtual IECore::ConstRunTimeTypedPtr property( const IECore::InternedString &name ) const;
		virtual PathPtr copy() const;

		// Returns true if this FileSystemPath includes FileSequences
		bool getIncludeSequences() const;
		// Determines whether this FileSystemPath includes FileSequences
		void setIncludeSequences( bool includeSequences );
		// Returns true if the path represents a FileSequence.
		bool isFileSequence() const;
		// Returns the FileSequence that represents the current leaf
		// or NULL if this path is not a leaf, or does not represent
		// a FileSequence.
		IECore::FileSequencePtr fileSequence() const;

		static PathFilterPtr createStandardFilter( const std::vector<std::string> &extensions = std::vector<std::string>(), const std::string &extensionsLabel = "", bool includeSequenceFilter = false );

	protected :

		virtual void doChildren( std::vector<PathPtr> &children ) const;

	private :

		bool m_includeSequences;

};

} // namespace Gaffer

#endif // GAFFER_FILESYSTEMPATH_H
