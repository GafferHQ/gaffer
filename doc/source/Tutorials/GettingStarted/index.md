Getting Started
===============

This tutorial is intended to give new users a first taste of lighting and rendering in
Gaffer. As such it will cover a lot of ground quickly and will necessarily gloss over
some details. Our goal is to learn to make images as quickly as possible, and provide
a minimal basis for further exploration using the rest of this guide. Hold on tight!

> Note : This tutorial uses the open source Appleseed renderer, as it is included with
> Gaffer and is ready to run out of the box. The Appleseed specific nodes that are used
> here can be substituted with direct equivalents for Arnold or 3delight, but we do
> recommend that you complete the tutorial using Appleseed before flying solo with your
> renderer of choice.

Launching Gaffer
----------------

After completing the [installation chapter][1], launch Gaffer from a shell with the following
command :

```
> gaffer
```

You should be presented with the default UI layout.

![Default layout](images/defaultLayout.png)

Loading some geometry
---------------------

As Gaffer is primarily a lighting package, it is expected that modelling and animation will be performed in an external package and then imported into Gaffer in the form of an animation cache. Gaffer supports both the Alembic (.abc) file format and its own native SceneCache (.scc) format.

Let's start by creating a [SceneReader][2] node to load some geometry :

- Locate the [NodeGraph][3] editor in the lower left pane.
- _Right-Click_ inside the NodeGraph to pop up a menu for creating nodes.
- Create a SceneReader using the _/Scene/File/Reader_ menu item.

![Empty SceneReader](images/emptySceneReader.png)

The newly created node has been selected automatically, and each of the editor panes has been updated to show the selection. We haven't yet specified a cache to load though, so there's not much to see. Let's remedy that.

- Locate the NodeEditor in the top right pane.
- Enter `${GAFFER_ROOT}/resources/gafferBot/caches/gafferBot.scc` into the **File Name** field.
- Move the mouse into the [Viewer][4] in the top left pane and press 'f' to frame the full scene.

![SceneReader Bounding Box](images/sceneReaderBound.png)

Something seems to be happening, but frankly not much. The SceneHierarchy in the bottom right pane has updated to show we have a "GAFFERBOT" located at the root of our scene, and the Viewer in the top left is showing a mysterious new bounding box. It seems that our SceneReader is loading _something_, but how do we find out what exactly?

> Tip : As mentioned above, by default the UI updates to view the currently selected node.
> This can be confusing if you accidentally deselect a node, because the editors will go blank.
> Later on we'll see various ways of managing which node is viewed, but for now it is enough
> to know that you can reselect a node by _Left-Clicking_ on it in the NodeGraph.

Navigating the scene
--------------------

One of the key features that allows Gaffer to deal with highly complex scenes is that it loads geometry lazily on demand, processing only the portions of the scene that have been requested by the user. Any geometry that has not yet been requested is displayed as a simple bounding box, like the one we're looking at. Let's find out what's in the box.

- Locate the SceneHierarchy editor in the bottom right pane.
- _Left-Click_ the triangle to the left of "GAFFERBOT". The "GAFFERBOT" location should expand to show a child named "C_torso_GRP".
- _Left-Click_ the triangle to the left of "C_torso_GRP" to expand to show its children.

We can now see the basic structure of the model coming into view.

![SceneHierarchy Expanded Two Levels](images/sceneHierarchyExpandedTwoLevels.png)

It would be tedious to expand the whole scene location by location like this, so let's speed things along a little :

- _Shift+Left-Click_ the triangle to the left of "C_head_GRP".
- _Shift+Left-Click_ the triangle to the left of "L_legUpper_GRP".

Shift clicking loads the entire scene below the location which was clicked, so we can now see all the geometry which is part of the head and left leg of our new mechanical friend.

![Head and Leg Expanded](images/headAndLegExpanded.png)

> Note : You may have noticed that the cache file used in this tutorial contains objects named using a
> specific convention, with suffixes like "GRP", "CPT" and "REN". It should be noted that Gaffer places no
> significance whatsoever in these names, and you are free to name your own creations however you see fit.

Navigating using the Viewer
---------------------------

As we navigated the scene using the SceneHierarchy editor, the [Viewer][4] was loading the geometry we discovered and displaying it. We can also control this expansion process directly within the Viewer itself :

