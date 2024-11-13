##########################################################################
#
#  Copyright (c) 2024, Cinesite VFX Ltd. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import Gaffer
import GafferUI

from csgaffer.nodes import CsVisualiseVertexIdTool

if CsVisualiseVertexIdTool is not None:
    Gaffer.Metadata.registerNode(
        CsVisualiseVertexIdTool,
        "description",
        """
        Tool for displaying the vertex ids of a primitive with a "P" primitive variable.

        Use keys (+/-) to change the size of the displayed text.
        """,
        "viewer:shortCut",
        "U",
        "viewer:shouldAutoActivate",
        False,
        "order",
        1004,
        "tool:exclusive",
        False,
        "layout:activator:activatorFalse",
        lambda node: False,
        plugs={
            "active": (
                "boolPlugValueWidget:image",
                "node_icons/tools/visualise_vertex_ids.png",
                "layout:visibilityActivator",
                "activatorFalse",
            ),
            "size": (
                "description",
                """
                Specifies the size of the displayed text labels.
                """,
                "layout:index",
                0,
                "layout:section",
                "Settings",
                "label",
                "Text Size",
            ),
            "colour": (
                "description",
                """
                Specifies the colour of the displayed text labels.
                """,
                "layout:index",
                1,
                "layout:section",
                "Settings",
                "label",
                "Text Colour",
            ),
            "cursorColour": (
                "description",
                """
                Specifies the colour of the displayed cursor text label.
                """,
                "layout:index",
                2,
                "layout:section",
                "Settings",
                "label",
                "Cursor Text Colour",
            ),
            "cursorRadius": (
                "description",
                """
                Specifies the search radius distance used to find the nearest vertex id to the cursor.
                Set to zero to disable cursor vertex id search.
                """,
                "layout:index",
                3,
                "layout:section",
                "Settings",
                "label",
                "Cursor Search Radius",
            ),
        },
    )

    class _SettingsNodeUI(GafferUI.NodeUI):
        def __init__(self, node, **kw):
            self.__mainColumn = GafferUI.ListContainer(
                GafferUI.ListContainer.Orientation.Vertical, spacing=4, borderWidth=4
            )

            GafferUI.NodeUI.__init__(self, node, self.__mainColumn, **kw)

            with self.__mainColumn:
                self.__plugLayout = GafferUI.PlugLayout(node, rootSection="Settings")

        def plugValueWidget(self, plug):
            hierarchy = []
            while not plug.isSame(self.node()):
                hierarchy.insert(0, plug)
                plug = plug.parent()

            widget = self.__plugLayout.plugValueWidget(hierarchy[0])
            if widget is None:
                return None

            for i in range(1, len(hierarchy)):
                widget = widget.childPlugValueWidget(hierarchy[i])
                if widget is None:
                    return None

            return widget

        def setReadOnly(self, readOnly):
            if readOnly == Gaffer.MetadataAlgo.getReadOnly(self.node()):
                return

            Gaffer.NodeUI.setReadOnly(readOnly)

            self.__plugLayout.setReadOnly(readOnly)

    def __launchToolSettings(node, plugValueWidget):
        w = GafferUI.Window(sizeMode=GafferUI.Window.SizeMode.Automatic)
        w.setTitle("Tool Settings (%s)" % (CsVisualiseVertexIdTool.staticTypeName()))
        w.setChild(GafferUI.NodeUI.create(node))
        plugValueWidget.ancestor(GafferUI.Window).addChildWindow(w, removeOnClose=True)
        w.setVisible(True)

    def __plugPopupMenu(menuDefinition, plugValueWidget):
        try:
            plug = plugValueWidget.getPlug()
        except:
            pass
        else:
            node = plug.node()
            if plug.getName() == "active" and isinstance(node, CsVisualiseVertexIdTool):
                import functools

                menuDefinition.append("/Tool Settings Divider", {"divider": True})
                menuDefinition.append(
                    "/Tool Settings", {"command": functools.partial(__launchToolSettings, node, plugValueWidget)}
                )

    GafferUI.NodeUI.registerNodeUI(CsVisualiseVertexIdTool, _SettingsNodeUI)
    GafferUI.PlugValueWidget.popupMenuSignal().connect(__plugPopupMenu, scoped=False)
