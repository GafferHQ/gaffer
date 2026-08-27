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

#include "GafferOSL/OSLCode.h"

#include "GafferOSL/Private/CapturingErrorHandler.h"

#include "Gaffer/Metadata.h"
#include "Gaffer/Process.h"
#include "Gaffer/RampPlug.h"
#include "Gaffer/StringPlug.h"

#include "IECore/Exception.h"
#include "IECore/SearchPath.h"
#include "IECore/StringAlgo.h"

#include "OSL/oslcomp.h"

#include "boost/algorithm/string/replace.hpp"
#include "boost/bind/bind.hpp"
#include "boost/filesystem.hpp"

#include <fstream>

using namespace std;
using namespace boost::placeholders;
using namespace IECore;
using namespace OSL;
using namespace Gaffer;
using namespace GafferOSL;

//////////////////////////////////////////////////////////////////////////
// Code generation
//////////////////////////////////////////////////////////////////////////

namespace
{

string colorSplineParameter( const RampfColor3fPlug *plug )
{
	string result;
	result += "\tfloat " + plug->getName().string() + "Positions[] = { 0, 0, 1, 1 },\n";
	result += "\tcolor " + plug->getName().string() + "Values[] = { 0, 0, 1, 1 },\n";
	result += "\tstring " + plug->getName().string() + "Basis = \"catmull-rom\",\n";
	return result;
}

void hashParameter( const Plug *plug, IECore::MurmurHash &h )
{
	h.append( plug->getName() );
	h.append( plug->typeId() );
}

string parameter( const Plug *plug )
{
	const Gaffer::TypeId plugType = (Gaffer::TypeId)plug->typeId();
	if( plugType == RampfColor3fPlugTypeId )
	{
		return colorSplineParameter( static_cast<const RampfColor3fPlug *>( plug ) );
	}

	string type;
	string defaultValue;
	switch( (int)plugType )
	{
		case FloatPlugTypeId :
			defaultValue = "0.0";
			type = "float";
			break;
		case IntPlugTypeId :
			defaultValue = "0";
			type = "int";
			break;
		case Color3fPlugTypeId :
			defaultValue = "color( 0.0 )";
			type = "color";
			break;
		case V3fPlugTypeId :
			defaultValue = "vector( 0.0 )";
			type = "vector";
			break;
		case M44fPlugTypeId :
			defaultValue = "1";
			type = "matrix";
			break;
		case StringPlugTypeId :
			defaultValue = "\"\"";
			type = "string";
			break;
		case ClosurePlugTypeId :
			defaultValue = "0";
			type = "closure color";
			break;
		default :
			throw IECore::Exception( string( "Unsupported plug type \"" ) + plug->typeName() + "\"" );
	}

	string direction = plug->direction() == Plug::Out ? "output " : "";
	return "\t" + direction + type + " " + plug->getName().string() + " = " + defaultValue + ",\n";
}

string generate( const OSLCode *shader, string &shaderName )
{
	// Start with parameters

	string result;

	for( Plug::Iterator it( shader->parametersPlug() ); !it.done(); ++it )
	{
		result += parameter( it->get() );
	}

	result += "\n";

	for( Plug::Iterator it( shader->outPlug() ); !it.done(); ++it )
	{
		result += parameter( it->get() );
	}

	result += ")\n";

	// Reset line numbers reported by the OSL parser, so that they
	// don't include the stuff above.

	result += "#line 1\n";

	// Add on body

	const std::string code = shader->codePlug()->getValue();
	result += "{\n" + code;

	if( code.size() && *code.rbegin() != ';' )
	{
		result += ";";
	}

	result += "\n}\n";

	// The result so far uniquely characterises our shader,
	// so generate the shader name from its hash (unless we've
	// been given a name explicitly).

	if( shaderName.empty() )
	{
		IECore::MurmurHash hash;
		hash.append( result );
		shaderName = "oslCode" + hash.toString();
	}

	// Now we have the shader name, we can add on the header
	// for the shader, consisting of a constant set of includes
	// and the shader name itself.

	string header;
	header += "#include \"GafferOSL/ObjectProcessing.h\"\n";
	header += "#include \"GafferOSL/ImageProcessing.h\"\n";
	header += "#include \"GafferOSL/Spline.h\"\n\n";

	header += "shader " + shaderName + "(\n";

	result = header + result;
	return result;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// Shader compilation
//////////////////////////////////////////////////////////////////////////

namespace
{

class ScopedDirectory : boost::noncopyable
{

	public :

		ScopedDirectory( const std::filesystem::path &p )
			:	m_path( p )
		{
			std::filesystem::create_directories( m_path );
		}

		~ScopedDirectory()
		{
			std::filesystem::remove_all( m_path );
		}

	private :

		std::filesystem::path m_path;

};

std::filesystem::path compile( const std::string &shaderName, const std::string &shaderSource )
{

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

	std::filesystem::path directory = std::filesystem::temp_directory_path() / "gafferOSLCode";
	if( const char *cd = getenv( "GAFFEROSL_CODE_DIRECTORY" ) )
	{
		directory = cd;
	}

	for( size_t i = 0; i < shaderName.length(); i += 8 )
	{
		// Split the name into multiple subdirectory names, to avoid
		// creating lots of files in a single directory.
		directory /= shaderName.substr( i, 8 );
	}

	const std::filesystem::path osoFileName = directory / ( shaderName + ".oso" );

	// If that exists, then someone else has done our work already.

	if( std::filesystem::exists( osoFileName ) )
	{
		return osoFileName.generic_string();
	}

	// Make a temporary directory we can do our compilation in. The
	// ScopedDirectory class will remove it for us automatically on
	// destruction, so we don't need to worry about exception handling.

	const std::filesystem::path tempDirectory = directory / boost::filesystem::unique_path().string();
	ScopedDirectory scopedTempDirectory( tempDirectory );

	// Write the source code out.

	const std::string tempOSLFileName = ( tempDirectory / ( shaderName + ".osl" ) ).generic_string();
	std::ofstream f( tempOSLFileName.c_str() );
	if( !f.good() )
	{
		throw IECore::IOException( "Unable to open file \"" + tempOSLFileName + "\"" );
	}
	f << shaderSource;
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
		SearchPath searchPaths( includePaths );
		for( const auto &p : searchPaths.paths )
		{
			options.push_back( string( "-I" ) + p.generic_string() );
		}
	}

	const std::string tempOSOFileName = ( tempDirectory / ( shaderName + ".oso" ) ).generic_string();
	options.push_back( "-o" );
	options.push_back( tempOSOFileName );

	if( !compiler.compile( tempOSLFileName, options ) )
	{
		if( errorHandler.errors().size() )
		{
			string error = errorHandler.errors();
			boost::replace_all( error, tempOSLFileName, "code" );
			throw IECore::Exception( error );
		}
		else
		{
			throw IECore::Exception( "Unknown compilation error" );
		}
	}

	if( !std::filesystem::file_size( tempOSLFileName ) )
	{
		// Belt and braces. `compiler.compile()` should be reporting all errors,
		// but on rare occasions we have still seen empty `.oso` files being
		// produced. Detect this and warn so we can get to the bottom of it.
		throw IECore::Exception( "Empty file after compilation : \"" + tempOSLFileName + "\"" );
	}

	// Move temp file where we really want it, and clean up.

	std::filesystem::rename( tempOSOFileName, osoFileName );

	if( !std::filesystem::file_size( osoFileName ) )
	{
		// Belt and braces. `rename()` should be reporting all errors,
		// but on rare occasions we have still seen empty `.oso` files being
		// produced. Detect this and warn so we can get to the bottom of it.
		throw IECore::Exception( "Empty file after rename : \"" + osoFileName.generic_string() + "\"" );
	}

	return osoFileName;
}

} // namespace

//////////////////////////////////////////////////////////////////////////
// OSLCode
//////////////////////////////////////////////////////////////////////////

GAFFER_NODE_DEFINE_TYPE( OSLCode );

size_t OSLCode::g_firstPlugIndex;

OSLCode::OSLCode( const std::string &name )
	:	OSLShader( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );

