import { Card } from "./ui/card";
import { Badge } from "./ui/badge";

interface MainContentProps {
  activeSection: string;
  onFileSelect: (file: string) => void;
  projectName?: string;
}

export function MainContent({
  activeSection,
  onFileSelect,
  projectName,
}: MainContentProps) {
  const renderContent = () => {
    switch (activeSection) {
      case "overview":
      case "metrics":
        return (
          <div className="space-y-8">
            {/* 项目概述 */}
            <div>
              <h1>{projectName ? `${projectName} - 项目概览` : "项目概览"}</h1>
              <p className="text-gray-600 mt-2">
                {projectName
                  ? `${projectName} 项目的详细分析和文档。`
                  : "这是一个基于 Python 的 Web 应用程序，采用 Flask 框架构建。本应用提供了完整的用户认证系统和内容管理功能，采用现代化的架构设计和最佳实践。"}
              </p>
            </div>

            {/* 关键指标 */}
            <div>
              <h2 className="mb-4">关键指标</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="p-4">
                  <h3>代码行数</h3>
                  <p className="text-2xl font-bold text-blue-600">12,450</p>
                  <p className="text-sm text-gray-500">Python 代码</p>
                </Card>
                <Card className="p-4">
                  <h3>文件数量</h3>
                  <p className="text-2xl font-bold text-green-600">156</p>
                  <p className="text-sm text-gray-500">源代码文件</p>
                </Card>
                <Card className="p-4">
                  <h3>模块数量</h3>
                  <p className="text-2xl font-bold text-purple-600">23</p>
                  <p className="text-sm text-gray-500">Python 模块</p>
                </Card>
              </div>
            </div>
          </div>
        );

      case "data-models":
      case "entity-diagram":
        return (
          <div className="space-y-6">
            <div>
              <h1>数据模型浏览器</h1>
              <p className="text-gray-600 mt-2">
                AI 摘要: User 模型是系统的核心，管理用户认证和权限。Post
                模型负责���容�����理，两者通过外键关联。
              </p>
            </div>

            <Card className="p-6">
              <h3 className="mb-4">实体关系图</h3>
              <div className="bg-gray-50 rounded-lg p-8 min-h-80 flex items-center justify-center">
                <div className="space-y-8">
                  {/* User Entity */}
                  <div
                    className="bg-white border-2 border-blue-300 rounded-lg p-4 cursor-pointer hover:shadow-lg hover:border-blue-400 transition-all duration-200"
                    onClick={() => onFileSelect("src/models/user.py")}
                  >
                    <h4 className="font-bold text-blue-700 mb-2">User</h4>
                    <div className="text-sm text-gray-600 space-y-1">
                      <div className="flex justify-between">
                        <span>id</span>
                        <span className="text-xs text-blue-600">
                          Integer (PK)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>email</span>
                        <span className="text-xs text-gray-500">String</span>
                      </div>
                      <div className="flex justify-between">
                        <span>password_hash</span>
                        <span className="text-xs text-gray-500">String</span>
                      </div>
                      <div className="flex justify-between">
                        <span>created_at</span>
                        <span className="text-xs text-gray-500">DateTime</span>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-blue-600">
                      点击查看源代码 →
                    </div>
                  </div>

                  {/* Relationship line */}
                  <div className="flex justify-center">
                    <div className="flex flex-col items-center">
                      <div className="w-px h-8 bg-gray-400"></div>
                      <div className="text-xs text-gray-500 bg-white px-2 py-1 rounded border">
                        1:N
                      </div>
                      <div className="w-px h-8 bg-gray-400"></div>
                    </div>
                  </div>

                  {/* Post Entity */}
                  <div
                    className="bg-white border-2 border-green-300 rounded-lg p-4 cursor-pointer hover:shadow-lg hover:border-green-400 transition-all duration-200"
                    onClick={() => onFileSelect("src/models/post.py")}
                  >
                    <h4 className="font-bold text-green-700 mb-2">Post</h4>
                    <div className="text-sm text-gray-600 space-y-1">
                      <div className="flex justify-between">
                        <span>id</span>
                        <span className="text-xs text-green-600">
                          Integer (PK)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>title</span>
                        <span className="text-xs text-gray-500">String</span>
                      </div>
                      <div className="flex justify-between">
                        <span>content</span>
                        <span className="text-xs text-gray-500">Text</span>
                      </div>
                      <div className="flex justify-between">
                        <span>user_id</span>
                        <span className="text-xs text-orange-600">
                          Integer (FK)
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>published_at</span>
                        <span className="text-xs text-gray-500">DateTime</span>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-green-600">
                      点击查看源代码 →
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        );

      case "glossary":
      case "terms":
        return (
          <div className="space-y-6">
            <div>
              <h1>领域术语词典</h1>
              <p className="text-gray-600 mt-2">项目中的核心概念和术语解释</p>
            </div>

            <div className="space-y-4">
              {[
                {
                  term: "User",
                  definition: "系统用户，包含认证信息和个人资料",
                  file: "src/models/user.py",
                },
                {
                  term: "Post",
                  definition: "用户发布的内容文章，支持富文本格式",
                  file: "src/models/post.py",
                },
                {
                  term: "Authentication",
                  definition: "用户身份验证机制，基于 JWT Token",
                  file: "src/api/auth.py",
                },
                {
                  term: "Migration",
                  definition: "数据库结构变更的版本控制机制",
                  file: null,
                },
                {
                  term: "Blueprint",
                  definition: "Flask 应用的模块化组织方式",
                  file: null,
                },
              ].map((item) => (
                <Card key={item.term} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <Badge variant="secondary">{item.term}</Badge>
                      <p className="text-gray-700 flex-1">{item.definition}</p>
                    </div>
                    {item.file && (
                      <button
                        onClick={() => onFileSelect(item.file)}
                        className="text-sm text-blue-600 hover:text-blue-800 ml-4"
                      >
                        查看源码 →
                      </button>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        );

      case "architecture":
      case "external-deps":
        return (
          <div className="space-y-6">
            <div>
              <h1>架构边界</h1>
              <p className="text-gray-600 mt-2">系统的外部依赖和内部接口分析</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="p-4">
                <h3 className="mb-4">外部依赖</h3>
                <div className="space-y-3">
                  {[
                    {
                      name: "PostgreSQL",
                      type: "数据库",
                      description: "主要数据存储",
                    },
                    {
                      name: "Redis",
                      type: "缓存",
                      description: "会话和缓存存储",
                    },
                    {
                      name: "AWS S3",
                      type: "存储",
                      description: "文件上传存储",
                    },
                    {
                      name: "SendGrid",
                      type: "API",
                      description: "邮件发送服务",
                    },
                  ].map((dep) => (
                    <div
                      key={dep.name}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <div className="font-medium">{dep.name}</div>
                        <div className="text-sm text-gray-600">
                          {dep.description}
                        </div>
                      </div>
                      <Badge variant="outline">{dep.type}</Badge>
                    </div>
                  ))}
                </div>
              </Card>

              <Card className="p-4">
                <h3 className="mb-4">内部接口</h3>
                <div className="space-y-3">
                  {[
                    {
                      path: "/api/auth/login",
                      method: "POST",
                      description: "用户登录认证",
                      file: "src/api/auth.py",
                    },
                    {
                      path: "/api/auth/register",
                      method: "POST",
                      description: "用户注册",
                      file: "src/api/auth.py",
                    },
                    {
                      path: "/api/posts",
                      method: "GET",
                      description: "获取文章列表",
                      file: "src/api/posts.py",
                    },
                    {
                      path: "/api/posts",
                      method: "POST",
                      description: "创建新文章",
                      file: "src/api/posts.py",
                    },
                  ].map((api) => (
                    <div
                      key={`${api.method}-${api.path}`}
                      className="p-3 bg-gray-50 rounded-lg"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline">{api.method}</Badge>
                          <code className="text-sm">{api.path}</code>
                        </div>
                        <button
                          onClick={() => onFileSelect(api.file)}
                          className="text-xs text-blue-600 hover:text-blue-800"
                        >
                          查看实现 →
                        </button>
                      </div>
                      <div className="text-sm text-gray-600">
                        {api.description}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          </div>
        );

      case "call-graph":
      case "module-graph":
        return (
          <div className="space-y-6">
            <div>
              <h1>调用图谱</h1>
              <p className="text-gray-600 mt-2">模块依赖关系和函数调用链分析</p>
            </div>

            <Card className="p-6">
              <h3 className="mb-4">模块依赖图</h3>
              <div className="bg-gray-50 rounded-lg p-8 min-h-96">
                <div className="space-y-8">
                  {/* API/表现层 */}
                  <div className="space-y-3">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-700 bg-blue-100 rounded-full py-2 px-4 inline-block">
                        API / 表现层
                      </h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        {
                          module: "认证接口",
                          files: [
                            { name: "auth.py", path: "src/api/auth.py" },
                            {
                              name: "middleware.py",
                              path: "src/api/middleware.py",
                            },
                          ],
                        },
                        {
                          module: "内容接口",
                          files: [
                            { name: "posts.py", path: "src/api/posts.py" },
                            {
                              name: "comments.py",
                              path: "src/api/comments.py",
                            },
                          ],
                        },
                        {
                          module: "用户接口",
                          files: [
                            { name: "users.py", path: "src/api/users.py" },
                            {
                              name: "profiles.py",
                              path: "src/api/profiles.py",
                            },
                          ],
                        },
                      ].map((module) => (
                        <div
                          key={module.module}
                          className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4"
                        >
                          <div className="font-medium text-blue-900 mb-3 text-center">
                            {module.module}
                          </div>
                          <div className="space-y-1">
                            {module.files.map((file) => (
                              <div
                                key={file.name}
                                className="text-sm bg-white rounded px-2 py-1 cursor-pointer hover:bg-blue-100 transition-colors"
                                onClick={() => onFileSelect(file.path)}
                              >
                                {file.name}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 分层分割线 */}
                  <div className="flex justify-center">
                    <div className="text-2xl text-gray-400">⬇</div>
                  </div>

                  {/* 业务逻辑层 */}
                  <div className="space-y-3">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-700 bg-purple-100 rounded-full py-2 px-4 inline-block">
                        业务逻辑层
                      </h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        {
                          module: "认证服务",
                          files: [
                            {
                              name: "auth_service.py",
                              path: "src/services/auth_service.py",
                            },
                            {
                              name: "token_service.py",
                              path: "src/services/token_service.py",
                            },
                          ],
                        },
                        {
                          module: "业务服务",
                          files: [
                            {
                              name: "post_service.py",
                              path: "src/services/post_service.py",
                            },
                            {
                              name: "user_service.py",
                              path: "src/services/user_service.py",
                            },
                          ],
                        },
                      ].map((module) => (
                        <div
                          key={module.module}
                          className="bg-purple-50 border-2 border-purple-200 rounded-lg p-4"
                        >
                          <div className="font-medium text-purple-900 mb-3 text-center">
                            {module.module}
                          </div>
                          <div className="space-y-1">
                            {module.files.map((file) => (
                              <div
                                key={file.name}
                                className="text-sm bg-white rounded px-2 py-1 cursor-pointer hover:bg-purple-100 transition-colors"
                                onClick={() => onFileSelect(file.path)}
                              >
                                {file.name}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 分层分割线 */}
                  <div className="flex justify-center">
                    <div className="text-2xl text-gray-400">⬇</div>
                  </div>

                  {/* 数据访问层 */}
                  <div className="space-y-3">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-700 bg-green-100 rounded-full py-2 px-4 inline-block">
                        数据访问层
                      </h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        {
                          module: "数据模型",
                          files: [
                            { name: "user.py", path: "src/models/user.py" },
                            { name: "post.py", path: "src/models/post.py" },
                          ],
                        },
                        {
                          module: "数据库工具",
                          files: [
                            {
                              name: "database.py",
                              path: "src/core/database.py",
                            },
                            { name: "migrations/", path: "src/migrations/" },
                          ],
                        },
                        {
                          module: "缓存层",
                          files: [
                            {
                              name: "redis_client.py",
                              path: "src/core/redis_client.py",
                            },
                            {
                              name: "cache_service.py",
                              path: "src/services/cache_service.py",
                            },
                          ],
                        },
                      ].map((module) => (
                        <div
                          key={module.module}
                          className="bg-green-50 border-2 border-green-200 rounded-lg p-4"
                        >
                          <div className="font-medium text-green-900 mb-3 text-center">
                            {module.module}
                          </div>
                          <div className="space-y-1">
                            {module.files.map((file) => (
                              <div
                                key={file.name}
                                className="text-sm bg-white rounded px-2 py-1 cursor-pointer hover:bg-green-100 transition-colors"
                                onClick={() => onFileSelect(file.path)}
                              >
                                {file.name}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 分层分割线 */}
                  <div className="flex justify-center">
                    <div className="text-2xl text-gray-400">⬇</div>
                  </div>

                  {/* 基础设施层 */}
                  <div className="space-y-3">
                    <div className="text-center">
                      <h4 className="font-medium text-gray-700 bg-gray-200 rounded-full py-2 px-4 inline-block">
                        基础设施层
                      </h4>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        {
                          module: "数据库",
                          files: [
                            { name: "PostgreSQL", path: null },
                            { name: "Redis", path: null },
                          ],
                        },
                        {
                          module: "外部服务",
                          files: [
                            { name: "AWS S3", path: null },
                            { name: "SendGrid", path: null },
                          ],
                        },
                      ].map((module) => (
                        <div
                          key={module.module}
                          className="bg-gray-100 border-2 border-gray-300 rounded-lg p-4"
                        >
                          <div className="font-medium text-gray-700 mb-3 text-center">
                            {module.module}
                          </div>
                          <div className="space-y-1">
                            {module.files.map((file) => (
                              <div
                                key={file.name}
                                className={`text-sm rounded px-2 py-1 ${
                                  file.path
                                    ? "bg-white cursor-pointer hover:bg-gray-200 transition-colors"
                                    : "bg-gray-50 text-gray-600"
                                }`}
                                onClick={() =>
                                  file.path && onFileSelect(file.path)
                                }
                              >
                                {file.name}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        );

      default:
        return (
          <div className="space-y-6">
            <div>
              <h1>选择左侧菜单查看内容</h1>
              <p className="text-gray-600 mt-2">
                请从左侧导航栏选择要查看的分析结果
              </p>
            </div>
          </div>
        );
    }
  };

  return <div className="p-8 max-w-none">{renderContent()}</div>;
}
