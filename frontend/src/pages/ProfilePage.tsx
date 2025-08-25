import { useNavigate } from "react-router-dom";
import PersonalSpace from "../components/PersonalSpace";
import { useProject } from "../contexts/ProjectContext";

export default function ProfilePage() {
  const navigate = useNavigate();
  const { getProjectUrl } = useProject();

  const handleBack = () => {
    navigate(getProjectUrl());
  };

  return <PersonalSpace onBack={handleBack} />;
}
