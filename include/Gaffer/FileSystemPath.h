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

#include "Gaffer/Path.h"
#include "Gaffer/PathFilter.h"

#include "IECore/FileSequence.h"

namespace Gaffer
{

/// The FileSystemPath class provides cross-platform file path functions.
/// Paths can be a native formatted path - elements are separated by "/"
/// on Linux and MacOS and "\" on Windows - or by the Gaffer standard
/// path separator "/" on all platforms.
///
/// The root of a FileSystemPath will be "" for relative paths. On Linux and
/// MacOS, an absolute path root will be "/".
/// On Windows, an absolute path root will be either "<driveLetter>:/" for
/// drive-letter paths, or "//<serverName>/" for UNC paths.
class GAFFER_API FileSystemPath : public Path
{

	public :

		FileSystemPath( PathFilterPtr filter = nullptr, bool includeSequences = false );
		FileSystemPath( const std::string &path, PathFilterPtr filter = nullptr, bool includeSequences = false );
		FileSystemPath( const Names &names, const IECore::InternedString &root = "/", PathFilterPtr filter = nullptr, bool includeSequences = false );

		IE_CORE_DECLARERUNTIMETYPEDEXTENSION( Gaffer::FileSystemPath, FileSystemPathTypeId, Path );

		~FileSystemPath() override;

		bool isValid( const IECore::Canceller *canceller = nullptr ) const override;
		bool isLeaf( const IECore::Canceller *canceller = nullptr ) const override;
		void propertyNames( std::vector<IECore::InternedString> &names, const IECore::Canceller *canceller = nullptr ) const override;
		/// Supported properties :
		///
		/// "fileSystem:owner" -> StringData
		/// "fileSystem:group" -> StringData
		/// "fileSystem:modificationTime" -> DateTimeData, in UTC time
		/// "fileSystem:size" -> UInt64Data, in bytes
		/// "fileSystem:frameRange" -> StringData
		IECore::ConstRunTimeTypedPtr property( const IECore::InternedString &name, const IECore::Canceller *canceller = nullptr ) const override;
		PathPtr copy() const override;

		// Returns true if this FileSystemPath includes FileSequences
		bool getIncludeSequences() const;
		// Determines whether this FileSystemPath includes FileSequences
		void setIncludeSequences( bool includeSequences );
		// Returns true if the path represents a FileSequence.
		bool isFileSequence() const;
		// Returns the FileSequence that represents the current leaf
		// or nullptr if this path is not a leaf, or does not represent
		// a FileSequence.
		IECore::FileSequencePtr fileSequence() const;

		// Returns the path converted to the OS native format
		std::string nativeString() const;

		static PathFilterPtr createStandardFilter( const std::vector<std::string> &extensions = std::vector<std::string>(), const std::string &extensionsLabel = "", bool includeSequenceFilter = false );

	protected :

		void doChildren( std::vector<PathPtr> &children, const IECore::Canceller *canceller ) const override;

	private :

#ifdef _MSC_VER

		/// Sets the path root and names in generic format from an OS native path string
		void rootAndNames( const std::string &string, IECore::InternedString &root, Names &names ) const override;

#endif

		bool m_includeSequences;

};

} // namespace Gaffer

#endif // GAFFER_FILESYSTEMPATH_H
