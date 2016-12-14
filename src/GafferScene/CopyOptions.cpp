#include "GafferScene/CopyOptions.h"
#include "Gaffer/StringAlgo.h"

#include "boost/algorithm/string/predicate.hpp"

// using namespace IECore;
using namespace Gaffer;
using namespace GafferScene;

IE_CORE_DEFINERUNTIMETYPED( CopyOptions );

size_t CopyOptions::g_firstPlugIndex = 0;

CopyOptions::CopyOptions( const std::string &name )
	:	GlobalsProcessor( name )
{
	storeIndexOfNextChild( g_firstPlugIndex );
	addChild( new ScenePlug( "source", Plug::In ) );
	addChild( new StringPlug( "names" , Plug::In, "" ) );

	// Fast pass-throughs for things we don't modify
	outPlug()->childNamesPlug()->setInput( inPlug()->childNamesPlug() );
	outPlug()->objectPlug()->setInput( inPlug()->objectPlug() );
	outPlug()->setNamesPlug()->setInput( inPlug()->setNamesPlug() );
	outPlug()->setPlug()->setInput( inPlug()->setPlug() );
	outPlug()->attributesPlug()->setInput( inPlug()->attributesPlug() );
	outPlug()->transformPlug()->setInput( inPlug()->transformPlug() );
	outPlug()->boundPlug()->setInput( inPlug()->boundPlug() );
}

CopyOptions::~CopyOptions()
{
}

GafferScene::ScenePlug *CopyOptions::sourcePlug()
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

const GafferScene::ScenePlug *CopyOptions::sourcePlug() const
{
	return getChild<ScenePlug>( g_firstPlugIndex );
}

Gaffer::StringPlug *CopyOptions::namesPlug()
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::StringPlug *CopyOptions::namesPlug() const
{
	return getChild<StringPlug>( g_firstPlugIndex + 1 );
}

void CopyOptions::affects( const Gaffer::Plug *input, AffectedPlugsContainer &outputs ) const
{
	GlobalsProcessor::affects( input, outputs );

	if( input == sourcePlug()->globalsPlug() || input == namesPlug() )
	{
		outputs.push_back( outPlug()->globalsPlug() );
	}
}

void CopyOptions::hashProcessedGlobals( const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
	sourcePlug()->globalsPlug()->hash( h );
	namesPlug()->hash( h );
}

IECore::ConstCompoundObjectPtr CopyOptions::computeProcessedGlobals( const Gaffer::Context *context, IECore::ConstCompoundObjectPtr inputGlobals ) const
{

	IECore::CompoundObjectPtr result = new IECore::CompoundObject;
	// Since we're not going to modify any existing members (only add new ones),
	// and our result becomes const on returning it, we can directly reference
	// the input members in our result without copying. Be careful not to modify
	// them though!
	result->members() = inputGlobals->members();

	// copy matching options
	const std::string prefix = "option:";
	const std::string names = namesPlug()->getValue();

	IECore::ConstCompoundObjectPtr sourceGlobals = sourcePlug()->globalsPlug()->getValue();
	for( IECore::CompoundObject::ObjectMap::const_iterator it = sourceGlobals->members().begin(), eIt = sourceGlobals->members().end(); it != eIt; ++it )
	{
		if( boost::starts_with( it->first.c_str(), prefix ) )
		{
			if( StringAlgo::matchMultiple( it->first.c_str() + prefix.size(), names.c_str() ) )
			{
				result->members()[it->first] = it->second;
			}
		}
	}

	return result;
}
