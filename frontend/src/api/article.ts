import apiClient, { type ApiResponse } from './client'
import { ApiCache } from '../utils/apiCache'

export interface ArticleSaveParams {
  path: string
  content: string
  sha: string
  title?: string
  message?: string
}

export const articleApi = {
  // 获取数据版本
  getVersion: () => apiClient.get<any, ApiResponse<{ version: string }>>('/version'),

  // 获取文章列表（带缓存策略）
  getList: async (forceRefresh = false) => {
    const CACHE_KEY = 'cms_article_list';
    
    if (!forceRefresh) {
      const cached = await ApiCache.get<any[]>(CACHE_KEY);
      if (cached) {
        try {
          // 双重校验：检查后端版本
          const vRes = await apiClient.get<any, ApiResponse<{ version: string }>>('/version');
          if (vRes.code === 200 && vRes.data.version === cached.version) {
            console.log('Frontend Cache Hit: List');
            return { code: 200, msg: 'success', data: cached.data, total: cached.data.length, fromCache: true };
          }
        } catch (e) {
          console.warn('Version check failed, using cache fallback', e);
          return { code: 200, msg: 'success (offline)', data: cached.data, total: cached.data.length, fromCache: true };
        }
      }
    }

    // 穿透到后端
    const res = await apiClient.get<any, ApiResponse<any[]>>('/articles', { params: { force_refresh: forceRefresh } });
    
    // 成功后写入缓存
    if (res.code === 200) {
      // 异步获取最新版本号用于缓存标记
      apiClient.get('/version').then(vRes => {
        if (vRes.data && vRes.data.version) {
          ApiCache.set(CACHE_KEY, res.data, vRes.data.version);
        }
      }).catch(console.error);
    }
    return res;
  },

  // 获取文章详情（带缓存策略）
  getDetail: async (path: string, forceRefresh = false) => {
    const CACHE_KEY = `cms_article_${path}`;
    
    if (!forceRefresh) {
      const cached = await ApiCache.get<{ path: string, title: string, content: string }>(CACHE_KEY);
      if (cached) {
        try {
          const vRes = await apiClient.get('/version');
          if (vRes.status === 200 && vRes.data.version === cached.version) {
             console.log('Frontend Cache Hit: Detail', path);
             // 注意：这里缺少 SHA，如果依赖 SHA 进行编辑可能需要重新考虑。
             // 但通常 SHA 包含在 content_file 元数据里。
             // 后端 getDetail 返回 data 和 sha 字段。
             // 我们缓存时只存了 data? 需要把 response 整体缓存或者把 SHA 塞进去。
             // 让我们修改 ApiCache 存储整个 response data 部分（包含 sha?）
             // 后端返回结构: { data: {...}, sha: "..." }
             // 所以我们缓存 cached.data 应该是整个 response.data ? 不，response.data 是 content.
             // response 顶层有 sha.
             // 简单起见，我们还是请求一次吧，详情页通常需要最新的 SHA 来避免冲突。
             // 或者：如果版本没变，SHA 肯定没变。
             // 我们需要把 SHA 也缓存起来。
             return { ...cached.data, fromCache: true }; 
          }
        } catch (e) {
           return { ...cached.data, fromCache: true };
        }
      }
    }

    const res = await apiClient.get<any, ApiResponse<{
      path: string;
      title: string;
      content: string;
    }>>('/article/detail', { params: { path, force_refresh: forceRefresh } });

    if (res.code === 200) {
      apiClient.get('/version').then(vRes => {
        if (vRes.status === 200) {
           // 缓存整个 res 结构不太好，因为类型不匹配。
           // 构造一个包含 data 和 sha 的对象存入
           const cacheData = { 
               code: 200, 
               msg: 'success', 
               data: res.data, 
               sha: res.sha 
           };
           ApiCache.set(CACHE_KEY, cacheData, vRes.data.version);
        }
      }).catch(console.error);
    }
    return res;
  },

  // 保存文章
  save: async (data: ArticleSaveParams) => {
    const res = await apiClient.post<any, ApiResponse<{ sha: string }>>('/article/save', data);
    if (res.code === 200) {
      // 激进失效策略
      await ApiCache.remove('cms_article_list');
      await ApiCache.remove(`cms_article_${data.path}`);
    }
    return res;
  },

  // 重命名
  rename: async (oldPath: string, newPath: string, sha: string) => {
    const res = await apiClient.post<any, ApiResponse<{ sha: string }>>('/article/rename', { old_path: oldPath, new_path: newPath, sha });
    if (res.code === 200) {
      await ApiCache.remove('cms_article_list');
      await ApiCache.remove(`cms_article_${oldPath}`);
      await ApiCache.remove(`cms_article_${newPath}`);
    }
    return res;
  },

  // 删除文章
  delete: async (path: string, sha: string, message?: string) => {
    const res = await apiClient.post<any, ApiResponse<null>>('/article/delete', { path, sha, message });
    if (res.code === 200) {
      await ApiCache.remove('cms_article_list');
      await ApiCache.remove(`cms_article_${path}`);
    }
    return res;
  },

  // 图片上传（如果是直接由 Vditor 调用，保持原样；如果手动调用可写在这）
  uploadImage: (formData: FormData) => 
    apiClient.post<any, ApiResponse<{ url: string }>>('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  // 改变密码
  changePassword: async (data: { currentPassword: string; newPassword: string }) => {
    // 注意：apiClient 已经配置了 baseURL 为 /api，所以这里不要再加 /api 前缀
    const res = await apiClient.post<any, ApiResponse<null>>('/password/change', {
      current_password: data.currentPassword,
      new_password: data.newPassword
    })
    if (res.code === 200) {
      // 密码改变后，需要重新登录
      await ApiCache.remove('cms_user')
    }
    return res
  }
}
