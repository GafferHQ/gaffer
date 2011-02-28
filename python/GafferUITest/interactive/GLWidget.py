import IECore
import Gaffer
import GafferUI
import IECore
import gtk
from OpenGL.GL import *

## \todo Rejig this to remove all gtk specific code, and use only GafferUI classes instead

class TestWidget( GafferUI.GLWidget ) :

	def __init__( self ) :
		
			GafferUI.GLWidget.__init__( self )
	
	def draw( self ) :
			
		glClearColor( 0, 0, 0, 0 )
		glClearDepth( 1 )
		
		glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
		
window = GafferUI.Window( title="GLWidget test" )
window.gtkWidget().connect( "delete_event", gtk.main_quit )

s = TestWidget()
window.setChild( s )

window.show()

GafferUI.EventLoop.start()
