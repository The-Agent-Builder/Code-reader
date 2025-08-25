import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import { router } from "./router/index.tsx";
import { ProjectProvider } from "./contexts/ProjectContext.tsx";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <ProjectProvider>
    <RouterProvider router={router} />
  </ProjectProvider>
);
