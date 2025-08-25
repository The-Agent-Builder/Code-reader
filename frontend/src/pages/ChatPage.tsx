import { useNavigate, useOutletContext } from "react-router-dom";
import ChatInterface from "../components/ChatInterface";
import { useProject } from "../contexts/ProjectContext";

interface OutletContext {
  currentVersionId: string;
}

export default function ChatPage() {
  const navigate = useNavigate();
  const { currentVersionId } = useOutletContext<OutletContext>();
  const { getProjectUrl } = useProject();

  const handleBack = () => {
    navigate(getProjectUrl());
  };

  return (
    <ChatInterface onBack={handleBack} currentVersionId={currentVersionId} />
  );
}
