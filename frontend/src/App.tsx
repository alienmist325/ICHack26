import "./App.css";
import styled from "styled-components";
import { HeaderContainer } from "./components/layout/HeaderContainer";
import { FooterContainer } from "./components/layout/FooterContainer";
import { ExampleScreen } from "./components/screens/ExampleScreen";
import {
  FilterContext,
  useSetupFilter,
} from "./components/hooks/useSetupFilter";
import {
  GlobalDataContext,
  useSetupGlobalData,
} from "./components/hooks/useSetupGlobalData";

const AppContainer = styled.div`
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
`;

function App() {
  const filter = useSetupFilter();
  const globalData = useSetupGlobalData();

  return (
    <GlobalDataContext.Provider value={globalData}>
      <FilterContext.Provider value={filter}>
        <AppContainer>
          <HeaderContainer>Not Rightmove</HeaderContainer>
          <ExampleScreen></ExampleScreen>
          <FooterContainer> Made for IC Hack 2026 </FooterContainer>
        </AppContainer>
      </FilterContext.Provider>
    </GlobalDataContext.Provider>
  );
}

export default App;
