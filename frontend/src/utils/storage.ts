import localforage from 'localforage';
import CryptoJS from 'crypto-js';

const STORE_NAME = 'cms_local_articles';
// 在生产环境中，密钥应该由用户输入或后端下发，这里为了演示离线能力使用固定密钥
const SECRET_KEY = 'cms_offline_secret_key_v1'; 

localforage.config({
  name: 'LiuSiteCMS',
  storeName: STORE_NAME
});

export interface LocalArticle {
  id: string; // UUID
  title: string;
  content: string;
  path: string; // 虚拟路径，例如 src/posts/2026/hello.md
  updatedAt: number;
  isSynced: boolean; // 是否已同步到云端
}

// 加密
const encrypt = (data: any): string => {
  try {
    return CryptoJS.AES.encrypt(JSON.stringify(data), SECRET_KEY).toString();
  } catch (e) {
    console.error('Encryption failed', e);
    return '';
  }
};

// 解密
const decrypt = (ciphertext: string): any => {
  try {
    const bytes = CryptoJS.AES.decrypt(ciphertext, SECRET_KEY);
    const decryptedData = bytes.toString(CryptoJS.enc.Utf8);
    if (!decryptedData) return null;
    return JSON.parse(decryptedData);
  } catch (e) {
    console.error('Decryption failed', e);
    return null;
  }
};

/**
 * 保存文章到本地存储（加密）
 */
export const saveLocalArticle = async (article: LocalArticle): Promise<void> => {
  try {
    const encrypted = encrypt(article);
    if (!encrypted) throw new Error('加密失败');
    
    await localforage.setItem(article.id, encrypted);
  } catch (error: any) {
    // 捕获存储空间不足错误
    if (error.name === 'QuotaExceededError' || error.name === 'NS_ERROR_DOM_QUOTA_REACHED') {
       throw new Error('本地存储空间不足，请清理浏览器缓存或删除旧文章');
    }
    throw new Error('本地保存失败: ' + (error.message || '未知错误'));
  }
};

/**
 * 获取单篇文章
 */
export const getLocalArticle = async (id: string): Promise<LocalArticle | null> => {
  try {
    const item = await localforage.getItem<string>(id);
    if (!item) return null;
    return decrypt(item);
  } catch (e) {
    console.error('Failed to load local article', e);
    return null;
  }
};

/**
 * 删除本地文章
 */
export const removeLocalArticle = async (id: string): Promise<void> => {
  await localforage.removeItem(id);
};

/**
 * 获取所有本地文章列表
 */
export const getAllLocalArticles = async (): Promise<LocalArticle[]> => {
  try {
    const keys = await localforage.keys();
    const articles: LocalArticle[] = [];
    for (const key of keys) {
      const article = await getLocalArticle(key);
      if (article) articles.push(article);
    }
    // 按更新时间倒序
    return articles.sort((a, b) => b.updatedAt - a.updatedAt);
  } catch (e) {
    console.error('Failed to load all local articles', e);
    return [];
  }
};
