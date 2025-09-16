import { createBrowserRouter, Navigate } from "react-router-dom";
import Layout from "../components/Layout";
import UploadPage from "../pages/UploadPage";
import ConfigPage from "../pages/ConfigPage";
import AnalysisPage from "../pages/AnalysisPage";
import DeepWikiPage from "../pages/DeepWikiPage";
import BackgroundPage from "../pages/BackgroundPage";
import ProfilePage from "../pages/ProfilePage";
import ChatPage from "../pages/ChatPage";
import ProtectedRoute from "../components/ProtectedRoute";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <Layout />,
        children: [
            {
                index: true,
                element: <Navigate to="/upload" replace />,
            },
            {
                path: "upload",
                element: (
                    <ProtectedRoute>
                        <UploadPage />
                    </ProtectedRoute>
                ),
            },
            {
                path: "config",
                element: (
                    <ProtectedRoute>
                        <ConfigPage />
                    </ProtectedRoute>
                ),
            },
            {
                path: "analysis",
                element: (
                    <ProtectedRoute>
                        <AnalysisPage />
                    </ProtectedRoute>
                ),
            },
            {
                path: "result/:projectName",
                element: <DeepWikiPage />,
            },
            {
                path: "background",
                element: <BackgroundPage />,
            },
            {
                path: "profile",
                element: <ProfilePage />,
            },
            {
                path: "chat",
                element: <ChatPage />,
            },
        ],
    },
]);
