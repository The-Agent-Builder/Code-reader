# AI 代码库领航员 (AI Codebase Navigator)

This is a code bundle for AI 代码库领航员 (AI Codebase Navigator). The original project is available at https://www.figma.com/design/GdQKzN4wWCbJB2GeJDdVPJ/AI-%E4%BB%A3%E7%A0%81%E5%BA%93%E9%A2%86%E8%88%AA%E5%91%98--AI-Codebase-Navigator-.

## Running the code

Run `npm i` to install the dependencies.

Run `npm run dev` to start the development server.

## 端口配置

前端开发服务器的端口可以通过项目根目录的 `.env` 文件进行配置。

### 配置方法

1. 在项目根目录的 `.env` 文件中设置 `VITE_PORT` 变量：

```bash
# 前端配置
VITE_PORT=3000
```

2. 启动开发服务器：

```bash
npm run dev
```

### 默认配置

- 默认端口：3000
- 如果 `.env` 文件中没有设置 `VITE_PORT`，将使用默认端口 3000

### 示例

要将前端服务器端口更改为 3001：

1. 编辑项目根目录的 `.env` 文件：

```bash
VITE_PORT=3001
```

2. 重新启动开发服务器：

```bash
npm run dev
```

服务器将在 http://localhost:3001 启动。

### 注意事项

- 端口配置在 `vite.config.ts` 中通过 `loadEnv` 函数从项目根目录的 `.env` 文件加载
- 修改端口后需要重新启动开发服务器才能生效
- 确保选择的端口没有被其他应用程序占用
