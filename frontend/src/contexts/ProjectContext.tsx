import { createContext, useContext, useState, ReactNode } from "react";

interface RepositoryInfo {
  id: number;
  name: string;
  full_name: string;
  url: string;
  description: string;
  language: string;
  created_at: string;
  updated_at: string;
}

interface ProjectContextType {
  currentProjectName: string;
  setCurrentProjectName: (name: string) => void;
  getProjectUrl: (projectName?: string) => string;
  // 新增：支持通过full_name哈希值生成URL
  getProjectUrlByFullName: (fullNameHash?: string) => string;
  // 新增：当前仓库信息管理
  currentRepository: RepositoryInfo | null;
  setCurrentRepository: (repository: RepositoryInfo | null) => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [currentProjectName, setCurrentProjectName] =
    useState<string>("my-awesome-project");
  const [currentRepository, setCurrentRepository] =
    useState<RepositoryInfo | null>(null);

  const getProjectUrl = (projectName?: string) => {
    return `/result/${projectName || currentProjectName}`;
  };

  const getProjectUrlByFullName = (fullNameHash?: string) => {
    return `/result/${fullNameHash || currentProjectName}`;
  };

  return (
    <ProjectContext.Provider
      value={{
        currentProjectName,
        setCurrentProjectName,
        getProjectUrl,
        getProjectUrlByFullName,
        currentRepository,
        setCurrentRepository,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error("useProject must be used within a ProjectProvider");
  }
  return context;
}