- _Left-Drag_ over the bounding box of the other leg to select it. It should highlight to show that you have been successful.
- Press _Down-Arrow_ on the keyboard to expand it one level.
- Press _Shift+Down-Arrow_ on the keyboard to expand it fully.

![Head and legs expanded](images/headAndLegsExpanded.png)

As you might have guessed, we can also collapse the selection to return to a bounding box view :

- Keeping the currently selected leg geometry, press _Up-Arrow_ to collapse it.
- Press _Up-Arrow_ repeatedly until all the geometry is collapsed back into the root bounding box.

Navigating individual parts of a scene like this can be invaluable when dealing with very complex scenes, but we've already established that our mechanical friend is fairly lightweight and loads quickly, so it would be convenient to automatically keep the entire scene loaded at all times. This will also help in the rest of this tutorial as we switch between scenes and rearrange the hierarchy.

- Locate the main toolbar at the top of the Viewer.
- Locate the ![scene expansion menu](images/expansion.png) button and _Left-Click_ it to show the scene expansion popup menu.
- Choose "Expand All".

![Fully Expanded](images/fullyExpanded.png)

Finally, we can see our guy in all his vintage glory. Now would be a good time to get to grips with interactive camera movement within the viewer, so we can move around and get a better look at our guy. All movement is controlled by the mouse, but is accessed by holding down the _Alt_ key to the left of the space bar.

- Hold down _Alt_ and _Left-Drag_ to tumble around, and view the model from all angles.
- Hold down _Alt_ and _Right-Drag_ to dolly in and out.
- Hold down _Alt_ and _Middle-Drag_ to track from side to side.

Now we're familiar with the model we're going to be rendering, we can move on to the next steps.

Making a camera
---------------

Before we can render anything, we'll need a camera to render from. Just as we created a SceneReader node to load in the model, we'll create another node to generate a camera. You'll remember from the previous section that we can create nodes by making a _Right-Click_ inside the NodeGraph and finding the node we want in the menu that appears. This time though, we'll take a shortcut :

- Make sure the mouse is inside the NodeGraph.
- Press _Tab_ to show the node menu, and note that it has a search field at the top, which already has the keyboard focus.
- Type "Camera" into the search field. Note that a new submenu has appeared showing the search results.
- Press _Return_ to activate the highlighted search result and create a Camera node.

As before, our newly created node has been selected automatically, and the UI has updated to show the selection.

![Camera](images/camera.png)

We appear to have a problem though - although we can see our new camera, our model has disappeared!

> Note : Many users find that the _Tab_ node search shortcut makes them more productive, but
> it can also be useful to browse the full menu to explore all the nodes that are available.
> For the rest of this tutorial, we'll just say "Create a SceneReader node _(/Scene/File/Reader)_" and expect
> you to make your own choice as to which method you use.

Grouping the camera with the model
----------------------------------

Each node in Gaffer outputs an entire self contained scene. Our SceneReader node is outputting a robot scene, and our Camera node is outputting a scene containing a camera, but each of these are separate. By _Left-Clicking_ on each node in the NodeGraph we can select which scene we want to view and edit, but before we can render we need to combine them into a scene with both a robot _and_ a camera.

Gaffer allows scenes to be modified by making connections between nodes so that input scenes flow into a node, are modified, and then flow out again. The inputs and outputs of nodes are called **plugs**, and are represented in the NodeGraph as circles on the edges of the nodes. Let's make a new node and connect it up so that it combines the robot and camera into a single scene.

- Deselect all nodes by _Left-Clicking_ in empty space in the NodeGraph.
- Create a Group node _(/Scene/Hierarchy/Group)_.
- Arrange the nodes by _Left-Dragging_ them into position.
	- Place the SceneReader at the top left.
	- Place the Camera at the top right.
	- Place the Group below them.
- _Left-Drag_ from the _output_ of the SceneReader onto the _input_ of the Group.
  Note that a second input appears on the Group.
- _Left-Drag_ from the _output_ of the Camera onto the second _input_ of the Group.
- Select the Group node by _Left-Clicking_ on it.

![Group](images/group.png)

The Group node is generating a new scene which combines the input scenes by placing them both under a new parent called "group", as can be seen in the SceneHierarchy in the bottom right panel. Note that this is an entirely non-destructive process, and the upstream scenes from the SceneReader and Camera nodes are still available at any time simply by selecting the relevant node.

Positioning the camera
----------------------

Next we need to position the camera so that it frames our subject :

