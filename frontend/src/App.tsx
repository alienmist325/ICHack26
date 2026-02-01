import "./App.css";
import styled from "styled-components";
import { HeaderContainer } from "./components/layout/HeaderContainer";
import { FooterContainer } from "./components/layout/FooterContainer";
import { HouseSearch } from "./components/screens/HouseSearch";
// import { ExampleScreen } from "./components/screens/ExampleScreen";
import {
  FilterContext,
  useSetupFilter,
} from "./components/hooks/useSetupFilter";
import {
  GlobalDataContext,
  useSetupGlobalData,
} from "./components/hooks/useSetupGlobalData";
import {
  ToastContext,
  useSetupToast,
} from "./components/hooks/useToast";
import { ToastList } from "./components/ui/Toast";

import { GiMushroomHouse } from "react-icons/gi";
import { NavigationPane } from "./components/layout/NavigationPane";
import { useState } from "react";
import { rightMoveBlue } from "./constants";
import { Button } from "./components/layout/Button";

const AppContainer = styled.div`
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
`;

const SidebarButton = styled(Button)`
  background-color: ${rightMoveBlue};
`;

const TopRightCorner = styled.div`
  position: absolute;
  right: 0;
  top: 0;
  margin: 0.75rem;
`;

const CenteredContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
`;

function App() {
  const filter = useSetupFilter();
  const globalData = useSetupGlobalData();
  const toast = useSetupToast();

  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);
  const toggleLeftSidebar = () => setLeftSidebarOpen(!leftSidebarOpen);

  // Set global toast context for useToast hook
  if (typeof window !== 'undefined') {
    window.__toastContext = toast;
  }

  return (
    <GlobalDataContext.Provider value={globalData}>
      <FilterContext.Provider value={filter}>
        <ToastContext.Provider value={toast}>
          <AppContainer>
            <HeaderContainer>
              <>
                <CenteredContainer>
                  <GiMushroomHouse />
                  Not Rightmove
                </CenteredContainer>

                <TopRightCorner>
                  <SidebarButton onClick={toggleLeftSidebar}>☰</SidebarButton>
                </TopRightCorner>
              </>
            </HeaderContainer>
            <NavigationPane
              leftSidebarOpen={leftSidebarOpen}
              toggleLeftSidebar={toggleLeftSidebar}
            ></NavigationPane>
            <HouseSearch></HouseSearch>
            <FooterContainer> Made for IC Hack 2026 </FooterContainer>
            <ToastList toasts={toast.toasts} onRemove={toast.removeToast} />
          </AppContainer>
        </ToastContext.Provider>
      </FilterContext.Provider>
    </GlobalDataContext.Provider>
  );
}

export default App;
