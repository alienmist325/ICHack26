#!/usr/bin/env python3
"""
Integration test for the Rightmove scraper backend.

This test demonstrates:
1. Creating a RightmoveScraperInput configuration
2. Mocking a Rightmove API response
3. Converting properties to database schema
4. Storing properties in the database
5. Retrieving and filtering properties
"""

import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models.rightmove import (
    RightmoveScraperInput,
    ListUrl,
    RightmoveProperty,
    Coordinates,
)
from backend.app.crud import (
    rightmove_property_to_create,
    upsert_property,
    get_properties,
    get_property_with_score,
)
from backend.app.schemas import PropertyFilters
from backend.app.database import init_db


def create_mock_properties():
    """Create mock Rightmove properties for testing."""
    return [
        RightmoveProperty(
            id="TEST_001",
            title="3 bedroom detached house for sale in London",
            url="https://www.rightmove.co.uk/properties/TEST_001",
            displayAddress="123 Test Street, London, SW1A 1AA",
            addedOn="01/01/2026",
            bedrooms=3,
            bathrooms=2,
            propertyType="Detached",
            price=450000,
            listingUpdateReason="new",
            listingUpdateDate=datetime(2026, 1, 1, 10, 0, 0),
            firstVisibleDate=datetime(2026, 1, 1, 9, 0, 0),
            displayStatus="",
            coordinates=Coordinates(latitude=51.5, longitude=-0.1),
            type="sale",
            description="A lovely 3 bedroom detached house in central London",
            images=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            agent="Premium London Properties",
            agentPhone="020 1234 5678",
            agentProfileUrl="https://rightmove.co.uk/agent/premium-london",
            sizeSqFeetMin="1200",
            sizeSqFeetMax="1500",
        ),
        RightmoveProperty(
            id="TEST_002",
            title="2 bedroom flat to rent in Manchester",
            url="https://www.rightmove.co.uk/properties/TEST_002",
            displayAddress="456 High Street, Manchester, M1 2AB",
            addedOn="01/01/2026",
            bedrooms=2,
            bathrooms=1,
            propertyType="Flat",
            price=1200,
            listingUpdateReason="new",
            listingUpdateDate=datetime(2026, 1, 1, 10, 30, 0),
            firstVisibleDate=datetime(2026, 1, 1, 9, 30, 0),
            displayStatus="",
            coordinates=Coordinates(latitude=53.48, longitude=-2.23),
            type="rent",
            description="Modern 2 bedroom flat in city centre",
            images=["https://example.com/img3.jpg"],
            agent="City Centre Lettings",
            agentPhone="0161 999 8888",
            agentProfileUrl="https://rightmove.co.uk/agent/city-centre",
            sizeSqFeetMin="650",
            sizeSqFeetMax="750",
        ),
        RightmoveProperty(
            id="TEST_003",
            title="4 bedroom house for sale in Bristol",
            url="https://www.rightmove.co.uk/properties/TEST_003",
            displayAddress="789 Park Lane, Bristol, BS1 3XY",
            addedOn="01/01/2026",
            bedrooms=4,
            bathrooms=3,
            propertyType="Semi-Detached",
            price=550000,
            listingUpdateReason="new",
            listingUpdateDate=datetime(2026, 1, 1, 11, 0, 0),
            firstVisibleDate=datetime(2026, 1, 1, 10, 0, 0),
            displayStatus="",
            coordinates=Coordinates(latitude=51.45, longitude=-2.58),
            type="sale",
            description="Spacious 4 bedroom family home near parks",
            images=["https://example.com/img4.jpg"],
            agent="Bristol Family Homes",
            agentPhone="0117 234 5678",
            agentProfileUrl="https://rightmove.co.uk/agent/bristol-homes",
            sizeSqFeetMin="2000",
            sizeSqFeetMax="2500",
        ),
    ]


