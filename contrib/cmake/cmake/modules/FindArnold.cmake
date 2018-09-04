# - Arnold finder module
# This module searches for a valid Arnold instalation.
#
# Variables that will be defined:
# ARNOLD_FOUND             Defined if a Arnold installation has been detected
# ARNOLD_LIBRARY           Path to ai library (for backward compatibility)
# ARNOLD_LIBRARIES         Path to ai library
# ARNOLD_INCLUDE_DIR       Path to the include directory (for backward compatibility)
# ARNOLD_INCLUDE_DIRS      Path to the include directory
# ARNOLD_VERSION           Version of arnold

# Naming convention:
#  Local variables of the form _arnold_foo
#  Input variables from CMake of the form Arnold_FOO
#  Output variables of the form ARNOLD_FOO
#

find_library(ARNOLD_LIBRARY
    NAMES ai
    PATHS ${ARNOLD_ROOT}/lib
    DOC "Arnold library")

find_path(ARNOLD_INCLUDE_DIR ai.h
    PATHS ${ARNOLD_ROOT}/include
    DOC "Arnold include path")

set(ARNOLD_LIBRARIES ${ARNOLD_LIBRARY})
set(ARNOLD_INCLUDE_DIRS ${ARNOLD_INCLUDE_DIR})

# get the arnold version from ai_version.h
file(STRINGS ${ARNOLD_INCLUDE_DIR}/ai_version.h _lines
     REGEX "^#define AI_VERSION_[A-Z_ 0-9\"]+$" )
list(LENGTH _lines _linenum)
if (_linenum EQUAL 4)
    foreach(_line ${_lines})
        string(REGEX MATCH "[0-9]+" _num ${_line})
        if (NOT DEFINED ARNOLD_VERSION)
            set(ARNOLD_VERSION ${_num})
        else()
            set(ARNOLD_VERSION "${ARNOLD_VERSION}.${_num}")
        endif()
    endforeach()
else()
    message(WARNING "Could not determine ARNOLD_VERSION")
endif()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(Arnold DEFAULT_MSG
    ARNOLD_LIBRARY ARNOLD_INCLUDE_DIR)