	addChild( new StringPlug( "code", Plug::In, "", Plug::Default, IECore::StringAlgo::NoSubstitutions ) );
	addChild( new StringPlug( "__shaderName", Plug::Out, "", Plug::Default | Plug::AcceptsDependencyCycles ) );

	typePlug()->setValue( "osl:shader" );
	namePlug()->setInput( shaderNamePlug() );
	// Disable serialisation of private internal connection.
	namePlug()->setFlags( Plug::Serialisable, false );

	outPlug()->childAddedSignal().connect( boost::bind( &OSLCode::outputAdded, this ) );
	outPlug()->childRemovedSignal().connect( boost::bind( &OSLCode::outputRemoved, this ) );
}

OSLCode::~OSLCode()
{
}

Gaffer::StringPlug *OSLCode::codePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *OSLCode::codePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *OSLCode::shaderNamePlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *OSLCode::shaderNamePlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

std::string OSLCode::source( const std::string shaderName ) const
{
	string shaderNameCopy = shaderName;
	return generate( this, shaderNameCopy );
}

void OSLCode::loadShader( const std::string &shaderName, bool keepExistingValues )
{
}

void OSLCode::affects( const Plug *input, AffectedPlugsContainer &outputs ) const
{
	OSLShader::affects( input, outputs );
	if(
		parametersPlug()->isAncestorOf( input ) ||
		outPlug()->isAncestorOf( input ) ||
		input == codePlug()
	)
	{
		outputs.push_back( shaderNamePlug() );
	}
}

