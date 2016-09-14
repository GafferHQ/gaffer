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

#include <fstream>

#include "boost/filesystem.hpp"

#include "OSL/oslcomp.h"

#include "Gaffer/StringAlgo.h"

#include "GafferOSL/Private/CapturingErrorHandler.h"
#include "GafferOSL/OSLCode.h"

using namespace std;
using namespace OSL;
using namespace Gaffer;
using namespace GafferOSL;

//////////////////////////////////////////////////////////////////////////
// OSO Cache
//////////////////////////////////////////////////////////////////////////

namespace
{

class ScopedDirectory : boost::noncopyable
{

	public :

		ScopedDirectory( const boost::filesystem::path &p )
			:	m_path( p )
		{
			boost::filesystem::create_directories( m_path );
		}

		~ScopedDirectory()
		{
			boost::filesystem::remove_all( m_path );
		}

	private :

		boost::filesystem::path m_path;

};

boost::filesystem::path shader( const std::string &code )
{
	if( code == "" )
	{
		return "";
	}

	// We need to ensure the existence of a unique .oso file
	// containing the compiled code. We allow the user to specify
	// the base location for such files using the GAFFEROSL_CODE_DIRECTORY
	// environment variable, but we must also assume that multiple processes
	// on multiple machines will be concurrently trying to ensure the
	// same .oso files exist (think renderfarm). We achieve this as follows :
	//
	// - Use a hash of the code itself to generate the final .oso filename.
	//   This does nothing to resolve concurrent accesses, but ensures that
	//   different code goes in different files.
	// - If the required file does not exist yet, first generate it in a temporary
	//   location unique to this process.
	// - Finally, move the file into place using an atomic `rename()`.

	// Start by generating our final desired filename.

	boost::filesystem::path directory = boost::filesystem::temp_directory_path() / "gafferOSLCode";
	if( const char *cd = getenv( "GAFFEROSL_CODE_DIRECTORY" ) )
	{
		directory = cd;
	}

	IECore::MurmurHash hash;
	hash.append( code );
	const std::string hashString = hash.toString();
	for( size_t i = 0; i < hashString.length(); i += 8 )
	{
		// Split the hash into multiple subdirectory names, to avoid
		// creating lots of files in a single directory.
		directory /= hashString.substr( i, 8 );
	}

	const boost::filesystem::path osoFileName = directory / ( "oslCode" + hashString + ".oso" );

	// If that exists, then someone else has done our work already.

	if( boost::filesystem::exists( osoFileName ) )
	{
		return osoFileName.string();
	}

	// Make a temporary directory we can do our compilation in. The
	// ScopedDirectory class will remove it for us automatically on
	// destruction, so we don't need to worry about exception handling.

	const boost::filesystem::path tempDirectory = directory / boost::filesystem::unique_path();
	ScopedDirectory scopedTempDirectory( tempDirectory );

	// Write the source code out.

	const std::string tempOSLFileName = ( tempDirectory / ( "oslCode" + hashString + ".osl" ) ).string();
	std::ofstream f( tempOSLFileName.c_str() );
	if( !f.good() )
	{
		throw IECore::IOException( "Unable to open file \"" + tempOSLFileName + "\"" );
	}
	f << code;
	if( !f.good() )
	{
		throw IECore::IOException( "Failed to write to \"" + tempOSLFileName + "\"" );
	}
	f.close();

	// Compile.

	GafferOSL::Private::CapturingErrorHandler errorHandler;
	OSLCompiler compiler( &errorHandler );

	vector<string> options;
	if( const char *includePaths = getenv( "OSL_SHADER_PATHS" ) )
	{
		tokenize( includePaths, ':', options );
		for( vector<string>::iterator it = options.begin(), eIt = options.end(); it != eIt; ++it )
		{
			it->insert( 0, "-I" );
		}
	}

	const std::string tempOSOFileName = ( tempDirectory / ( "oslCode" + hashString + ".oso" ) ).string();
	options.push_back( "-o" );
	options.push_back( tempOSOFileName );

	if( !compiler.compile( tempOSLFileName, options ) )
	{
		if( errorHandler.errors().size() )
		{
			throw IECore::Exception( errorHandler.errors() );
		}
		else
		{
			throw IECore::Exception( "Unknown compilation error" );
		}
	}

	// Move temp file where we really want it, and clean up.

	boost::filesystem::rename( tempOSOFileName, osoFileName );

	return osoFileName;
}

};

//////////////////////////////////////////////////////////////////////////
// OSLCode
//////////////////////////////////////////////////////////////////////////

IE_CORE_DEFINERUNTIMETYPED( OSLCode );

OSLCode::OSLCode( const std::string &name )
	:	OSLShader( name )
{
}

OSLCode::~OSLCode()
{
}

void OSLCode::setCode( const std::string &code )
{
	if( code == m_code )
	{
		return;
	}

	loadShader( shader( code ).replace_extension().string(), /* keepExistingValues = */ true );
	m_code = code;
	codeChangedSignal();
}

std::string OSLCode::getCode() const
{
	return m_code;
}

OSLCode::CodeChangedSignal &OSLCode::codeChangedSignal()
{
	return m_codeChangedSignal;
}
