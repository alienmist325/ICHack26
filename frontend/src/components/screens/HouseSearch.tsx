import styled from "styled-components";
import { useGlobalData } from "../hooks/useGlobalData";
import { HouseCard } from "../layout/HouseCard";
import { FilterPane } from "../layout/FilterPane";

const ContentArea = styled.div`
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 0;
`;

const BottomRightCorner = styled.div`
  position: absolute;
  right: 0;
  bottom: 0;
  margin: 0.75rem;
`;

const VerticalList = styled.div`
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
`;

const Layout = styled.div`
  display: flex;
  flex-direction: row;
  height: 100%;
  overflow: hidden;
`;

const SidebarContainer = styled.div`
  flex: 0 0 auto;
  min-height: 0;
`;

export function HouseSearch() {
  const { houses } = useGlobalData();

  return (
    <ContentArea>
      <Layout>
        <SidebarContainer>
          <FilterPane />
        </SidebarContainer>

        <VerticalList>
          {houses.map((house) => (
            <HouseCard key={house.id} house={house} />
          ))}
        </VerticalList>
      </Layout>
    </ContentArea>
  );
}
