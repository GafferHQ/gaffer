# Tutorial: Assembling the Gaffer Bot #

In this tutorial, we will give you a first taste of Gaffer by covering its basic operations and concepts. The goal is for you to learn to make renders of a basic scene as quickly as possible, and provide a minimal basis to further explore the documentation. It will cover a lot of ground quickly, and some details will be glossed over.

By the end of this tutorial you will have built a basic scene with Gaffer's robot mascot, Gaffy, and render an output image. You will learn the following lessons, not necessarily in this order:

- Gaffer UI fundamentals
- Creating and connecting nodes
- Importing geometry
- Constructing a basic scene hierarchy
- Adding basic script settings
- Importing textures
- Building a simple shader
- Applying a shader to geometry
- Creating an environment light
- Using an interactive renderer

> Note :
> This tutorial uses the Appleseed renderer, as it is included with Gaffer. While the Appleseed-specific nodes described here can be substituted with equivalents from Arnold or 3Delight, we recommend that you complete this tutorial using Appleseed before moving on to your preferred renderer.


## Starting a New Script ##

After [installing Gaffer](../InstallingGaffer/index.md), launch Gaffer [from its directory](../LaunchingGafferFirstTime/index.md), or using the ["gaffer" command](../SettingUpGafferCommand/index.md). Gaffer will start, and you will be presented with an empty graph in the default UI layout.

![An empty graph in the default layout](images/mainDefaultLayout.png "An empty graph in the default layout")

> Note :
> To avoid confusion between Gaffer files, its UI, and node graphs in general, we refer to the files you work on as **scripts**.


## Importing a Geometry Scene Cache ##

As Gaffer is a tool primarily designed for LookDev, lighting, and VFX process automation, we expect that your shot's modelling and animation will be created in an external tool like Maya, and then imported into Gaffer as a geometry/animation cache. Gaffer supports the standard Alembic (.abc) and USD (.usd) file formats, as well as its own native SceneCache (.scc) file format. Most scenes begin by importing geometry or images via one of the two types of Reader nodes: [SceneReader](../../Reference/NodeReference/GafferScene/SceneReader.md) or [ImageReader](../../Reference/NodeReference/GafferScene/ImageReader.md).

First, load Gaffy's geometry cache with a SceneReader node:

1. In the _Graph Editor_ in the bottom-left panel, right-click. The node creation menu will appear.

2. Using the drop-down menu, select _Scene_ > _File_ > _Reader_. The SceneReader node will appear in the _Graph Editor_ and be selected automatically.
    
    ![A new SceneReader node](images/mainSceneReaderNode.png "A new SceneReader node") <!-- TODO: add annotation? -->

3. The _Node Editor_ in the top-right panel now reads _Node Editor : SceneReader_. Under its _Settings_ tab, in the File Name field, type `${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc`.

4. Hover the cursor over the background of the _Viewer_ (in the top panel), and hit <kbd>F</kbd>. The view will reframe to cover the whole scene.
    
    ![The bounding box of the selected SceneReader node](images/viewerSceneReaderBounding.png "The bounding box of the selected SceneReader node") <!-- TODO: add annotation -->

The SceneReader node has loaded, and the _Viewer_ is showing a bounding box, but the geometry remains invisible. You can confirm that the scene has loaded by examining the _Scene Hierarchy_ in the bottom-right panel. It too has updated, and shows that you have _GAFFERBOT_ at the root of the scene. In order to view the geometry, you will need to expand the scene's locations down to their roots.

> Important :
> By default, the _Viewer_, _Node Editor_, and _Scene Hierarchy_ update to reflect the selected node, and go blank when no node is selected.


## The Scene Hierarchy ##

When you load a geometry cache, Gaffer only reads its scene hierarchy: at no point does it write to the file. This lets you manipulate the scene's locations without risk to the file.

> Important :
> Scenes hierarchies in Gaffer can have their locations non-destructively hidden, added to, changed, and deleted.

