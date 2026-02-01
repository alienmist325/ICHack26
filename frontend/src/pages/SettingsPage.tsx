import styled from "styled-components";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import BackgroundPattern from "../components/BackgroundPattern";
import Button from "../components/FormElements/Button";
import CardComponent from "../components/FormElements/Card";
import PageHeader from "../components/PageHeader";
import { colors, spacing, animations } from "../constants";
import UnifiedHeader from "../components/layout/UnifiedHeader";
import { FooterContainer } from "../components/layout/FooterContainer";

const PageContainer = styled.div`
  min-height: 100vh;
  width: 100vw;
  box-sizing: border-box;
  background: ${colors.lightBg};
  padding-top: 80px;
  padding-bottom: 60px;
  padding-left: 20px;
  padding-right: 20px;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const SettingsContainer = styled(CardComponent)`
  max-width: 600px;
  width: 100%;
  animation: slideUp 0.6s ease-out;

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(40px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;

const SettingGroup = styled.div`
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid ${colors.borderColor};

  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
  }
`;

const SettingLabel = styled.label`
  display: block;
  font-size: 1rem;
  color: ${colors.medText};
  margin-bottom: 0.5rem;
  font-weight: 500;
`;

const SettingDescription = styled.p`
  font-size: 0.9rem;
  color: ${colors.lightText};
  margin: 0.5rem 0 0 0;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 2rem;

  @media (max-width: 600px) {
    flex-direction: column;
  }
`;

export function SettingsPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <>
      <UnifiedHeader />
      <PageContainer>
        <SettingsContainer>
          <PageHeader
            title="Settings"
            subtitle="Manage your account preferences"
            showBackButton={true}
            onBack={() => navigate("/")}
          />

          <SettingGroup>
            <SettingLabel>Theme</SettingLabel>
            <SettingDescription>
              Customize your app appearance (Coming soon)
            </SettingDescription>
          </SettingGroup>

          <SettingGroup>
            <SettingLabel>Notifications</SettingLabel>
            <SettingDescription>
              Manage notification preferences (Coming soon)
            </SettingDescription>
          </SettingGroup>

          <SettingGroup>
            <SettingLabel>Privacy</SettingLabel>
            <SettingDescription>
              Control your privacy settings (Coming soon)
            </SettingDescription>
          </SettingGroup>

          <SettingGroup>
            <SettingLabel>Account</SettingLabel>
            <SettingDescription>
              Manage your account information (Coming soon)
            </SettingDescription>
          </SettingGroup>

          <ButtonGroup>
            <Button
              variant="secondary"
              onClick={() => navigate("/")}
              style={{ flex: 1 }}
            >
              Back to Home
            </Button>
            <Button
              variant="danger"
              onClick={handleLogout}
              style={{ flex: 1 }}
            >
              Logout
            </Button>
          </ButtonGroup>
        </SettingsContainer>
      </PageContainer>
      <FooterContainer />
    </>
  );
}
