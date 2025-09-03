import { createContext, useContext, useState, ReactNode } from "react";

interface ProjectContextType {
  currentProjectName: string;
  setCurrentProjectName: (name: string) => void;
  getProjectUrl: (projectName?: string) => string;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [currentProjectName, setCurrentProjectName] =
    useState<string>("my-awesome-project");

  const getProjectUrl = (projectName?: string) => {
    return `/result/${projectName || currentProjectName}`;
  };

  return (
    <ProjectContext.Provider
      value={{
        currentProjectName,
        setCurrentProjectName,
        getProjectUrl,
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
