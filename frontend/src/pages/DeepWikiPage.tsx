import { useNavigate, useOutletContext, useParams } from "react-router-dom";
import DeepWikiInterface from "../components/DeepWikiInterface";

interface OutletContext {
  currentVersionId: string;
}

export default function DeepWikiPage() {
  const navigate = useNavigate();
  const { projectName } = useParams<{ projectName: string }>();
  const { currentVersionId } = useOutletContext<OutletContext>();

  const handleBackToUpload = () => {
    navigate("/upload");
  };

  const handleGoToProfile = () => {
    navigate("/profile");
  };

  return (
    <DeepWikiInterface
      onBackToUpload={handleBackToUpload}
      onGoToProfile={handleGoToProfile}
      currentVersionId={currentVersionId}
      projectName={projectName}
    />
  );
}
