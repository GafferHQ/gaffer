//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2011-2012, John Haddon. All rights reserved.
//  Copyright (c) 2011-2013, Image Engine Design Inc. All rights reserved.
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

#include "Gaffer/ApplicationRoot.h"

#include "Gaffer/Preferences.h"
#include "Gaffer/Version.h"

#include <filesystem>

using namespace Gaffer;

GAFFER_GRAPHCOMPONENT_DEFINE_TYPE( ApplicationRoot );

ApplicationRoot::ApplicationRoot( const std::string &name )
	:	GraphComponent( name )
{
	ScriptContainerPtr s = new ScriptContainer;
	setChild( "scripts", s );
	PreferencesPtr p = new Preferences;
	setChild( "preferences", p );
}

ApplicationRoot::~ApplicationRoot()
{
}

bool ApplicationRoot::acceptsChild( const GraphComponent *potentialChild ) const
{
	if( children().size()<2 )
	{
		return true;
	}
	return false;
}

bool ApplicationRoot::acceptsParent( const GraphComponent *potentialParent ) const
{
	return false;
}

ScriptContainer *ApplicationRoot::scripts()
{
	return getChild<ScriptContainer>( "scripts" );
}

const ScriptContainer *ApplicationRoot::scripts() const
{
	return getChild<ScriptContainer>( "scripts" );
}

const IECore::Object *ApplicationRoot::getClipboardContents() const
{
	return m_clipboardContents.get();
}

void ApplicationRoot::setClipboardContents( const IECore::Object *clip )
{
	if( !m_clipboardContents || m_clipboardContents->isNotEqualTo( clip ) )
	{
		m_clipboardContents = clip->copy();
		clipboardContentsChangedSignal()( this );
	}
}

ApplicationRoot::ClipboardSignal &ApplicationRoot::clipboardContentsChangedSignal()
{
	return m_clipboardContentsChangedSignal;
}

Preferences *ApplicationRoot::preferences()
{
	return getChild<Preferences>( "preferences" );
}

const Preferences *ApplicationRoot::preferences() const
{
	return getChild<Preferences>( "preferences" );
}

void ApplicationRoot::savePreferences() const
{
	savePreferences( defaultPreferencesFileName() );
}

void ApplicationRoot::savePreferences( const std::filesystem::path &fileName ) const
{
	throw IECore::Exception( "Cannot save preferences from an ApplicationRoot not created in Python." );
}

std::filesystem::path ApplicationRoot::preferencesLocation() const
{
	const char *home = getenv( "HOME" );
	if( !home )
	{
		throw IECore::Exception( "$HOME environment variable not set" );
	}

	std::filesystem::path result = home;
	result = result / "gaffer" / fmt::format( "startup-{}.{}", GAFFER_MILESTONE_VERSION, GAFFER_MAJOR_VERSION ) / getName().string();

	std::filesystem::create_directories( result );

	return result;
}

std::filesystem::path ApplicationRoot::defaultPreferencesFileName() const
{
	return preferencesLocation() / "preferences.py";
}
