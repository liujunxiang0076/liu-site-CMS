
import dayjs from 'dayjs';

/**
 * 比较两个内容是否实质上不同
 * 忽略空白字符、换行符差异
 */
export const hasSubstantialDifference = (contentA: string, contentB: string): boolean => {
  if (!contentA && !contentB) return false;
  if (!contentA || !contentB) return true;

  // 1. 移除所有空白字符后比较
  const cleanA = contentA.replace(/\s+/g, '');
  const cleanB = contentB.replace(/\s+/g, '');
  
  if (cleanA === cleanB) return false;

  // 2. 如果仅仅是 Frontmatter 中的 updated/date 字段不同，视为相同
  // 简单的正则检查，提取 frontmatter
  const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
  const matchA = contentA.match(frontmatterRegex);
  const matchB = contentB.match(frontmatterRegex);

  if (matchA && matchB) {
    // 如果主体内容（去除 frontmatter 后）相同
    const bodyA = contentA.replace(frontmatterRegex, '').trim();
    const bodyB = contentB.replace(frontmatterRegex, '').trim();

    if (bodyA === bodyB) {
      // 进一步检查 frontmatter
      // 这里可以解析 yaml，为了简单起见，我们假设只有日期字段导致的差异是可以忽略的
      // 实际场景中，可能需要更复杂的 yaml 解析
      // 暂时策略：如果主体内容一致，且总长度差异极小（< 20 chars，通常是时间戳变化），则认为一致
      if (Math.abs(contentA.length - contentB.length) < 20) {
        return false;
      }
    }
  }

  return true;
};

/**
 * 记录一致性检查日志
 */
export const logConsistencyCheck = (
  path: string, 
  result: 'MATCH' | 'MISMATCH' | 'IGNORED', 
  details?: string
) => {
  const timestamp = dayjs().format('YYYY-MM-DD HH:mm:ss');
  console.groupCollapsed(`[Consistency Check] ${path} - ${result} at ${timestamp}`);
  if (details) console.log(details);
  console.groupEnd();
};
