import styled from "styled-components";
import { useNavigate } from "react-router-dom";
import { FiHeart } from "react-icons/fi";
import BackgroundPattern from "../components/BackgroundPattern";
import Button from "../components/FormElements/Button";
import CardComponent from "../components/FormElements/Card";
import { colors } from "../constants";
import UnifiedHeader from "../components/layout/UnifiedHeader";
import { FooterContainer } from "../components/layout/FooterContainer";

const PageContainer = styled.div`
  min-height: 100vh;
  width: 100vw;
  box-sizing: border-box;
  background: ${colors.lightBg};
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
  padding-top: 100px;
  padding-bottom: 100px;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
`;

const Content = styled(CardComponent)`
  max-width: 600px;
  width: 100%;
  text-align: center;
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

const IconWrapper = styled.div`
  font-size: 4rem;
  color: ${colors.teal};
  margin-bottom: 1rem;
  display: inline-block;
  animation: heartbeat 1.5s ease-in-out infinite;

  @keyframes heartbeat {
    0%, 100% {
      transform: scale(1);
    }
    25% {
      transform: scale(1.05);
    }
    50% {
      transform: scale(1.1);
    }
    75% {
      transform: scale(1.05);
    }
  }
`;

const Title = styled.h1`
  font-size: 2.5rem;
  color: ${colors.teal};
  margin: 0 0 1rem 0;
`;

const Description = styled.p`
  font-size: 1.1rem;
  color: ${colors.lightText};
  margin: 0 0 2rem 0;
  line-height: 1.6;
`;

export function FavoritesPage() {
  const navigate = useNavigate();

  return (
    <>
      <UnifiedHeader />
      <PageContainer>
        <BackgroundPattern />
        <Content>
          <IconWrapper>
            <FiHeart fill="currentColor" />
          </IconWrapper>
          <Title>Favorites</Title>
          <Description>
            Your favorite properties will appear here. This feature is coming
            soon! Browse properties on the home page and add them to your
            favorites.
          </Description>
          <Button
            variant="primary"
            onClick={() => navigate("/")}
          >
            Back to Home
          </Button>
        </Content>
      </PageContainer>
      <FooterContainer />
    </>
  );
}