Further, Gaffer uses locations in the scene's hierarchy to selectively render the geometry you need: expanded locations have their geometry shown in the _Viewer_, while collapsed locations appear only as bounding boxes. This on-demand geometry loading allows Gaffer to handle highly complex scenes (we informally call it "lazy loading"). Currently, only a bounding box is visible in the _Viewer_.

> Important :
> Only geometry that has its parent locations expanded will show in the _Viewer_. Geometry that still has its parent locations collapsed will show as a bounding box.


### Navigating the Scene Using the _Scene Hierarchy_ ###

Until you expand the scene's locations in the _Scene Hierarchy_, Gaffy's geometry will remain invisible.

Use the _Scene Hierarchy_ to show Gaffy's geometry:

1. If the SceneReader node is deselected, select it by clicking it.

2. In the _Scene Hierarchy_, click the triangle next to _GAFFERBOT_. The _GAFFERBOT_ location will expand to show a child location named *C_torso_GRP*.

3. Click ![the triangle](images/collapsibleArrowRight.png "Triangle") next to *C_torso_GRP* to show its child locations.

    ![The scene hierarchy, expanded down two levels](images/hierarchySceneExpandedTwoLevels.png "The scene hierarchy, expanded down two levels") <!-- TODO: add annotation -->

> Note :
> Gaffy's geometry cache contains primitive and location names with affixes like _C_, _R_, _L_, _GRP_, _CPT_ and _REN_. Gaffer places no significance whatsoever on these names, and you or your studio are free to use whichever naming conventions you see fit.

In the _Viewer_, you can now see the bounding boxes of multiple geometry primitives (or groups of primitives), revealing more of the scene's structure. However, it would be tedious to expand the whole scene, location-by-location, in this manner. Instead, you can expand a location, its children, and all its sub-children by <kbd>Shift</kbd> + clicking.

Expand Gaffy's head and left leg locations and their children:

1. In the _Scene Hierarchy_, <kbd>Shift</kbd> + click ![the triangle](images/collapsibleArrowRight.png "Triangle") next to *C_head_GRP*. All the locations under *C_head_GRP* will expand. Now the _Viewer_ will show all of the geometry that comprises Gaffy's head.

2. <kbd>Shift</kbd> + click ![the triangle](images/collapsibleArrowRight.png "Triangle") next to *L_legUpper_GRP*. All the locations under *L_legUpper_GRP* will expand. Now the _Viewer_ will show all of the geometry that comprises Gaffy's left leg.

![The head and left leg geometry, expanded](images/mainHeadAndLeftLegExpanded.png "The head and left leg geometry, expanded")


### Navigating the Scene Using the _Viewer_ ###

As you navigated the scene using the _Scene Hierarchy_, the _Viewer_ updated to show the geometry you expanded. The _Viewer_ also has the useful feature of letting you expand the scene by directly interacting with the geometry and bounding boxes it displays. Navigating discrete parts of a scene like this can be invaluable when dealing with very complex scenes.

Using the arrow keys, expand the scene hierarchy through the _Viewer:_

1. In the _Viewer_, select Gaffy's right leg by click-dragging a marquee over its bounding box. The leg's bounding box will highlight.

2. Hit <kbd>↓</kbd> to expand the selection down one level. The highlighted bounding box will be replaced by two smaller bounding boxes, indicating that you have expanded the location and selected the right leg's children.

3. Hit <kbd>Shift</kbd> + <kbd>↓</kbd> to fully expand all the right leg's locations.

    ![The head and legs geometry, expanded](images/viewerHeadAndLegsExpanded.png "The head and legs geometry, expanded")

You can also collapse the selection in a similar manner using the _Viewer:_

1. With the right leg geometry still selected, hit <kbd>↑</kbd>.

2. Keep hitting <kbd>↑</kbd> until all the geometry is collapsed back into the root bounding box.

You may have noticed that when you expanded and collapsed parts of the scene using the _Viewer_, the locations and geometry were also highlighted and selected in the _Scene Hierarchy_. This is because:

