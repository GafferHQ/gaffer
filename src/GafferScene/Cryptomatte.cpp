//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2021, Murray Stevenson. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//       copyright notice, this list of conditions and the following
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

#include "GafferScene/Cryptomatte.h"

#include "GafferImage/ImageAlgo.h"

#include "Gaffer/Context.h"

#include "IECore/MessageHandler.h"

#include <boost/filesystem.hpp>
#include <boost/iostreams/stream.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <boost/regex.hpp>

#include <unordered_map>
#include <unordered_set>

using namespace std;
using namespace IECore;
using namespace Gaffer;

namespace 
{

//-----------------------------------------------------------------------------
// MurmurHash3 was written by Austin Appleby, and is placed in the public
// domain. The author hereby disclaims copyright to this source code.

inline uint32_t rotl32( uint32_t x, int8_t r )
{
    return (x << r) | (x >> (32 - r));
}

inline uint32_t fmix( uint32_t h )
{
    h ^= h >> 16;
    h *= 0x85ebca6b;
    h ^= h >> 13;
    h *= 0xc2b2ae35;
    h ^= h >> 16;

    return h;
}

uint32_t MurmurHash3_x86_32( const void *key, size_t len, uint32_t seed )
{
    const uint8_t *data = (const uint8_t *)key;
    const size_t nblocks = len / 4;

    uint32_t h1 = seed;

    const uint32_t c1 = 0xcc9e2d51;
    const uint32_t c2 = 0x1b873593;

    /* body */

    const uint32_t *blocks = (const uint32_t *)(data + nblocks * 4);

    for( size_t i = -nblocks; i; i++ )
    {
        uint32_t k1 = blocks[i];

        k1 *= c1;
        k1 = rotl32( k1, 15 );
        k1 *= c2;

        h1 ^= k1;
        h1 = rotl32( h1, 13 );
        h1 = h1 * 5 + 0xe6546b64;
    }

    /* tail */

    const uint8_t *tail = (const uint8_t *)(data + nblocks * 4);

    uint32_t k1 = 0;

    switch( len & 3 )
    {
    case 3:
        k1 ^= tail[2] << 16;
    case 2:
        k1 ^= tail[1] << 8;
    case 1:
        k1 ^= tail[0];
        k1 *= c1;
        k1 = rotl32( k1, 15 );
        k1 *= c2;
        h1 ^= k1;
    }

    /* finalization */

    h1 ^= len;

    h1 = fmix( h1 );

    return h1;
}

//-----------------------------------------------------------------------------

inline float matteNameToValue( const std::string &matteName )
{
    uint32_t hash = MurmurHash3_x86_32( matteName.c_str(), matteName.length(), 0);
    
    // Taken from the Cryptomatte specification - https://github.com/Psyop/Cryptomatte/blob/master/specification/cryptomatte_specification.pdf
    //​ ​if​ ​all​ ​exponent​ ​bits​ ​are​ ​0​ ​(subnormals,​ ​+zero,​ ​-zero)​ ​set​ ​exponent​ ​to​ ​1 ​ ​​ ​​ ​​
    //​ ​if​ ​all​ ​exponent​ ​bits​ ​are​ ​1​ ​(NaNs,​ ​+inf,​ ​-inf)​ ​set​ ​exponent​ ​to​ ​254
    const uint32_t exponent = hash >> 23 & 255;
    //​ ​extract​ ​exponent​ ​(8​ ​bits)
    if( exponent == 0 || exponent == 255 )
    {
        hash ^= 1 << 23; //​ ​toggle​ ​bit
    }
    float result;
    std::memcpy( &result, &hash, sizeof( uint32_t ) );

    return result;
}

inline std::string hashLayerName( const std::string &layerName )
{
    // hash the layer name to find manifest keys from image metadata
    return boost::str( boost::format( "%08x" ) % MurmurHash3_x86_32( layerName.c_str(), layerName.length(), 0 ) );
}

IECore::CompoundDataPtr propertyTreeToCompoundData( const boost::property_tree::ptree &pt )
{
    boost::regex instanceDataRegex( "^instance:[0-9a-f]+$" );

    IECore::CompoundDataPtr resultData = new IECore::CompoundData();
    CompoundDataMap &result = resultData->writable();
       
    uint32_t hash;

    for( auto &it : pt )
    {
        // NOTE: exclude locations starting with "instance:" under root
        if( boost::regex_match( it.first, instanceDataRegex ) )
        {
            continue;
        }
        
        std::sscanf( it.second.data().c_str(), "%x", &hash );

        result[hash] = new StringData( it.first );
    }
    
    return resultData;
}

IECore::CompoundDataPtr parseManifestFromMetadata( const std::string &cryptomatteLayer, ConstCompoundDataPtr metadata ) 
{
    const std::string manifestKey = boost::str( boost::format( "cryptomatte/%.7s/manifest" ) % hashLayerName( cryptomatteLayer ) );

    if( metadata->readable().find( manifestKey ) == metadata->readable().end() )
    {
        IECore::msg( IECore::Msg::Error, "Cryptomatte", boost::format( "Manifest metadata key not found: %s" ) % manifestKey );
        return nullptr;
    }

    const StringData *manifest = metadata->member<StringData>( manifestKey );
    boost::iostreams::stream<boost::iostreams::array_source> stream( manifest->readable().c_str(), manifest->readable().size() );
    boost::property_tree::ptree pt;

    try 
    {
        boost::property_tree::read_json( stream, pt );
    }
    catch( const boost::property_tree::json_parser::json_parser_error &e )
    {
        IECore::msg( IECore::Msg::Error, "Cryptomatte", boost::format( "Error parsing manifest metadata: %s" ) % e.what() );
        return nullptr;
    }

    return propertyTreeToCompoundData( pt );
}

IECore::CompoundDataPtr parseManifestFromFile( const std::string &manifestFile ) 
{
    if( manifestFile == "" || !boost::filesystem::is_regular_file( manifestFile ) )
    {
        return nullptr;
    }

    boost::property_tree::ptree pt;

    try
    {
        boost::property_tree::read_json( manifestFile, pt );
    }
    catch( const boost::property_tree::json_parser::json_parser_error &e )
    {
        IECore::msg( IECore::Msg::Error, "Cryptomatte", boost::format( "Error parsing manifest file: %s" ) % e.what() );
        return nullptr;
    }

   return propertyTreeToCompoundData( pt );
}

IECore::CompoundDataPtr parseSidecarManifestFromMetadata( const std::string &cryptomatteLayer, ConstCompoundDataPtr metadata, const std::string &sidecarDirectory ) 
{
    if( sidecarDirectory == "" || !boost::filesystem::is_directory( sidecarDirectory ) )
    {
        return nullptr;
    }

    const std::string manifestFileKey = boost::str( boost::format( "cryptomatte/%.7s/manif_file" ) % hashLayerName( cryptomatteLayer ) );

    if( metadata->readable().find( manifestFileKey ) == metadata->readable().end() )
    {
        return nullptr;
    }

    const StringData *manifestFile = metadata->member<StringData>( manifestFileKey );
    boost::filesystem::path p( sidecarDirectory );
    // append manifest file metadata to sidecar directory path
    p /= manifestFile->readable();
    
    return parseManifestFromFile( p.string() );
}

} // namespace

