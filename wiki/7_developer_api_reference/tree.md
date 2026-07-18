# Module: `tree`\n\n## Classes\n### `TreeDescriptor`\n\n### `TreeEntry`\n\n## Public Functions\n### `parse_descriptor()`\n\n### `read_leaf_entries()`\nTraverse a bounds-checked BOM B+ tree and return its leaf records.

Node reference pairs are ``(value block, key block)``. In leaves they are
the user value/key blocks. In internal nodes the value reference is a child
node and the key reference is its separator key. Apple-generated internal
nodes list children in traversal order; leaf forward/backward links are not
needed for a root-based walk.\n\n