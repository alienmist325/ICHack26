import styled from "styled-components";
import { useNavigate } from "react-router-dom";

const PageContainer = styled.div`
  width: 100vw;
  box-sizing: border-box;
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
`;

const Content = styled.div`
  background: white;
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  max-width: 600px;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  color: #667eea;
  margin: 0 0 1rem 0;
`;

const Description = styled.p`
  font-size: 1.1rem;
  color: #718096;
  margin: 0 0 2rem 0;
  line-height: 1.6;
`;

const BackButton = styled.button`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
  }
`;

export function FavoritesPage() {
  const navigate = useNavigate();

  return (
    <PageContainer>
      <Content>
        <Title>Favorites</Title>
        <Description>
          Your favorite properties will appear here. This feature is coming
          soon! Browse properties on the home page and add them to your
          favorites.
        </Description>
        <BackButton onClick={() => navigate("/")}>Back to Home</BackButton>
      </Content>
    </PageContainer>
  );
}
