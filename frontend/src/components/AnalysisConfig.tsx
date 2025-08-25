import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
import { RadioGroup, RadioGroupItem } from './ui/radio-group';
import { Label } from './ui/label';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { 
  FileText, 
  Folder, 
  FolderOpen,
  Code, 
  Settings, 
  ChevronRight, 
  ChevronDown,
  CheckCircle2,
  Search,
  Filter,
  FileCode,
  FileJson,
  Database,
  Palette,
  Globe,
  FileImage,
  Archive,
  FileSpreadsheet,
  Info
} from 'lucide-react';

interface AnalysisConfigProps {
  selectedFiles: FileList;
  onStartAnalysis: (config: AnalysisConfiguration) => void;
  onBack: () => void;
}

interface AnalysisConfiguration {
  mode: 'overall' | 'individual';
  selectedFiles: string[];
}

interface FileTreeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  size?: number;
  extension?: string;
  selected: boolean;
  expanded?: boolean;
  children?: FileTreeNode[];
  parent?: FileTreeNode;
}

const getFileIcon = (extension: string) => {
  const ext = extension.toLowerCase();
  
  // 根据文件类型返回对应的lucide图标组件
  if (['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rs', 'php', 'rb', 'cs', 'swift', 'kt'].includes(ext)) {
    return <FileCode className="h-4 w-4 text-blue-600" />;
  }
  if (['vue', 'html', 'htm'].includes(ext)) {
    return <Globe className="h-4 w-4 text-orange-600" />;
  }
  if (['css', 'scss', 'sass', 'less'].includes(ext)) {
    return <Palette className="h-4 w-4 text-pink-600" />;
  }
  if (['json', 'yml', 'yaml', 'xml', 'ini', 'conf', 'config'].includes(ext)) {
    return <FileJson className="h-4 w-4 text-yellow-600" />;
  }
  if (['sql', 'db', 'sqlite'].includes(ext)) {
    return <Database className="h-4 w-4 text-green-600" />;
  }
  if (['md', 'txt', 'rst', 'adoc'].includes(ext)) {
    return <FileText className="h-4 w-4 text-gray-600" />;
  }
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico'].includes(ext)) {
    return <FileImage className="h-4 w-4 text-purple-600" />;
  }
  if (['zip', 'rar', 'tar', 'gz', '7z'].includes(ext)) {
    return <Archive className="h-4 w-4 text-gray-600" />;
  }
  if (['xlsx', 'xls', 'csv'].includes(ext)) {
    return <FileSpreadsheet className="h-4 w-4 text-green-600" />;
  }
  
  // 默认文件图标
  return <FileText className="h-4 w-4 text-gray-500" />;
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

// 构建文件树结构
const buildFileTree = (fileList: FileList): FileTreeNode => {
  const root: FileTreeNode = {
    name: 'root',
    path: '',
    type: 'folder',
    selected: true,
    expanded: true,
    children: []
  };

  const folderMap = new Map<string, FileTreeNode>();
  folderMap.set('', root);

  // 首先创建所有文件节点
  for (let i = 0; i < fileList.length; i++) {
    const file = fileList[i];
    const fullPath = file.webkitRelativePath || file.name;
    const pathParts = fullPath.split('/');
    const fileName = pathParts[pathParts.length - 1];
    const extension = fileName.split('.').pop() || '';

    // 创建所有父文件夹
    let currentPath = '';
    for (let j = 0; j < pathParts.length - 1; j++) {
      const folderName = pathParts[j];
      const parentPath = currentPath;
      currentPath = currentPath ? `${currentPath}/${folderName}` : folderName;

      if (!folderMap.has(currentPath)) {
        const folderNode: FileTreeNode = {
          name: folderName,
          path: currentPath,
          type: 'folder',
          selected: true,
          expanded: true,
          children: []
        };

        folderMap.set(currentPath, folderNode);

        // 添加到父文件夹
        const parent = folderMap.get(parentPath);
        if (parent) {
          parent.children!.push(folderNode);
          folderNode.parent = parent;
        }
      }
    }

    // 创建文件节点
    const fileNode: FileTreeNode = {
      name: fileName,
      path: fullPath,
      type: 'file',
      size: file.size,
      extension,
      selected: true
    };

    // 添加到父文件夹
    const parentPath = pathParts.slice(0, -1).join('/');
    const parent = folderMap.get(parentPath);
    if (parent) {
      parent.children!.push(fileNode);
      fileNode.parent = parent;
    }
  }

  // 对所有文件夹的children进行排序：文件夹在前，文件在后，然后按名称排序
  const sortChildren = (node: FileTreeNode) => {
    if (node.children) {
      node.children.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'folder' ? -1 : 1;
        }
        return a.name.localeCompare(b.name);
      });
      node.children.forEach(sortChildren);
    }
  };

  sortChildren(root);
  return root;
};

