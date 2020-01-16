# CMake version required
cmake_minimum_required( VERSION 2.8 )

set (CMAKE_CXX_STANDARD 11)

# Declare a Cortex Project
project( Gaffer )

# Declare the version


option( WITH_TESTS "Compile tests" ON )

set( GAFFER_SOURCE_DIR ${CMAKE_SOURCE_DIR}/../.. )

file( READ  ${GAFFER_SOURCE_DIR}/SConstruct SCONSTRUCT)

string( REGEX MATCH "gafferMilestoneVersion = ([0-9]+)" ${SCONSTRUCT} )
set( GAFFER_MILESTONE_VERSION ${CMAKE_MATCH_1} )

string( REGEX MATCH "gafferMajorVersion = ([0-9]+)" ${SCONSTRUCT} )
set( GAFFER_MAJOR_VERSION ${CMAKE_MATCH_1} )

string( REGEX MATCH "gafferMinorVersion = ([0-9]+)" ${SCONSTRUCT} )
set( GAFFER_MINOR_VERSION ${CMAKE_MATCH_1} )

string( REGEX MATCH "gafferPatchVersion = ([0-9]+)" ${SCONSTRUCT} )
set( GAFFER_PATCH_VERSION ${CMAKE_MATCH_1} )

message(STATUS "Configuring Gaffer : " ${GAFFER_MILESTONE_VERSION}.${GAFFER_MAJOR_VERSION}.${GAFFER_MINOR_VERSION}.${GAFFER_PATCH_VERSION})

add_definitions( -DGAFFER_MILESTONE_VERSION=${GAFFER_MILESTONE_VERSION}
        -DGAFFER_MAJOR_VERSION=${GAFFER_MAJOR_VERSION}
        -DGAFFER_MINOR_VERSION=${GAFFER_MINOR_VERSION}
        -DGAFFER_PATCH_VERSION=${GAFFER_PATCH_VERSION} )
#-******************************************************************************
#-******************************************************************************
# PLATFORM SPECIFIC
#-******************************************************************************
#-******************************************************************************

# Windows flag
set( WINDOWS FALSE )
if( "${CMAKE_SYSTEM_NAME}" MATCHES "Windows" )
  set( WINDOWS TRUE )
endif()

set( DARWIN FALSE )
if( "${CMAKE_SYSTEM_NAME}" MATCHES "Darwin" )
  set( DARWIN TRUE )
  if( ${CMAKE_SYSTEM_VERSION} MATCHES "13." )
       ADD_DEFINITIONS( "-std=c++11" )
  endif()
endif()

set( LINUX FALSE )
if( "${CMAKE_SYSTEM_NAME}" MATCHES "Linux" )
  set( LINUX TRUE )
endif()

# Set some debug vs opt flags
IF ( "${CMAKE_BUILD_TYPE}" MATCHES "Debug" )
  ADD_DEFINITIONS( -DDEBUG=1 -UNDEBUG )
  IF ( NOT WINDOWS )
    ADD_DEFINITIONS( -pipe -Wall -O0  -Wno-unused-local-typedefs -Wno-strict-aliasing -Wno-maybe-uninitialized -Wno-deprecated -D_GLIBCXX_USE_CXX11_ABI=0)
  ENDIF()
ELSEIF ( "${CMAKE_BUILD_TYPE}" MATCHES "Release" )
  ADD_DEFINITIONS( -DNDEBUG=1 -UDEBUG )
  IF ( NOT WINDOWS )
    ADD_DEFINITIONS( -pipe -Wall  -O3 -DNDEBUG -DBOOST_DISABLE_ASSERTS -Wno-unused-local-typedefs -Wno-strict-aliasing -Wno-maybe-uninitialized -Wno-strict-overflow  -D_GLIBCXX_USE_CXX11_ABI=0) #-Wno-return-type )
  ENDIF()
ENDIF()

if( ${WINDOWS} )
  add_definitions( -DGAFFER_PLATFORM=win)
  add_definitions( -DOPENEXR_DLL -DNOMINMAX -D__PRETTY_FUNCTION__=__FUNCSIG__ -DBOOST_ALL_DYN_LINK )
  set( CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS} /MP )
  set( PLATFORM_LIBS winmm.lib Ws2_32.lib )
endif()

#-******************************************************************************
#-******************************************************************************
# GLOBAL PACKAGE & INCLUDE/LINK DEPENDENCY
#-******************************************************************************
#-******************************************************************************

# check in the source directory
set( CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${PROJECT_SOURCE_DIR}/cmake )

