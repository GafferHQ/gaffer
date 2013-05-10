//////////////////////////////////////////////////////////////////////////
//  
//  Copyright (c) 2013, Image Engine Design Inc. All rights reserved.
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

#include "boost/tokenizer.hpp"

#include "Gaffer/Context.h"

#include "GafferScene/Constraint.h"

using namespace Imath;
using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( Constraint );

size_t Constraint::g_firstPlugIndex = 0;

Constraint::Constraint( const std::string &name )
	:	SceneElementProcessor( name, Filter::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new StringPlug( "target" ) );
	addChild( new IntPlug( "targetMode", Plug::In, Origin, Origin, BoundCenter ) );
}

Constraint::~Constraint()
{
}

Gaffer::StringPlug *Constraint::targetPlug()
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Constraint::targetPlug() const
{
	return getChild<Gaffer::StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Constraint::targetModePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Constraint::targetModePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex + 1 );
}
		
void Constraint::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );
	
	if( input == targetPlug() || input == targetModePlug() || affectsConstraint( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
}

bool Constraint::processesTransform() const
{
	return true;
}

void Constraint::hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	ScenePath parentPath = path;
	parentPath.pop_back();
	h.append( inPlug()->fullTransformHash( parentPath ) );
	
	ScenePath targetPath;
	tokenizeTargetPath( targetPath );
	h.append( inPlug()->fullTransformHash( targetPath ) );
	
	const TargetMode targetMode = (TargetMode)targetModePlug()->getValue();
	h.append( targetMode );
	if( targetMode != Origin )
	{
		h.append( inPlug()->boundHash( targetPath ) );
	}
	
	hashConstraint( context, h );
}

Imath::M44f Constraint::computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	ScenePath parentPath = path;
	parentPath.pop_back();
	
	const M44f parentTransform = inPlug()->fullTransform( parentPath );
	const M44f fullInputTransform = inputTransform * parentTransform;
		
	ScenePath targetPath;
	tokenizeTargetPath( targetPath );
	M44f fullTargetTransform = inPlug()->fullTransform( targetPath );
	
	const TargetMode targetMode = (TargetMode)targetModePlug()->getValue();
	if( targetMode != Origin )
	{
		const Box3f targetBound = inPlug()->bound( targetPath );
		if( !targetBound.isEmpty() )
		{
			switch( targetMode )
			{
				case BoundMin :
					fullTargetTransform.translate( targetBound.min );
					break;
				case BoundMax :
					fullTargetTransform.translate( targetBound.max );
					break;
				case BoundCenter :
					fullTargetTransform.translate( targetBound.center() );
					break;
				default :
					break;
			}
		}
	}
	
	const M44f fullConstrainedTransform = computeConstraint( fullTargetTransform, fullInputTransform );
	return fullConstrainedTransform * parentTransform.inverse();
}

void Constraint::tokenizeTargetPath( ScenePath &path ) const
{
	/// \todo We really need a plug type which stores a path internally.
	typedef boost::tokenizer<boost::char_separator<char> > Tokenizer;
	std::string targetPathAsString = targetPlug()->getValue();
	Tokenizer tokenizer( targetPathAsString, boost::char_separator<char>( "/" ) );	
	for( Tokenizer::const_iterator it = tokenizer.begin(), eIt = tokenizer.end(); it != eIt; it++ )
	{
		path.push_back( *it );
	}
}
