# Variables defined by this module:
#   Inkscape_FOUND
#   Inkscape_COMMAND
#   Inkscape_PATH
#
# Usage:
#   FIND_PACKAGE( Inkscape )
#   FIND_PACKAGE( Inkscape REQUIRED )

find_path( Inkscape_PATH
  NAMES inkscape inkscape.exe
  PATHS ${INKSCAPE_ROOT} $ENV{PATH}
  )

find_program( Inkscape_COMMAND
  NAMES inkscape.exe inkscape
  PATHS ${INKSCAPE_ROOT} $ENV{PATH}
  )

# did we find everything?
include( FindPackageHandleStandardArgs )
FIND_PACKAGE_HANDLE_STANDARD_ARGS( "Inkscape" DEFAULT_MSG
  Inkscape_COMMAND
  Inkscape_PATH
  )