import { useState } from "react";
import styled from "styled-components";

const Pane = styled.div<{ isOpen: boolean }>`
  width: ${(props) => (props.isOpen ? "20rem" : "2rem")};
  height: 100%;
  background-color: #f8f9fa;
  border-right: 1px solid #dee2e6;
  display: flex;
  flex-direction: row;
  transition:
    width 0.3s ease,
    min-width 0.3s ease;
`;

const ToggleBar = styled.div`
  width: 30px;
  height: 100%;
  cursor: pointer;
  background-color: #e9ecef;
  display: flex;
  align-items: center;
  justify-content: center;
  border-left: 1px solid #dee2e6;
  &:hover {
    background-color: #dee2e6;
  }
  flex-shrink: 0;
  user-select: none;
  color: #495057;
  font-weight: bold;
`;

const FilterContentWrapper = styled.div<{ isOpen: boolean }>`
  flex: 1;
  overflow-y: auto;
  opacity: ${(props) => (props.isOpen ? 1 : 0)};
  transition: opacity 0.2s ease;
  min-width: 0;
`;

const FilterContainer = styled.div`
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
`;

const FilterGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const FilterLabel = styled.label`
  font-weight: 600;
  font-size: 0.9rem;
  color: #212529;
`;

const StyledInput = styled.input`
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
`;

const CheckboxGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
`;

const CheckboxLabel = styled.label`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  color: #495057;
`;


export const FilterPane = () => {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <Pane isOpen={isOpen}>
      <FilterContentWrapper isOpen={isOpen}>
        <FilterContainer>
          <h3>Filters</h3>
          <FilterGroup>
            <FilterLabel>Price Range</FilterLabel>
            <StyledInput type="number" placeholder="Min Price" />
            <StyledInput type="number" placeholder="Max Price" />
          </FilterGroup>
          <FilterGroup>
            <FilterLabel>Bedrooms</FilterLabel>
            <StyledInput type="number" placeholder="Min Bedrooms" />
          </FilterGroup>
          <FilterGroup>
            <FilterLabel>Property Type</FilterLabel>
            <CheckboxGroup>
              <CheckboxLabel>
                <input type="checkbox" /> Detached
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Semi-Detached
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Terraced
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Flat
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Bungalow
              </CheckboxLabel>
            </CheckboxGroup>
          </FilterGroup>
          <FilterGroup>
            <FilterLabel>Features</FilterLabel>
            <CheckboxGroup>
              <CheckboxLabel>
                <input type="checkbox" /> Garden
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Parking
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Garage
              </CheckboxLabel>
            </CheckboxGroup>
          </FilterGroup>
          <FilterGroup>
            <FilterLabel>Price Range</FilterLabel>
            <StyledInput type="number" placeholder="Min Price" />
            <StyledInput type="number" placeholder="Max Price" />
          </FilterGroup>
          <FilterGroup>
            <FilterLabel>Bedrooms</FilterLabel>
            <StyledInput type="number" placeholder="Min Bedrooms" />
          </FilterGroup>
          <FilterGroup>
            <FilterLabel>Property Type</FilterLabel>
            <CheckboxGroup>
              <CheckboxLabel>
                <input type="checkbox" /> Detached
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Semi-Detached
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Terraced
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Flat
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Bungalow
              </CheckboxLabel>
            </CheckboxGroup>
          </FilterGroup>
          <FilterGroup>
            <FilterLabel>Features</FilterLabel>
            <CheckboxGroup>
              <CheckboxLabel>
                <input type="checkbox" /> Garden
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Parking
              </CheckboxLabel>
              <CheckboxLabel>
                <input type="checkbox" /> Garage
              </CheckboxLabel>
            </CheckboxGroup>
          </FilterGroup>
        </FilterContainer>
      </FilterContentWrapper>
      <ToggleBar onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? "<" : ">"}
      </ToggleBar>
    </Pane>
  );
};
