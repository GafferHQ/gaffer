
from glob import glob
from pprint import pprint
import os,sys

gcc = '4.1.2'
# try to get an env var, if not exists return value
def get(var, value):
    import os
    if os.environ.has_key(var):
        return os.environ[var]
    return value

# constructs the cortex version number+svn revision
def getCortexVersion( folder='.' ):
    import os
    f = os.path.abspath(folder)
    iecoreVersion = os.popen( "echo `grep ieCoreMajorVersion= %s/SConstruct | cut -d'=' -f2`.`grep ieCoreMinorVersion= %s/SConstruct | cut -d'=' -f2`.`grep ieCorePatchVersion= %s/SConstruct | cut -d'=' -f2`"  % (f,f,f) ).readlines()[0].strip()
    if 'trunk' in folder:
        revision = os.popen( "svn info %s | grep Revision | cut -d' ' -f2" % f).readlines()[0].strip()
        cortexVersion = "%s.r%s" % (iecoreVersion, revision )
    else:
        cortexVersion = "%s" % (iecoreVersion)
    return cortexVersion



python  = get('PYTHON', 	'2.6.8')
tbb     = get('TBB', 		'2.2.004' )
boost   = get('BOOST', 		'1.46.1' )
openexr = get('OPENEXR', 	'1.6.1' )
ilmbase = get('ILMBASE', 	'1.0.1' )
glew    = get('GLEW', 		'1.5.3' )
glut    = get('GLUT', 		'2.6.0' )
arnold  = get('ARNOLD', 	'4.0.1.0' ) 
prman   = get('DELIGHT',        '10.0.118' )
#prman   = get('PRMAN', 		'17.0' )
maya    = get('MAYA', 		'2012' )
nuke    = get('NUKE', 		'7.0v4' )
houdini = get('HOUDINI', 	'hfs12.1.125' )
#katana  = get('KATANA', versions['katana'] )
#abc     = get('ALEMBIC', versions['alembic'] )
cortex = get('CORTEX',     '8.0.0' )
hdf5    = '1.8.10'
qt = '4.8.4'
pyside = '1.1.2'
oiio = get('OIIO', '1.1.13855fa')
ocio = get('OCIO', '1.0.8')

LOCATE_DEPENDENCY_CPPPATH=[]
LOCATE_DEPENDENCY_LIBPATH=[]


libs = '/atomo/pipeline/libs/linux/x86_64/gcc-%s/' % gcc