namespace GafferScene
{
GAFFER_NODE_DEFINE_TYPE( Cryptomatte );

size_t Cryptomatte::g_firstPlugIndex = 0;

// first channel contains id, second contains alpha contribution
typedef std::unordered_map<std::string, std::string> ChannelMap;
static const ChannelMap g_channelMap = {
    {"R", "G"}, 
    {"B", "A"}, 
};

const std::string g_firstDataChannelSuffix = "00.R";                                        
const std::string g_cryptomatteChannelPattern = "^%s[0-9]+\\.[RGBA]";

Cryptomatte::Cryptomatte( const std::string &name )
    : GafferImage::FlatImageProcessor( name )
{
    storeIndexOfNextChild( g_firstPlugIndex );
    addChild( new StringPlug( "layer", Gaffer::Plug::In, "" ) );
    addChild( new IntPlug( "manifestSource", Gaffer::Plug::In, (int)ManifestSource::Metadata, /* min */ (int)ManifestSource::Metadata, /* max */ (int)ManifestSource::Sidecar ) );
    addChild( new StringPlug( "sidecarManifestPath", Gaffer::Plug::In, "") );
    addChild( new StringPlug( "outputChannel", Gaffer::Plug::In, "A") );
    addChild( new StringVectorDataPlug( "matteNames", Gaffer::Plug::In, new StringVectorData() ) );
    addChild( new FloatVectorDataPlug( "__matteValues", Gaffer::Plug::Out, new FloatVectorData() ) );
    addChild( new AtomicCompoundDataPlug( "__manifest", Gaffer::Plug::Out, new CompoundData() ) );
    addChild( new PathMatcherDataPlug( "__manifestPaths", Gaffer::Plug::Out, new PathMatcherData ) );
    addChild( new ScenePlug( "__manifestScene", Gaffer::Plug::Out ) );
    addChild( new FloatVectorDataPlug( "__matteChannelData", Gaffer::Plug::Out, GafferImage::ImagePlug::blackTile() ) );
    
    outPlug()->formatPlug()->setInput( inPlug()->formatPlug() );
    outPlug()->metadataPlug()->setInput( inPlug()->metadataPlug() );
    outPlug()->dataWindowPlug()->setInput( inPlug()->dataWindowPlug() );
}

Cryptomatte::~Cryptomatte()
{
}

Gaffer::StringPlug *Cryptomatte::layerPlug()
{
    return getChild<StringPlug>( g_firstPlugIndex );
}

const Gaffer::StringPlug *Cryptomatte::layerPlug() const
{
    return getChild<StringPlug>( g_firstPlugIndex );
}

Gaffer::IntPlug *Cryptomatte::manifestSourcePlug()
{
    return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

const Gaffer::IntPlug *Cryptomatte::manifestSourcePlug() const
{
    return getChild<IntPlug>( g_firstPlugIndex + 1 );
}

Gaffer::StringPlug *Cryptomatte::manifestPathPlug()
{
    return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

const Gaffer::StringPlug *Cryptomatte::manifestPathPlug() const
{
    return getChild<StringPlug>( g_firstPlugIndex + 2 );
}

Gaffer::StringPlug *Cryptomatte::outputChannelPlug()
{
    return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

const Gaffer::StringPlug *Cryptomatte::outputChannelPlug() const
{
    return getChild<StringPlug>( g_firstPlugIndex + 3 );
}

Gaffer::StringVectorDataPlug *Cryptomatte::matteNamesPlug()
{
    return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
}

const Gaffer::StringVectorDataPlug *Cryptomatte::matteNamesPlug() const
{
    return getChild<StringVectorDataPlug>( g_firstPlugIndex + 4 );
}

Gaffer::FloatVectorDataPlug *Cryptomatte::matteValuesPlug()
{
    return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 5 );
}

const Gaffer::FloatVectorDataPlug *Cryptomatte::matteValuesPlug() const
{
    return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 5 );
}

Gaffer::AtomicCompoundDataPlug *Cryptomatte::manifestPlug()
{
    return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 6 );
}

const Gaffer::AtomicCompoundDataPlug *Cryptomatte::manifestPlug() const
{
    return getChild<AtomicCompoundDataPlug>( g_firstPlugIndex + 6 );
}

Gaffer::PathMatcherDataPlug *Cryptomatte::manifestPathDataPlug()
{
    return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 7 );
}

