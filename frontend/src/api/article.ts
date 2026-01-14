import apiClient from './client'

export interface ArticleSaveParams {
  path: string
  content: string
  sha: string
  title?: string
  message?: string
}

export const articleApi = {
  // 获取文章列表
  getList: () => apiClient.get('/articles'),

  // 获取文章详情
  getDetail: (path: string) => apiClient.get('/article/detail', { params: { path } }),

  // 保存文章
  save: (data: ArticleSaveParams) => apiClient.post('/article/save', data),

  // 重命名
  rename: (oldPath: string, newPath: string, sha: string) => 
    apiClient.post('/article/rename', { old_path: oldPath, new_path: newPath, sha }),

  // 删除文章
  delete: (path: string, sha: string) => 
    apiClient.post('/article/delete', { path, sha }),

  // 图片上传（如果是直接由 Vditor 调用，保持原样；如果手动调用可写在这）
  uploadImage: (formData: FormData) => 
    apiClient.post('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
}
