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

from csgaffer.nodes import CsVisualiseOrientTool

if CsVisualiseOrientTool is not None:
    Gaffer.Metadata.registerNode(
        CsVisualiseOrientTool,
        "description",
        """
        Tool for displaying named primitive variables of type Quatf as coordinate frame.

        Use keys (+/-) to change the scale of the displayed coordinate frame.
        """,
        "viewer:shortCut",
        "O",
        "viewer:shouldAutoActivate",
        False,
        "order",
        1003,
        "tool:exclusive",
        False,
        "layout:activator:activatorFalse",
        lambda node: False,
        plugs={
            "active": (
                "boolPlugValueWidget:image",
                "node_icons/tools/visualise_orient_data.png",
                "layout:visibilityActivator",
                "activatorFalse",
            ),
            "name": (
                "description",
                """
                Specifies the name of the primitive variable to visualise. The data should
                be of type Imath::Quatf.
                """,
                "layout:index",
                0,
                "layout:section",
                "Settings",
                "label",
                "Name",
            ),
            "scale": (
                "description",
                """
                Scale factor applied to the orientation data visualisation.
                """,
                "layout:index",
                1,
                "layout:section",
                "Settings",
                "label",
                "Scale",
            ),
            "colourX": (
                "description",
                """
                Colour applied to the orientation X axis visualisation.
                """,
                "layout:index",
                2,
                "layout:section",
                "Settings",
                "label",
                "Colour X",
            ),
            "colourY": (
                "description",
                """
                Colour applied to the orientation Y axis visualisation.
                """,
                "layout:index",
                3,
                "layout:section",
                "Settings",
                "label",
                "Colour Y",
            ),
            "colourZ": (
                "description",
                """
                Colour applied to the orientation Z axis visualisation.
                """,
                "layout:index",
                4,
                "layout:section",
                "Settings",
                "label",
                "Colour Z",
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

            Gaffer.NodeUI.setReadOnly(self, readOnly)

            self.__plugLayout.setReadOnly(readOnly)

    def __launchToolSettings(node, plugValueWidget):
        w = GafferUI.Window(sizeMode=GafferUI.Window.SizeMode.Automatic)
        w.setTitle("Tool Settings (%s)" % (CsVisualiseOrientTool.staticTypeName()))
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
            if plug.getName() == "active" and isinstance(node, CsVisualiseOrientTool):
                import functools

                menuDefinition.append("/Tool Settings Divider", {"divider": True})
                menuDefinition.append(
                    "/Tool Settings", {"command": functools.partial(__launchToolSettings, node, plugValueWidget)}
                )

    GafferUI.NodeUI.registerNodeUI(CsVisualiseOrientTool, _SettingsNodeUI)
    GafferUI.PlugValueWidget.popupMenuSignal().connect(__plugPopupMenu, scoped=False)
