import axios from 'axios'
import { ElMessage } from 'element-plus'

const apiClient = axios.create({
  baseURL: '/api', // 所有的请求都会加上 /api 前缀
  timeout: 10000,
})

// 响应拦截器：统一处理错误提示
apiClient.interceptors.response.use(
  (response) => {
    const res = response.data;
    
    switch (res.code) {
      case 200:
        return res; // 成功直接返回
      case 401:
        ElMessage.warning('登录已过期，请重新登录');
        // router.push('/login'); 
        break;
      case 404:
        ElMessage.error('找不到相关资源');
        break;
      case 502:
        ElMessage.error('GitHub 接口响应超时，请检查网络或配置');
        break;
      default:
        ElMessage.error(res.msg || '未知逻辑错误');
    }
    return Promise.reject(new Error(res.msg));
  },
  (error) => {
    // 这里的 error 处理的是网络层面的（如 500 服务器崩了或断网）
    ElMessage.error('服务器响应失败，请联系管理员');
    return Promise.reject(error);
  }
);

export default apiClient