def test_conversion():
    """Test converting Rightmove properties to database format."""
    print("\n" + "=" * 80)
    print("TEST 1: Rightmove Property Conversion")
    print("=" * 80)
    
    properties = create_mock_properties()
    
    for prop in properties:
        try:
            converted = rightmove_property_to_create(prop)
            print(f"\n✓ Converted property {prop.id}")
            print(f"  - Title: {converted.listing_title[:50]}...")
            print(f"  - Price: £{converted.price:,.0f}")
            print(f"  - Bedrooms: {converted.bedrooms}")
            print(f"  - Bathrooms: {converted.bathrooms}")
            print(f"  - Type: {converted.property_type}")
            print(f"  - Location: {converted.latitude:.2f}, {converted.longitude:.2f}")
        except Exception as e:
            print(f"✗ Failed to convert {prop.id}: {e}")
            return False
    
    return True


def test_storage():
    """Test storing properties in the database."""
    print("\n" + "=" * 80)
    print("TEST 2: Database Storage & Retrieval")
    print("=" * 80)
    
    # Initialize database
    init_db()
    
    properties = create_mock_properties()
    stored_count = 0
    
    for prop in properties:
        try:
            converted = rightmove_property_to_create(prop)
            stored_prop, created = upsert_property(converted)
            stored_count += 1
            action = "Created" if created else "Updated"
            print(f"\n✓ {action} property {prop.id} in database")
            print(f"  - Database ID: {stored_prop.id}")
            print(f"  - Rightmove ID: {stored_prop.rightmove_id}")
            print(f"  - Created at: {stored_prop.created_at}")
        except Exception as e:
            print(f"✗ Failed to store {prop.id}: {e}")
            return False
    
    print(f"\n✓ Successfully stored {stored_count}/{len(properties)} properties")
    return True


def test_filtering():
    """Test filtering and retrieving properties."""
    print("\n" + "=" * 80)
    print("TEST 3: Property Filtering & Retrieval")
    print("=" * 80)
    
    # Test 1: Get all properties
    all_props = get_properties()
    print(f"\n✓ Retrieved all properties: {len(all_props)} found")
    for prop in all_props:
        print(f"  - {prop.listing_title[:50]}... (£{prop.price:,.0f})")
    
    # Test 2: Filter by price
    filters = PropertyFilters(min_price=400000, max_price=500000)
    price_filtered = get_properties(filters=filters)
    print(f"\n✓ Filtered by price (£400k-£500k): {len(price_filtered)} found")
    for prop in price_filtered:
        print(f"  - {prop.listing_title[:50]}... (£{prop.price:,.0f})")
    
    # Test 3: Filter by bedrooms
    filters = PropertyFilters(min_bedrooms=3)
    bedroom_filtered = get_properties(filters=filters)
    print(f"\n✓ Filtered by bedrooms (3+): {len(bedroom_filtered)} found")
    for prop in bedroom_filtered:
        print(f"  - {prop.listing_title[:50]}... ({prop.bedrooms} bed)")
    
    # Test 4: Filter by property type
    filters = PropertyFilters(property_type="Flat")
    type_filtered = get_properties(filters=filters)
    print(f"\n✓ Filtered by type (Flat): {len(type_filtered)} found")
    for prop in type_filtered:
        print(f"  - {prop.listing_title[:50]}... ({prop.property_type})")
    
    return True


def test_scoring():
    """Test property scoring system."""
    print("\n" + "=" * 80)
    print("TEST 4: Property Scoring System")
    print("=" * 80)
    
    all_props = get_properties(limit=1)
    if not all_props:
        print("✗ No properties to score")
        return False
    
    for prop in all_props:
        scored_prop = get_property_with_score(prop.id)
        if scored_prop:
            print(f"\n✓ Scored property: {scored_prop.listing_title[:50]}...")
            print(f"  - Upvotes: {scored_prop.upvotes}")
            print(f"  - Downvotes: {scored_prop.downvotes}")
            print(f"  - Total votes: {scored_prop.total_votes}")
            print(f"  - Score: {scored_prop.score:.2f}")
        else:
            print(f"✗ Failed to score property {prop.id}")
            return False
    
    return True


def main():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("RIGHTMOVE SCRAPER BACKEND - INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        ("Conversion", test_conversion),
        ("Storage", test_storage),
        ("Filtering", test_filtering),
        ("Scoring", test_scoring),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{status}: {name}")
    
    total_passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {total_passed}/{total} tests passed")
    
    return all(success for _, success in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