> Important :
> Manually selecting, expanding, and collapsing elements of the scene in the _Viewer_ is synonymous with using the _Scene Hierarchy_.


## Adjusting the View in the _Viewer_ ##

Like in other 3D tools, you can adjust the _Viewer's_ angle, field of view, and the position of the virtual camera.

- To rotate/tumble, <kbd>Alt</kbd> + click and drag.
- To zoom/dolly in and out, <kbd>Alt</kbd> + right click and drag, or scroll the middle mouse.
- To track from side to side, <kbd>Alt</kbd> + middle click and drag.

> Tip :
> If you lose sight of the scene and cannot find your place again, you can always refocus on the currently selected location by hovering the cursor over the _Viewer_ and hitting <kbd>F</kbd>.


## Creating and Setting Up a Camera ##

Before you can start any rendering, you will need to create a render camera. Just like how you created a SceneReader node to load in the geometry, you will add another node to generate a camera.

Earlier, you learned how to find a node by navigating the node creation menu in the _Graph Editor_. If you know the name of the node you wish to create, and do not feel like navigating the menu, you can instead use the menu's search feature:

1. Hover the cursor over the background in the _Graph Editor_.

2. Right-click. The node creation menu will open.

> Tip :
> With the cursor hovering over the _Graph Editor_, you can also hit <kbd>Tab</kbd> to open the node creation menu.

3. Type `Camera`. A list of search results will appear. By default, _Camera_ will be highlighted.

4. Hit <kbd>Enter</kbd> to create a new Camera node.

    ![A new Camera node](images/mainCameraNode.png "A new Camera node")

As before, the newly created node will be selected automatically, and the _Viewer_, _Scene Hierarchy_, and _Node Editor_ will update to reflect this new selection.


## Nodes, Scenes, and Plugs ##

So far, your script is set up as such: the SceneReader node is outputting a scene containing Gaffy's geometry, and the Camera node is outputting a scene containing a camera. Since neither node is connected, each scene remains separate. This is because each node in Gaffer outputs an entire self-contained scene hierarchy at its position in the graph. If they do not join somewhere later in the graph, the two scenes will never interface with each other. A key part to understand about the node graph is that:

> Important :
> Each node contains either the scene that has been passed to it through a plug, or the scene that it creates.

In short, the scene is not a single hierarchy that exists in the background of the graph, but is instead carried by the nodes. You can test this by clicking the background of the _Graph Editor_, and observing that once the you have no node selected, the _Scene Hierarchy_ goes blank. This will become very relevant when you begin combining scenes together and selectively modifying a scene's locations.

Gaffer allows scenes to be built and modified by creating connections between nodes. For most nodes, the scene flows into it through its input, is then modified by the node, and then flows out through it. A node's inputs and outputs are called **plugs**, and are represented in the _Graph Editor_ as colored circles around a node's edges.

