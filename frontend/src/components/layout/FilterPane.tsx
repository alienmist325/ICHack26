import { useState, useEffect } from "react";
import styled from "styled-components";
import { useGlobalData } from "../hooks/useGlobalData";
import { api } from "../../api/client";
import { colors } from "../../constants";
import { useToast } from "../hooks/useToast";

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
  display: flex;
  flex-direction: column;
`;

const FilterContainer = styled.div`
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  flex: 1;
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
  
  &:focus {
    outline: none;
    border-color: ${colors.rightMoveBlue};
    box-shadow: 0 0 0 2px rgba(240, 80, 40, 0.1);
  }
`;

const StyledSelect = styled.select`
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
  background-color: white;
  
  &:focus {
    outline: none;
    border-color: ${colors.rightMoveBlue};
    box-shadow: 0 0 0 2px rgba(240, 80, 40, 0.1);
  }
`;

const ApplyButtonContainer = styled.div`
  padding: 1rem 1.5rem;
  border-top: 1px solid #dee2e6;
  background-color: white;
`;

const ApplyButton = styled.button`
  width: 100%;
  padding: 0.75rem 1rem;
  background-color: ${colors.rightMoveBlue};
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;

  &:hover {
    background-color: #d84020;
  }

  &:active {
    background-color: #c03818;
  }

  &:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
`;

export const FilterPane = () => {
  const [isOpen, setIsOpen] = useState(true);
  const { setHousesWithFilters, setError } = useGlobalData();
  const { addToast } = useToast();

  // Filter state
  const [minPrice, setMinPrice] = useState<number | undefined>(undefined);
  const [maxPrice, setMaxPrice] = useState<number | undefined>(undefined);
  const [minBedrooms, setMinBedrooms] = useState<number | undefined>(undefined);
  const [propertyType, setPropertyType] = useState<string>("");
  const [outcode, setOutcode] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isApplying, setIsApplying] = useState(false);

  // Data for dropdowns
  const [propertyTypes, setPropertyTypes] = useState<string[]>([]);
  const [outcodes, setOutcodes] = useState<string[]>([]);

  // Fetch dropdown data on mount
  useEffect(() => {
    const fetchDropdownData = async () => {
      try {
        const [types, codes] = await Promise.all([
          api.getPropertyTypes(),
          api.getOutcodes(),
        ]);
        setPropertyTypes(types);
        setOutcodes(codes);
      } catch (err) {
        console.error("Failed to fetch dropdown data:", err);
      }
    };

    fetchDropdownData();
  }, []);

  const handleApplyFilters = async () => {
    setIsApplying(true);

    try {
      const filters = {
        search_query: searchQuery || undefined,
        min_price: minPrice,
        max_price: maxPrice,
        min_bedrooms: minBedrooms,
        property_type: propertyType || undefined,
        outcode: outcode || undefined,
      };

      // Fetch properties with the new filters
      const response = await api.getProperties({
        ...filters,
        limit: 10,
        offset: 0,
      });

      // Transform response to House interface
      const transformedHouses = response.properties.map((prop) => ({
        id: prop.id,
        rightmoveId: prop.rightmove_id,
        listingTitle: prop.listing_title,
        listingUrl: prop.listing_url,
        full_address: prop.full_address,
        address: prop.full_address,
        price: prop.price,
        bedrooms: prop.bedrooms,
        bathrooms: prop.bathrooms,
        images: prop.images,
        property_type: prop.property_type,
        text_description: prop.text_description,
        agent_name: prop.agent_name,
        agent_phone: prop.agent_phone,
        score: prop.score,
      }));

      // Update global state with filters (so pagination remembers them)
      if (setHousesWithFilters) {
        setHousesWithFilters(transformedHouses, response.total_count, filters);
      }

      // Show toast notification
      const message = response.total_count === 0
        ? "No properties found matching your filters"
        : `Found ${response.total_count} properties matching your filters`;
      addToast(message, response.total_count === 0 ? "info" : "success", 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to apply filters";
      setError(errorMessage);
      console.error("Error applying filters:", err);
      addToast("Failed to apply filters", "error", 3000);
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <Pane isOpen={isOpen}>
      <FilterContentWrapper isOpen={isOpen}>
        <FilterContainer>
          <h3>Filters & Search</h3>

          {/* Search */}
          <FilterGroup>
            <FilterLabel>Search</FilterLabel>
            <StyledInput
              type="text"
              placeholder="Search properties..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </FilterGroup>

          {/* Price Range */}
          <FilterGroup>
            <FilterLabel>Price Range</FilterLabel>
            <StyledInput
              type="number"
              placeholder="Min Price"
              value={minPrice || ""}
              onChange={(e) => setMinPrice(e.target.value ? Number(e.target.value) : undefined)}
            />
            <StyledInput
              type="number"
              placeholder="Max Price"
              value={maxPrice || ""}
              onChange={(e) => setMaxPrice(e.target.value ? Number(e.target.value) : undefined)}
            />
          </FilterGroup>

          {/* Bedrooms */}
          <FilterGroup>
            <FilterLabel>Min Bedrooms</FilterLabel>
            <StyledInput
              type="number"
              placeholder="Min Bedrooms"
              value={minBedrooms || ""}
              onChange={(e) => setMinBedrooms(e.target.value ? Number(e.target.value) : undefined)}
            />
          </FilterGroup>

          {/* Property Type */}
          <FilterGroup>
            <FilterLabel>Property Type</FilterLabel>
            <StyledSelect
              value={propertyType}
              onChange={(e) => setPropertyType(e.target.value)}
            >
              <option value="">All Types</option>
              {propertyTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </StyledSelect>
          </FilterGroup>

          {/* Postcode */}
          <FilterGroup>
            <FilterLabel>Postcode (Outcode)</FilterLabel>
            <StyledSelect
              value={outcode}
              onChange={(e) => setOutcode(e.target.value)}
            >
              <option value="">All Postcodes</option>
              {outcodes.map((code) => (
                <option key={code} value={code}>
                  {code}
                </option>
              ))}
            </StyledSelect>
          </FilterGroup>
        </FilterContainer>

        <ApplyButtonContainer>
          <ApplyButton onClick={handleApplyFilters} disabled={isApplying}>
            {isApplying ? "Applying..." : "Apply Filters"}
          </ApplyButton>
        </ApplyButtonContainer>
      </FilterContentWrapper>
      <ToggleBar onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? "<" : ">"}
      </ToggleBar>
    </Pane>
  );
};
