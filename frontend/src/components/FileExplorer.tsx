import { useState } from "react";
import { ChevronDown, ChevronRight, File, Folder } from "lucide-react";
import { Button } from "./ui/button";

interface FileNode {
  name: string;
  type: "file" | "folder";
  path: string;
  children?: FileNode[];
}

interface FileExplorerProps {
  selectedFile: string | null;
  onFileSelect: (path: string) => void;
  fileTree?: FileNode | null;
  isLoading?: boolean;
  error?: string | null;
}

const mockFileTree: FileNode = {
  name: "src",
  type: "folder",
  path: "src",
  children: [
    {
      name: "api",
      type: "folder",
      path: "src/api",
      children: [
        { name: "routes.py", type: "file", path: "src/api/routes.py" },
        { name: "auth.py", type: "file", path: "src/api/auth.py" },
        { name: "posts.py", type: "file", path: "src/api/posts.py" },
        { name: "users.py", type: "file", path: "src/api/users.py" },
      ],
    },
    {
      name: "models",
      type: "folder",
      path: "src/models",
      children: [
        { name: "user.py", type: "file", path: "src/models/user.py" },
        { name: "post.py", type: "file", path: "src/models/post.py" },
        { name: "__init__.py", type: "file", path: "src/models/__init__.py" },
      ],
    },
    {
      name: "services",
      type: "folder",
      path: "src/services",
      children: [
        {
          name: "auth_service.py",
          type: "file",
          path: "src/services/auth_service.py",
        },
        {
          name: "post_service.py",
          type: "file",
          path: "src/services/post_service.py",
        },
      ],
    },
    {
      name: "utils",
      type: "folder",
      path: "src/utils",
      children: [
        { name: "helpers.py", type: "file", path: "src/utils/helpers.py" },
        {
          name: "validators.py",
          type: "file",
          path: "src/utils/validators.py",
        },
      ],
    },
    { name: "app.py", type: "file", path: "src/app.py" },
    { name: "config.py", type: "file", path: "src/config.py" },
  ],
};

function FileTreeNode({
  node,
  level = 0,
  selectedFile,
  onFileSelect,
}: {
  node: FileNode;
  level?: number;
  selectedFile: string | null;
  onFileSelect: (path: string) => void;
}) {
  const [isExpanded, setIsExpanded] = useState(level < 2); // Auto-expand first 2 levels
  const isSelected = selectedFile === node.path;

  const handleClick = () => {
    if (node.type === "folder") {
      setIsExpanded(!isExpanded);
    } else {
      onFileSelect(node.path);
    }
  };

  return (
    <div>
      <Button
        variant="ghost"
        className={`
          w-full justify-start px-2 py-1 h-auto text-sm
          ${
            isSelected
              ? "bg-blue-100 text-blue-700"
              : "text-gray-700 hover:bg-gray-100"
          }
        `}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        onClick={handleClick}
      >
        {node.type === "folder" && (
          <>
            {isExpanded ? (
              <ChevronDown className="h-3 w-3 mr-1" />
            ) : (
              <ChevronRight className="h-3 w-3 mr-1" />
            )}
            <Folder className="h-4 w-4 mr-2 text-blue-500" />
          </>
        )}
        {node.type === "file" && (
          <File className="h-4 w-4 mr-2 ml-4 text-gray-500" />
        )}
        <span className="truncate">{node.name}</span>
      </Button>

      {node.type === "folder" && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode
              key={child.path}
              node={child}
              level={level + 1}
              selectedFile={selectedFile}
              onFileSelect={onFileSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function FileExplorer({
  selectedFile,
  onFileSelect,
  fileTree,
  isLoading,
  error,
}: FileExplorerProps) {
  // 如果正在加载
  if (isLoading) {
    return (
      <div className="p-4 flex items-center justify-center">
        <div className="flex items-center space-x-2 text-gray-500">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
          <span className="text-sm">Loading files...</span>
        </div>
      </div>
    );
  }

  // 如果有错误
  if (error) {
    return (
      <div className="p-4">
        <div className="text-red-600 text-sm">
          <p className="font-medium">Error loading files:</p>
          <p className="mt-1">{error}</p>
        </div>
      </div>
    );
  }

  // 如果没有文件树数据，显示静态数据（用于my-awesome-project）
  const treeToRender = fileTree || mockFileTree;

  // 安全检查
  if (!treeToRender) {
    return (
      <div className="p-4">
        <div className="text-gray-500 text-sm py-4">No file tree available</div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-1">
      {/* 渲染文件树 */}
      {treeToRender.children &&
      Array.isArray(treeToRender.children) &&
      treeToRender.children.length > 0 ? (
        treeToRender.children.map((child) => (
          <FileTreeNode
            key={child.path}
            node={child}
            selectedFile={selectedFile}
            onFileSelect={onFileSelect}
          />
        ))
      ) : (
        <div className="text-gray-500 text-sm py-4">No files found</div>
      )}

      {/* 如果使用静态数据，显示根级文件 */}
      {!fileTree && (
        <div className="pt-2 border-t border-gray-200 mt-4">
          {[
            { name: "README.md", path: "README.md" },
            { name: "requirements.txt", path: "requirements.txt" },
            { name: ".env.example", path: ".env.example" },
          ].map((file) => (
            <Button
              key={file.path}
              variant="ghost"
              className={`
                w-full justify-start px-2 py-1 h-auto text-sm
                ${
                  selectedFile === file.path
                    ? "bg-blue-100 text-blue-700"
                    : "text-gray-700 hover:bg-gray-100"
                }
              `}
              onClick={() => onFileSelect(file.path)}
            >
              <File className="h-4 w-4 mr-2 text-gray-500" />
              <span className="truncate">{file.name}</span>
            </Button>
          ))}
        </div>
      )}
    </div>
  );
}