// 递归计算文件夹的选择状态
const updateFolderSelection = (node: FileTreeNode): { selected: number; total: number } => {
  if (node.type === 'file') {
    return { selected: node.selected ? 1 : 0, total: 1 };
  }

  let selectedCount = 0;
  let totalCount = 0;

  if (node.children) {
    for (const child of node.children) {
      const { selected, total } = updateFolderSelection(child);
      selectedCount += selected;
      totalCount += total;
    }
  }

  // 更新文件夹的选择状态
  if (selectedCount === 0) {
    node.selected = false;
  } else if (selectedCount === totalCount) {
    node.selected = true;
  } else {
    // 部分选择状态，这里我们设为true但需要特殊显示
    node.selected = true;
  }

  return { selected: selectedCount, total: totalCount };
};

// 获取所有选中的文件路径
const getSelectedFiles = (node: FileTreeNode, result: string[] = []): string[] => {
  if (node.type === 'file' && node.selected) {
    result.push(node.path);
  } else if (node.children) {
    for (const child of node.children) {
      getSelectedFiles(child, result);
    }
  }
  return result;
};

// 切换节点选择状态
const toggleNodeSelection = (node: FileTreeNode, selected: boolean) => {
  node.selected = selected;
  if (node.children) {
    for (const child of node.children) {
      toggleNodeSelection(child, selected);
    }
  }
};

