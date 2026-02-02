import { LocationCoordinate } from "./api/client";

export interface FilterStates {
  maxPrice?: number;
}

export interface FilterSetters {
  setMaxPrice: (maxPrice: number) => void;
}

export interface GlobalDataStates {
  randomConfig?: string;
  houses: House[];
  totalCount: number;
  currentPage: number;
  pageSize?: number;
  isLoading: boolean;
  error: string | null;
  keyLocations: LocationCoordinate[];
}

export interface GlobalDataSetters {
  setRandomConfig: (randomConfig: string) => void;
  setHouses: (houses: House[]) => void;
  setTotalCount: (count: number) => void;
  setCurrentPage: (page: number) => void;
  setIsLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  updateFiltersAndFetch?: (filters: any) => void;
  setHousesWithFilters?: (
    houses: House[],
    totalCount: number,
    filters: any
  ) => void;
  currentFilters?: any;
  setKeyLocations: (locations: LocationCoordinate[]) => void;
}

export type GlobalData = GlobalDataStates & GlobalDataSetters;
export type Filter = FilterStates & FilterSetters;

export interface House {
  id: number;
  rightmoveId: string;
  listingTitle: string;
  listingUrl: string;
  full_address: string;
  address?: string; // for backward compatibility
  price: number;
  bedrooms?: number;
  bathrooms?: number;
  features?: string[];
  images?: string[];
  property_type?: string;
  text_description?: string;
  agent_name?: string;
  agent_phone?: string;
  score?: number;
}
