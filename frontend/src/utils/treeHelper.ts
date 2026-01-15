
/**
 * Finds a node in the tree by its path.
 * Returns the node object (for folders) or the array of nodes (for root).
 */
export const findNodeByPath = (nodes: any[], path: string): any | any[] | null => {
  // Special case for root
  if (path === 'src/posts' || path === 'src') {
    return nodes;
  }

  for (const node of nodes) {
    if (node.path === path) {
      return node;
    }
    if (node.children) {
      const found = findNodeByPath(node.children, path);
      if (found) return found;
    }
  }
  return null;
};

/**
 * Gets the children array of a target path.
 */
export const getChildrenByPath = (nodes: any[], path: string): any[] => {
  const result = findNodeByPath(nodes, path);
  if (Array.isArray(result)) {
    return result;
  }
  if (result && result.type === 'folder') {
    return result.children || [];
  }
  return [];
};

/**
 * Removes a node from the tree by ID or Path.
 * Returns true if removed, false otherwise.
 */
export const removeNodeFromTree = (nodes: any[], identifier: { id?: string, path?: string }): boolean => {
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    
    // Check match:
    // 1. If ID is provided, strictly match by ID (for local drafts)
    // 2. If no ID provided, match by Path (for remote files)
    // 3. Fallback: if node has ID but we only have path, still check path just in case
    const match = (identifier.id && node.id === identifier.id) || 
                  (identifier.path && node.path === identifier.path);
    
    if (match) {
      nodes.splice(i, 1);
      return true;
    }

    if (node.children && node.children.length > 0) {
      if (removeNodeFromTree(node.children, identifier)) {
        return true;
      }
    }
  }
  return false;
};