const Gaffer::PathMatcherDataPlug *Cryptomatte::manifestPathDataPlug() const
{
    return getChild<PathMatcherDataPlug>( g_firstPlugIndex + 7 );
}

GafferScene::ScenePlug *Cryptomatte::manifestScenePlug()
{
    return getChild<GafferScene::ScenePlug>( g_firstPlugIndex + 8 );
}

const GafferScene::ScenePlug *Cryptomatte::manifestScenePlug() const
{
    return getChild<GafferScene::ScenePlug>( g_firstPlugIndex + 8 );
}

Gaffer::FloatVectorDataPlug *Cryptomatte::matteChannelDataPlug()
{
    return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 9 );
}

const Gaffer::FloatVectorDataPlug *Cryptomatte::matteChannelDataPlug() const
{
    return getChild<FloatVectorDataPlug>( g_firstPlugIndex + 9 );
}

void Cryptomatte::affects(const Gaffer::Plug *input, AffectedPlugsContainer &outputs) const
{
    FlatImageProcessor::affects(input, outputs);

    if( input == inPlug()->channelDataPlug() ||
        input == layerPlug() ||
        input == outputChannelPlug() ||
        input == matteValuesPlug() )
    {
        outputs.push_back( matteChannelDataPlug() );
    }

    if( input == matteChannelDataPlug() )
    {
        outputs.push_back( outPlug()->channelDataPlug() );
    }

    if( input == inPlug()->channelNamesPlug() ||
        input == outputChannelPlug() )
    {
        outputs.push_back( outPlug()->channelNamesPlug() );
    }

    if( input == layerPlug() ||
        input == manifestPathPlug() ||
        input == manifestSourcePlug() ||
        input == inPlug()->metadataPlug() )
    {
        outputs.push_back( manifestPlug() );
    }

    if( input == matteNamesPlug() ||
        input == manifestPlug() )
    {
        outputs.push_back( matteValuesPlug() );
    }

    if( input == manifestPlug() )
    {
        outputs.push_back( manifestPathDataPlug() );
    }

    if( input == manifestPathDataPlug() )
    {
        outputs.push_back( manifestScenePlug()->childNamesPlug() );
    }
}

