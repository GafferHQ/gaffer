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

#include "Gaffer/ContextAlgo.h"
#include "Gaffer/MetadataAlgo.h"
#include "Gaffer/ValuePlug.h"

using namespace Gaffer;

static IECore::InternedString g_inPlugName( "in" );
static IECore::InternedString g_outPlugName( "out" );

class ContextProcessor::ProcessedScope : public Context::EditableScope
{

	public :

		ProcessedScope( const Context *context, const ContextProcessor *processor )
			:	EditableScope( context )
		{
			ContextAlgo::GlobalScope globalScope( context, processor->inPlug() );
			if( processor->enabledPlug()->getValue() )
			{
				processor->processContext( *this, m_storage );
			}
		}

	private :

		IECore::ConstRefCountedPtr m_storage;

};

GAFFER_NODE_DEFINE_TYPE( ContextProcessor );

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

void ContextProcessor::setup( const Plug *plug )
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

Plug *ContextProcessor::inPlug()
{
	return getChild<Plug>( g_inPlugName );
}

const Plug *ContextProcessor::inPlug() const
{
	return getChild<Plug>( g_inPlugName );
}

Plug *ContextProcessor::outPlug()
{
	return getChild<Plug>( g_outPlugName );
}

const Plug *ContextProcessor::outPlug() const
{
	return getChild<Plug>( g_outPlugName );
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
		if( const Plug *output = oppositePlug( input ) )
		{
			outputs.push_back( output );
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
	ProcessedScope processedScope( Context::current(), this );
	return new Context( *processedScope.context() );
}

void ContextProcessor::hash( const ValuePlug *output, const Context *context, IECore::MurmurHash &h ) const
{
	auto input = IECore::runTimeCast<const ValuePlug>( oppositePlug( output ) );
	if( input )
	{
		ProcessedScope processedScope( context, this );
		h = input->hash();
		return;
	}

	ComputeNode::hash( output, context, h );
}

void ContextProcessor::compute( ValuePlug *output, const Context *context ) const
{
	auto input = IECore::runTimeCast<const ValuePlug>( oppositePlug( output ) );
	if( input )
	{
		ProcessedScope processedScope( context, this );
		output->setFrom( input );
		return;
	}

	return ComputeNode::compute( output, context );
}

const Plug *ContextProcessor::correspondingDescendant( const Plug *plug, const Plug *plugAncestor, const Plug *oppositeAncestor )
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
	const Plug *plugParent = plug->parent<Plug>();
	if( !plugParent )
	{
		// looks like the "plug" we initially called this function with wasn't
		// a descendant of plugAncestor and we've recursed up into nothing, so
		// we return nullptr:
		return nullptr;
	}

	// find the corresponding plug for the parent:
	const Plug *oppositeParent = correspondingDescendant( plugParent, plugAncestor, oppositeAncestor );
	if( !oppositeParent )
	{
		return nullptr;
	}

	// find the child corresponding to "plug"
	return oppositeParent->getChild<ValuePlug>( plug->getName() );
}

const Plug *ContextProcessor::oppositePlug( const Plug *plug ) const
{
	const Plug *inPlug = this->inPlug();
	const Plug *outPlug = this->outPlug();

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
