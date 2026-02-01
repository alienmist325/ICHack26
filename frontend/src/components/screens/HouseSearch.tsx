import styled from "styled-components";
import { useGlobalData } from "../hooks/useGlobalData";
import { HouseCard } from "../layout/HouseCard";
import { FilterPane } from "../layout/FilterPane";
import { Pagination } from "../layout/Pagination";
import { LoadingCard } from "../layout/LoadingCard";
import { TravelTimeDisplay } from "../layout/TravelTimeDisplay";
import { colors, spacing } from "../../constants";
import { Button } from "../layout/Button";

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

const EmptyState = styled.div`
  padding: 3rem 2rem;
  text-align: center;
  color: ${colors.lightText};
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
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

const MainContent = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: ${colors.white};
  border-left: 2px solid ${colors.borderColor};
`;

const ListWrapper = styled.div`
  flex: 1;
  overflow-y: auto;
`;

export function HouseSearch() {
  const { houses, totalCount, currentPage, setCurrentPage, isLoading } =
    useGlobalData();
  const { houses, totalCount, currentPage, setCurrentPage, isLoading } =
    useGlobalData();

  const PAGE_SIZE = 10;
  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  return (
    <ContentArea>
      <Layout>
        <SidebarContainer>
          <FilterPane />
        </SidebarContainer>

        <MainContent>
          <ListWrapper>
            <VerticalList>
              <TravelTimeDisplay property_id={houses[0].id}></TravelTimeDisplay>
              {isLoading ? (
                // Show loading skeletons
                Array.from({ length: 3 }).map((_, i) => (
                  <LoadingCard key={`loading-${i}`} />
                ))
              ) : houses.length > 0 ? (
                houses.map((house) => (
                  <HouseCard key={house.id} house={house} />
                ))
              ) : (
                <EmptyState>
                  🔍
                  <p>No properties found. Try adjusting your filters.</p>
                </EmptyState>
              )}
            </VerticalList>
          </ListWrapper>

          {totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalCount={totalCount}
              pageSize={PAGE_SIZE}
              isLoading={isLoading}
              onPageChange={setCurrentPage}
            />
          )}
        </MainContent>
      </Layout>
    </ContentArea>
  );
}