void Cryptomatte::hash( const Gaffer::ValuePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
    FlatImageProcessor::hash( output, context, h );

    if( output == manifestPlug() )
    {
        GafferImage::ImagePlug::GlobalScope globalScope( context );
        layerPlug()->hash( h );
        manifestPathPlug()->hash( h );
        manifestSourcePlug()->hash( h );
        inPlug()->metadataPlug()->hash( h );
    }
    else if( output == matteValuesPlug() )
    {
        GafferImage::ImagePlug::GlobalScope globalScope( context );
        manifestPlug()->hash( h );
        matteNamesPlug()->hash( h );
    }
    else if( output == manifestPathDataPlug() )
    {
        GafferImage::ImagePlug::GlobalScope globalScope( context );
        manifestPlug()->hash( h );
    }
    else if( output == manifestScenePlug()->childNamesPlug() )
    {
        GafferImage::ImagePlug::GlobalScope globalScope( context );
        const GafferScene::ScenePlug::ScenePath &scenePath = context->get<GafferScene::ScenePlug::ScenePath>( GafferScene::ScenePlug::scenePathContextName );
        h.append( &scenePath.front(), scenePath.size() );
        manifestPathDataPlug()->hash(h);
    }
    else if( output == matteChannelDataPlug() )
    {
        inPlug()->channelDataPlug()->hash( h );

        std::string cryptomatteLayer; 
        ConstStringVectorDataPtr channelNamesData;
        {
            GafferImage::ImagePlug::GlobalScope globalScope( context );
            cryptomatteLayer = layerPlug()->getValue();
            channelNamesData = inPlug()->channelNamesPlug()->getValue();

            matteValuesPlug()->hash( h );
        }

        boost::regex channelNameRegex( boost::str( boost::format( g_cryptomatteChannelPattern ) % cryptomatteLayer ) );
        GafferImage::ImagePlug::ChannelDataScope channelDataScope( context );
        for( const auto &c : channelNamesData->readable() )
        {
            if( boost::regex_match( c, channelNameRegex ) )
            {
                channelDataScope.setChannelName( &c );
                inPlug()->channelDataPlug()->hash( h );
            }
        }
    }
}