LOCATE_DEPENDENCY_CPPPATH.append( '%s/python/%s/include'  % ( libs, python ) )
LOCATE_DEPENDENCY_CPPPATH.append( '%s/python/%s/include/python%s'  % ( libs, python, '.'.join(python.split('.')[:2]) ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/python/%s/lib'      % ( libs, python ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/tbb/%s/include'  % ( libs, tbb ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/tbb/%s/lib'      % ( libs, tbb ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/openexr/%s/include'  % ( libs, openexr ) )
LOCATE_DEPENDENCY_CPPPATH.append( '%s/openexr/%s/include/OpenEXR'  % ( libs, openexr ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/openexr/%s/lib'      % ( libs, openexr ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/ilmbase/%s/include'  % ( libs, ilmbase ) )
LOCATE_DEPENDENCY_CPPPATH.append( '%s/ilmbase/%s/include/OpenEXR'  % ( libs, ilmbase ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/ilmbase/%s/lib'      % ( libs, ilmbase ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/glew/%s/include'  % ( libs, glew ) )
LOCATE_DEPENDENCY_CPPPATH.append( '%s/glew/%s/include/GL'  % ( libs, glew ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/glew/%s/lib'      % ( libs, glew ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/glut/%s/include'  % ( libs, glut ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/glut/%s/lib'      % ( libs, glut ) )

#LOCATE_DEPENDENCY_CPPPATH.append( '%s/arnold/%s/include'  % ( libs, arnold ) )
#LOCATE_DEPENDENCY_LIBPATH.append( '%s/arnold/%s/lib'      % ( libs, arnold ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/delight/%s/include'  % ( libs, prman ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/delight/%s/lib'      % ( libs, prman ) )

#LOCATE_DEPENDENCY_CPPPATH.append( '%s/maya/%s/include'  % ( libs, maya ) )
#LOCATE_DEPENDENCY_LIBPATH.append( '%s/maya/%s/lib'      % ( libs, maya ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/nuke/%s/include'  % ( libs, nuke ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/nuke/%s/lib'      % ( libs, nuke ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/cortex/%s/include'  % ( libs, cortex ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/cortex/%s/lib'      % ( libs, cortex ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/cortex/%s/lib/python%s'      % ( libs, cortex, '.'.join(python.split('.')[:2]) ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/cortex/%s/alembic/1.1.1'      % ( libs, cortex ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/cortex/%s/maya/%s/lib'      % ( libs, cortex, maya ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/cortex/%s/nuke/%s/lib'      % ( libs, cortex, nuke ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/cortex/%s/delight/%s/lib'      % ( libs, cortex, prman ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/qt/%s/include'  % ( libs, qt ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/qt/%s/lib'      % ( libs, qt ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/pyside/%s/include'  % ( libs, pyside ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/pyside/%s/lib'      % ( libs, pyside ) )

LOCATE_DEPENDENCY_CPPPATH.append( '%s/oiio/%s/include'  % ( libs, oiio ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/oiio/%s/lib'      % ( libs, oiio ) )
OIIO_LIB_SUFFIX = ''

LOCATE_DEPENDENCY_CPPPATH.append( '%s/ocio/%s/include'  % ( libs, ocio ) )
LOCATE_DEPENDENCY_LIBPATH.append( '%s/ocio/%s/lib'      % ( libs, ocio ) )



def rest(gcc, LOCATE_DEPENDENCY_CPPPATH, LOCATE_DEPENDENCY_LIBPATH):
 from glob import glob   
 for each in glob( '/atomo/pipeline/libs/linux/x86_64/gcc-%s/*' % gcc):
    if 'gcc' not in each[-3:]:
        app = each.split('/')[-1]
        if not filter( lambda x: app in x, LOCATE_DEPENDENCY_CPPPATH):
            versions = glob( '%s/*' % each )
            versions.sort()
            versions.reverse()
            LOCATE_DEPENDENCY_CPPPATH.append( '%s/include' % (versions[0]) )
            LOCATE_DEPENDENCY_LIBPATH.append( '%s/lib' % (versions[0]) )
 return (LOCATE_DEPENDENCY_CPPPATH, LOCATE_DEPENDENCY_LIBPATH)
        
LOCATE_DEPENDENCY_CPPPATH, LOCATE_DEPENDENCY_LIBPATH = rest(gcc, LOCATE_DEPENDENCY_CPPPATH, LOCATE_DEPENDENCY_LIBPATH)    

BOOST_LIB_SUFFIX = '-mt'

#BUILD_DEPENDENCY_OIIO = True
#OIIO_SRC_DIR = os.getcwd()+'/oiio'

#pprint( LOCATE_DEPENDENCY_LIBPATH )
#pprint( LOCATE_DEPENDENCY_CPPPATH )
CXX="/atomo/pipeline/libs/linux/x86_64/gcc-%s/gcc/bin/g++" % gcc
CC="/atomo/pipeline/libs/linux/x86_64/gcc-%s/gcc/bin/gcc"  % gcc

#CXXFLAGS=[ "-pipe", "-Wall", "-Werror", "-O2", "-DNDEBUG", "-DBOOST_DISABLE_ASSERTS" ]
CXXFLAGS=[ "-pipe", "-Wall", "-O2", "-DNDEBUG", "-DBOOST_DISABLE_ASSERTS" ]
LINKFLAGS=[
#    "-Wl,-rpath,%sgcc/lib64"  % libs,
    "-Wl,-rpath,%sboost/%s/lib"  % (libs, boost),
    "-Wl,-rpath,%scortex/%s/lib"  % (libs, cortex),
    "-Wl,-rpath,%stbb/%s/lib"  % (libs, tbb),
    "-Wl,-rpath,%soiio/%s/lib"  % (libs, oiio),
    "-Wl,-rpath,%socio/%s/lib"  % (libs, ocio),
    "-Wl,-rpath,%sqt/%s/lib"  % (libs, qt),
    "-Wl,-rpath,%spyside/%s/lib"  % (libs, pyside),
    "-Wl,-rpath,%spython/%s/lib"  % (libs, python),
]   
PYTHON_LINK_FLAGS=LINKFLAGS
SHLINKFLAGS=LINKFLAGS


#INSTALL_DIR="/atomo/pipeline/libs/linux/x86_64/gcc-%s/gaffer/%s/" % (gcc, getCortexVersion())
INSTALL_DIR="/atomo/apps/linux/x86_64/gaffer/%s/" % getCortexVersion()


