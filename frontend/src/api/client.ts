import { House } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface ApiError {
  status: number;
  message: string;
}

export interface PropertyResponse {
  id: number;
  rightmove_id: string;
  listing_title: string;
  listing_url: string;
  full_address: string;
  price: number;
  bedrooms?: number;
  bathrooms?: number;
  images?: string[];
  property_type?: string;
  text_description?: string;
  agent_name?: string;
  agent_phone?: string;
  score?: number;
}

export interface ListPropertiesResponse {
  properties: PropertyResponse[];
  total_count: number;
  limit: number;
  offset: number;
}

export interface RatingResponse {
  id: number;
  property_id: number;
  vote_type: 'upvote' | 'downvote';
  voted_at: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async handleResponse(response: Response) {
    if (!response.ok) {
      const error: ApiError = {
        status: response.status,
        message: `API Error: ${response.statusText}`,
      };
      throw error;
    }
    return response.json();
  }

  async getProperties(params: {
    search_query?: string;
    min_price?: number;
    max_price?: number;
    min_bedrooms?: number;
    max_bedrooms?: number;
    property_type?: string;
    furnishing_type?: string;
    outcode?: string;
    limit: number;
    offset: number;
  }): Promise<ListPropertiesResponse> {
    const queryParams = new URLSearchParams();

    if (params.search_query) queryParams.append('search_query', params.search_query);
    if (params.min_price !== undefined) queryParams.append('min_price', String(params.min_price));
    if (params.max_price !== undefined) queryParams.append('max_price', String(params.max_price));
    if (params.min_bedrooms !== undefined) queryParams.append('min_bedrooms', String(params.min_bedrooms));
    if (params.max_bedrooms !== undefined) queryParams.append('max_bedrooms', String(params.max_bedrooms));
    if (params.property_type) queryParams.append('property_type', params.property_type);
    if (params.furnishing_type) queryParams.append('furnishing_type', params.furnishing_type);
    if (params.outcode) queryParams.append('outcode', params.outcode);
    queryParams.append('limit', String(params.limit));
    queryParams.append('offset', String(params.offset));

    const response = await fetch(`${this.baseUrl}/properties?${queryParams}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return this.handleResponse(response);
  }

  async getProperty(id: number): Promise<House> {
    const response = await fetch(`${this.baseUrl}/properties/${id}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return this.handleResponse(response);
  }

  async postRating(propertyId: number, voteType: 'upvote' | 'downvote'): Promise<RatingResponse> {
    const response = await fetch(`${this.baseUrl}/ratings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        property_id: propertyId,
        vote_type: voteType,
      }),
    });

    return this.handleResponse(response);
  }

  async getRatings(propertyId: number): Promise<RatingResponse[]> {
    const response = await fetch(`${this.baseUrl}/properties/${propertyId}/ratings`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return this.handleResponse(response);
  }

  async getPropertyTypes(): Promise<string[]> {
    const response = await fetch(`${this.baseUrl}/property-types`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return this.handleResponse(response);
  }

   async getOutcodes(): Promise<string[]> {
     const response = await fetch(`${this.baseUrl}/outcodes`, {
       method: 'GET',
       headers: {
         'Content-Type': 'application/json',
       },
     });

     return this.handleResponse(response);
   }

   private getAuthHeaders() {
     const tokens = localStorage.getItem('auth_tokens');
     const authHeader: HeadersInit = {};
     if (tokens) {
       const parsed = JSON.parse(tokens);
       authHeader['Authorization'] = `Bearer ${parsed.accessToken}`;
     }
     return authHeader;
   }

   async starProperty(propertyId: number): Promise<any> {
     const response = await fetch(`${this.baseUrl}/properties/${propertyId}/star`, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         ...this.getAuthHeaders(),
       },
     });

     return this.handleResponse(response);
   }

   async unstarProperty(propertyId: number): Promise<any> {
     const response = await fetch(`${this.baseUrl}/properties/${propertyId}/unstar`, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         ...this.getAuthHeaders(),
       },
     });

     return this.handleResponse(response);
   }

   async setPropertyStatus(propertyId: number, status: string): Promise<any> {
     const response = await fetch(`${this.baseUrl}/properties/${propertyId}/status`, {
       method: 'POST',
       headers: {
         'Content-Type': 'application/json',
         ...this.getAuthHeaders(),
       },
       body: JSON.stringify({ status }),
     });

     return this.handleResponse(response);
   }

   async get(endpoint: string): Promise<any> {
     const response = await fetch(`${this.baseUrl}${endpoint}`, {
       method: 'GET',
       headers: {
         'Content-Type': 'application/json',
         ...this.getAuthHeaders(),
       },
     });

     return this.handleResponse(response);
   }

   async put(endpoint: string, data: any): Promise<any> {
     const response = await fetch(`${this.baseUrl}${endpoint}`, {
       method: 'PUT',
       headers: {
         'Content-Type': 'application/json',
         ...this.getAuthHeaders(),
       },
       body: JSON.stringify(data),
     });

     return this.handleResponse(response);
   }

   async delete(endpoint: string): Promise<any> {
     const response = await fetch(`${this.baseUrl}${endpoint}`, {
       method: 'DELETE',
       headers: {
         'Content-Type': 'application/json',
         ...this.getAuthHeaders(),
       },
     });

     return this.handleResponse(response);
   }
}

export const api = new ApiClient(BASE_URL);
