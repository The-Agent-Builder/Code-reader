import { useState, useRef, useEffect } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { Textarea } from "./ui/textarea";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { ScrollArea } from "./ui/scroll-area";
import {
  Send,
  Bot,
  User,
  Sparkles,
  FileCode,
  Database,
  GitBranch,
  MessageSquare,
  Lightbulb,
  Code,
  Brain,
  ChevronLeft,
  Copy,
  Check,
  ArrowUp,
} from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  isTyping?: boolean;
}

interface ChatInterfaceProps {
  onBack: () => void;
  currentVersionId: string;
}

const suggestedQuestions = [
  {
    icon: FileCode,
    text: "这个项目的主要架构是什么？",
    category: "架构分析",
  },
  {
    icon: Database,
    text: "项目中使用了哪些数据库技术？",
    category: "技术栈",
  },
  {
    icon: GitBranch,
    text: "代码的依赖关系如何？",
    category: "依赖分析",
  },
  {
    icon: Code,
    text: "有哪些可以优化的地方？",
    category: "代码优化",
  },
  {
    icon: Brain,
    text: "这个项目适合新手学习吗？",
    category: "学习建议",
  },
  {
    icon: Lightbulb,
    text: "如何快速上手这个项目？",
    category: "入门指南",
  },
];

const mockResponses = [
  `根据我对您项目的分析，这是一个使用React + TypeScript构建的现代化前端应用。项目采用了模块化的组件设计，具有良好的可维护性。

**主要特点：**
• 使用了Tailwind CSS进行样式管理
• 采用了shadcn/ui组件库
• 项目结构清晰，分离了业务逻辑和UI组件

**架构模式：**
- 单页应用(SPA)架构
- 组件化开发模式
- 状态提升和属性下传的数据流

这种架构设计既保证了代码的可维护性，又提供了良好的用户体验。`,

  `从代码分析来看，这个项目主要使用了以下技术栈：

**前端技术：**
• React 18+ (函数式组件 + Hooks)
• TypeScript (类型安全)
• Tailwind CSS (原子化CSS)
• Lucide React (图标库)

**构建工具：**
• Vite (现代化构建工具)
• ESLint + Prettier (代码规范)

**UI组件：**
• shadcn/ui (现代化组件库)
• Radix UI (无障碍组件基础)

目前没有发现数据库相关的技术栈，这是一个纯前端项目。如果需要数据持久化，建议考虑集成后端API或使用浏览器本地存储。`,

  `项目的依赖关系分析如下：

**核心依赖：**
• React生态系统组件相互依赖
• UI组件之间存在层级关系
• 工具函数模块被广泛引用

**组件依赖图：**
\`\`\`
App.tsx (根组件)
├── TopNavigation
├── UploadPage
├── AnalysisProgress  
├── DeepWikiInterface
├── PersonalSpace
└── ChatInterface
\`\`\`

**建议：**
依赖关系整体健康，没有循环依赖问题。组件间耦合度适中，便于维护和扩展。`,

  `基于代码分析，我发现以下可以优化的地方：

**性能优化：**
• 可以使用React.memo()优化组件重渲染
• 大列表可以考虑虚拟滚动
• 图片懒加载可以提升页面加载速度

**代码结构：**
• 一些组件过于复杂，建议拆分
• 状态管理可以考虑使用Context或状态管理库
• 添加单元测试覆盖

**用户体验：**
• 添加加载状态指示器
• 错误边界处理
• 键盘导航支持

**代码示例：**
\`\`\`typescript
// 使用React.memo优化性能
export const OptimizedComponent = React.memo(({ data }) => {
  return <div>{data}</div>;
});
\`\`\``,

  `这个项目非常适合新手学习！原因如下：

**学习友好性：**
• 使用了现代React最佳实践
• 代码结构清晰，注释完善
• 采用了TypeScript，有助于理解类型系统

**技术覆盖面：**
• 涵盖了现代前端开发的核心技术
• 组件设计模式值得学习
• 状态管理和事件处理示例丰富

**推荐学习顺序：**
1. 从基础组件开始理解
2. 学习状态管理模式
3. 理解组件间通信
4. 掌握TypeScript类型定义

这个项目可以作为很好的React学习案例。`,

  `快速上手这个项目的建议：

**第一步：环境搭建**
\`\`\`bash
npm install
npm run dev
\`\`\`

**第二步：理解项目结构**
• \`/components\` - 所有React组件
• \`/styles\` - 全局样式文件
• \`App.tsx\` - 应用主入口

**第三步：从简单页面开始**
1. 先看UploadPage组件，理解基础交互
2. 研究UI组件的使用方法
3. 理解状态管理逻辑

**第四步：尝试修改**
• 调整样式看效果
• 添加新的功能按钮
• 修改文案内容

**注意事项：**
确保Node.js版本 >= 16，推荐使用最新的LTS版本。`,
];

