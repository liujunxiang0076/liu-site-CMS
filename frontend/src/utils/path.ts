
/**
 * Resolves the target directory path for creating a new file/folder.
 * 
 * @param selectedNode - The currently selected node in the file tree.
 * @param rootPath - The default root path if no node is selected.
 * @returns The resolved directory path.
 */
export const resolveTargetDir = (selectedNode: any | null, rootPath: string = 'src/posts'): string => {
  // 1. If nothing is selected, return root path
  if (!selectedNode) {
    return rootPath;
  }

  // 2. If a folder is selected, return its path
  if (selectedNode.type === 'folder') {
    return normalizePath(selectedNode.path);
  }

  // 3. If a file is selected, return its parent directory
  if (selectedNode.type === 'file') {
    return getParentPath(selectedNode.path);
  }

  // Fallback (should not happen given types)
  return rootPath;
};

/**
 * Normalizes a path string to ensure consistent separators and no trailing slashes.
 * Currently assumes forward slashes as used in the virtual FS.
 */
export const normalizePath = (path: string): string => {
  if (!path) return '';
  // Replace backslashes with forward slashes for consistency
  let normalized = path.replace(/\\/g, '/');
  // Remove trailing slash if present (unless it's just "/")
  if (normalized.length > 1 && normalized.endsWith('/')) {
    normalized = normalized.slice(0, -1);
  }
  return normalized;
};

/**
 * Gets the parent directory of a given path.
 */
export const getParentPath = (path: string): string => {
  const normalized = normalizePath(path);
  const lastSlashIndex = normalized.lastIndexOf('/');
  
  if (lastSlashIndex === -1) {
    return ''; // Or return '.' depending on requirement, but empty implies top level relative
  }
  
  return normalized.substring(0, lastSlashIndex);
};

/**
 * Joins path segments securely.
 */
export const joinPath = (...segments: string[]): string => {
  return segments
    .map(normalizePath)
    .filter(Boolean)
    .join('/');
};
