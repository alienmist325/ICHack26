export interface FilterStates {
  maxPrice?: number;
}

export interface FilterSetters {
  setMaxPrice: (maxPrice: number) => void;
}

export interface GlobalDataStates {
  randomConfig?: string;
  houses: House[];
}

export interface GlobalDataSetters {
  setRandomConfig: (randomConfig: string) => void;
  setHouses: (houses: House[]) => void;
}

export type GlobalData = GlobalDataStates & GlobalDataSetters;
export type Filter = FilterStates & FilterSetters;

export interface House {
  id: string;
  rightmoveId: string;
  listingTitle: string;
  listingUrl: string;
  address: string;
  price: number;
  bedrooms?: number;
  bathrooms?: number;
  features?: string[];
}
