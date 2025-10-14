# Code Reader Kubernetes 部署说明

本项目完全通过 GitHub Actions CI/CD 自动部署到 Kubernetes 集群，使用 NodePort 方式暴露服务。

## 📋 文件结构

```
k8s/
├── 00-namespace.yaml    # 命名空间配置
├── 01-frontend.yaml     # 前端 Deployment 和 Service (NodePort)
├── 02-backend.yaml      # 后端 Deployment 和 Service (NodePort)
├── 03-config.yaml       # ConfigMap 配置
├── 04-pvc.yaml          # 持久化存储配置
├── 05-rbac.yaml         # RBAC 权限配置
└── README.md            # 本文档
```

## 🚀 部署流程

### 自动部署（推荐）

通过 GitHub Actions 自动部署：

#### 1. 前端部署
```bash
# 创建前端版本标签
git tag frontend-v1.0.0
git push origin frontend-v1.0.0
```

#### 2. 后端部署
```bash
# 创建后端版本标签
git tag backend-v1.0.0
git push origin backend-v1.0.0
```

#### 3. 测试环境部署
```bash
# 推送到 main 分支自动触发测试部署
git push origin main

# 或创建 Pull Request
```

### 手动部署（备用）

如果需要手动部署，使用 kubectl：

```bash
# 1. 配置 kubectl 连接到集群
kubectl config set-cluster k8s-cluster --server=https://your-k8s-api:6443 --insecure-skip-tls-verify=true
kubectl config set-credentials github-actions --token=your-k8s-token
kubectl config set-context default --cluster=k8s-cluster --user=github-actions
kubectl config use-context default

# 2. 部署所有资源
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/03-config.yaml
kubectl apply -f k8s/04-pvc.yaml
kubectl apply -f k8s/05-rbac.yaml
kubectl apply -f k8s/01-frontend.yaml
kubectl apply -f k8s/02-backend.yaml

# 3. 检查部署状态
kubectl get pods -n code-reader
kubectl get services -n code-reader
```

## 🔧 配置要求

### GitHub Secrets

在 GitHub 仓库的 Settings > Secrets and variables > Actions 中配置：

| 密钥名称 | 说明 | 示例 |
|---------|------|------|
| `K8S_TOKEN` | Kubernetes 访问令牌 | `eyJhbGci...` |
| `K8S_API_URL` | Kubernetes API 服务器地址 | `https://your-k8s-api:6443` |

### 获取 K8S_TOKEN

```bash
# 创建 ServiceAccount
kubectl create serviceaccount github-actions -n code-reader

# 创建 RoleBinding
kubectl create rolebinding github-actions-binding \
  --clusterrole=admin \
  --serviceaccount=code-reader:github-actions \
  --namespace=code-reader

# 获取 Token
kubectl create token github-actions -n code-reader --duration=87600h
```

## 🌐 访问服务

使用 NodePort 方式访问服务：

### 生产环境
- **前端**: `http://<节点IP>:30080`
- **后端**: `http://<节点IP>:30800`

### 测试环境
- **前端**: `http://<节点IP>:30081`
- **后端**: `http://<节点IP>:30801`

### 获取节点 IP

```bash
# 获取所有节点
kubectl get nodes -o wide

# 或使用 Service 信息
kubectl get services -n code-reader
```

## 📝 ConfigMap 配置

在部署前，需要配置 `k8s/03-config.yaml` 中的环境变量：

```bash
# 编辑 ConfigMap
kubectl edit configmap code-reader-config -n code-reader

# 或直接修改文件后应用
kubectl apply -f k8s/03-config.yaml
```

ConfigMap 使用单个 `env` 键存储所有配置（JSON 格式）：

```yaml
data:
  env: |
    {
      "DATABASE_URL": "mysql://user:pass@host:3306/db",
      "OPENAI_API_KEY": "sk-xxx",
      "GITHUB_TOKEN": "ghp_xxx"
    }
```

## 🔍 监控和调试

### 查看部署状态

```bash
# 查看 Pods
kubectl get pods -n code-reader
kubectl get pods -n code-reader-test

# 查看 Services
kubectl get services -n code-reader
kubectl get services -n code-reader-test

# 查看 PVC
kubectl get pvc -n code-reader
```

### 查看日志

