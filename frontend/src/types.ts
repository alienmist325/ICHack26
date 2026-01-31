export interface FilterStates {
  maxPrice?: number;
}

export interface FilterSetters {
  setMaxPrice: (maxPrice: number) => void;
}

export interface GlobalDataStates {
  randomConfig?: string;
}

export interface GlobalDataSetters {
  setRandomConfig: (randomConfig: string) => void;
}

export type GlobalData = GlobalDataStates & GlobalDataSetters;
export type Filter = FilterStates & FilterSetters;
