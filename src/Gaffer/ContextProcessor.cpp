//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2012, John Haddon. All rights reserved.
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

#include "Gaffer/ContextProcessor.h"

#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ValuePlug.h"

using namespace Gaffer;

static IECore::InternedString g_inPlugName( "in" );
static IECore::InternedString g_outPlugName( "out" );

IE_CORE_DEFINERUNTIMETYPED( ContextProcessor );

size_t ContextProcessor::g_firstPlugIndex = 0;

ContextProcessor::ContextProcessor( const std::string &name )
	:	ComputeNode( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new BoolPlug( "enabled", Gaffer::Plug::In, true ) );
}

ContextProcessor::~ContextProcessor()
{
}

void ContextProcessor::setup( const ValuePlug *plug )
{
	if( inPlug() )
	{
		throw IECore::Exception( "ContextProcessor already has an \"in\" plug." );
	}
	if( outPlug() )
	{
		throw IECore::Exception( "ContextProcessor already has an \"out\" plug." );
	}

	PlugPtr in = plug->createCounterpart( g_inPlugName, Plug::In );
	MetadataAlgo::copyColors( plug , in.get() , /* overwrite = */ false  );
	in->setFlags( Plug::Serialisable, true );
	addChild( in );

	PlugPtr out = plug->createCounterpart( g_outPlugName, Plug::Out );
	MetadataAlgo::copyColors( plug , out.get() , /* overwrite = */ false  );
	addChild( out );
}

ValuePlug *ContextProcessor::inPlug()
{
	return getChild<ValuePlug>( g_inPlugName );
}

const ValuePlug *ContextProcessor::inPlug() const
{
	return getChild<ValuePlug>( g_inPlugName );
}

ValuePlug *ContextProcessor::outPlug()
{
	return getChild<ValuePlug>( g_outPlugName );
}

const ValuePlug *ContextProcessor::outPlug() const
{
	return getChild<ValuePlug>( g_outPlugName );
}

BoolPlug *ContextProcessor::enabledPlug()
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

const BoolPlug *ContextProcessor::enabledPlug() const
{
	return getChild<BoolPlug>( g_firstPlugIndex );
}

Plug *ContextProcessor::correspondingInput( const Plug *output )
{
	if( const ValuePlug *v = IECore::runTimeCast<const ValuePlug>( output ) )
	{
		return const_cast<Plug *>( static_cast<const Plug *>( oppositePlug( v ) ) );
	}
	return nullptr;
}

const Plug *ContextProcessor::correspondingInput( const Plug *output ) const
{
	if( const ValuePlug *v = IECore::runTimeCast<const ValuePlug>( output ) )
	{
		return oppositePlug( v );
	}
	return nullptr;
}

void ContextProcessor::affects( const Plug *input, DependencyNode::AffectedPlugsContainer &outputs ) const
{
	ComputeNode::affects( input, outputs );

	if( input->direction() == Plug::In )
	{
		if( const ValuePlug *inputValuePlug = IECore::runTimeCast<const ValuePlug>( input ) )
		{
			const ValuePlug *output = oppositePlug( inputValuePlug );
			if( output )
			{
				outputs.push_back( output );
			}
		}
	}

	if( input == enabledPlug() || affectsContext( input ) )
	{
		if( const Plug *out = outPlug() )
		{
			if( out->children().size() )
			{
				for( RecursiveOutputPlugIterator it( out ); !it.done(); ++it )
				{
					if( !(*it)->children().size() )
					{
						outputs.push_back( it->get() );
					}
				}
			}
			else
			{
				outputs.push_back( out );
			}
		}
	}
}

ContextPtr ContextProcessor::inPlugContext() const
{
	if( enabledPlug()->getValue() )
	{
		Context::EditableScope scope( Context::current() );
		processContext( scope );
		return new Context( *Context::current() );
	}
	else
	{
		return new Context( *Context::current() );
	}
}

void ContextProcessor::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	const ValuePlug *input = oppositePlug( output );
	if( input )
	{
		if( enabledPlug()->getValue() )
		{
			Context::EditableScope scope( context );
			processContext( scope );
			h = input->hash();
		}
		else
		{
			h = input->hash();
		}
		return;
	}

	ComputeNode::hash( output, context, h );
}

void ContextProcessor::compute( ValuePlug *output, const Context *context ) const
{
	const ValuePlug *input = oppositePlug( output );
	if( input )
	{
		if( enabledPlug()->getValue() )
		{
			Context::EditableScope scope( context );
			processContext( scope );
			output->setFrom( input );
		}
		else
		{
			output->setFrom( input );
		}
		return;
	}

	return ComputeNode::compute( output, context );
}

const ValuePlug *ContextProcessor::correspondingDescendant( const ValuePlug *plug, const ValuePlug *plugAncestor, const ValuePlug *oppositeAncestor )
{
	// this method recursively computes oppositeAncestor->descendant( plug->relativeName( plugAncestor ) ).
	// ie it finds the relative path from plugAncestor to plug, and follows it from oppositeAncestor.

	if( plug == plugAncestor )
	{
		// we're already at plugAncestor, so the relative path has zero length
		// and we can return oppositeAncestor:
		return oppositeAncestor;
	}

	// now we find the corresponding descendant of plug->parent(), and
	// return its child with the same name as "plug" (if either of those things exist):

	// get parent of this plug:
	const ValuePlug *plugParent = plug->parent<ValuePlug>();
	if( !plugParent )
	{
		// looks like the "plug" we initially called this function with wasn't
		// a descendant of plugAncestor and we've recursed up into nothing, so
		// we return nullptr:
		return nullptr;
	}

	// find the corresponding plug for the parent:
	const ValuePlug *oppositeParent = correspondingDescendant( plugParent, plugAncestor, oppositeAncestor );
	if( !oppositeParent )
	{
		return nullptr;
	}

	// find the child corresponding to "plug"
	return oppositeParent->getChild<ValuePlug>( plug->getName() );
}

const ValuePlug *ContextProcessor::oppositePlug( const ValuePlug *plug ) const
{
	const ValuePlug *inPlug = this->inPlug();
	const ValuePlug *outPlug = this->outPlug();

	if( !( outPlug && inPlug ) )
	{
		return nullptr;
	}

	if( plug->direction() == Plug::Out )
	{
		return correspondingDescendant( plug, outPlug, inPlug );
	}
	else
	{
		return correspondingDescendant( plug, inPlug, outPlug );
	}
}