// 格式化消息内容，支持Markdown风格的基本格式
const formatMessageContent = (content: string) => {
  const lines = content.split("\n");
  const formattedLines = lines.map((line, index) => {
    // 代码块处理
    if (line.trim().startsWith("```")) {
      return { type: "code-fence", content: line, key: index };
    }

    // 标题处理
    if (line.startsWith("**") && line.endsWith("**") && line.length > 4) {
      return {
        type: "heading",
        content: line.slice(2, -2),
        key: index,
      };
    }

    // 列表项处理
    if (line.trim().startsWith("•") || line.trim().startsWith("-")) {
      return {
        type: "list-item",
        content: line.trim().slice(1).trim(),
        key: index,
      };
    }

    // 代码行处理
    if (
      line.trim().startsWith("`") &&
      line.trim().endsWith("`") &&
      line.trim().length > 2
    ) {
      return {
        type: "inline-code",
        content: line.trim().slice(1, -1),
        key: index,
      };
    }

    // 普通文本
    return { type: "text", content: line, key: index };
  });

  return formattedLines;
};

// 渲染格式化的消息内容
const MessageContent = ({ content }: { content: string }) => {
  const formattedLines = formatMessageContent(content);
  let inCodeBlock = false;
  let codeBlockContent: string[] = [];
  let codeBlockLanguage = "";

  const elements: JSX.Element[] = [];

  formattedLines.forEach((line, index) => {
    if (line.type === "code-fence") {
      if (!inCodeBlock) {
        // 开始代码块
        inCodeBlock = true;
        codeBlockLanguage = line.content.replace("```", "").trim();
        codeBlockContent = [];
      } else {
        // 结束代码块
        inCodeBlock = false;
        elements.push(
          <div key={`code-block-${index}`} className="my-3">
            <div className="bg-gray-900 rounded-lg overflow-hidden">
              <div className="flex items-center justify-between px-4 py-2 bg-gray-800 text-gray-300 text-sm">
                <span className="flex items-center space-x-2">
                  <Code className="h-4 w-4" />
                  <span>{codeBlockLanguage || "code"}</span>
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 text-gray-400 hover:text-white"
                  onClick={() =>
                    navigator.clipboard.writeText(codeBlockContent.join("\n"))
                  }
                >
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
              <pre className="p-4 text-sm text-gray-100 overflow-x-auto">
                <code>{codeBlockContent.join("\n")}</code>
              </pre>
            </div>
          </div>
        );
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockContent.push(line.content);
      return;
    }

    switch (line.type) {
      case "heading":
        elements.push(
          <h4
            key={line.key}
            className="font-semibold text-gray-900 mt-4 mb-2 first:mt-0"
          >
            {line.content}
          </h4>
        );
        break;

      case "list-item":
        elements.push(
          <div key={line.key} className="flex items-start space-x-2 ml-4 my-1">
            <span className="text-blue-600 mt-1">•</span>
            <span className="text-gray-700">{line.content}</span>
          </div>
        );
        break;

      case "inline-code":
        elements.push(
          <div key={line.key} className="my-2">
            <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded text-sm font-mono">
              {line.content}
            </code>
          </div>
        );
        break;

      case "text":
        if (line.content.trim()) {
          elements.push(
            <p
              key={line.key}
              className="text-gray-700 leading-relaxed my-2 first:mt-0 last:mb-0"
            >
              {line.content}
            </p>
          );
        } else {
          elements.push(<div key={line.key} className="h-2" />);
        }
        break;
    }
  });

  return <div className="space-y-1">{elements}</div>;
};

export default function ChatInterface({
  onBack,
  currentVersionId,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    // 模拟AI响应延迟
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          mockResponses[Math.floor(Math.random() * mockResponses.length)],
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1000 + Math.random() * 2000);
  };

  const handleSuggestedQuestion = (question: string) => {
    handleSendMessage(question);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const copyToClipboard = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="flex-shrink-0 p-4 bg-white/80 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-none mx-auto px-4 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={onBack} className="p-2">
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">AI 代码助手</h1>
                <p className="text-sm text-gray-600">
                  基于项目 v{currentVersionId} 的智能问答
                </p>
              </div>
            </div>
          </div>

          <Badge variant="secondary" className="flex items-center space-x-1">
            <Sparkles className="h-3 w-3" />
            <span>本地AI模型</span>
          </Badge>
        </div>
      </div>

      {/* Chat Content */}
      <div className="flex-1 flex max-w-none mx-auto w-full px-8 py-6 space-x-8">
        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col min-w-0">
          <Card className="flex-1 flex flex-col shadow-lg">
            {/* Messages Area */}
            <div className="flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                {messages.length === 0 ? (
                  /* Welcome Message */
                  <div className="h-full flex flex-col items-center justify-center p-12">
                    <div className="text-center space-y-6 max-w-2xl">
                      <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto">
                        <MessageSquare className="h-10 w-10 text-white" />
                      </div>
                      <div className="space-y-3">
                        <h3 className="text-2xl font-bold text-gray-900">
                          欢迎使用 AI 代码助手
                        </h3>
                        <p className="text-gray-600 leading-relaxed">
                          我已经深入分析了您的项目代码，可以回答关于架构设计、技术栈选择、依赖关系、优化建议等任何问题。让我们开始探索您的代码库吧！
                        </p>
                      </div>
                      <div className="flex items-center justify-center space-x-4 text-sm text-gray-500">
                        <div className="flex items-center space-x-1">
                          <Brain className="h-4 w-4" />
                          <span>智能分析</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <FileCode className="h-4 w-4" />
                          <span>代码理解</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Lightbulb className="h-4 w-4" />
                          <span>优化建议</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Messages List */
                  <div className="p-8 space-y-8">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${
                          message.role === "user"
                            ? "justify-end"
                            : "justify-start"
                        }`}
                      >
                        <div
                          className={`flex items-start space-x-4 max-w-[90%] ${
                            message.role === "user"
                              ? "flex-row-reverse space-x-reverse"
                              : ""
                          }`}
                        >
                          {/* Avatar */}
                          <div
                            className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-md ${
                              message.role === "user"
                                ? "bg-blue-600"
                                : "bg-gradient-to-r from-blue-500 to-purple-600"
                            }`}
                          >
                            {message.role === "user" ? (
                              <User className="h-5 w-5 text-white" />
                            ) : (
                              <Bot className="h-5 w-5 text-white" />
                            )}
                          </div>

                          {/* Message Content */}
                          <div
                            className={`group flex-1 ${
                              message.role === "user"
                                ? "text-right"
                                : "text-left"
                            }`}
                          >
                            <div
                              className={`inline-block p-4 rounded-xl relative shadow-sm ${
                                message.role === "user"
                                  ? "bg-blue-600 text-white rounded-br-md"
                                  : "bg-white border border-gray-200 text-gray-900 rounded-bl-md"
                              }`}
                            >
                              {message.role === "user" ? (
                                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                                  {message.content}
                                </div>
                              ) : (
                                <MessageContent content={message.content} />
                              )}

                              {/* Copy button for assistant messages */}
                              {message.role === "assistant" && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="absolute top-2 right-2 h-7 w-7 p-0 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-50 hover:bg-gray-100"
                                  onClick={() =>
                                    copyToClipboard(message.content, message.id)
                                  }
                                >
                                  {copiedMessageId === message.id ? (
                                    <Check className="h-3 w-3 text-green-600" />
                                  ) : (
                                    <Copy className="h-3 w-3 text-gray-600" />
                                  )}
                                </Button>
                              )}
                            </div>

                            <div
                              className={`text-xs text-gray-500 mt-2 ${
                                message.role === "user"
                                  ? "text-right"
                                  : "text-left"
                              }`}
                            >
                              {formatTimestamp(message.timestamp)}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* Loading indicator */}
                    {isLoading && (
                      <div className="flex justify-start">
                        <div className="flex items-start space-x-4 max-w-[90%]">
                          <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0 shadow-md">
                            <Bot className="h-5 w-5 text-white" />
                          </div>
                          <div className="bg-white border border-gray-200 rounded-xl rounded-bl-md p-4 shadow-sm">
                            <div className="flex items-center space-x-3">
                              <div className="flex space-x-1">
                                <div
                                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                  style={{ animationDelay: "0ms" }}
                                ></div>
                                <div
                                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                  style={{ animationDelay: "150ms" }}
                                ></div>
                                <div
                                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                                  style={{ animationDelay: "300ms" }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-500">
                                AI正在分析思考...
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>
                )}
              </ScrollArea>
            </div>

            {/* Input Area */}
            <div className="p-6 border-t border-gray-200 bg-gray-50/50">
              <div className="flex space-x-4">
                <div className="flex-1 relative">
                  <Textarea
                    ref={textareaRef}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="询问关于代码库的任何问题... (Enter发送，Shift+Enter换行)"
                    className="resize-none bg-white border-gray-300 focus:border-blue-500 focus:ring-blue-500 text-base"
                    rows={4}
                    disabled={isLoading}
                  />
                </div>
                <Button
                  onClick={() => handleSendMessage(inputValue)}
                  disabled={!inputValue.trim() || isLoading}
                  className="self-end h-auto px-5 py-4"
                >
                  <ArrowUp className="h-5 w-5" />
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar with Suggested Questions */}
        <div className="w-96 space-y-4 flex-shrink-0">
          <Card className="p-5 shadow-lg">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <Lightbulb className="h-5 w-5 text-yellow-500" />
              <span>推荐问题</span>
            </h3>

            <div className="space-y-3">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question.text)}
                  className="w-full p-4 text-left rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 group disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={isLoading}
                >
                  <div className="flex items-start space-x-3">
                    <question.icon className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5 group-hover:text-blue-700" />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900 group-hover:text-blue-700 leading-relaxed">
                        {question.text}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {question.category}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </Card>

          <Card className="p-5 shadow-lg">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center space-x-2">
              <Brain className="h-5 w-5 text-purple-500" />
              <span>AI 能力</span>
            </h3>

            <div className="space-y-4 text-sm">
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-blue-50">
                <FileCode className="h-4 w-4 text-blue-600" />
                <span className="text-blue-800 font-medium">代码架构分析</span>
              </div>
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-green-50">
                <Database className="h-4 w-4 text-green-600" />
                <span className="text-green-800 font-medium">技术栈识别</span>
              </div>
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-orange-50">
                <GitBranch className="h-4 w-4 text-orange-600" />
                <span className="text-orange-800 font-medium">
                  依赖关系梳理
                </span>
              </div>
              <div className="flex items-center space-x-3 p-2 rounded-lg bg-purple-50">
                <Code className="h-4 w-4 text-purple-600" />
                <span className="text-purple-800 font-medium">
                  代码优化建议
                </span>
              </div>
            </div>

            <Separator className="my-4" />

            <div className="text-xs text-gray-500 space-y-1">
              <p className="flex items-center space-x-1">
                <Sparkles className="h-3 w-3" />
                <span>基于本地AI模型，确保代码安全</span>
              </p>
              <p className="text-gray-400">数据不出域，隐私有保障</p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