void OSLCode::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	if( output == shaderNamePlug() )
	{
		OSLShader::hash( output, context, h );
		for( const auto &plug : Plug::Range( *parametersPlug() ) )
		{
			hashParameter( plug.get(), h );
		}
		for( const auto &plug : Plug::Range( *outPlug() ) )
		{
			hashParameter( plug.get(), h );
		}
		codePlug()->hash( h );
	}
	else
	{
		OSLShader::hash( output, context, h );
	}
}

void OSLCode::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
	if( output == shaderNamePlug() )
	{
		string shaderName;
		const string shaderSource = generate( this, shaderName );
		std::filesystem::path shaderFile = compile( shaderName, shaderSource );
		static_cast<StringPlug *>( output )->setValue( shaderFile.replace_extension() );
	}
	else
	{
		OSLShader::compute( output, context );
	}
}

ValuePlug::CachePolicy OSLCode::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
	if( output == shaderNamePlug() )
	{
		// We don't use TBB, but it's common for many clients to want the same thing
		// at once, and there's no point in parallel threads fighting over the creation
		// of the file.
		return ValuePlug::CachePolicy::TaskCollaboration;
	}
	return OSLShader::computeCachePolicy( output );
}

void OSLCode::outputAdded()
{
	if( outPlug()->children().size() == 1 )
	{
		// OSLShaderUI registers a dynamic metadata entry which depends on whether or
		// not the plug has children, so we must notify the world that the value will
		// have changed.
		Metadata::plugValueChangedSignal( this )( outPlug(), "nodule:type", Metadata::ValueChangedReason::StaticRegistration );
	}
}

void OSLCode::outputRemoved()
{
	if( outPlug()->children().size() == 0 )
	{
		// OSLShaderUI registers a dynamic metadata entry which depends on whether or
		// not the plug has children, so we must notify the world that the value will
		// have changed.
		Metadata::plugValueChangedSignal( this )( outPlug(), "nodule:type", Metadata::ValueChangedReason::StaticRegistration );
	}
}
