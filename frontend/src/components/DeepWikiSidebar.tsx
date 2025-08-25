import { ChevronDown, ChevronRight, BarChart3, Network, Layers } from 'lucide-react';
import { Button } from './ui/button';

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

const menuItems = [
  {
    id: 'overview',
    label: '项目概览',
    icon: BarChart3,
    children: [
      { id: 'metrics', label: '关键指标' },
      { id: 'summary', label: '项目摘要' },
    ]
  },
  {
    id: 'data-models',
    label: '数据模型浏览器',
    icon: Layers,
    children: [
      { id: 'entity-diagram', label: '实体关系图' },
      { id: 'model-list', label: '模型列表' },
    ]
  },
  {
    id: 'architecture',
    label: '架构边界',
    icon: Network,
    children: [
      { id: 'external-deps', label: '外部依赖' },
      { id: 'internal-apis', label: '内部接口' },
      { id: 'services', label: '服务架构' },
    ]
  },
  {
    id: 'call-graph',
    label: '调用图谱',
    icon: Network,
    children: [
      { id: 'module-graph', label: '模块依赖图' },
      { id: 'function-calls', label: '函数调用链' },
    ]
  },
];

export function Sidebar({ activeSection, onSectionChange }: SidebarProps) {
  return (
    <nav className="p-4 space-y-2">
      {menuItems.map((item) => {
        const Icon = item.icon;
        const isExpanded = activeSection.startsWith(item.id) || 
                          item.children?.some(child => child.id === activeSection);
        
        return (
          <div key={item.id} className="space-y-1">
            <Button
              variant="ghost"
              className={`
                w-full justify-start px-2 py-1 h-auto
                ${activeSection === item.id ? 'bg-blue-100 text-blue-700' : 'text-gray-700 hover:bg-gray-100'}
              `}
              onClick={() => onSectionChange(item.id)}
            >
              <Icon className="h-4 w-4 mr-2" />
              <span className="text-sm">{item.label}</span>
            </Button>
            
            {isExpanded && item.children && (
              <div className="ml-6 space-y-1">
                {item.children.map((child) => (
                  <Button
                    key={child.id}
                    variant="ghost"
                    className={`
                      w-full justify-start px-2 py-1 h-auto text-sm
                      ${activeSection === child.id ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-50'}
                    `}
                    onClick={() => onSectionChange(child.id)}
                  >
                    {child.label}
                  </Button>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}