void Cryptomatte::compute( Gaffer::ValuePlug *output, const Gaffer::Context *context ) const
{
    FlatImageProcessor::compute( output, context );
    
    if( output == manifestPlug() )
    {
        const std::string cryptomatteLayer = layerPlug()->getValue();
        if( cryptomatteLayer == "" )
        {
            static_cast<AtomicCompoundDataPlug *>( output )->setToDefault();
            return;
        }

        IECore::CompoundDataPtr resultData = nullptr;

        switch( (ManifestSource)manifestSourcePlug()->getValue() )
        {
            case ManifestSource::Metadata :
            {
                ConstCompoundDataPtr metadata = inPlug()->metadataPlug()->getValue();
                resultData = parseManifestFromMetadata( cryptomatteLayer, metadata );
                break;
            }
            case ManifestSource::Sidecar :
            {
                const std::string manifestPath = manifestPathPlug()->getValue();

                if( manifestPath == "" )
                {
                    break;
                }
                else if( boost::filesystem::is_regular_file( manifestPath ) )
                {
                    resultData = parseManifestFromFile( manifestPath );
                }
                else if( boost::filesystem::is_directory( manifestPath ) )
                {
                    ConstCompoundDataPtr metadata = inPlug()->metadataPlug()->getValue();
                    resultData = parseSidecarManifestFromMetadata( cryptomatteLayer, metadata, manifestPath ); 
                }
                else
                {
                    throw IECore::Exception( boost::str( boost::format( "Invalid manifest path: %s" ) % manifestPath ) );
                }
                break;
            }
        }

        if( resultData )
        {
            static_cast<AtomicCompoundDataPlug *>( output )->setValue( resultData );
        }
        else
        {
            static_cast<AtomicCompoundDataPlug *>( output )->setToDefault();
        }
    }
    else if( output == matteValuesPlug() )
    {
        FloatVectorDataPtr resultData = new IECore::FloatVectorData();
        std::vector<float> &result = resultData->writable();
        std::unordered_set<float> matteValues;

        ConstStringVectorDataPtr matteNames = matteNamesPlug()->getValue();
        ConstCompoundDataPtr manifest;
        try
        { 
            manifest = manifestPlug()->getValue();
        }
        catch( const std::exception &e )
        {
            IECore::msg( IECore::Msg::Error, "Cryptomatte::matteValues", boost::format( "Error reading manifest: %s" ) % e.what() );
        }

        IECore::PathMatcher pathMatcher;
        for( const auto &name : matteNames->readable() )
        {
            if( name.size() > 0 && name.front() == '<' && name.back() == '>' )
            {
                try 
                {
                    matteValues.insert( std::stof( name.substr(1, name.size() - 2) ) );
                }
                catch( const std::exception &e )
                {
                    IECore::msg( IECore::Msg::Error, "Cryptomatte::matteValues", boost::format( "Error converting value: %s" ) % name );
                    continue;
                }
            }
            else
            {
                if( manifest )
                {
                    pathMatcher.addPath( name );
                }

                if( !StringAlgo::hasWildcards( name ) || name.find( "..." ) == string::npos )
                {
                    // Hash names without wildcards directly. This allows them to still be matched if no manifest exists or has been truncated by the renderer
                    matteValues.insert( matteNameToValue( name ) );
                }
            }
        }

        if( manifest )
        {
            for( const auto &manifestEntry : manifest->readable() )
            {
                const std::string &matteName = static_cast<IECore::StringData *>( manifestEntry.second.get() )->readable();
                if( pathMatcher.match( matteName ) & ( IECore::PathMatcher::ExactMatch | IECore::PathMatcher::AncestorMatch ) )
                {
                    matteValues.insert( matteNameToValue( matteName ) );
                }
            }
        }

        result.insert( result.end(), matteValues.begin(), matteValues.end() );
        // NOTE: pre-sort values as they're later used in a binary_search
        std::sort( result.begin(), result.end() );

        static_cast<FloatVectorDataPlug *>( output )->setValue( resultData );
    }
    else if( output == manifestPathDataPlug() )
    {
        PathMatcherDataPtr resultData = new PathMatcherData;
        PathMatcher &pathMatcher = resultData->writable();

        ConstCompoundDataPtr manifest = manifestPlug()->getValue(); 
        
        if( manifest )
        {
            for( const auto &manifestEntry : manifest->readable() )
            {
                pathMatcher.addPath( static_cast<IECore::StringData *>( manifestEntry.second.get() )->readable() );
            }
        }

        static_cast<PathMatcherDataPlug *>( output )->setValue( resultData );
    }
    else if( output == manifestScenePlug()->childNamesPlug() )
    {
        InternedStringVectorDataPtr resultData = new InternedStringVectorData;
        std::vector<InternedString> &result = resultData->writable();

        ConstPathMatcherDataPtr manifestPathData;
        {
            ScenePlug::GlobalScope globalScope( context );
            manifestPathData = manifestPathDataPlug()->getValue();
        }
         
        const PathMatcher &manifestPaths = manifestPathData->readable();
        
        const GafferScene::ScenePlug::ScenePath &scenePath = context->get<GafferScene::ScenePlug::ScenePath>( GafferScene::ScenePlug::scenePathContextName );
        
        auto match = manifestPaths.subTree( scenePath );
        PathMatcher::RawIterator it = match.begin();

        while( it != match.end() )
        {
            if( it->size() == 1 )
            {
                result.push_back( it->back() );
                it.prune();
            }

            ++it;
        }

        std::sort( 
            result.begin(), result.end(), 
            [] ( const InternedString a, const InternedString b ) {
                return a.string() < b.string();
            } 
        );

        static_cast<InternedStringVectorDataPlug *>( output )->setValue( resultData );
    }
    else if( output->parent() == manifestScenePlug() )
    {
        output->setToDefault();
    }
    else if( output == matteChannelDataPlug() )
    {
        FloatVectorDataPtr resultData = new IECore::FloatVectorData();
        std::vector<float> &result = resultData->writable();
        result.resize( GafferImage::ImagePlug::tilePixels(), 0.0f );

        ConstStringVectorDataPtr channelNamesData;
        std::string cryptomatteLayer;
        ConstFloatVectorDataPtr matteValuesData;
        {
            GafferImage::ImagePlug::GlobalScope c( context );
            channelNamesData = inPlug()->channelNamesPlug()->getValue();
            cryptomatteLayer = layerPlug()->getValue();
            matteValuesData = matteValuesPlug()->getValue();
        }

        const std::vector<std::string> &channelNames = channelNamesData->readable();
        const std::vector<float> &matteValues = matteValuesData->readable();

        boost::regex channelNameRegex( boost::str( boost::format( g_cryptomatteChannelPattern ) % cryptomatteLayer ) );
        GafferImage::ImagePlug::ChannelDataScope channelDataScope( context );
        for( const auto &c : channelNames )
        {
            if( boost::regex_match( c, channelNameRegex ) )
            {
                ChannelMap::const_iterator cIt = g_channelMap.find( GafferImage::ImageAlgo::baseName( c ) );
                if( cIt == g_channelMap.end() )
                {
                    continue;
                }

                const std::string &alphaChannel = GafferImage::ImageAlgo::channelName( GafferImage::ImageAlgo::layerName( c ), cIt->second );
                if( !GafferImage::ImageAlgo::channelExists( channelNames, alphaChannel ) )
                {
                    continue;
                }

                channelDataScope.setChannelName( &c );
                ConstFloatVectorDataPtr valueData = inPlug()->channelDataPlug()->getValue();
                const std::vector<float> &value = valueData->readable();
                
                channelDataScope.setChannelName( &alphaChannel );
                ConstFloatVectorDataPtr alphaData = inPlug()->channelDataPlug()->getValue();
                const std::vector<float> &alpha = alphaData->readable();
                
                std::vector<float>::const_iterator vIt = value.begin();
                std::vector<float>::const_iterator aIt = alpha.begin();
                for( std::vector<float>::iterator it = result.begin(), eIt = result.end(); it != eIt; ++it, ++vIt, ++aIt )
                {
                    if( std::binary_search( matteValues.begin(), matteValues.end(), *vIt ) )
                    {
                        *it += *aIt;
                    }
                }
            }
        }

        static_cast<FloatVectorDataPlug *>( output )->setValue( resultData );
    }
}

