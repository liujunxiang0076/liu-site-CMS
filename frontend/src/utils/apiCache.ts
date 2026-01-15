import localforage from 'localforage';

const CACHE_STORE_NAME = 'cms_api_cache';
const apiCacheStore = localforage.createInstance({
  name: 'LiuSiteCMS',
  storeName: CACHE_STORE_NAME
});

export interface CacheItem<T> {
  data: T;
  timestamp: number;
  ttl: number; // milliseconds
  version: string; // data version (commit sha)
}

export const ApiCache = {
  async get<T>(key: string): Promise<CacheItem<T> | null> {
    try {
      const item = await apiCacheStore.getItem<CacheItem<T>>(key);
      if (!item) return null;
      
      const now = Date.now();
      if (now - item.timestamp > item.ttl) {
        await apiCacheStore.removeItem(key);
        return null;
      }
      
      return item;
    } catch (e) {
      console.error('Cache read error', e);
      return null;
    }
  },

  async set<T>(key: string, data: T, version: string, ttl: number = 3600 * 1000): Promise<void> {
    try {
      const item: CacheItem<T> = {
        data,
        timestamp: Date.now(),
        ttl,
        version
      };
      await apiCacheStore.setItem(key, item);
    } catch (e) {
       console.error('Cache write error', e);
    }
  },

  async remove(key: string): Promise<void> {
    await apiCacheStore.removeItem(key);
  },

  async clear(): Promise<void> {
    await apiCacheStore.clear();
  }
};
