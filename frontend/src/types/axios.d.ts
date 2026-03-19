import 'axios'

declare module 'axios' {
  interface AxiosRequestConfig {
    skipErrorHandle?: boolean
  }

  interface InternalAxiosRequestConfig {
    skipErrorHandle?: boolean
  }
}