- Select the Camera node by _Left-Clicking_ on it in the NodeGraph.
- In the NodeEditor (top right panel), _Left-Click_ on the **Transform** tab to expose the transform settings.
- Use the numeric widgets to set the camera position.
	- Set **Translate** to `19, 13, 31`
	- Set **Rotate** to `0, 30, 0`
- Reselect the Group node in the NodeGraph to see the position of the camera
  relative to the robot.

![Group](images/cameraTransform.png)

> Note : In the previous section we referred to the inputs and outputs of the nodes as **plugs**,
> and connected them by dragging and dropping within the NodeGraph. But in fact, the **Translate**
> and **Rotate** values we have just edited on the Camera node are _also_ **plugs** : they also
> provide input to the node, and can also be connected together if needed. The NodeGraph and NodeEditor
> each display only a subset of the available plugs for ease of use, and informally we may tend to
> refer to them as "connections" or "settings" respectively, but more formally they are all **plugs**.
> This fact will become more relevant in advanced tutorials involving expressions and scripting.

Rendering a first image
-----------------------

Now that we have the layout of our scene defined, we want to do a quick test render to check everything is
working as expected. To do that we need to lay down some more nodes to define our render settings.

- Select the Group node in the NodeGraph.
- Create a StandardOptions node (_/Scene/Globals/StandardOptions_). Note that it has been automatically
  connected to the output of the Group, and selected.
- Create an AppleseedOptions node (_/Appleseed/Options_). Note that it has been automatically connected to
  the output of the StandardOptions node and selected.
- Create an Outputs node (_Scene/Globals/Outputs_). This too will be automatically added to the end of
  the chain.
- Create an InteractiveAppleseedRender node (_/Appleseed/InteractiveRender/_) to complete the chain.
- Create a Display node (_/Image/Source/Display_) node. This doesn't need any input connections - just
  place it to one side of the InteractiveAppleseedRender node.

![Render settings](images/renderSettings.png)

Even though we need only have one camera, we still need to tell Gaffer that we wish to render with it, rather than with a default camera :

- Select the StandardOptions node.
- Use the NodeEditor to specify the camera.
	- Open the Camera section by _Left-Clicking_ on it.
	- _Left-Click_ the switch to enable the camera setting.
	- Type `/group/camera` into the camera text field.

Next we need to define what images we want to output :

- Select the Outputs node.
- Use the NodeEditor to add an output, by _Left-Clicking_ on the ![Plus icon](images/plus.png) and choosing the _/Interactive/Beauty_ item from the popup menu.

Now we can start the renderer :

- Select the InteractiveAppleseedRender node.
- Use the NodeEditor to set the renderer state to running.

And finally we can view the result :

- Select the Display node.
- Move the mouse into the Viewer and press 'f' to frame the image.

![First render](images/firstRender.png)

It's hardly worthy of an Oscar, but we've successfully made our first image, and are in a good place to start adding some lighting and shading.

Organising the user interface
-----------------------------

Before we dive into lighting and shading though, let's take a brief detour to reorganise the user interface a little better for our workflow. As we've already learned, editors such as the Viewer, NodeEditor and SceneHierarchy always show the currently selected node by default. This isn't always convenient, because often we want to edit one node while viewing the effects in another. This can be achieved by "pinning" specific nodes into an editor, so that they stay there regardless of the selection :

- Select the InteractiveAppleseedRender node by _Left-Clicking_ on it in the NodeGraph.
- Locate the  pinning icon ![Pinning](images/targetNodesUnlocked.png) at the top right
  of the Viewer panel, and _Left-Click_ to activate it.
- Deselect the InteractiveAppleseedRender node by _Left-Clicking_ in empty space in the NodeGraph.
- Note that the Viewer is still showing the pinned node.

It'd be useful to pin the same node into the SceneHierarchy, so let's use a shortcut to do that :

- _Middle-Drag_ the InteractiveAppleseedRender node from the NodeGraph panel into the
  SceneHierarchy panel.
- Note that the SceneHierarchy is now showing our node, and the pinning icon has highlighted
  to notify us of the pinning ![Pinning](images/targetNodesLocked.png).

Now we're free to select any node we want to edit it in the NodeEditor, but will always be viewing the results
downstream, in our final scene. It's a pity that we're no longer viewing our Display node containing the rendered
image though, so let's rectify that.

