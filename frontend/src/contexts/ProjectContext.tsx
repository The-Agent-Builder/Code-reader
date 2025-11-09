import React, { createContext, useContext, useState, ReactNode } from "react";
import { api } from "../services/api";

interface RepositoryInfo {
    id: number;
    name: string;
    full_name: string;
    url: string;
    description: string;
    language: string;
    created_at: string;
    updated_at: string;
    claude_session_id?: string;
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

// 认证上下文
interface AuthContextType {
    isAuthenticated: boolean;
    login: (password: string) => Promise<boolean>;
    logout: () => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);
const AuthContext = createContext<AuthContextType | undefined>(undefined);

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

export function AuthProvider({ children }: { children: ReactNode }) {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
        // 从localStorage检查认证状态
        return localStorage.getItem("isAuthenticated") === "true";
    });

    const login = async (password: string): Promise<boolean> => {
        try {
            const result = await api.verifyPassword(password);
            if (result.success) {
                setIsAuthenticated(true);
                localStorage.setItem("isAuthenticated", "true");
                return true;
            }
            return false;
        } catch (error) {
            console.error("密码验证失败:", error);
            return false;
        }
    };

    const logout = () => {
        setIsAuthenticated(false);
        localStorage.removeItem("isAuthenticated");
    };

    return (
        <AuthContext.Provider
            value={{
                isAuthenticated,
                login,
                logout,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useProject() {
    const context = useContext(ProjectContext);
    if (context === undefined) {
        throw new Error("useProject must be used within a ProjectProvider");
    }
    return context;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}
