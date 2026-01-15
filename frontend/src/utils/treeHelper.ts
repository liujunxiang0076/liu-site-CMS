
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