```bash
# 前端日志
kubectl logs -f deployment/code-reader-frontend -n code-reader

# 后端日志
kubectl logs -f deployment/code-reader-backend -n code-reader

# 测试环境日志
kubectl logs -f deployment/code-reader-frontend-test -n code-reader-test
kubectl logs -f deployment/code-reader-backend-test -n code-reader-test
```

### 调试 Pod

```bash
# 进入 Pod
kubectl exec -it <pod-name> -n code-reader -- /bin/sh

# 查看 Pod 详情
kubectl describe pod <pod-name> -n code-reader

# 查看事件
kubectl get events -n code-reader --sort-by='.lastTimestamp'
```

## 🔄 更新部署

### 通过 CI/CD 自动更新（推荐）

创建新的版本标签即可自动触发更新：

```bash
# 更新前端
git tag frontend-v1.0.1
git push origin frontend-v1.0.1

# 更新后端
git tag backend-v1.0.1
git push origin backend-v1.0.1
```

### 手动更新镜像

```bash
# 更新前端镜像
kubectl set image deployment/code-reader-frontend \
  code-reader-frontend=ghcr.io/your-username/code-reader-frontend:new-tag \
  -n code-reader

# 更新后端镜像
kubectl set image deployment/code-reader-backend \
  code-reader-backend=ghcr.io/your-username/code-reader-backend:new-tag \
  -n code-reader

# 查看更新状态
kubectl rollout status deployment/code-reader-frontend -n code-reader
kubectl rollout status deployment/code-reader-backend -n code-reader
```

### 回滚部署

```bash
# 查看部署历史
kubectl rollout history deployment/code-reader-backend -n code-reader

# 回滚到上一个版本
kubectl rollout undo deployment/code-reader-backend -n code-reader

# 回滚到指定版本
kubectl rollout undo deployment/code-reader-backend -n code-reader --to-revision=2
```

## 🗑️ 清理资源

```bash
# 删除生产环境
kubectl delete namespace code-reader

# 删除测试环境
kubectl delete namespace code-reader-test

# 或分别删除资源
kubectl delete -f k8s/02-backend.yaml
kubectl delete -f k8s/01-frontend.yaml
kubectl delete -f k8s/06-rbac.yaml
kubectl delete -f k8s/04-pvc.yaml
kubectl delete -f k8s/03-config.yaml
kubectl delete -f k8s/00-namespace.yaml
```

## ⚠️ 注意事项

1. **镜像地址**: 确保 YAML 文件中的 `your-username` 已替换为实际的 GitHub 用户名
2. **存储类**: 检查 PVC 中的 `storageClassName` 是否与集群匹配
3. **NodePort 范围**: NodePort 端口必须在 30000-32767 范围内
4. **资源限制**: 根据实际情况调整 CPU 和内存限制
5. **持久化数据**: PVC 数据在删除 namespace 时会被删除，注意备份

## 📊 资源配置

### 生产环境

| 服务 | 副本数 | CPU 请求/限制 | 内存请求/限制 | 端口 |
|------|--------|--------------|--------------|------|
| 前端 | 2 | 50m/100m | 64Mi/128Mi | 30080 |
| 后端 | 2 | 100m/200m | 256Mi/512Mi | 30800 |

### 测试环境

| 服务 | 副本数 | CPU 请求/限制 | 内存请求/限制 | 端口 |
|------|--------|--------------|--------------|------|
| 前端 | 1 | 100m/200m | 128Mi/256Mi | 30081 |
| 后端 | 1 | 200m/500m | 512Mi/1Gi | 30801 |

## 🆘 故障排除

### Pod 启动失败

```bash
# 查看 Pod 状态
kubectl describe pod <pod-name> -n code-reader

# 查看日志
kubectl logs <pod-name> -n code-reader --previous
```

### 镜像拉取失败

```bash
# 检查镜像地址
kubectl describe pod <pod-name> -n code-reader | grep Image

# 检查 GitHub Package 权限
```

### 服务无法访问

```bash
# 检查 Service
kubectl get svc -n code-reader

# 检查 Endpoints
kubectl get endpoints -n code-reader

# 测试服务连接
kubectl run -it --rm debug --image=busybox --restart=Never -- wget -O- http://code-reader-backend-service:8000/health
```

## 📚 相关文档

- [Kubernetes 官方文档](https://kubernetes.io/docs/)
- [kubectl 命令参考](https://kubernetes.io/docs/reference/kubectl/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)