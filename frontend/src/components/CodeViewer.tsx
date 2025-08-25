import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  ArrowLeft,
  Code,
  Brain,
  FileText,
  Users,
  Clock,
  Loader2,
} from "lucide-react";
import { api } from "../services/api";

interface CodeViewerProps {
  filePath: string;
  fileAnalysisId?: number;
  onBack: () => void;
}

// 模拟代码内容和分析数据
const mockFileData: { [key: string]: any } = {
  "src/models/user.py": {
    language: "Python",
    lines: 45,
    complexity: "Low",
    lastModified: "2 days ago",
    author: "Alice Chen",
    code: `from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

Base = declarative_base()

class User(Base):
    """用户模型 - 系统的核心实体"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    username = Column(String(80), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """设置用户密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证用户密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'`,
    analysis: {
      summary:
        "User 模型是系统的核心实体，负责用户认证和基本信息管理。使用 SQLAlchemy ORM 实现，包含了密码加密和验证功能。",
      keyFunctions: [
        {
          name: "set_password",
          purpose: "安全地设置用户密码，使用 Werkzeug 进行哈希加密",
        },
        { name: "check_password", purpose: "验证用户输入的密码是否正确" },
        { name: "__repr__", purpose: "提供用户对象的字符串表示，便于调试" },
      ],
      dependencies: ["sqlalchemy", "werkzeug.security", "datetime"],
      usedBy: ["src/api/auth.py", "src/services/auth_service.py"],
      designPatterns: ["Active Record", "Entity"],
      securityNotes: "使用了安全的密码哈希，避免明文存储密码",
    },
  },
  "src/models/post.py": {
    language: "Python",
    lines: 38,
    complexity: "Low",
    lastModified: "1 day ago",
    author: "Bob Wilson",
    code: `from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .user import Base

class Post(Base):
    """文章模型 - 内容管理核心"""
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    author = relationship("User", backref="posts")
    
    def __repr__(self):
        return f'<Post {self.title[:30]}...>'
    
    @property
    def is_published(self):
        """检查文章是否已发布"""
        return self.published_at <= datetime.utcnow()`,
    analysis: {
      summary:
        "Post 模型管理用户发布的内容，与 User 模型通过外键关联。支持时间戳追踪和发布状态管理。",
      keyFunctions: [
        { name: "is_published", purpose: "计算属性，判断文章是否已经发布" },
        { name: "__repr__", purpose: "提供文章对象的简短字符串表示" },
      ],
      dependencies: ["sqlalchemy", "datetime", ".user"],
      usedBy: ["src/api/posts.py", "src/services/post_service.py"],
      designPatterns: ["Active Record", "Foreign Key Association"],
      relationships: [
        {
          type: "多对一 (Many-to-One)",
          target: "User",
          description: "每篇文章属于一个用户，一个用户可以有多篇文章",
        },
      ],
    },
  },
  "src/api/auth.py": {
    language: "Python",
    lines: 78,
    complexity: "Medium",
    lastModified: "3 hours ago",
    author: "Alice Chen",
    code: `from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models.user import User
from ..services.auth_service import AuthService
import re

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册端点"""
    data = request.get_json()
    
    # 验证必填字段
    if not all(k in data for k in ('email', 'password', 'username')):
        return jsonify({'error': '缺少必填字段'}), 400
    
    # 邮箱格式验证
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', data['email']):
        return jsonify({'error': '邮箱格式不正确'}), 400
    
    try:
        user = AuthService.create_user(
            email=data['email'],
            password=data['password'],
            username=data['username']
        )
        
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username
            }
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录端点"""
    data = request.get_json()
    
    if not all(k in data for k in ('email', 'password')):
        return jsonify({'error': '邮箱和密码不能为空'}), 400
    
    user = AuthService.authenticate_user(data['email'], data['password'])
    
    if not user:
        return jsonify({'error': '邮箱或密码错误'}), 401
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'username': user.username
        }
    })

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户资料"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({
        'id': user.id,
        'email': user.email,
        'username': user.username,
        'created_at': user.created_at.isoformat()
    })`,
    analysis: {
      summary:
        "Auth API 模块提供用户认证相关的 REST 端点，包括注册、登录和获取用户资料功能。使用 JWT 进行身份验证。",
      keyFunctions: [
        {
          name: "register",
          purpose: "处理用户注册请求，包含数据验证和用户创建",
        },
        { name: "login", purpose: "处理用户登录，验证凭据并返回 JWT Token" },
        { name: "get_profile", purpose: "获取当前登录用户的资料信息" },
      ],
      dependencies: [
        "flask",
        "flask_jwt_extended",
        "..models.user",
        "..services.auth_service",
        "re",
      ],
      apiEndpoints: [
        { method: "POST", path: "/api/auth/register", description: "用户注册" },
        { method: "POST", path: "/api/auth/login", description: "用户登录" },
        {
          method: "GET",
          path: "/api/auth/profile",
          description: "获取用户资料 (需要认证)",
        },
      ],
      securityFeatures: [
        "JWT Token 认证",
        "邮箱格式验证",
        "输入数据验证",
        "错误信息标准化",
      ],
    },
  },
  "src/services/auth_service.py": {
    language: "Python",
    lines: 52,
    complexity: "Medium",
    lastModified: "1 day ago",
    author: "Bob Wilson",
    code: `from ..models.user import User
from sqlalchemy.exc import IntegrityError
from flask import current_app

class AuthService:
    """认证服务 - 处理用户认证相关的业务逻辑"""
    
    @staticmethod
    def create_user(email, password, username):
        """创建新用户"""
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            raise ValueError("邮箱已被注册")
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            raise ValueError("用户名已被占用")
        
        # 创建新用户
        user = User()
        user.email = email
        user.username = username
        user.set_password(password)
        
        try:
            current_app.db.session.add(user)
            current_app.db.session.commit()
            return user
        except IntegrityError:
            current_app.db.session.rollback()
            raise ValueError("创建用户失败")
    
    @staticmethod
    def authenticate_user(email, password):
        """验证用户凭据"""
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            return user
        return None
    
    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        return User.query.get(user_id)`,
    analysis: {
      summary:
        "AuthService 是认证相关的服务层，封装了用户创建、验证和查询的业务逻辑，与数据层解耦。",
      keyFunctions: [
        {
          name: "create_user",
          purpose: "创建新用户，包含重复性检查和事务处理",
        },
        { name: "authenticate_user", purpose: "验证用户登录凭据" },
        { name: "get_user_by_id", purpose: "根据用户ID查询用户信息" },
      ],
      dependencies: ["..models.user", "sqlalchemy.exc", "flask"],
      designPatterns: ["Service Layer", "Static Factory"],
      businessRules: [
        "邮箱必须唯一",
        "用户名必须唯一",
        "密码加密存储",
        "数据库操作事务性",
      ],
    },
  },
};