// 获取文件统计信息
const getFileStats = (node: FileTreeNode) => {
  const stats = {
    code: 0,
    config: 0,
    docs: 0,
    total: 0,
    selected: 0,
    totalSize: 0
  };

  const traverse = (n: FileTreeNode) => {
    if (n.type === 'file') {
      stats.total++;
      if (n.selected) {
        stats.selected++;
        stats.totalSize += n.size || 0;
      }

      const ext = n.extension?.toLowerCase() || '';
      const codeExtensions = ['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'go', 'rs', 'php', 'rb', 'cs', 'swift', 'kt', 'vue'];
      const configExtensions = ['json', 'yml', 'yaml', 'xml', 'ini', 'conf', 'config'];
      const docExtensions = ['md', 'txt', 'rst', 'adoc'];

      if (codeExtensions.includes(ext)) {
        stats.code++;
      } else if (configExtensions.includes(ext)) {
        stats.config++;
      } else if (docExtensions.includes(ext)) {
        stats.docs++;
      }
    } else if (n.children) {
      n.children.forEach(traverse);
    }
  };

  traverse(node);
  return stats;
};

// 获取所有可见的文件节点（按显示顺序）
const getAllVisibleNodes = (node: FileTreeNode, result: FileTreeNode[] = []): FileTreeNode[] => {
  if (node.type === 'file' || node.children) {
    result.push(node);
  }
  
  if (node.type === 'folder' && node.expanded && node.children) {
    for (const child of node.children) {
      getAllVisibleNodes(child, result);
    }
  }
  
  return result;
};

// 批量选择范围内的节点
const selectNodeRange = (startNode: FileTreeNode, endNode: FileTreeNode, allNodes: FileTreeNode[], selected: boolean) => {
  const startIndex = allNodes.findIndex(node => node.path === startNode.path);
  const endIndex = allNodes.findIndex(node => node.path === endNode.path);
  
  if (startIndex === -1 || endIndex === -1) return;
  
  const minIndex = Math.min(startIndex, endIndex);
  const maxIndex = Math.max(startIndex, endIndex);
  
  for (let i = minIndex; i <= maxIndex; i++) {
    const node = allNodes[i];
    if (node.type === 'file') {
      node.selected = selected;
    } else if (node.type === 'folder') {
      toggleNodeSelection(node, selected);
    }
  }
};

// FileTreeNodeComponent - 单独的组件来处理每个节点
const FileTreeNodeComponent = ({ 
  node, 
  depth, 
  onToggleSelection, 
  onToggleExpansion,
  onShiftClick,
  isLastClicked
}: {
  node: FileTreeNode;
  depth: number;
  onToggleSelection: (node: FileTreeNode, isShiftClick: boolean, event: React.MouseEvent) => void;
  onToggleExpansion: (node: FileTreeNode) => void;
  onShiftClick: (node: FileTreeNode, selected: boolean) => void;
  isLastClicked: boolean;
}) => {
  const checkboxRef = useRef<HTMLInputElement>(null);
  
  const isPartiallySelected = node.type === 'folder' && node.children && 
    node.children.some(child => child.selected) && 
    !node.children.every(child => child.selected || (child.type === 'folder' && child.children?.every(c => !c.selected)));

  // 使用 useEffect 来设置 indeterminate 状态
  useEffect(() => {
    if (checkboxRef.current) {
      checkboxRef.current.indeterminate = isPartiallySelected;
    }
  }, [isPartiallySelected]);

  const handleClick = (e: React.MouseEvent) => {
    onToggleSelection(node, e.shiftKey, e);
  };

  return (
    <div className="select-none">
      <div
        className={`
          flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors
          ${node.selected && !isPartiallySelected ? 'bg-blue-50' : ''}
          ${isLastClicked ? 'ring-2 ring-blue-300 ring-opacity-50' : ''}
        `}
        style={{ paddingLeft: `${depth * 20 + 12}px` }}
      >
        {node.type === 'folder' && node.children && node.children.length > 0 && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onToggleExpansion(node);
            }}
            className="p-1 hover:bg-gray-200 rounded"
          >
            {node.expanded ? (
              <ChevronDown className="h-3 w-3 text-gray-500" />
            ) : (
              <ChevronRight className="h-3 w-3 text-gray-500" />
            )}
          </button>
        )}
        
        <div
          className="flex items-center space-x-3 flex-1 min-w-0"
          onClick={handleClick}
        >
          <div className="relative">
            <Checkbox 
              checked={node.selected && !isPartiallySelected}
              onChange={() => handleClick({} as React.MouseEvent)}
            />
            {/* 隐藏的原生checkbox用于设置indeterminate状态 */}
            <input
              ref={checkboxRef}
              type="checkbox"
              className="absolute inset-0 opacity-0 pointer-events-none"
              checked={node.selected && !isPartiallySelected}
              readOnly
            />
          </div>
          
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            <div className="flex-shrink-0">
              {node.type === 'folder' ? (
                node.expanded ? <FolderOpen className="h-4 w-4 text-blue-500" /> : <Folder className="h-4 w-4 text-blue-500" />
              ) : (
                node.extension ? getFileIcon(node.extension) : <FileText className="h-4 w-4 text-gray-500" />
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {node.name}
                </p>
                {node.type === 'file' && node.extension && (
                  <Badge variant="secondary" className="text-xs">
                    {node.extension.toUpperCase()}
                  </Badge>
                )}
              </div>
              
              {node.type === 'file' && (
                <p className="text-xs text-gray-500">
                  {formatFileSize(node.size || 0)}
                </p>
              )}
            </div>
          </div>

          {node.selected && !isPartiallySelected && (
            <CheckCircle2 className="h-4 w-4 text-blue-600 flex-shrink-0" />
          )}
        </div>
      </div>

      {node.type === 'folder' && node.expanded && node.children && (
        <div>
          {node.children.map(child => 
            <FileTreeNodeComponent
              key={child.path}
              node={child}
              depth={depth + 1}
              onToggleSelection={onToggleSelection}
              onToggleExpansion={onToggleExpansion}
              onShiftClick={onShiftClick}
              isLastClicked={isLastClicked && child.path === node.path}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default function AnalysisConfig({ selectedFiles, onStartAnalysis, onBack }: AnalysisConfigProps) {
  const [analysisMode, setAnalysisMode] = useState<'overall' | 'individual'>('overall');
  const [fileTree, setFileTree] = useState<FileTreeNode>(() => buildFileTree(selectedFiles));
  const [lastClickedNode, setLastClickedNode] = useState<FileTreeNode | null>(null);

  // 更新文件夹选择状态
  const updateTreeSelection = (tree: FileTreeNode) => {
    updateFolderSelection(tree);
    setFileTree({ ...tree });
  };

  const handleShiftClick = useCallback((targetNode: FileTreeNode, selected: boolean) => {
    if (lastClickedNode) {
      const allVisibleNodes = getAllVisibleNodes(fileTree).filter(node => node.type === 'file');
      selectNodeRange(lastClickedNode, targetNode, allVisibleNodes, selected);
      updateTreeSelection(fileTree);
    }
  }, [lastClickedNode, fileTree]);

  const toggleFileSelection = useCallback((targetNode: FileTreeNode, isShiftClick: boolean, event: React.MouseEvent) => {
    if (isShiftClick && lastClickedNode && targetNode.type === 'file') {
      // Shift+点击：范围选择
      const newSelected = !targetNode.selected;
      handleShiftClick(targetNode, newSelected);
    } else {
      // 普通点击：单个切换
      const newSelected = !targetNode.selected;
      toggleNodeSelection(targetNode, newSelected);
      updateTreeSelection(fileTree);
    }
    
    // 只有在点击文件时才更新lastClickedNode
    if (targetNode.type === 'file') {
      setLastClickedNode(targetNode);
    }
  }, [lastClickedNode, handleShiftClick, fileTree]);

  const toggleFolderExpansion = (targetNode: FileTreeNode) => {
    targetNode.expanded = !targetNode.expanded;
    setFileTree({ ...fileTree });
  };

  const toggleSelectAll = () => {
    const stats = getFileStats(fileTree);
    const newSelected = stats.selected !== stats.total;
    toggleNodeSelection(fileTree, newSelected);
    updateTreeSelection(fileTree);
  };

  const handleStartAnalysis = () => {
    const selectedFilePaths = getSelectedFiles(fileTree);
    
    onStartAnalysis({
      mode: analysisMode,
      selectedFiles: selectedFilePaths
    });
  };

  const stats = getFileStats(fileTree);

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="flex-shrink-0 p-6 bg-white/80 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" onClick={onBack} className="p-2">
                <ChevronRight className="h-4 w-4 rotate-180" />
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">分析配置</h1>
                <p className="text-gray-600">选择分析模式并筛选需要分析的文件</p>
              </div>
            </div>

            {/* Header右侧操作区 */}
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                onClick={toggleSelectAll}
              >
                {stats.selected === stats.total ? '取消全选' : '全选'}
              </Button>
              
              <Button 
                onClick={handleStartAnalysis}
                disabled={stats.selected === 0}
                className="px-8"
              >
                <Search className="h-4 w-4 mr-2" />
                开始分析 ({stats.selected})
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* 分析模式配置栏 */}
      <div className="flex-shrink-0 p-4 bg-white/60 backdrop-blur-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-8">
              {/* 分析模式选择 */}
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Settings className="h-5 w-5 text-blue-600" />
                  <h3 className="font-semibold text-gray-900">分析模式</h3>
                </div>
                
                <RadioGroup 
                  value={analysisMode} 
                  onValueChange={(value: 'overall' | 'individual') => setAnalysisMode(value)}
                  className="flex items-center space-x-6"
                >
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="overall" id="overall" />
                    <Label htmlFor="overall" className="font-medium">
                      代码整体分析
                    </Label>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <RadioGroupItem value="individual" id="individual" />
                    <Label htmlFor="individual" className="font-medium">
                      代码逐个解析
                    </Label>
                  </div>
                </RadioGroup>
              </div>
            </div>

            {/* 统计信息 */}
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 px-3 py-1 bg-blue-50 rounded-lg">
                  <Code className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-700">代码 {stats.code}</span>
                </div>
                
                <div className="flex items-center space-x-2 px-3 py-1 bg-green-50 rounded-lg">
                  <Settings className="h-4 w-4 text-green-600" />
                  <span className="text-sm font-medium text-green-700">配置 {stats.config}</span>
                </div>
                
                <div className="flex items-center space-x-2 px-3 py-1 bg-purple-50 rounded-lg">
                  <FileText className="h-4 w-4 text-purple-600" />
                  <span className="text-sm font-medium text-purple-700">文档 {stats.docs}</span>
                </div>
              </div>

              <Separator orientation="vertical" className="h-6" />

              <div className="text-sm text-gray-600">
                <span className="font-medium">{formatFileSize(stats.totalSize)}</span>
                <span className="mx-2">·</span>
                <span className="font-medium">{stats.selected}/{stats.total}</span> 文件
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 文件树主体区域 - 全屏滚动 */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full max-w-7xl mx-auto p-6">
          <Card className="h-full flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Filter className="h-5 w-5 text-blue-600" />
                  <h3 className="font-semibold text-gray-900">文件结构筛选</h3>
                  <Badge variant="outline" className="ml-2">
                    {stats.selected} 个文件已选择
                  </Badge>
                </div>
                
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <Info className="h-4 w-4" />
                  <span>按住 Shift 点击可批量选择</span>
                </div>
              </div>
            </div>

            <div className="flex-1 overflow-hidden">
              <ScrollArea className="h-full">
                <div className="p-4">
                  <div className="space-y-1">
                    {fileTree.children && fileTree.children.map(child => 
                      <FileTreeNodeComponent
                        key={child.path}
                        node={child}
                        depth={0}
                        onToggleSelection={toggleFileSelection}
                        onToggleExpansion={toggleFolderExpansion}
                        onShiftClick={handleShiftClick}
                        isLastClicked={lastClickedNode?.path === child.path}
                      />
                    )}
                  </div>
                </div>
              </ScrollArea>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}