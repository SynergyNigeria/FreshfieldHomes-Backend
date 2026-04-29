from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from homes.models import (
    Agent,
    PartialHome,
    PartialHomeFeature,
    PartialHomeImage,
    Property,
    PropertyFeature,
    PropertyImage,
)


class Command(BaseCommand):
    help = "Seed demo data based on the current frontend sample content"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        agent_data = [
            {
                "public_id": "a1",
                "name": "Sarah Mitchell",
                "phone": "(555) 123-4567",
                "email": "sarah@freshfieldshomes.com",
                "image": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop",
            },
            {
                "public_id": "a2",
                "name": "James Carter",
                "phone": "(555) 234-5678",
                "email": "james@freshfieldshomes.com",
                "image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop",
            },
            {
                "public_id": "a3",
                "name": "Emily Rodriguez",
                "phone": "(555) 345-6789",
                "email": "emily@freshfieldshomes.com",
                "image": "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&h=200&fit=crop",
            },
        ]

        agent_map = {}
        for row in agent_data:
            agent, _ = Agent.objects.update_or_create(public_id=row["public_id"], defaults=row)
            agent_map[row["public_id"]] = agent

        properties = [
            {
                "public_id": "1",
                "title": "Modern Farmhouse Retreat",
                "address": "1234 Oak Valley Drive",
                "city": "Austin",
                "state": "TX",
                "price": 875000,
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 3200,
                "image": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&h=600&fit=crop",
                "property_type": "house",
                "status": "for-sale",
                "year_built": 2021,
                "description": "This stunning modern farmhouse blends rustic charm with contemporary design.",
                "agent": agent_map["a1"],
                "is_featured": True,
                "images": [
                    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?w=800&h=600&fit=crop",
                ],
                "features": [
                    "Open Floor Plan",
                    "Chef's Kitchen",
                    "Quartz Countertops",
                    "Hardwood Floors",
                ],
            },
            {
                "public_id": "2",
                "title": "Downtown Luxury Loft",
                "address": "567 Main Street, Unit 12B",
                "city": "Denver",
                "state": "CO",
                "price": 620000,
                "bedrooms": 2,
                "bathrooms": 2,
                "sqft": 1800,
                "image": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=600&fit=crop",
                "property_type": "apartment",
                "status": "for-sale",
                "year_built": 2019,
                "description": "Sophisticated urban living in this beautifully converted loft space.",
                "agent": agent_map["a2"],
                "is_featured": True,
                "images": [
                    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600573472591-ee6981cf81f0?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=800&h=600&fit=crop",
                ],
                "features": [
                    "Floor-to-Ceiling Windows",
                    "Exposed Brick",
                    "Rooftop Access",
                    "In-Unit Laundry",
                ],
            },
            {
                "public_id": "3",
                "title": "Coastal Family Home",
                "address": "890 Seaside Boulevard",
                "city": "Charleston",
                "state": "SC",
                "price": 1250000,
                "bedrooms": 5,
                "bathrooms": 4,
                "sqft": 4100,
                "image": "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=800&h=600&fit=crop",
                "property_type": "house",
                "status": "for-sale",
                "year_built": 2018,
                "description": "Elegant coastal living at its finest.",
                "agent": agent_map["a3"],
                "is_featured": True,
                "images": [
                    "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600210492493-0946911123ea?w=800&h=600&fit=crop",
                ],
                "features": ["Ocean Views", "Gourmet Kitchen", "Pool & Spa", "Wine Cellar"],
            },
            {
                "public_id": "4",
                "title": "Charming Victorian Townhouse",
                "address": "321 Heritage Lane",
                "city": "Savannah",
                "state": "GA",
                "price": 485000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 2200,
                "image": "https://images.unsplash.com/photo-1600573472591-ee6981cf81f0?w=800&h=600&fit=crop",
                "property_type": "townhouse",
                "status": "for-sale",
                "year_built": 1895,
                "description": "Step into history with this restored Victorian townhouse.",
                "agent": agent_map["a1"],
                "is_featured": False,
                "images": [
                    "https://images.unsplash.com/photo-1600573472591-ee6981cf81f0?w=800&h=600&fit=crop",
                ],
                "features": ["Original Moldings", "Updated Kitchen", "Private Garden"],
            },
            {
                "public_id": "5",
                "title": "Sleek Waterfront Condo",
                "address": "1500 Marina Way, Unit 8A",
                "city": "Miami",
                "state": "FL",
                "price": 950000,
                "bedrooms": 3,
                "bathrooms": 3,
                "sqft": 2400,
                "image": "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=800&h=600&fit=crop",
                "property_type": "condo",
                "status": "pending",
                "year_built": 2023,
                "description": "Ultra-modern waterfront living with unobstructed bay views.",
                "agent": agent_map["a2"],
                "is_featured": False,
                "images": [
                    "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=800&h=600&fit=crop",
                ],
                "features": ["Bay Views", "Private Balcony", "Infinity Pool", "Valet Parking"],
            },
            {
                "public_id": "6",
                "title": "Mountain View Estate",
                "address": "7890 Summit Ridge Road",
                "city": "Asheville",
                "state": "NC",
                "price": 1750000,
                "bedrooms": 6,
                "bathrooms": 5,
                "sqft": 5500,
                "image": "https://images.unsplash.com/photo-1600210492493-0946911123ea?w=800&h=600&fit=crop",
                "property_type": "house",
                "status": "for-sale",
                "year_built": 2020,
                "description": "Breathtaking mountain estate set on 5 acres of pristine land.",
                "agent": agent_map["a3"],
                "is_featured": False,
                "images": [
                    "https://images.unsplash.com/photo-1600210492493-0946911123ea?w=800&h=600&fit=crop",
                ],
                "features": ["Mountain Views", "5 Acres", "Infinity Pool", "Guest House"],
            },
        ]

        for row in properties:
            images = row.pop("images")
            features = row.pop("features")
            obj, _ = Property.objects.update_or_create(public_id=row["public_id"], defaults=row)
            obj.images.all().delete()
            obj.features.all().delete()
            for index, image in enumerate(images):
                PropertyImage.objects.create(property=obj, image=image, sort_order=index)
            for feature in features:
                PropertyFeature.objects.create(property=obj, name=feature)

        partial_homes = [
            {
                "public_id": "ph1",
                "title": "Sunlit Garden Bungalow",
                "address": "44 Maple Grove Lane",
                "city": "Austin",
                "state": "TX",
                "full_price": 540000,
                "amount_paid": 216000,
                "remaining_amount": 324000,
                "percentage_paid": 40,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 1950,
                "image": "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&h=600&fit=crop",
                "property_type": "house",
                "year_built": 2017,
                "description": "A charming garden bungalow with an open-plan living space.",
                "payer_name": "Marcus T.",
                "payer_amount_paid": 216000,
                "payer_date_paid": date(2025, 2, 14),
                "payer_percentage_paid": 40,
                "secure_code": "1998runs",
                "agent": agent_map["a1"],
                "images": [
                    "https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=800&h=600&fit=crop",
                ],
                "features": ["Hardwood Floors", "Sun Deck", "Open Kitchen"],
            },
            {
                "public_id": "ph2",
                "title": "Modern Urban Townhouse",
                "address": "210 Birchwood Avenue",
                "city": "Denver",
                "state": "CO",
                "full_price": 720000,
                "amount_paid": 360000,
                "remaining_amount": 360000,
                "percentage_paid": 50,
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 2600,
                "image": "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=800&h=600&fit=crop",
                "property_type": "townhouse",
                "year_built": 2020,
                "description": "Sleek townhouse where half the purchase price is already committed.",
                "payer_name": "Priya K.",
                "payer_amount_paid": 360000,
                "payer_date_paid": date(2024, 10, 3),
                "payer_percentage_paid": 50,
                "secure_code": "1998runs",
                "agent": agent_map["a2"],
                "images": [
                    "https://images.unsplash.com/photo-1605276374104-dee2a0ed3cd6?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600573472591-ee6981cf81f0?w=800&h=600&fit=crop",
                ],
                "features": ["Rooftop Terrace", "Chef's Kitchen", "EV Charging"],
            },
            {
                "public_id": "ph3",
                "title": "Coastal Breeze Condo",
                "address": "88 Shoreline Drive, Unit 5C",
                "city": "Miami",
                "state": "FL",
                "full_price": 895000,
                "amount_paid": 178000,
                "remaining_amount": 717000,
                "percentage_paid": 20,
                "bedrooms": 2,
                "bathrooms": 2,
                "sqft": 1400,
                "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop",
                "property_type": "condo",
                "year_built": 2022,
                "description": "Ocean-view condo with premium amenities and a committed initial deposit.",
                "payer_name": "Derek & Anita O.",
                "payer_amount_paid": 178000,
                "payer_date_paid": date(2026, 1, 9),
                "payer_percentage_paid": 20,
                "secure_code": "1998runs",
                "agent": agent_map["a3"],
                "images": [
                    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600607687644-c7171b42498f?w=800&h=600&fit=crop",
                ],
                "features": ["Ocean Views", "Infinity Pool", "Private Balcony"],
            },
            {
                "public_id": "ph4",
                "title": "Rolling Hills Estate",
                "address": "5 Ridgecrest Way",
                "city": "Asheville",
                "state": "NC",
                "full_price": 1100000,
                "amount_paid": 770000,
                "remaining_amount": 330000,
                "percentage_paid": 70,
                "bedrooms": 5,
                "bathrooms": 4,
                "sqft": 4400,
                "image": "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=800&h=600&fit=crop",
                "property_type": "house",
                "year_built": 2019,
                "description": "A luxury mountain retreat with 70% already paid.",
                "payer_name": "Nathaniel B.",
                "payer_amount_paid": 770000,
                "payer_date_paid": date(2025, 3, 22),
                "payer_percentage_paid": 70,
                "secure_code": "1998runs",
                "agent": agent_map["a1"],
                "images": [
                    "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=800&h=600&fit=crop",
                    "https://images.unsplash.com/photo-1600210492493-0946911123ea?w=800&h=600&fit=crop",
                ],
                "features": ["Mountain Views", "Heated Pool", "Wine Cellar"],
            },
        ]

        for row in partial_homes:
            images = row.pop("images")
            features = row.pop("features")
            obj, _ = PartialHome.objects.update_or_create(public_id=row["public_id"], defaults=row)
            obj.images.all().delete()
            obj.features.all().delete()
            for index, image in enumerate(images):
                PartialHomeImage.objects.create(partial_home=obj, image=image, sort_order=index)
            for feature in features:
                PartialHomeFeature.objects.create(partial_home=obj, name=feature)

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