Gaffer::ValuePlug::CachePolicy Cryptomatte::computeCachePolicy( const Gaffer::ValuePlug *output ) const
{
    if( output == matteValuesPlug() ||
        output == manifestPlug() ||
        output == manifestPathDataPlug() )
    {
        // Request blocking compute to avoid concurrent threads computing the manifest redundantly.
        return ValuePlug::CachePolicy::Standard;
    }
    
    return ImageNode::computeCachePolicy( output );
}

void Cryptomatte::hashChannelNames( const GafferImage::ImagePlug *parent, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
    FlatImageProcessor::hashChannelNames( parent, context, h );
    inPlug()->channelNamesPlug()->hash( h );
    outputChannelPlug()->hash( h );
}

IECore::ConstStringVectorDataPtr Cryptomatte::computeChannelNames( const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
    StringVectorDataPtr resultData = inPlug()->channelNamesPlug()->getValue()->copy();
    std::vector<std::string> &result = resultData->writable();
    const std::string alphaChannel = outputChannelPlug()->getValue();

    for( const auto &channelName : { "R", "G", "B" } )
    {
        if( find( result.begin(), result.end(), channelName ) == result.end() )
        {
            result.push_back( channelName );
        }
    }

    if( alphaChannel != "" && find( result.begin(), result.end(), alphaChannel ) == result.end() )
    {
        result.push_back( alphaChannel );
    }
    
    return resultData;
}

