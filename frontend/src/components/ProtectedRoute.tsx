import { ReactNode } from "react";
import { useAuth } from "../contexts/ProjectContext";
import LoginForm from "./LoginForm";

interface ProtectedRouteProps {
    children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated } = useAuth();

    if (!isAuthenticated) {
        return <LoginForm />;
    }

    return <>{children}</>;
}
