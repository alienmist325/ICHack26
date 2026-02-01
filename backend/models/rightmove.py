from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Coordinates(BaseModel):
    """Geographic coordinates of a property."""

    latitude: float
    longitude: float


class RightmoveProperty(BaseModel):
    """A single property listing from Rightmove API."""

    id: str = Field(..., description="Property ID")
    url: str = Field(..., description="Property URL on Rightmove")
    title: str = Field(..., description="Property title/description")
    displayAddress: str = Field(..., description="Property address for display")
    addedOn: str = Field(..., description="Date property was added/updated")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    bedrooms: int = Field(..., description="Number of bedrooms")
    propertyType: str = Field(
        ..., description="Type of property (e.g., 'Detached', 'Semi-Detached')"
    )
    price: int = Field(..., description="Property price in GBP")
    listingUpdateReason: str = Field(
        ..., description="Reason for listing update (e.g., 'new', 'price_reduced')"
    )
    listingUpdateDate: datetime = Field(
        ..., description="ISO timestamp of listing update"
    )
    firstVisibleDate: datetime = Field(
        ..., description="ISO timestamp when property first became visible"
    )
    displayStatus: str = Field(..., description="Display status of the listing")
    productLabel: Optional[str] = Field(
        None, description="Product label (e.g., 'Premium Listing', 'Swimming Pool')"
    )
    coordinates: Coordinates = Field(..., description="Geographic coordinates")
    type: str = Field(..., description="Transaction type (e.g., 'sale', 'rent')")
    description: str = Field(..., description="Full property description")
    images: List[str] = Field(..., description="List of image URLs")
    tags: List[str] = Field(
        default_factory=list, description="List of property tags (e.g., 'NEW_HOME')"
    )
    agent: str = Field(..., description="Agent/estate agent name")
    agentPhone: str = Field(..., description="Agent phone number")
    agentProfileUrl: str = Field(..., description="URL to agent's profile")
    sizeSqFeetMin: str = Field(
        ..., description="Minimum property size in sq ft (can be empty string)"
    )
    sizeSqFeetMax: str = Field(
        ..., description="Maximum property size in sq ft (can be empty string)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "87561351",
                "url": "https://www.rightmove.co.uk/properties/87561351#/?channel=RES_BUY",
                "title": "3 bedroom semi-detached house for sale",
                "displayAddress": "Addison Close, Gillingham, SP8",
                "addedOn": "21/01/2026",
                "bathrooms": None,
                "bedrooms": 3,
                "propertyType": "Semi-Detached",
                "price": 309000,
                "listingUpdateReason": "new",
                "listingUpdateDate": "2026-01-21T03:53:02Z",
                "firstVisibleDate": "2026-01-21T03:47:03Z",
                "displayStatus": "",
                "productLabel": "Incentives Available",
                "coordinates": {"latitude": 51.03297, "longitude": -2.26877},
                "type": "sale",
                "description": "The Gosford is a good option for first time buyers...",
                "images": ["https://media.rightmove.co.uk/..."],
                "tags": ["NEW_HOME"],
                "agent": "Taylor Wimpey",
                "agentPhone": "01747 449979",
                "agentProfileUrl": "https://www.rightmove.co.uk/developer/branch/...",
                "sizeSqFeetMin": "",
                "sizeSqFeetMax": "",
            }
        }
    )


class RightmoveResponse(BaseModel):
    """Response from Rightmove API containing a list of properties."""

    properties: List[RightmoveProperty] = Field(..., description="List of properties")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "properties": [
                    {
                        "id": "87561351",
                        "url": "https://www.rightmove.co.uk/properties/87561351#/?channel=RES_BUY",
                        "title": "3 bedroom semi-detached house for sale",
                        # ... rest of property fields
                    }
                ]
            }
        }
    )


class ListUrl(BaseModel):
    """A single list page URL for the Rightmove scraper."""

    url: str = Field(..., description="URL of a Rightmove list page to scrape")


class PropertyUrl(BaseModel):
    """A single property page URL for the Rightmove scraper."""

    url: str = Field(..., description="URL of a specific Rightmove property to scrape")


