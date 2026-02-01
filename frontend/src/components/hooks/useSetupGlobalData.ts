import { createContext, useState, useEffect } from "react";
import { GlobalData, House } from "../../types";
import { api } from "../../api/client";

export const GlobalDataContext = createContext<GlobalData | null>(null);

const PAGE_SIZE = 10;

export function useSetupGlobalData(): GlobalData {
  const [randomConfig, setRandomConfig] = useState<string | undefined>(
    "this is a thing"
  );
  const [houses, setHouses] = useState<House[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPageState] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentFilters, setCurrentFilters] = useState<any>(null);

  // Fetch properties on mount
  useEffect(() => {
    fetchProperties(0, currentFilters);
  }, []);

  const fetchProperties = async (page: number, filters?: any) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getProperties({
        ...(filters || {}),
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });

      // Transform backend response to House interface
      const transformedHouses: House[] = response.properties.map((prop) => ({
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

      setHouses(transformedHouses);
      setTotalCount(response.total_count);
      setCurrentPageState(page);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch properties";
      setError(errorMessage);
      console.error("Error fetching properties:", err);
      
      if (typeof window !== 'undefined' && window.__toastContext) {
        window.__toastContext.addToast("Failed to load properties. Please try again.", "error", 3000);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const setCurrentPage = (page: number) => {
    fetchProperties(page, currentFilters);
  };

  const updateFiltersAndFetch = (filters: any) => {
    setCurrentFilters(filters);
    fetchProperties(0, filters);
  };

  // Also expose a way to update filters from FilterPane and keep them in sync
  const setHousesWithFilters = (newHouses: House[], totalCount: number, filters: any) => {
    setHouses(newHouses);
    setTotalCount(totalCount);
    setCurrentFilters(filters);
    setCurrentPageState(0);
  };

  return {
    randomConfig,
    setRandomConfig,
    houses,
    setHouses,
    totalCount,
    setTotalCount,
    currentPage,
    setCurrentPage,
    isLoading,
    setIsLoading,
    error,
    setError,
    currentFilters,
    updateFiltersAndFetch,
    setHousesWithFilters,
  };
}