<!-- TODO: add close-up of node plugs ![A node's plug.](images/nodePlug.png) -->

For your two nodes to occupy the same scene (and later render together), you will need to combine them into a single scene at some point later in the graph. You can connect both of their output plugs to a Group node, and you can also rearrange the nodes to better represent the visual hierarchy.


### Connecting Plugs ###

It's time to connect the SceneReader and Camera nodes to combine their scenes:

1. Click the background of the _Graph Editor_ to deselect all nodes.

2. Create a Group node (_Scene_ > _Hierarchy_ > _Group_).

3. Click and drag the SceneReader node's _out_ plug (at the bottom; blue) onto the Group node's _in0_ plug (at the top; also blue). As you drag, a node connector will appear. Once you connect them, a second input plug (_in1_) will appear on the Group node, next to the first.

4. Click and drag the Camera node's _out_ plug onto the Group node's _in1_ plug.

    ![A new Group node](images/mainGroupNode.png "A new Group node")

The Group node is now generating a new scene combining the input scenes from the two nodes above it, under a new parent location called _group_. You can see this new hierarchy by selecting the Group node and examining the _Scene Hierarchy_.

Only the combined scene at the Group node has been modified. The upstream nodes' scenes are unaffected. You can verify this by reselecting one of them and checking the _Scene Hierarchy_.


### Navigating the _Graph Editor_ ###

You may have noticed that you can intuitively click and drag the nodes around in the _Graph Editor_. You can also pan and zoom around the _Graph Editor_, just like in the _Viewer_.

- To pan the view, <kbd>Alt</kbd> + click and drag, or middle-click and drag.
- To zoom in and out, <kbd>Alt</kbd> + right-click and drag, or scroll the middle mouse.
- To focus on the currently selected node, hover the cursor over the _Graph Editor_ and hit <kbd>F</kbd>.


## Positioning the Camera ##

Next, you should reposition the camera so that it frames Gaffy.

To set the camera's position:

1. Select the Camera node.

2. In the _Node Editor_, click the _Transform_ tab.

3. Edit the position and rotation values:
    - Set the Translate plug to `19` `13` `31`.
    - Set the Rotate plug to `0` `30` `0`.

    ![The transform values](images/nodeEditorWindowCameraTransform.png "The transform values")

4. Select the Group node.

5. Hover the cursor over the _Viewer_ and hit <kbd>F</kbd> to see Gaffy and the camera in the same frame.

> Note :
> In the previous section, we referred to the inputs and outputs of the nodes as plugs, and connected them by dragging and dropping within the _Graph Editor_. In actuality, the Translate and Rotate values you just edited in the Camera node are also plugs: they are part of the node's input plug, and can also be connected to other plugs, if needed. For ease of use, by default nodes in _Graph Editor_ and _Node Editor_ each present only a subset of their available plugs.


## Rendering Your First Image ##

Now that you have defined the layout of your scene, you should perform a quick test-render to check that everything is working as expected. In order to do that, you need to place some render-related nodes to define your script's render settings.

Create the render settings nodes:

1. Select the Group node.

2. Create a StandardOptions node (_Scene_ > _Globals_ > _StandardOptions_). It will automatically connect to the output of the Group node and become selected.

3. Create an AppleseedOptions node (_Appleseed_ > _Options_). It will connect automatically to the output of the StandardOptions node and become selected.

4. Create an Outputs node (_Scene_ > _Globals_ > _Outputs_). It will connect and become selected like the others.

5. Create an InteractiveAppleseedRender node (_Appleseed_ > _InteractiveRender_).

6. Create a Catalogue node (_Image_ > _Utility_ > _Catalogue_). It does not need to be connected to anything. Instead, place it next to the InteractiveAppleseedRender node.

    ![The render-related nodes](images/graphEditorRenderSettings.png "The render-related nodes")

Briefly, here is the function of each of these nodes:
- StandardOptions node: Determines the camera, resolution, and blur settings of the scene.
- AppleseedOptions node: Determines the settings of the Appleseed renderer.
- Outputs node: Determines what kind of output render will be created.
- InteractiveAppleseedRender node: An instance of Appleseed's interactive (responsive) renderer.
- Catalogue node: Global list of images/renders that you can preview within Gaffer. Renders you generate will appear in this node's list.

In keeping with what we said earlier about nodes passing scenes to other nodes: with the exception of the Catalogue node, each of these render options nodes only apply to the scene delivered to them through their input plugs. If you had another unconnected scene running in parallel, none of these render settings would apply to it.

Although the scene contains a camera, you will need to point the StandardOptions node to it:

1. Select the StandardOptions node.

2. Specify the camera using the _Node Editor:_
	1. Click the _Camera_ section to expand it.
	2. Toggle the switch next to the Camera plug to enable it.
	3. Type `/group/camera` into the plug's field.

Next, you need to add an image type to render:

1. Select the Outputs node.

2. In the _Node Editor_, click ![the plus button](images/plus.png "Plus") and select _Interactive_ > _Beauty_ from the drop-down menu.

With all the settings complete, start the interactive renderer:

1. Select the InteractiveAppleseedRender node.

2. In the _Node Editor_, click ![the play button](images/timelinePlay.png "Play") to start the renderer.

3. Select the Catalogue node.

4. Hover the cursor over the _Viewer_ and hit <kbd>F</kbd> to frame the Catalogue node's live image of the interactive render.

    ![The first render](images/mainRenderGrey.png "The first render")

Congratulations! You have successfully rendered your first image. Gaffy is currently lacking shading, lighting, and texturing. We will move on to those soon. First, you should adjust the UI to provide yourself a more optimal workflow.


## Pinning an Editor to a Node ##

As mentioned earlier, the _Viewer_, _Scene Hierarchy_, and _Node Editor_ (each an **editor**) show their respective outputs of the currently selected node. This is not always convenient, because often you will need to edit one node while viewing the output of another. You can solve this by **pinning** an editor while a node is selected, which keeps that editor focused on the node.

To make switching between viewing Gaffy's geometry and the render easier, you can modify the UI so you're working with two Viewers. First, start by pinning the last node in the graph that contains the scene:

1. Select the InteractiveAppleseedRender node.

2. Click ![the pin button](images/targetNodesUnlocked.png "Pin button") at the top-right
  of the top pane. The pin button will highlight: ![highlighted pin](images/targetNodesLocked.png "Highlighted pin").

The _Viewer_ is now locked to the InteractiveAppleseedRender node's scene (which contains all of the parts from its upstream scenes), and will only show that scene, even if you deselect it or select a different node.

Next, pin the same node to the _Scene Hierarchy_. This time, use the middle-click shortcut:

1. Select the InteractiveAppleseedRender node.

2. Middle-click and drag the InteractiveAppleseedRender node from the _Graph Editor_ into the
  _Scene Hierarchy_.

As with the _Viewer_, the _Scene Hierarchy_ will now remain locked to the output of InteractiveAppleseedRender, regardless of your selection. Now you are free to select any node for editing in the _Node Editor_, but you will always be viewing the final results of the last node in the graph.

For the final adjustment to the UI, create another _Viewer_ in the top-left panel, and pin the Catalogue node to it:

1. At the top-right of the top panel, click ![the layout menu button](images/layoutButton.png "Layout menu button") to open the layout menu.

2. Select _Viewer_. A new _Viewer_ will appear on the panel next to the first one.

3. Middle-click and drag the Catalogue node onto the new _Viewer_. That _Viewer_ is now pinned to that node.

Now you can switch between the scene's geometry (first _Viewer_) and the rendered image (second _Viewer_). Now it is time to shade Gaffy.


## Adding Shaders and Lighting ##

It's time to add shaders and lighting. It will help to think of a graph as being composed of three distinct phases: generating the geometry, applying the lighting and shading, and rendering. Lights act like another scene object, so you can group one into the scene like the other nodes. The shaders, however, are different: in order for the render option nodes to apply to the geometry and to inherit the shaders, you will need to add them somewhere between the scene-creating nodes and render options nodes.


### Making Some Space ###

Since you will be adding shaders nodes between the scene nodes and the render options nodes, you will first need to add some space in the graph.

To create some empty space in the centre of the graph:

1. Select the lower five nodes by clicking and dragging a marquee over them.

2. Click and drag the nodes to a lower position in the graph.

    ![The graph with some added space](images/mainRenderSettingsWithGap.png "The graph with some added space")


### Adding a Shader ###

Now that you have more space, it's time to add some shading nodes:

1. Below and to the left of the Group node, create a Disney Material node (_Appleseed_ > _Shader_ > _Material_ > *As_Disney_Material*).

2. In the _Node Editor_, give the shader some reflective surface properties:
	- Set the Specular plug to `0.6`.
	- Set the Roughness plug to `0.35`.

3. With the Disney Material node still selected, create a ShaderAssignment node (_Scene_ > _Attributes_ > _ShaderAssignment_).

4. Click and drag the ShaderAssignment node onto the connector connecting the Group and StandardOptions nodes. The ShaderAssignment_node will be interjected between them.

    ![The ShaderAssignment and Disney Material nodes](images/graphEditorFirstShaderNodes.png "The ShaderAssignment and Disney Material nodes")

Note that the input and output plugs on the Disney Material node flow from left to right. This is because in Gaffer:

> Important :
> Scenes flow from top to bottom, and shaders flow from left to right.

In your newly shaded graph, the ShaderAssignment node takes the material flowing in from the left and assigns it to Gaffy's geometry flowing in from the top. Now that Gaffy has received a proper material assignment, you will need to light the scene.


### Adding an Environment Light ###

Lights, like geometry and cameras, are objects that need to be combined with the main scene. For simplicity, you should add a global environment light:

1. Create a PhysicalSky node (_Appleseed_ > _Environment_ > _PhysicalSky_).

2. Place it next to the Camera node.

3. In the _Node Editor_, adjust the node's angle and brightness:
	- Set the Sun Phi Angle plug to `100`.
	- Set the Luminance plug to `2.5`.

4. Connect the PhysicalSky node's _out_ plug to the Group node's _in3_ plug.

![A new environment light node](images/graphEditorEnvironmentLightNode.png "A new environment light node")

For the light to take effect, you will need to enable environment lighting in the AppleseedOptions node:

1. Select the AppleseedOptions node.

2. In the _Node Editor_, expand the _Environment_ section.

3. Toggle the switch next to the Environment Light plug to enable it.

4. Type `/group/light` into the plug's field.

The interactive render will now be in the process of updating, and you will be able to see Gaffy with some basic shaders and lighting.

![The first render with a shader and lighting](images/viewerRenderOneShader.png "The first render with a shader and lighting")


### Adding Textures ###

As Gaffy is looking a bit bland, you should assign some textures to the shader:

1. Create an Appleseed Color Texture node (_Appleseed_ > _Shader_ > _Texture2d_ > *As_color_texture*).

2. In the _Node Editor_, point the node to the textures:
	1. Type `${GAFFER_ROOT}/resources/gafferBot/textures/base_COL/base_COL_` into the _Filename_ value's field.
	2. Select `mari` from the _UDIM_ drop-down menu.

3. In the _Graph Editor_, connect the AppleSeed Color Texture node's ColorOut plug to the Disney Material node's BaseColor plug. Gaffy's textures will now mix with the shader, and the render will update to show the combined results.

    ![Gaffy with textures](images/viewerRenderTextures.png "Gaffy with textures")


### Adding Another Shader ###

With the textures assigned, the surface of all of Gaffy's geometry looks the same, because the material shader is applying to everything. To fix this, you should create an additional metallic shader and apply it selectively to different parts of the geometry.

Begin by creating another shader:

1. Create another Disney Material node.

2. In the _Node Editor_, give the shader some metallic properties:
	1. Set Metallic to `0.8`
	2. Set Roughness to `0.4`

3. With the new Disney Material node still selected, create another ShaderAssignment node

4. Click and drag the new ShaderAssignment node onto the connector under the first ShaderAssignment node. The new ShaderAssignment node will come after the fist shader in the graph flow.

    ![A second shader in the Graph Editor](images/graphEditorSecondShaderNodes.png "A second shader in the Graph Editor")

The _Viewer_ will update to show the new shader.

![The second shader, rendered](images/mainRenderTwoShaders.png "The second shader, rendered")

You will immediately notice something is wrong: _all_ the geometry is metallic. The new shader has overridden the previous one. This is because:

> Important :
> The last ShaderAssignment node applied to geometry in a scene takes precedence over all others.

### Filtering a Shader ###

In order to selectively apply a shader to only certain parts of the scene's geometry, you will need to **filter** the shader assignment, using a filter node that selects parts of a scene by name:

1. Create a PathFilter node (_Scene_ > _Filters_ > _PathFilter_).

2. In the _Node Editor_, click ![the plus button](images/plus.png "Plus") next to _Paths_. This will add a new text field.

3. Double-click the text field and type `/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/L_ear001_REN`. This is the full path to Gaffy's left ear.

4. Connect the PathFilter node's _out_ plug to the filter input on the right hand side of the ShaderAssignment1 node's filter plug (yellow; on the right).

    ![The connected PathFilter node](images/graphEditorPathFilterNode.png "The connected PathFilter node")

Now when you check the render, you will see that the chrome shader is only applied to Gaffy's left ear. There are many other parts of Gaffy that could use the chrome treatment, but it would be tedious for you to manually enter multiple locations. There are two ways you can more easily add geometry to the filter: using text wildcards, and interacting directly with the geometry.


#### Filtering Using Wildcards ####

A wildcard tells text interpreters to take a value of any length where there is an asterisk `*`. They are useful if you know part of a path, but don't want to have to look up or type it in its entirety. Earlier, you used `/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/L_ear001_REN`, which only pointed to the left ear. You could apply the filter to _both_ ears by adding wildcards to the `/L_ear001_REN` location in the path.

To use a wildcard in the path filter:

1. Select the PathFilter node.

2. In the _Node Editor_, double-click the path field you created earlier, and change it to `/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/*_ear*`. The filter will now match the left and the right ears.


#### Filtering by Dragging Selections ####

As your final operation, add the metallic shader to the rest of the appropriate parts of Gaffy. This time, you can add to the path filter using a visual method:

1. In the top panel, switch to the _Viewer_ containing the 3D geometry view.
2. Zoom and pan to Gaffy's face.
3. Click the eyebrows to select them.
4. <kbd>Shift</kbd> + click the mouth to add it to the selection.

    ![The face, with selection](images/viewerSelectionFace.png "The face, with selection")

5. Click and drag the selection (the cursor will change to ![the "replace objects" icon](images/replaceObjects.png "Replace objects")), and hold it over the PathFilter node without releasing.

6. While still dragging, hold <kbd>Shift</kbd> (the cursor will change to ![the "add objects" icon](images/addObjects.png "Add objects")). You are now adding to the path, rather than replacing it.

7. Release the selection over the PathFilter node. This will add the geometry as new path fields to the node.

Just as geometry can be added by holding <kbd>Shift</kbd>, they can be removed by holding <kbd>Control</kbd> (the cursor will change to ![the "remove objects" icon](images/removeObjects.png "Remove objects")). With this in mind, you can add and remove geometry from path filter as you see fit. Remember to switch between the _Viewer_ editors to check the render output as it updates. After adding Gaffy's hands and bolts to the filter, you should achieve an image similar to this:

![The final render](images/viewerRenderFinal.png "The final render")


## Recap ##

Congratulations! You've built and rendered your first scene in Gaffer.

You should now have a basic understanding of Gaffer's interface, how a script should flow, how to manipulate the scene, and how to add geometry, lights, textures, and shaders.

You should now have a solid basis for further learning and exploration.


<!-- ## See Also ## -->

<!-- TODO: - [Installing Gaffer](../GettingStarted/InstallingGaffer/index.md) -->
<!-- TODO: - [Launching Gaffer for the first time]<!-- TODO: (../GettingStarted/LaunchingGafferFirstTime/index.md) -->
<!-- TODO: - [Setting up the "Gaffer" command](../GettingStarted/SettingUpGafferCommand/index.md) -->
<!-- TODO: - [Tutorial: LookDev](../IntermediateTutorial/index.md) -->
<!-- TODO: - [Graph flow](../../UnderstandingTheNodeGraph/GraphFlow/NodeTypes/index.md) -->
<!-- TODO: - [Node types](../../UnderstandingTheNodeGraph/GraphFlow/GraphFlow/index.md) -->
<!-- TODO: - [Manipulating the scene hierarchy](../../WorkingWithScenes/ManipulatingSceneHierarchy/index.md) -->