- Locate the layout button ![Layout](images/layoutButton.png) in the top right of the Viewer panel, and _Left-Click_ to show the layout menu.
- Choose the _Viewer_ menu item to add a new Viewer.
- _Middle-Drag_ the Display node into the new Viewer to pin it there.

This allows us to switch between the 3d scene and the rendered image using the tabs at the top of the viewer panel. Now we've
got everything arranged to our liking, we're finally ready to go ahead and start shading some pixels.

Assigning a shader
------------------

> Tip : As we're about to add to our collection of nodes in the NodeGraph, we might need to move around
> around and zoom in and out to navigate between them. This is achieved in the same way as navigating
> in the Viewer, by holding down _Alt_ and _dragging_ :
>
> - Hold down _Alt_ and _Left-Drag_ to move around.
> - Hold down _Alt_ and _Right-Drag_ to zoom in and out.
> - Alternatively, use the _scroll wheel_ to zoom in and out.

It makes sense to think of our node graph as being composed of three distinct phases - generating the geometry, applying the lighting and shading, and finally rendering. Let's create some empty space in the centre of the graph so that we have somewhere to insert the nodes for our lighting and shading phase.

- In the NodeGraph, _Left-Drag_ over the lower five nodes to select them.
- _Left-Drag_ on one of the nodes to move them all down to leave some space in the middle.
- Use the _scroll wheel_ or hold down _Alt_ and _Right-Drag_ to zoom out and frame the whole node graph.

![Making space](images/renderSettingsWithGap.png)

Now we have some space we can drop our shading nodes into.

- Make a Disney material (_/Appleseed/Shader/Material/As_Disney_Material_)
- Edit it using the NodeEditor
	- Set the **Specular** to `0.6`
	- Set the **Roughness** to `0.35`
- Keeping the Disney material selected, create a ShaderAssignment (_/Scene/Attributes/ShaderAssignment_). Note that it has been automatically connected to the material.
- _Left-Drag_ the ShaderAssignment onto the connection between the Group and StandardOptions nodes
  to insert it into the stream.

![First shader assignment](images/firstShaderAssignment.png)

Note that the inputs and outputs on the material node flow from left to right. In Gaffer, by convention, scene data flows from top to bottom and shading networks flow from left to right. The ShaderAssignment node takes the material flowing in from the left and assigns it to the geometry flowing in from the top. This hasn't done much to improve our render though - now that we have a proper material assigned, we need to to create a light so we can see it.

Creating a light
----------------

We'll use an environment light so that we can get up and running quickly without needing to spend a lot of time tuning multiple lights.

- Create a PhysicalSky node (_/Appleseed/Environment/PhysicalSky_)
- Edit it using the NodeEditor
	- Set the **Sun Phi Angle** to `100`
	- Set the **Luminance** to `2.5`

This node outputs a new scene containing a single light. As we did before with the camera, we now need to add the light to the main scene so that it flows down to the render node. The quickest way of doing this would be to connect it in to the next available input on the Group node, but this time we'll take a different approach. Often when collaborating with others, you'll receive scenes which already contain the geometry and cameras, and it'll be inconvenient to use a Group node because it introduces a new level into the scene hierarchy. In these cases, we can use a Parent node to insert a new child anywhere in the input scene.

- Deselect the PhysicalSky node
- Create a Parent node (_/Scene/Hierarchy/Parent_)
- _Left-Drag_ it between the Group and ShaderAssignment nodes to insert it.
- Enter `/` in the Parent field in the NodeEditor, so that we'll be parenting the light directly under the scene root.
- Connect the output of the light node into the second (child) input of the Parent node.

![Parenting Node Graph](images/parentingNodeGraph.png)

We should have successfully inserted the light into the scene hierarchy, without affecting the structure of the rest of the scene.

![Parenting Scene Hierarchy](images/parentingSceneHierarchy.png)

Now we need to enable environment lighting in Appleseed for our light to take effect.

- Edit the AppleseedOptions node in the NodeEditor
- Open the Environment section
- Turn on the **Environment Light** switch
- Enter `/light` into the text field

Our render should now be in the process of updating with some basic lighting.

![First Lighting](images/firstLighting.png)

Adding some textures
--------------------

Our little chap is looking a bit monochrome, so let's assign some textures to cheer him up :

- Create an Appleseed texture node (_/Appleseed/Shaders/Texture2d/As_color_texture_)
- Edit it using the NodeEditor
	- Enter `${GAFFER_ROOT}/resources/gafferBot/textures/base_COL/base_COL_` into the **Filename** field.
	- Set the **UDIM** field to `mari`.