find_package( TBB REQUIRED )
find_package( PythonLibs 2.7 REQUIRED )
find_package( Boost REQUIRED COMPONENTS signals iostreams filesystem date_time wave regex system chrono python timer)
find_package( IlmBase REQUIRED )
find_package( OpenEXR REQUIRED )
find_package( Cortex REQUIRED )
find_package( OpenColorIO REQUIRED )
find_package( OpenImageIO REQUIRED )
find_package( OSL REQUIRED )
find_package( Freetype REQUIRED )
find_package( PNG REQUIRED ) # For freetype linking
find_package( Arnold REQUIRED )
find_package( OpenGL REQUIRED )
find_package( GLEW REQUIRED )
find_package( Qt5 5.6 REQUIRED Core Gui OpenGL )
find_package( Appleseed REQUIRED )
find_package( OpenVDB REQUIRED )

include_directories( ${GAFFER_SOURCE_DIR}/include )
include_directories( ${TBB_INCLUDE_DIRS} )
include_directories( ${PYTHON_INCLUDE_DIRS} )
include_directories( ${Boost_INCLUDE_DIRS} )
include_directories( ${ILMBASE_INCLUDE_DIR} )
include_directories( ${OPENEXR_INCLUDE_DIRS} )
include_directories( ${Cortex_INCLUDE_DIRS} )
include_directories( ${FREETYPE_INCLUDE_DIRS} )
include_directories( ${CORTEX_ARNOLD_INCLUDE_PATH} )
include_directories( ${APPLESEED_INCLUDE_DIRS} )

link_directories( ${TBB_LIBRARY_DIRS} )
link_directories( ${Boost_LIBRARY_DIRS} )

# Boost definitions
add_definitions( -DBOOST_FILESYSTEM_VERSION=3 )
add_definitions( -DBOOST_FILESYSTEM_NO_DEPRICATED )
add_definitions( -DBOOST_SIGNALS_NO_DEPRECATION_WARNING )
add_definitions( -DBOOST_PYTHON_MAX_ARITY=20 )

# Base libs to link to
set( BASE_LIBS
     ${Cortex_IECORE_LIBRARY}
     ${Boost_SIGNALS_LIBRARY}
     ${Boost_IOSTREAMS_LIBRARY}
     ${Boost_FILESYSTEM_LIBRARY}
     ${Boost_DATE_TIME_LIBRARY}
     ${Boost_THREAD_LIBRARY}
     ${Boost_WAVE_LIBRARY}
     ${Boost_REGEX_LIBRARY}
     ${Boost_SYSTEM_LIBRARY}
     ${Boost_CHRONO_LIBRARY}
     ${Boost_TIMER_LIBRARY}
     ${TBB_LIBRARIES}
     ${Ilmbase_HALF_LIBRARY}
     ${Ilmbase_IEX_LIBRARY}
     ${Ilmbase_IEXMATH_LIBRARY}
     ${Ilmbase_ILMTHREAD_LIBRARY}
     ${Ilmbase_IMATH_LIBRARY}
     ${Openexr_ILMIMF_LIBRARY}
     )

set( BASE_PYTHON_LIBS
     ${PYTHON_LIBRARIES}
     ${Boost_PYTHON_LIBRARY}
     ${Cortex_IECOREPYTHON_LIBRARY}
     Gaffer)

#-******************************************************************************
#-******************************************************************************
# GAFFER
#-******************************************************************************
#-******************************************************************************

# Includes
include_directories( ${CMAKE_SOURCE_DIR}/include )

set( GAFFER_LIB_NAMES
  Gaffer
  GafferAppleseed
  GafferArnold
  GafferArnoldUI
  GafferCortex
  GafferDispatch
  GafferImage
  GafferImageUI
  GafferOSL
  GafferDelight
  GafferScene
  GafferSceneUI
  GafferUI
  GafferVDB
  GafferVDBUI
  GafferOSLUI
  )

set( GAFFERBINDINGS_LIB_NAMES
  Gaffer
  )

set( GAFFERTEST_LIB_NAMES
  Gaffer
  GafferScene
  )

set( GAFFER_PYTHON_NAMES
  Gaffer
  GafferAppleseed
  GafferArnold
  GafferCortex
  GafferDispatch
  GafferImage
  GafferOSL
  GafferDelight
  GafferScene
  GafferTractor
  GafferVDB
  )

