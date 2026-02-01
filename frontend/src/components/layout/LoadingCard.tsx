import styled, { keyframes } from "styled-components";

const shimmer = keyframes`
  0% {
    background-position: -1200px 0;
  }
  100% {
    background-position: 1200px 0;
  }
`;

const CardContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1.5rem;
  border-bottom: 1px solid #eee;
`;

const ImageSkeletonContainer = styled.div`
  width: 250px;
  height: 200px;
  flex-shrink: 0;
  border-radius: 8px;
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 1200px 100%;
  animation: ${shimmer} 2s infinite;
`;

const ContentContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
`;

const SkeletonLine = styled.div<{ width?: string }>`
  height: 0.9rem;
  width: ${(props) => props.width || "100%"};
  border-radius: 4px;
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 1200px 100%;
  animation: ${shimmer} 2s infinite;
`;

const SkeletonSmall = styled(SkeletonLine)`
  height: 0.8rem;
  margin-top: 0.25rem;
  width: 70%;
`;

const SkeletonLarge = styled(SkeletonLine)`
  height: 1.2rem;
  width: 60%;
`;

export function LoadingCard() {
  return (
    <CardContainer>
      <ImageSkeletonContainer />
      <ContentContainer>
        <SkeletonLarge />
        <SkeletonLine width="85%" />
        <SkeletonLine width="80%" />
        <SkeletonSmall />
        <SkeletonSmall />
        <div style={{ marginTop: "0.5rem" }}>
          <SkeletonLine width="40%" />
        </div>
      </ContentContainer>
    </CardContainer>
  );
}
