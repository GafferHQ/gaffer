//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2013-2014, Image Engine Design Inc. All rights reserved.
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

#include "GafferScene/Transform.h"

#include "Gaffer/Context.h"

using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

GAFFER_NODE_DEFINE_TYPE( Transform );

size_t Transform::g_firstPlugIndex = 0;

Transform::Transform( const std::string &name )
	:	SceneElementProcessor( name, IECore::PathMatcher::NoMatch )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new IntPlug( "space", Plug::In, Local, Local, ResetWorld ) );
	addChild( new TransformPlug( "transform" ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
}

Transform::~Transform()
{
}

Gaffer::IntPlug *Transform::spacePlug()
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

const Gaffer::IntPlug *Transform::spacePlug() const
{
	return getChild<Gaffer::IntPlug>( g_firstPlugIndex );
}

Gaffer::TransformPlug *Transform::transformPlug()
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::TransformPlug *Transform::transformPlug() const
{
	return getChild<Gaffer::TransformPlug>( g_firstPlugIndex + 1 );
}

void Transform::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	SceneElementProcessor::affects( input, outputs );

	if( input == spacePlug() || transformPlug()->isAncestorOf( input ) )
	{
		outputs.push_back( outPlug()->transformPlug() );
		outputs.push_back( outPlug()->boundPlug() );
	}
}

bool Transform::processesTransform() const
{
	return true;
}

void Transform::hashProcessedTransform( const ScenePath &path, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	const Space space = static_cast<Space>( spacePlug()->getValue() );
	h.append( space );
	transformPlug()->hash( h );

	switch( space )
	{
		case Local :
		case Parent :
			// No special hashing needed
			break;
		case World :
			h.append( relativeParentTransformHash( path, context ) );
			break;
		case ResetLocal :
			// No special hashing needed
			break;
		case ResetWorld :
			h.append( relativeParentTransformHash( path, context ) );
			break;
	}
}

Imath::M44f Transform::computeProcessedTransform( const ScenePath &path, const Gaffer::Context *context, const Imath::M44f &inputTransform ) const
{
	const Space space = static_cast<Space>( spacePlug()->getValue() );
	const Imath::M44f matrix = transformPlug()->matrix();

	switch( space )
	{
		case Local :
			return matrix * inputTransform;
		case Parent :
			return inputTransform * matrix;
		case World :
		{
			bool matchingAncestorFound = false;
			const Imath::M44f parentMatrix = relativeParentTransform( path, context, matchingAncestorFound );
			if( matchingAncestorFound )
			{
				// The ancestor will have the relative world matrix applied,
				// and we will inherit it, so we don't need to do anything at all.
				return inputTransform;
			}
			else
			{
				// We're all on our own, so we invert the parent
				// matrix to get back to world space, apply the matrix
				// we want to get a new world space, and then reapply
				// all of our original transform.
				return inputTransform * parentMatrix * matrix * parentMatrix.inverse();
			}
		}
		case ResetLocal :
			return matrix;
		case ResetWorld :
		{
			bool matchingAncestorFound = false;
			const Imath::M44f parentMatrix = relativeParentTransform( path, context, matchingAncestorFound );
			if( matchingAncestorFound )
			{
				// We will be giving the ancestor the absolute
				// world space matrix we want, so we just have to
				// cancel out the relative matrix between us and
				// that ancestor.
				return parentMatrix.inverse();
			}
			else
			{
				// We're all on our own, so we invert the parent
				// matrix to get back to world space, and then
				// apply the world space matrix we want.
				return matrix * parentMatrix.inverse();
			}

		}
		default :
			// Should never get here.
			return Imath::M44f();
	}
}

Imath::M44f Transform::fullParentTransform( const ScenePath &path ) const
{
	ScenePath parentPath = path;
	parentPath.pop_back();
	return inPlug()->fullTransform( parentPath );
}

IECore::MurmurHash Transform::fullParentTransformHash( const ScenePath &path ) const
{
	ScenePath parentPath = path;
	parentPath.pop_back();
	return inPlug()->fullTransformHash( parentPath );
}

Imath::M44f Transform::relativeParentTransform( const ScenePath &path, const Gaffer::Context *context, bool &matchingAncestorFound ) const
{
	ScenePlug::PathScope pathScope( context );

	Imath::M44f result;
	matchingAncestorFound = false;

	ScenePath ancestorPath( path );
	while( ancestorPath.size() ) // Root transform is always identity so can be ignored
	{
		ancestorPath.pop_back();
		pathScope.setPath( &ancestorPath );
		if( filterValue( pathScope.context() ) & IECore::PathMatcher::ExactMatch )
		{
			matchingAncestorFound = true;
			return result;
		}
		result = result * inPlug()->transformPlug()->getValue();
	}

	return result;
}

IECore::MurmurHash Transform::relativeParentTransformHash( const ScenePath &path, const Gaffer::Context *context ) const
{
	ScenePlug::PathScope pathScope( context );

	IECore::MurmurHash result;

	ScenePath ancestorPath( path );
	while( ancestorPath.size() ) // Root transform is always identity so can be ignored
	{
		ancestorPath.pop_back();
		pathScope.setPath( &ancestorPath );
		if( filterValue( pathScope.context() ) & IECore::PathMatcher::ExactMatch )
		{
			result.append( true );
			return result;
		}
		result.append( false );
		inPlug()->transformPlug()->hash( result );
	}

	return result;
}
