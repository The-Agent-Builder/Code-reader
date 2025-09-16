import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./router/index.tsx";
import { ProjectProvider, AuthProvider } from "./contexts/ProjectContext.tsx";
import "./index.css";

createRoot(document.getElementById("root")!).render(
    <AuthProvider>
        <ProjectProvider>
            <RouterProvider router={router} />
        </ProjectProvider>
    </AuthProvider>
);