class ProxyConfig(BaseModel):
    """Proxy configuration for the Rightmove scraper."""

    useApifyProxy: bool = Field(
        default=True, description="Whether to use Apify's proxy service"
    )
    url: str = Field(default="", description="Proxy URL (if not using Apify proxy)")
    username: str = Field(
        default="", description="Proxy username (if authentication required)"
    )
    password: str = Field(
        default="", description="Proxy password (if authentication required)"
    )
    country: str = Field(
        default="", description="Proxy country (for country-specific proxies)"
    )


class RightmoveScraperInput(BaseModel):
    """Input parameters for the Apify Rightmove scraper (dhrumil/rightmove-scraper)."""

    listUrls: list[ListUrl] = Field(
        default_factory=list,
        description="List of Rightmove list page URLs to scrape (e.g., search results pages)",
    )
    propertyUrls: list[PropertyUrl] = Field(
        default_factory=list,
        description="List of specific property URLs to scrape (direct property links)",
    )
    monitoringMode: bool = Field(
        default=False, description="Enable monitoring mode for continuous updates"
    )
    deduplicateAtTaskLevel: bool = Field(
        default=False, description="Deduplicate results at task level"
    )
    fullPropertyDetails: bool = Field(
        default=False, description="Fetch full property details instead of basic info"
    )
    includePriceHistory: bool = Field(
        default=False, description="Include historical price data for properties"
    )
    includeNearestSchools: bool = Field(
        default=False, description="Include information about nearest schools"
    )
    enableDelistingTracker: bool = Field(
        default=False, description="Enable tracking of delisted properties"
    )
    addEmptyTrackerRecord: bool = Field(
        default=False, description="Add empty tracker record in results"
    )
    email: Optional[str] = Field(
        default="", description="Email address for notifications (optional)"
    )
    maxProperties: int = Field(
        default=1000, description="Maximum number of properties to fetch"
    )
    proxy: ProxyConfig = Field(
        default_factory=ProxyConfig, description="Proxy configuration"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "listUrls": [
                    {
                        "url": "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E2445"
                    },
                    {
                        "url": "https://www.rightmove.co.uk/property-for-sale/find.html?locationIdentifier=OUTCODE%5E2446"
                    },
                ],
                "propertyUrls": [
                    {"url": "https://www.rightmove.co.uk/properties/12345678"},
                    {"url": "https://www.rightmove.co.uk/properties/87654321"},
                ],
                "maxProperties": 5,
                "monitoringMode": False,
                "deduplicateAtTaskLevel": False,
                "fullPropertyDetails": False,
                "includePriceHistory": False,
                "includeNearestSchools": False,
                "enableDelistingTracker": False,
                "addEmptyTrackerRecord": False,
                "email": "",
                "proxy": {"useApifyProxy": True},
            }
        }
    )

    def to_apify_dict(self) -> dict:
        """
        Convert the model to a dictionary format compatible with Apify API.

        Excludes proxy configuration fields that are not relevant:
        - If useApifyProxy is True, excludes url, username, password, country
        - If useApifyProxy is False, only includes non-empty proxy fields
        """
        data = self.model_dump(by_alias=False, exclude_none=False)

        # Clean up proxy configuration
        if data.get("proxy"):
            if data["proxy"].get("useApifyProxy"):
                # Only keep useApifyProxy when using Apify proxy
                data["proxy"] = {"useApifyProxy": True}
            else:
                # When using custom proxy, remove empty fields
                proxy = data["proxy"]
                cleaned_proxy = {"useApifyProxy": False}

                # Only include non-empty custom proxy fields
                if proxy.get("url"):
                    cleaned_proxy["url"] = proxy["url"]
                if proxy.get("username"):
                    cleaned_proxy["username"] = proxy["username"]
                if proxy.get("password"):
                    cleaned_proxy["password"] = proxy["password"]
                if proxy.get("country"):
                    cleaned_proxy["country"] = proxy["country"]

                data["proxy"] = cleaned_proxy

        return data


class RightmoveData(BaseModel):
    """Data from the Rightmove scraper."""
