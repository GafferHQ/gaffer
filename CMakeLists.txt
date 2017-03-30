
include_directories(
            "include"
            "${CORTEX_ROOT}/include"
            "${CORTEX_ROOT}/contrib/IECoreAlembic/include"
            "${CORTEX_ROOT}/contrib/IECoreArnold/include"
            "${CORTEX_ROOT}/contrib/IECoreAppleseed/include"
            )

file(GLOB_RECURSE GAFFER_SRCS RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} *.cpp *.h *.inl)
add_library (Gaffer ${GAFFER_SRCS})
