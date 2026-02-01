import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const PageContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
`;

const Header = styled.div`
  color: white;
  margin-bottom: 2rem;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  margin: 0 0 0.5rem 0;
`;

const Subtitle = styled.p`
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
`;

const SettingsContainer = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 600px;
`;

const SettingGroup = styled.div`
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid #e2e8f0;

  &:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
  }
`;

const SettingLabel = styled.label`
  display: block;
  font-size: 1rem;
  color: #2d3748;
  margin-bottom: 0.5rem;
  font-weight: 500;
`;

const SettingDescription = styled.p`
  font-size: 0.9rem;
  color: #718096;
  margin: 0.5rem 0 0 0;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
`;

const Button = styled.button<{ danger?: boolean }>`
  flex: 1;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  background: ${props => props.danger ? '#f56565' : '#667eea'};
  color: white;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px ${props => props.danger ? 'rgba(245, 101, 101, 0.4)' : 'rgba(102, 126, 234, 0.4)'};
  }
`;

export function SettingsPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <PageContainer>
      <Header>
        <Title>Settings</Title>
        <Subtitle>Manage your account preferences</Subtitle>
      </Header>
      
      <SettingsContainer>
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
          <Button onClick={() => navigate('/')}>Back to Home</Button>
          <Button danger onClick={handleLogout}>
            Logout
          </Button>
        </ButtonGroup>
      </SettingsContainer>
    </PageContainer>
  );
}
