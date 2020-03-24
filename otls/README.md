# How to update the Alembic node properties

With new releases for Houdini, new properties get added to the Mantra node, and some get taken away.
These step will guide you through the process of updating the otl file.

1. Ensure you have locally cloned this repo, and then set the `tk-houdini-alembicnode` location in your config to point at the local repo using a dev descriptor.

2. Launch Houdini from Shotgun using the Houdini version you wish to check for parameter updates on.1

3. Open a new scene on an Asset so that the Mantra node is loaded.1

4. Run the following script in the Houdini Python shell.
    ```python
    import hou
    import pprint

    rop = hou.node('/out')
    alembic_node = rop.createNode('alembic')

    sgtk_alembic_node = rop.createNode('sgtk_alembic')

    alembic_props = set([str(p.name()) for p in alembic_node.parms()])
    sgtk_alembic_props = set([str(p.name()) for p in sgtk_alembic_node.parms()])
    diff = alembic_props - sgtk_alembic_props

    pprint.pprint(diff)
    ```
    This should create a standard Mantra node and sgtk Mantra node, and print out the list of properties that the sgtk node is missing.

5. Now select the sgtk Mantra node from the `out/` network.

6. In the parameter window for the selected node, click on the cog icon, just to the right of the node name, and choose "Type properties..."

7. In the newly opened Window, make sure you are in the parameters tab. Now it's case of moving any missing parameters
highlighted when running the script over from the Left side **Render Properties** tab > mantra node to the right side.
To ensure that they get placed in the correct folder and order, compare against the standard Mantra node positions.
Some nodes shouldn't be copied over as their functionality is handled by sgtk replacement logic.
   ```
   'images1',
   'output1',
   'output61',
   'sampling1',
   'vm_dsmfilename',
   'vm_inlinestorage',
   'vm_tmplocalstorage',
   'vm_tmpsharedstorage'
   ```

   Some

![](./)
