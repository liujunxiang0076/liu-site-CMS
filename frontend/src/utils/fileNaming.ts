
/**
 * Calculates the next available 2-digit sequence string (01-99).
 * Returns null if limit is reached (99).
 * 
 * @param existingFileNames - List of existing filenames in the directory
 */
export const getNextSequence = (existingFileNames: string[]): string | null => {
  const pattern = /^(\d{2})_/;
  const usedSequences = new Set<number>();

  existingFileNames.forEach(name => {
    const match = name.match(pattern);
    if (match) {
      usedSequences.add(parseInt(match[1], 10));
    }
  });

  for (let i = 1; i <= 99; i++) {
    if (!usedSequences.has(i)) {
      return i.toString().padStart(2, '0');
    }
  }

  return null;
};

/**
 * Formats the final filename with sequence.
 */
export const formatFileName = (sequence: string, name: string): string => {
  return `${sequence}_${name}`;
};

/**
 * Sorts nodes by name in ascending order.
 * Returns a new sorted array.
 */
export const sortNodes = (nodes: any[]): any[] => {
  return [...nodes].sort((a, b) => {
    return a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' });
  });
};