void Cryptomatte::hashChannelData( const GafferImage::ImagePlug *output, const Gaffer::Context *context, IECore::MurmurHash &h ) const
{
    FlatImageProcessor::hashChannelData( output, context, h );

    inPlug()->channelDataPlug()->hash( h );

    std::string cryptomatteLayer;
    std::string alphaChannel;
    ConstStringVectorDataPtr channelNamesData;
    {
        GafferImage::ImagePlug::GlobalScope globalScope( context );
        channelNamesData = inPlug()->channelNamesPlug()->getValue();
        cryptomatteLayer = layerPlug()->getValue();
        alphaChannel = outputChannelPlug()->getValue();

        outputChannelPlug()->hash( h );
        layerPlug()->hash( h );
        matteValuesPlug()->hash( h );
        inPlug()->metadataPlug()->hash( h );
    }

    const std::string channelName = context->get<std::string>( GafferImage::ImagePlug::channelNameContextName );
    
    if( channelName == "R" || channelName == "G" || channelName == "B" || channelName == alphaChannel )
    {
        if( channelName != "R" )
        {
            matteChannelDataPlug()->hash( h );
        }

        GafferImage::ImagePlug::ChannelDataScope channelDataScope( context );
        const std::string &firstDataChannel = cryptomatteLayer + g_firstDataChannelSuffix;
        if( GafferImage::ImageAlgo::channelExists( channelNamesData->readable(), firstDataChannel ) )
        {
            channelDataScope.setChannelName( &firstDataChannel );
            inPlug()->channelDataPlug()->hash( h );
        }
        h.append( channelName );
    }
}

IECore::ConstFloatVectorDataPtr Cryptomatte::computeChannelData( const std::string &channelName, const Imath::V2i &tileOrigin, const Gaffer::Context *context, const GafferImage::ImagePlug *parent ) const
{
    const std::string alphaChannel = outputChannelPlug()->getValue();
    
    if( channelName != "R" && channelName != "G" && channelName != "B" && channelName != alphaChannel )
    {
        return inPlug()->channelDataPlug()->getValue();
    }
    
    ConstStringVectorDataPtr channelNamesData;
    {
        GafferImage::ImagePlug::GlobalScope c( context );
        channelNamesData = inPlug()->channelNamesPlug()->getValue();
    }
    const std::vector<std::string> &channelNames = channelNamesData->readable();
    
    const std::string cryptomatteLayer = layerPlug()->getValue();
    if( cryptomatteLayer == "" )
    {
        if( find( channelNames.begin(), channelNames.end(), channelName ) != channelNames.end() )
        {
            return inPlug()->channelDataPlug()->getValue();
        }
        else
        {
            return GafferImage::ImagePlug::blackTile();
        }
    }

    if( channelName == "R" || channelName == "G" || channelName == "B" )
    {
        const std::string &firstDataChannel = cryptomatteLayer + g_firstDataChannelSuffix;
        if( !GafferImage::ImageAlgo::channelExists( channelNames, firstDataChannel ) )
        {
            return GafferImage::ImagePlug::blackTile();
        }

        GafferImage::ImagePlug::ChannelDataScope channelDataScope( context );        
        channelDataScope.setChannelName( &firstDataChannel );

        if( channelName == "R" )
        {
            return inPlug()->channelDataPlug()->getValue();
        }
        else if( channelName == "G" || channelName == "B" )
        {
            FloatVectorDataPtr resultData = new FloatVectorData;
            std::vector<float> &result = resultData->writable();
            result.resize( GafferImage::ImagePlug::tilePixels(), 0.0f );

            ConstFloatVectorDataPtr valueData = inPlug()->channelDataPlug()->getValue();
            const std::vector<float> &values = valueData->readable();

            ConstFloatVectorDataPtr alphaData = matteChannelDataPlug()->getValue();
            const std::vector<float> &alphas = alphaData->readable();

            const size_t shift = channelName == "G" ? 8 : 16;
            const float mult = channelName == "G" ? 0.25f : 0.75f;
            uint32_t h;

            std::vector<float>::const_iterator vIt = values.begin();
            std::vector<float>::const_iterator aIt = alphas.begin();
            for( std::vector<float>::iterator it = result.begin(), eIt = result.end(); it != eIt; ++it, ++vIt, ++aIt )
            {
                // Adapted from the Cryptomatte specification
                std::memcpy( &h, &(*vIt), sizeof( uint32_t ) );
                *it = (float)(h << shift) / (float)UINT32_MAX * 0.3f + *aIt * mult;
            }

            return resultData;
        }
    }
    else if( channelName == alphaChannel )
    {
        return matteChannelDataPlug()->getValue();
    }

    return GafferImage::ImagePlug::blackTile();
}

} // namespace GafferScene