# Get lists of files
foreach( GAFFER_LIB ${GAFFER_LIB_NAMES} )
  string( TOUPPER ${GAFFER_LIB} _GAFFER_LIB )
  file( GLOB ${_GAFFER_LIB}_CXX_FILES  ${GAFFER_SOURCE_DIR}/src/${GAFFER_LIB}/*.cpp )
  file( GLOB ${_GAFFER_LIB}_H_FILES ${GAFFER_SOURCE_DIR}/include/${GAFFER_LIB}/*.h ${GAFFER_SOURCE_DIR}/include/${GAFFER_LIB}/*.inl )
  file( GLOB ${_GAFFER_LIB}_CXX_MODULE_FILES ${GAFFER_SOURCE_DIR}/src/${GAFFER_LIB}Module/*.cpp )
  file( GLOB ${_GAFFER_LIB}_H_MODULE_FILES  ${GAFFER_SOURCE_DIR}/src/${GAFFER_LIB}Module/*.h ${GAFFER_SOURCE_DIR}/src/${GAFFER_LIB}Module/*.inl )
endforeach()

# Get test lists of files
foreach( GAFFER_LIB ${GAFFERTEST_LIB_NAMES} )
  string( TOUPPER ${GAFFER_LIB} _GAFFER_LIB )
  file( GLOB ${_GAFFER_LIB}TEST_CXX_FILES ${GAFFER_SOURCE_DIR}/src/${GAFFER_LIB}Test/*.cpp )
  file( GLOB ${_GAFFER_LIB}TEST_H_FILES ${GAFFER_SOURCE_DIR}/include/${GAFFER_LIB}Test/*.h ${GAFFER_SOURCE_DIR}/include/${GAFFER_LIB}Test/*.inl )
  file( GLOB ${_GAFFER_LIB}TEST_CXX_MODULE_FILES ${GAFFER_SOURCE_DIR}/src/${GAFFER_LIB}TestModule/*.cpp )
endforeach()

# Get binding list of files
foreach( GAFFER_LIB ${GAFFERBINDINGS_LIB_NAMES} )
  string( TOUPPER ${GAFFER_LIB} _GAFFER_LIB )
  file( GLOB ${_GAFFER_LIB}BINDINGS_CXX_FILES ${GAFFER_SOURCE_DIR}/src/${GAFFER_LIB}Bindings/*.cpp )
  file( GLOB ${_GAFFER_LIB}BINDINGS_H_FILES ${GAFFER_SOURCE_DIR}/include/${GAFFER_LIB}Bindings/*.h ${GAFFER_SOURCE_DIR}/include/${GAFFER_LIB}Bindings/*.inl )
endforeach()

# Get python list of files
foreach( GAFFER_LIB ${GAFFER_PYTHON_NAMES} )
  string( TOUPPER ${GAFFER_LIB} _GAFFER_LIB )
  file( GLOB ${_GAFFER_LIB}_PY_FILES ${GAFFER_SOURCE_DIR}/python/${GAFFER_LIB}/*.py
    python/${GAFFER_LIB}Test/*.py python/${GAFFER_LIB}UI/*.py python/${GAFFER_LIB}UITest/*.py )
endforeach()


set(sedSubstitutions "s/!GAFFER_MILESTONE_VERSION!/${GAFFER_MILESTONE_VERSION}/g\;s/!GAFFER_MAJOR_VERSION!/${GAFFER_MAJOR_VERSION}/g\;s/!GAFFER_MINOR_VERSION!/${GAFFER_MINOR_VERSION}/g\;s/!GAFFER_PATCH_VERSION!/${GAFFER_PATCH_VERSION}/g")


add_custom_command(
        OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/About.py
        COMMAND sed "${sedSubstitutions}" ${GAFFER_SOURCE_DIR}/python/Gaffer/About.py > ${CMAKE_CURRENT_BINARY_DIR}/About.py
        DEPENDS ${GAFFER_SOURCE_DIR}/resources/graphics.svg
        WORKING_DIRECTORY ${GAFFER_SOURCE_DIR}
)

add_custom_command(
        OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/Version.h
        COMMAND sed "${sedSubstitutions}" ${GAFFER_SOURCE_DIR}/include/Gaffer/Version.h > ${CMAKE_CURRENT_BINARY_DIR}/Version.h
        DEPENDS ${GAFFER_SOURCE_DIR}/resources/graphics.svg
        WORKING_DIRECTORY ${GAFFER_SOURCE_DIR}
)


# Build Graphics
# ==============


file( GLOB GAFFER_SVG_FILES ${GAFFER_SOURCE_DIR}/resources/*.svg)
set(outputPNGs "")

foreach(srcSvgFile ${GAFFER_SVG_FILES})
  # generate an object list from the svg file
  execute_process( COMMAND inkscape --query-all ${srcSvgFile} OUTPUT_VARIABLE svgContents)

  STRING(REGEX REPLACE ";" "\\\\;" svgContents "${svgContents}")
  STRING(REGEX REPLACE "\n" ";" svgContents "${svgContents}")

  set(svgExport "")

  foreach(svg ${svgContents})
    string(FIND ${svg} "forExport:" a)
    if("${a}" STREQUAL "0")
      list(APPEND svgExport ${svg})
    endif()
  endforeach()

  foreach(svg ${svgExport})
    string(SUBSTRING ${svg} 10 4096 svg)
    STRING(REGEX REPLACE "," ";" svg "${svg}")
    list(GET svg 0 name)
    list(GET svg 3 width)
    list(GET svg 4 height)

    list(APPEND outputPNGs ${CMAKE_CURRENT_BINARY_DIR}/graphics/${name}.png)
    add_custom_command(
            OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/graphics/${name}.png
            COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_CURRENT_BINARY_DIR}/graphics/
            COMMAND inkscape  --export-png=${CMAKE_CURRENT_BINARY_DIR}/graphics/${name}.png --export-id=forExport:${name} --export-width=${width} --export-height=${height} --export-background-opacity=0 ${srcSvgFile}
            DEPENDS ${srcSvgFile}
            WORKING_DIRECTORY ${GAFFER_SOURCE_DIR}
    )
  endforeach()
endforeach()


add_custom_target(Graphics ALL DEPENDS ${outputPNGs})

# Gaffer
add_library( Gaffer SHARED ${GAFFER_CXX_FILES} ${GAFFER_H_FILES} ${CMAKE_CURRENT_BINARY_DIR}/About.py ${CMAKE_CURRENT_BINARY_DIR}/Version.h)
target_link_libraries( Gaffer ${BASE_LIBS} )

# Gaffer Bindings
add_library( GafferBindings SHARED ${GAFFERBINDINGS_CXX_FILES} ${GAFFERBINDINGS_H_FILES} )
target_link_libraries( GafferBindings ${BASE_LIBS} ${BASE_PYTHON_LIBS} )

# Gaffer Module
add_library( _Gaffer MODULE ${GAFFER_CXX_MODULE_FILES} ${GAFFER_H_MODULE_FILES} )
target_link_libraries( _Gaffer ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferBindings )

# Gaffer Test
add_library( GafferTest SHARED ${GAFFERTEST_CXX_FILES} ${GAFFERTEST_H_FILES} )
target_link_libraries( GafferTest ${BASE_LIBS} Gaffer )

# Gaffer Test Module
add_library( _GafferTest MODULE ${GAFFERTEST_CXX_MODULE_FILES} )
target_link_libraries( _GafferTest ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferBindings GafferTest )

# GafferUI
add_library( GafferUI SHARED ${GAFFERUI_CXX_FILES} ${GAFFERUI_H_FILES} )
target_link_libraries( GafferUI Gaffer GafferScene ${BASE_LIBS} ${Iex_LIB} ${Cortex_IECOREGL_LIBRARY} ${OPENGL_LIBRARIES} ${GLEW_LIBRARIES} ${PLATFORM_LIBS} )
target_compile_definitions( GafferUI PRIVATE -DQT_NO_KEYWORDS -DQ_COMPILER_CONSTEXPR )

# GafferUI Python Module
add_library( _GafferUI MODULE ${GAFFERUI_CXX_MODULE_FILES} ${GAFFERUI_H_MODULE_FILES} )
target_link_libraries( _GafferUI GafferUI GafferBindings ${BASE_LIBS} ${BASE_PYTHON_LIBS} Qt5::Core Qt5::Gui Qt5::OpenGL )
target_compile_definitions( _GafferUI PRIVATE -DQT_NO_KEYWORDS -DQ_COMPILER_CONSTEXPR )

# GafferDisptach
add_library( GafferDispatch SHARED ${GAFFERDISPATCH_CXX_FILES} ${GAFFERDISPATCH_H_FILES} )
target_link_libraries( GafferDispatch ${BASE_LIBS} Gaffer )

# GafferDispatch Python Module
add_library( _GafferDispatch MODULE ${GAFFERDISPATCH_CXX_MODULE_FILES} )
target_link_libraries( _GafferDispatch ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferDispatch GafferBindings  )

# GafferImage
add_library( GafferImage SHARED ${GAFFERIMAGE_CXX_FILES} ${GAFFERIMAGE_H_FILES} )
target_link_libraries( GafferImage Gaffer GafferDispatch ${BASE_LIBS} ${ILMBASE_IEX_LIBRARY} ${OPENIMAGEIO_LIBRARIES} ${OPENCOLORIO_LIBRARIES} ${FREETYPE_LIBRARIES} ${PNG_LIBRARIES} ${Cortex_IECOREIMAGE_LIBRARY} ${PLATFORM_LIBS} )

# GafferImage Python Module
add_library( _GafferImage MODULE ${GAFFERIMAGE_CXX_MODULE_FILES} ${GAFFERIMAGE_H_MODULE_FILES} )
target_link_libraries( _GafferImage GafferImage GafferBindings ${BASE_LIBS} ${BASE_PYTHON_LIBS} )

# GafferImageUI
add_library( GafferImageUI SHARED ${GAFFERIMAGEUI_CXX_FILES} ${GAFFERIMAGEUI_H_FILES} )
target_link_libraries( GafferImageUI Gaffer GafferImage GafferUI ${BASE_LIBS} ${OPENGL_LIBRARIES} ${GLEW_LIBRARIES} )

# GafferImageUI Python Module
add_library( _GafferImageUI MODULE ${GAFFERIMAGEUI_CXX_MODULE_FILES} ${GAFFERIMAGEUI_H_MODULE_FILES} )
target_link_libraries( _GafferImageUI GafferImageUI GafferBindings ${BASE_LIBS} ${BASE_PYTHON_LIBS} )

# GafferScene
file( GLOB IECORESCENE_PREVIEW_H_FILES ${GAFFER_SOURCE_DIR}/include/GafferScene/Private/IECoreScenePreview/*.h )
file( GLOB IECORESCENE_PREVIEW_CPP_FILES ${GAFFER_SOURCE_DIR}/src/GafferScene/IECoreScenePreview/*.cpp )
file( GLOB IECOREGL_PREVIEW_CPP_FILES ${GAFFER_SOURCE_DIR}/src/GafferScene/IECoreGLPreview/*.cpp )
add_library( GafferScene SHARED ${GAFFERSCENE_CXX_FILES} ${GAFFERSCENE_H_FILES} ${IECORESCENE_PREVIEW_H_FILES} ${IECORESCENE_PREVIEW_CPP_FILES} ${IECOREGL_PREVIEW_CPP_FILES} )
target_link_libraries( GafferScene ${BASE_LIBS} Gaffer ${ILMBASE_IEX_LIBRARY} ${Cortex_IECOREGL_LIBRARY} ${Cortex_IECOREALEMBIC_LIBRARY} GafferImage GafferDispatch ${Cortex_IECORESCENE_LIBRARY} ${Cortex_IECOREGL_LIBRARY} ${OPENGL_LIBRARIES} ${GLEW_LIBRARIES} )

# GafferScene Python Module
add_library( _GafferScene MODULE ${GAFFERSCENE_CXX_MODULE_FILES} ${GAFFERSCENE_H_MODULE_FILES} )
target_link_libraries( _GafferScene GafferScene GafferBindings  ${BASE_LIBS} ${BASE_PYTHON_LIBS} )

# GafferScene Test
add_library( GafferSceneTest SHARED ${GAFFERSCENETEST_CXX_FILES} ${GAFFERIMAGETEST_H_FILES} )
target_link_libraries( GafferSceneTest ${BASE_LIBS} Gaffer GafferScene GafferDispatch )

# GafferScene Test Module
add_library( _GafferSceneTest MODULE ${GAFFERSCENETEST_CXX_MODULE_FILES} )
target_link_libraries( _GafferSceneTest ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferBindings GafferScene GafferSceneTest GafferDispatch )

# GafferSceneUI
add_library( GafferSceneUI SHARED ${GAFFERSCENEUI_CXX_FILES} ${GAFFERSCENEUI_H_FILES} )
target_link_libraries( GafferSceneUI ${BASE_LIBS} Gaffer GafferUI GafferImage GafferScene GafferImageUI ${ILMBASE_IEX_LIBRARY} ${Cortex_IECOREGL_LIBRARY} ${OPENGL_LIBRARIES} ${GLEW_LIBRARIES} )

# GafferSceneUI Python Module
add_library( _GafferSceneUI MODULE ${GAFFERSCENEUI_CXX_MODULE_FILES} ${GAFFERSCENEUI_H_MODULE_FILES} )
target_link_libraries( _GafferSceneUI GafferSceneUI ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferBindings )

# GafferCortex
add_library( GafferCortex SHARED ${GAFFERCORTEX_CXX_FILES} ${GAFFERCORTEX_H_FILES} )
target_link_libraries( GafferCortex ${BASE_LIBS} Gaffer GafferDispatch )

# GafferCortex Python Module
add_library( _GafferCortex MODULE ${GAFFERCORTEX_CXX_MODULE_FILES} ${GAFFERCORTEX_H_MODULE_FILES} )
target_link_libraries( _GafferCortex GafferCortex GafferBindings ${BASE_LIBS} ${BASE_PYTHON_LIBS} )

# GafferOSL
add_library( GafferOSL SHARED ${GAFFEROSL_CXX_FILES} ${GAFFEROSL_H_FILES} )
target_link_libraries( GafferOSL ${BASE_LIBS} Gaffer GafferScene GafferImage ${OPENIMAGEIO_LIBRARIES} ${OSL_QUERY_LIBRARY} ${OSL_EXEC_LIBRARY} ${ILMBASE_IEX_LIBRARY} )

# GafferOSL Python Module
add_library( _GafferOSL MODULE ${GAFFEROSL_CXX_MODULE_FILES} )
target_link_libraries( _GafferOSL ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferBindings GafferScene GafferImage GafferOSL GafferAppleseed ${Ilmbase_IEX_LIBRARY} )

# GafferVDB
add_library( GafferVDB SHARED ${GAFFERVDB_CXX_FILES} ${GAFFERVDB_H_FILES} )
target_link_libraries( GafferVDB ${BASE_LIBS} Gaffer GafferScene ${OpenVDB_LIBRARIES} ${Cortex_IECORESCENE_LIBRARY} )

# GafferVDB Python Module
add_library( _GafferVDB MODULE ${GAFFERVDB_CXX_MODULE_FILES} )
target_link_libraries( _GafferVDB GafferVDB ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferBindings GafferScene ${OpenVDB_LIBRARIES} ${Cortex_IECORESCENE_LIBRARY} )

# GafferVDBUI
add_library( GafferVDBUI SHARED ${GAFFERVDBUI_CXX_FILES} ${GAFFERVDBUI_H_FILES} )
target_link_libraries( GafferVDBUI ${BASE_LIBS} Gaffer GafferVDB GafferSceneUI ${OpenVDB_LIBRARIES} ${Cortex_IECOREGL_LIBRARY} )

# GafferVDBUI Python Module
add_library( _GafferVDBUI MODULE ${GAFFERVDBUI_CXX_MODULE_FILES} )
target_link_libraries( _GafferVDBUI GafferVDBUI )
set_target_properties(_GafferVDBUI PROPERTIES LINK_FLAGS "-Wl,--no-as-needed")

# GafferAppleseed
file( GLOB IECOREAPPLESEED_PREVIEW_CXX_FILES ${GAFFER_SOURCE_DIR}/src/GafferAppleseed/IECoreAppleseedPreview/*.cpp )
add_library( GafferAppleseed SHARED ${GAFFERAPPLESEED_CXX_FILES} ${GAFFERAPPLESEED_H_FILES} ${IECOREAPPLESEED_PREVIEW_CXX_FILES} )
target_link_libraries( GafferAppleseed ${BASE_LIBS} Gaffer GafferDispatch GafferScene ${APPLESEED_LIBRARY} ${Cortex_IECOREAPPLESEED_LIBRARY} ${OPENIMAGEIO_LIBRARIES} ${OSL_QUERY_LIBRARY} )
target_compile_options( GafferAppleseed PRIVATE -DAPPLESEED_ENABLE_IMATH_INTEROP -DAPPLESEED_USE_SSE )

# GafferAppleseed Python Module
add_library( _GafferAppleseed MODULE ${GAFFERAPPLESEED_CXX_MODULE_FILES} )
target_link_libraries( _GafferAppleseed ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferDispatch GafferScene GafferBindings GafferAppleseed )
target_compile_options( _GafferAppleseed PRIVATE -DAPPLESEED_ENABLE_IMATH_INTEROP -DAPPLESEED_USE_SSE )

# GafferArnold
file( GLOB IECOREARNOLD_PREVIEW_CXX_FILES ${GAFFER_SOURCE_DIR}/src/GafferArnold/IECoreArnoldPreview/*.cpp )
add_library( GafferArnold SHARED ${GAFFERARNOLD_CXX_FILES} ${GAFFERARNOLD_H_FILES} ${IECOREARNOLD_PREVIEW_CXX_FILES} )
target_link_libraries( GafferArnold ${BASE_LIBS} Gaffer GafferDispatch GafferScene GafferOSL GafferVDB ${OpenVDB_LIBRARIES} ${CORTEX_ARNOLD_LIBS} ${Cortex_IECOREARNOLD_LIBRARY} )

# GafferArnold Python Module
add_library( _GafferArnold MODULE ${GAFFERARNOLD_CXX_MODULE_FILES} )
target_link_libraries( _GafferArnold ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferScene GafferBindings GafferDispatch GafferArnold GafferBindings )

# GafferArnoldUI
add_library( GafferArnoldUI SHARED ${GAFFERARNOLDUI_CXX_FILES} ${GAFFERARNOLDUI_H_FILES} )
target_link_libraries( GafferArnoldUI ${BASE_LIBS} Gaffer GafferScene GafferSceneUI GafferOSL ${Cortex_IECOREGL_LIBRARY} )

# GafferArnoldUI Python Module
add_library( _GafferArnoldUI MODULE ${GAFFERARNOLDUI_CXX_MODULE_FILES} )
target_link_libraries( _GafferArnoldUI GafferArnoldUI )

# GafferDelight
add_library( GafferDelight SHARED ${GAFFERDELIGHT_CXX_FILES} ${GAFFERDELIGHT_H_FILES} )
target_link_libraries( GafferDelight ${BASE_LIBS} Gaffer GafferDispatch GafferScene )

# GafferDelight Python Module
add_library( _GafferDelight MODULE ${GAFFERDELIGHT_CXX_MODULE_FILES} )
target_link_libraries( _GafferDelight ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferScene GafferBindings GafferDispatch GafferDelight GafferBindings )

# GafferOSLUI
add_library( GafferOSLUI SHARED ${GAFFEROSLUI_CXX_FILES} ${GAFFEROSLUI_H_FILES} )
target_link_libraries( GafferOSLUI ${BASE_LIBS} Gaffer GafferOSL )

# GafferOSLUI Python Module
add_library( _GafferOSLUI MODULE ${GAFFEROSLUI_CXX_MODULE_FILES} )
target_link_libraries( _GafferOSLUI ${BASE_LIBS} ${BASE_PYTHON_LIBS} GafferOSLUI  GafferBindings  )

# Python modules need special naming
foreach( GAFFER_LIB ${GAFFER_LIB_NAMES} )
  if( DARWIN )
    set_target_properties( _${GAFFER_LIB} PROPERTIES SUFFIX ".so" )
    set_target_properties( _${GAFFER_LIB} PROPERTIES PREFIX "" )
  elif( WINDOWS )
    set_target_properties( _${GAFFER_LIB} PROPERTIES SUFFIX ".pyd" )
  else()
    set_target_properties( _${GAFFER_LIB} PROPERTIES PREFIX "" )
  endif()
endforeach()

foreach( GAFFER_LIB ${GAFFERTEST_LIB_NAMES} )
  if( DARWIN )
    set_target_properties( _${GAFFER_LIB}Test PROPERTIES SUFFIX ".so" )
    set_target_properties( _${GAFFER_LIB}Test PROPERTIES PREFIX "" )
    elif( WINDOWS )
    set_target_properties( _${GAFFER_LIB}Test PROPERTIES SUFFIX ".pyd" )
  else()
    set_target_properties( _${GAFFER_LIB}Test PROPERTIES PREFIX "" )
  endif()
endforeach()


# Gaffer OSL Shaders
file( GLOB_RECURSE OSL_HEADER_FILES ${GAFFER_SOURCE_DIR}/shaders/*.h)
file( GLOB_RECURSE OSL_SOURCE_FILES ${GAFFER_SOURCE_DIR}/shaders/*.osl)

# get the OSL library path so we can run oslc
list(GET OSL_LIBRARIES 1 OSL_LIBRARY_PATH)
get_filename_component(OSL_LIBRARY_PATH ${OSL_LIBRARY_PATH} DIRECTORY)

foreach(shaderFileName ${OSL_SOURCE_FILES})
    get_filename_component(shaderFileName ${shaderFileName} "ABSOLUTE")
    get_filename_component(shaderPathAbsolute ${GAFFER_SOURCE_DIR}/shaders "ABSOLUTE")

    string(REPLACE ${shaderPathAbsolute} ${CMAKE_CURRENT_BINARY_DIR}/shaders SHADER_OUTPUT ${shaderFileName} )

    get_filename_component(SDIR ${SHADER_OUTPUT} DIRECTORY)
    get_filename_component(SNAME ${SHADER_OUTPUT} NAME_WE)

    set(SHADER_OUTPUT ${SDIR}/${SNAME}.oso)
    get_filename_component(SHADER_OUTPUT_DIR ${SHADER_OUTPUT} "DIRECTORY")

    list(APPEND COMPILED_OSL_SHADERS ${SHADER_OUTPUT} )
    add_custom_command(OUTPUT "${SHADER_OUTPUT}"
            COMMAND ${CMAKE_COMMAND} -E make_directory ${SHADER_OUTPUT_DIR}
            COMMAND ${CMAKE_COMMAND} -E env "LD_LIBRARY_PATH=${OSL_LIBRARY_PATH}:$ENV{LD_LIBRARY_PATH}" ${OSL_COMPILER} -I./shaders -o ${SHADER_OUTPUT} ${shaderFileName}
            DEPENDS ${shaderFileName}
            WORKING_DIRECTORY ${GAFFER_SOURCE_DIR}
    )
endforeach()

add_custom_target(Shaders ALL DEPENDS ${COMPILED_OSL_SHADERS})


# Python modules need special naming
if( WIN32 )
  set_target_properties( _Gaffer PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferAppleseed PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferArnold PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferArnoldUI PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferCortex PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferDispatch PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferImage PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferImageUI PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferOSL PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferDelight PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferScene PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferSceneUI PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferUI PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferTest PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferSceneTest PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferImageTest PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferVDB PROPERTIES SUFFIX ".pyd" )
  set_target_properties( _GafferVDBUI PROPERTIES SUFFIX ".pyd" )
endif()

# Dependencies
add_dependencies( GafferAppleseed Gaffer GafferDispatch GafferScene )
add_dependencies( GafferArnold Gaffer GafferDispatch GafferScene GafferOSL )
add_dependencies( GafferArnoldUI Gaffer GafferScene GafferOSL GafferArnoldUI )
add_dependencies( GafferCortex Gaffer GafferDispatch )
add_dependencies( GafferDispatch Gaffer )
add_dependencies( GafferImage Gaffer GafferDispatch )
add_dependencies( GafferImageUI Gaffer GafferImage GafferUI GafferBindings GafferImage GafferDispatch GafferImageUI )
add_dependencies( GafferOSL Gaffer GafferScene GafferImage )
add_dependencies( GafferDelight Gaffer GafferDispatch GafferScene )
add_dependencies( GafferScene Gaffer GafferImage GafferDispatch )
add_dependencies( GafferSceneUI Gaffer GafferUI GafferImage GafferImageUI GafferScene )
add_dependencies( GafferUI Gaffer GafferScene )

# Binding Dependencies
add_dependencies( GafferBindings Gaffer Graphics)

# Test Dependencies
add_dependencies( GafferTest Gaffer )
add_dependencies( GafferSceneTest Gaffer GafferScene GafferDispatch )

# Module dependencies
add_dependencies( _Gaffer Gaffer GafferBindings )
add_dependencies( _GafferCortex Gaffer GafferCortex GafferBindings )
add_dependencies( _GafferDispatch Gaffer GafferDispatch GafferBindings )
add_dependencies( _GafferImage Gaffer GafferImage GafferBindings )
add_dependencies( _GafferImageUI Gaffer GafferImageUI GafferBindings )
add_dependencies( _GafferScene Gaffer GafferScene GafferBindings )
add_dependencies( _GafferSceneUI Gaffer GafferSceneUI GafferImageUI GafferBindings )
add_dependencies( _GafferUI Gaffer GafferUI GafferBindings )
add_dependencies( _GafferOSL GafferBindings GafferScene GafferImage GafferOSL )
add_dependencies( _GafferAppleseed GafferDispatch GafferScene GafferBindings GafferAppleseed )
add_dependencies( _GafferArnold Gaffer GafferScene GafferBindings GafferDispatch GafferArnold )
add_dependencies( _GafferArnoldUI Gaffer GafferArnoldUI )
add_dependencies( _GafferDelight Gaffer GafferScene GafferBindings GafferDispatch GafferDelight )

add_dependencies( _GafferTest Gaffer GafferBindings GafferTest )
add_dependencies( _GafferSceneTest Gaffer GafferBindings GafferScene GafferSceneTest GafferDispatch )

# Install Libs
foreach( GAFFER_LIB ${GAFFER_LIB_NAMES} )
  string( TOUPPER ${GAFFER_LIB} _GAFFER_LIB )
  install( TARGETS ${GAFFER_LIB}
           DESTINATION lib/ )
  install( FILES ${${_GAFFER_LIB}_H_FILES}
           DESTINATION include/${GAFFER_LIB} )
endforeach()

# Install Test Libs
foreach( GAFFER_LIB ${GAFFERTEST_LIB_NAMES} )
  string( TOUPPER ${GAFFER_LIB} _GAFFER_LIB )
  install( TARGETS ${GAFFER_LIB}Test
           DESTINATION lib/ )
  install( TARGETS _${GAFFER_LIB}Test
           DESTINATION python/${GAFFER_LIB}Test )
  install( FILES ${${_GAFFER_LIB}_H_FILES}
           DESTINATION include/${GAFFER_LIB}Test )
endforeach()

# Install Modules
foreach( GAFFER_LIB ${GAFFER_LIB_NAMES} )
  string( TOUPPER ${GAFFER_LIB} _GAFFER_LIB )
  install( TARGETS _${GAFFER_LIB}
           DESTINATION python/${GAFFER_LIB} )
endforeach()

# Install Bindings
foreach( GAFFER_LIB ${GAFFERBINDINGS_LIB_NAMES} )
  string( TOUPPER ${GAFFER_LIB} _GAFFER_LIB )
  install( TARGETS ${GAFFER_LIB}Bindings
           DESTINATION lib/ )
  install( FILES ${${_GAFFER_LIB}BINDINGS_H_FILES}
           DESTINATION include/${GAFFER_LIB}Bindings )
endforeach()

# Install Gaffer Files
install( DIRECTORY ${GAFFER_SOURCE_DIR}/apps
         DESTINATION . )
install( DIRECTORY ${GAFFER_SOURCE_DIR}/arnold
         DESTINATION . )
install( DIRECTORY ${GAFFER_SOURCE_DIR}/bin
         DESTINATION .
         FILES_MATCHING PATTERN "*gaffer*"
         PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ GROUP_EXECUTE GROUP_READ
        )
install( DIRECTORY ${GAFFER_SOURCE_DIR}/glsl
         DESTINATION . )
install( DIRECTORY ${GAFFER_SOURCE_DIR}/python
         DESTINATION . )
install( DIRECTORY ${GAFFER_SOURCE_DIR}/arnold
         DESTINATION . )
install( DIRECTORY ${GAFFER_SOURCE_DIR}/shaders
         DESTINATION . )
install( DIRECTORY ${GAFFER_SOURCE_DIR}/startup
         DESTINATION . )
install( FILES ${GAFFER_SOURCE_DIR}/LICENSE
          DESTINATION .)

install( DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/graphics DESTINATION . )
install( DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/shaders DESTINATION . )

install( FILES  ${CMAKE_CURRENT_BINARY_DIR}/About.py DESTINATION python/Gaffer)
install( FILES  ${CMAKE_CURRENT_BINARY_DIR}/Version.h DESTINATION include/Gaffer)