- Using the NodeGraph, Connect the **ColorOut** output into the **BaseColor** input of the disney material.

![Textured](images/textures.png)

The render should now be in the process of updating to show the results of our edit.

Filtering a shader assignment
-----------------------------

Everything is looking rather uniform right now, because so far we've used one material for everything. Let's assign a metallic material to a few objects to add some interest.

- Make a Disney material as before (_/Appleseed/Shader/Material/As_Disney_Material_)
- Edit it using the NodeEditor
	- Set **Metallic** to `0.8`
	- Set **Roughness** to `0.4`
- Create a Shader assignment as before (_/Scene/Attributes/ShaderAssignment_), and make sure the
  new material is connected into it.
- Insert the new ShaderAssignment into the connection below the previous one.

![Second shader assignment](images/secondShaderAssignment.png)

The viewer should update to show the new assignment.

![Second shader assignment render](images/secondShaderAssignmentRender.png)

Oops. Because the new ShaderAssignment is downstream from the first one, it has overridden the first assignment, and now _everything_ is chrome. We need a way of limiting the objects that the second ShaderAssignment is applied to - in Gaffer this is referred to as _filtering_ the ShaderAssignment, and it is done using special Filter nodes :

- Create a PathFilter node (_/Scene/Filters/PathFilter_). This chooses which objects to affect based on their names.
- Use the NodeEditor to add `/group/GAFFERBOT/C_torso_GRP/C_head_GRP/C_head_CPT/L_ear001_REN` to the **Paths**. This is the
  full name of the left ear of the robot, as you see it listed in the SceneHierarchy.
- Connect the output of the PathFilter into the filter input on the right hand side of the ShaderAssignment1 node.

![Filter connection](images/filterConnection.png)

The render should now update, with the chrome shader applied only to the ear.

Editing the filter
------------------

We might like to apply the chrome shader to more objects, but it'll be a bit tedious to continue entering object names manually as
we just did. First, let's use Gaffer's pattern matching to pick both ears :

- Select the PathFilter node to edit it in the NodeEditor
- Delete `L_ear001_REN` at the end of the path we entered previously, and replace it with `*_ear*`

The `*` automatically matches any sequence of characters, so the filter will now match the left _and_ the right ears. We're still some way from chromifying everything we want to though, so let's take a look at using a more visual approach.

- In the Viewer panel, switch to the tab containing the 3d view.
- Hold down _Alt_ and use the camera navigation controls to frame the face.
- Select the eyebrows by _Left-Clicking_ on them.
- Add the mouth to the selection by _Shift + Left-Clicking_ on it.

![Face selection](images/faceSelection.png)

- Start a _Left-Drag_ from the selected objects. The cursor should change to ![Objects Image](images/objects.png) to indicate you are dragging them.
- Continue the drag into the NodeGraph and hover over the PathFilter node.
- Hold _Shift_ to indicate that you wish to add to the PathFilter rather than replace the
  existing contents. The cursor will change from ![Replace Objects](images/replaceObjects.png) to ![Add Objects](images/addObjects.png) to indicate this.
- Finally, drop the objects to add them to the PathFilter.

Just as objects can be added by holding _Shift_, they can be removed by holding _Control_. With this in mind, we can add and remove objects from the shader assignment to taste, switching tabs to view the rendered image as it updates. After adding the grabbers and bolts to the filter, we should arrive at an image something like the following.

![Final render](images/finalRender.png)

Recap
-----

There is no doubt still a lot that could be done to improve our render, but alas, at this point your faithful author finds himself at the limits of his meagre artistic ability. We've seen how Gaffer allows caches to be loaded and navigated lazily on demand. We've seen how to create lights and cameras and combine them into a scene for rendering. We've demonstrated how to rearrange the UI for improved interaction, and we've seen how shading networks can be constructed and assigned.

Hopefully this provides a solid basis for your own further exploration, which will no doubt be less creatively challenged. You might like to start by exploring the addition of more lights, found in the _/Appleseed/Lights_ node menu, or by creating more expansive shading networks using the shaders found in the _/Appleseed/Shaders_ node menu.

[1]: ../../Installation/index.md
[2]: ../../Reference/NodeReference/GafferScene/SceneReader.md
[3]: ../../Reference/UIReference/NodeGraph.md
[4]: ../../Reference/UIReference/Viewer.md
