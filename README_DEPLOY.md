# 全流程部署指南

## 常见问题解决

### 🔴 内存不足 (JavaScript heap out of memory)
如果你的服务器内存较小（如 1GB 或 512MB），在构建前端时可能会报错。
请运行项目根目录下的 `enable_swap.sh` 脚本来开启虚拟内存：

```bash
# 在服务器上执行
chmod +x enable_swap.sh
./enable_swap.sh
```
开启 Swap 后，再次运行更新脚本即可。

---

## 0. 服务器环境准备
... (保持原有内容)
