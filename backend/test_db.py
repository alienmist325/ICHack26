# backend/test_db.py
"""
Simple script to test database functionality.
Run with: python -m backend.test_db
"""

from app import crud
from app.database import init_db
from app.schemas import PropertyCreate, RatingCreate, VoteType


def main():
    print("Initializing database...")
    init_db()
    print("✓ Database initialized\n")

    # Create a test property
    print("Creating test property...")
    test_property = PropertyCreate(
        rightmove_id="test_123",
        listing_title="Beautiful 2-Bed Flat in London",
        listing_url="https://www.rightmove.co.uk/properties/test_123",
        full_address="123 Test Street, London, SW1A 1AA",
        outcode="SW1A",
        incode="1AA",
        latitude=51.5074,
        longitude=-0.1278,
        property_type="Flat",
        listing_type="Rent",
        bedrooms=2,
        bathrooms=1,
        price=2000.0,
        deposit=2000.0,
        furnishing_type="Furnished",
        amenities=["Parking", "Garden"],
        text_description="A lovely property in the heart of London.",
        agent_name="Test Estate Agents",
        agent_phone="020 1234 5678",
    )

    property_obj, created = crud.upsert_property(test_property)
    print(f"✓ Property created with ID: {property_obj.id}")
    print(f"  Rightmove ID: {property_obj.rightmove_id}")
    print(f"  Title: {property_obj.listing_title}\n")

    # Add some ratings
    print("Adding ratings...")
    crud.create_rating(
        RatingCreate(property_id=property_obj.id, vote_type=VoteType.UPVOTE)
    )
    crud.create_rating(
        RatingCreate(property_id=property_obj.id, vote_type=VoteType.UPVOTE)
    )
    crud.create_rating(
        RatingCreate(property_id=property_obj.id, vote_type=VoteType.DOWNVOTE)
    )
    print("✓ Added 2 upvotes and 1 downvote\n")

    # Get property with score
    print("Calculating property score...")
    prop_with_score = crud.get_property_with_score(property_obj.id)
    print(f"✓ Property score calculated:")
    print(f"  Upvotes: {prop_with_score.upvotes}")
    print(f"  Downvotes: {prop_with_score.downvotes}")
    print(f"  Score: {prop_with_score.score:.2f}\n")

    # List all properties
    print("Listing all properties...")
    properties = crud.get_properties_with_scores(limit=10)
    print(f"✓ Found {len(properties)} properties\n")

    print("Database test completed successfully!")


if __name__ == "__main__":
    main()