export default function CodeViewer({
  filePath,
  fileAnalysisId,
  onBack,
}: CodeViewerProps) {
  const [activeTab, setActiveTab] = useState("code");
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [isLoadingAnalysis, setIsLoadingAnalysis] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  // 获取静态文件数据（用于源代码显示）
  const fileData = mockFileData[filePath] || {
    language: "Unknown",
    lines: 0,
    complexity: "Unknown",
    code: "// 文件内容加载中...",
    analysis: { summary: "暂无分析数据" },
  };

  // 加载AI分析数据
  const loadAnalysisData = async (fileAnalysisId: number) => {
    setIsLoadingAnalysis(true);
    setAnalysisError(null);

    try {
      console.log(
        "Loading analysis data for file_analysis_id:",
        fileAnalysisId
      );
      const response = await api.getAnalysisItemsByFileId(fileAnalysisId);

      if (response.status === "success") {
        // 直接使用API返回的数据
        const processedAnalysis = processAnalysisItems(response.items || []);
        setAnalysisData(processedAnalysis);
        console.log("Analysis data loaded:", processedAnalysis);

        if (!response.items || response.items.length === 0) {
          console.warn(
            "No analysis items found for file_analysis_id:",
            fileAnalysisId
          );
        }
      } else {
        setAnalysisData({ items: [], totalItems: 0 });
        console.warn(
          "API returned error for file_analysis_id:",
          fileAnalysisId,
          response.message
        );
      }
    } catch (error) {
      console.error("Error loading analysis data:", error);
      setAnalysisError(
        error instanceof Error ? error.message : "加载分析数据失败"
      );
      setAnalysisData({ items: [], totalItems: 0 });
    } finally {
      setIsLoadingAnalysis(false);
    }
  };

  // 直接返回原始分析项数据，不进行复杂处理
  const processAnalysisItems = (items: any[]) => {
    return {
      items: items || [],
      totalItems: items ? items.length : 0,
    };
  };

  // 当fileAnalysisId改变时加载分析数据
  useEffect(() => {
    if (fileAnalysisId) {
      loadAnalysisData(fileAnalysisId);
    } else {
      // 如果没有fileAnalysisId，显示无数据状态
      setAnalysisData({ items: [], totalItems: 0 });
    }
  }, [fileAnalysisId]);

  // 获取要显示的分析数据
  const displayAnalysis = analysisData || fileData.analysis;

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header with breadcrumb */}
      <div className="border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回文档
          </Button>

          <div className="text-sm text-gray-500">
            {filePath.split("/").map((segment, index, array) => (
              <span key={index}>
                {segment}
                {index < array.length - 1 && <span className="mx-1">/</span>}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* File info bar */}
      <div className="border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Badge variant="secondary">{fileData.language}</Badge>
            <span className="text-sm text-gray-600">{fileData.lines} 行</span>
            <span className="text-sm text-gray-600">
              复杂度: {fileData.complexity}
            </span>
          </div>

          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-1" />
              {fileData.author}
            </div>
            <div className="flex items-center">
              <Clock className="h-4 w-4 mr-1" />
              {fileData.lastModified}
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="h-full flex flex-col"
        >
          <div className="border-b border-gray-200 px-6">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="code" className="flex items-center">
                <Code className="h-4 w-4 mr-2" />
                源代码
              </TabsTrigger>
              <TabsTrigger value="analysis" className="flex items-center">
                <Brain className="h-4 w-4 mr-2" />
                AI 分析
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-hidden">
            <TabsContent
              value="code"
              className="h-full m-0 p-6 overflow-y-auto"
            >
              <Card className="p-0 overflow-hidden">
                <pre className="p-6 text-sm bg-gray-50 overflow-x-auto">
                  <code className="language-python">{fileData.code}</code>
                </pre>
              </Card>
            </TabsContent>

            <TabsContent
              value="analysis"
              className="h-full m-0 p-6 overflow-y-auto"
            >
              <div className="space-y-6">
                {/* 加载状态 */}
                {isLoadingAnalysis && (
                  <Card className="p-6">
                    <div className="flex items-center justify-center space-x-2">
                      <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                      <span className="text-gray-600">
                        正在加载AI分析数据...
                      </span>
                    </div>
                  </Card>
                )}

                {/* 错误状态 */}
                {analysisError && (
                  <Card className="p-6 border-red-200 bg-red-50">
                    <div className="flex items-center space-x-2 mb-2">
                      <Brain className="h-5 w-5 text-red-600" />
                      <h3 className="text-red-800">加载失败</h3>
                    </div>
                    <p className="text-red-700">{analysisError}</p>
                  </Card>
                )}

                {/* 分析结果 */}
                {!isLoadingAnalysis &&
                  displayAnalysis &&
                  displayAnalysis.items &&
                  displayAnalysis.items.length > 0 && (
                    <Card className="p-6">
                      <div className="flex items-center space-x-2 mb-6">
                        <Brain className="h-5 w-5 text-blue-600" />
                        <h3>分析结果</h3>
                        {/* {fileAnalysisId && (
                          <Badge variant="outline" className="text-xs">
                            动态加载
                          </Badge>
                        )} */}
                        <Badge variant="secondary" className="text-xs">
                          共 {displayAnalysis.totalItems} 项
                        </Badge>
                      </div>

                      <div className="space-y-6">
                        {displayAnalysis.items.map(
                          (item: any, index: number) => (
                            <div
                              key={item.id || index}
                              className="border-l-4 border-blue-200 pl-4"
                            >
                              {/* 标题 */}
                              <div className="mb-3">
                                <h4 className="text-lg font-medium text-gray-900 mb-1">
                                  {item.title || `分析项 ${index + 1}`}
                                </h4>
                                {item.source && (
                                  <div className="flex items-center space-x-2 text-sm text-gray-500">
                                    <FileText className="h-4 w-4" />
                                    <span>{item.source}</span>
                                  </div>
                                )}
                              </div>

                              {/* 描述 */}
                              {item.description && (
                                <div className="mb-4">
                                  <div className="bg-blue-50 rounded-lg p-4">
                                    <p className="text-gray-700 leading-relaxed">
                                      {item.description}
                                    </p>
                                  </div>
                                </div>
                              )}

                              {/* 代码 */}
                              {item.code && (
                                <div className="mb-4">
                                  <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                                    <pre className="text-sm text-gray-100">
                                      <code
                                        className={`language-${
                                          item.language || "text"
                                        }`}
                                      >
                                        {item.code}
                                      </code>
                                    </pre>
                                  </div>
                                  {item.start_line && item.end_line && (
                                    <div className="mt-2 text-xs text-gray-500">
                                      行 {item.start_line}-{item.end_line}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )
                        )}
                      </div>
                    </Card>
                  )}

                {/* 无分析数据时的提示 */}
                {!isLoadingAnalysis &&
                  (!displayAnalysis ||
                    !displayAnalysis.items ||
                    displayAnalysis.items.length === 0) && (
                    <Card className="p-6">
                      <div className="flex items-center space-x-2 mb-4">
                        <Brain className="h-5 w-5 text-gray-400" />
                        <h3 className="text-gray-600">分析结果</h3>
                      </div>
                      <div className="text-center py-8">
                        <div className="text-gray-400 mb-2">
                          <FileText className="h-12 w-12 mx-auto" />
                        </div>
                        <p className="text-gray-500">暂无分析数据</p>
                      </div>
                    </Card>
                  )}
              </div>
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
