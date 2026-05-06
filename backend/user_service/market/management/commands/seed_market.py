from decimal import Decimal
from django.core.management.base import BaseCommand
from market.models import AssetCategory, Asset


class Command(BaseCommand):
    help = 'Seed initial asset categories and assets'

    def handle(self, *args, **options):
        # Create categories
        food_cat, _ = AssetCategory.objects.get_or_create(
            name='Food',
            defaults={'description': 'Crystal-powered food production'}
        )
        air_cat, _ = AssetCategory.objects.get_or_create(
            name='Air',
            defaults={'description': 'Oxygen generation and filtration'}
        )
        medical_cat, _ = AssetCategory.objects.get_or_create(
            name='Medical',
            defaults={'description': 'Healthcare and healing resources'}
        )
        energy_cat, _ = AssetCategory.objects.get_or_create(
            name='Energy',
            defaults={'description': 'Power generation and storage'}
        )

        # Create sample assets
        assets_data = [
            {
                'name': 'AgriFlux Wheat',
                'category': food_cat,
                'base_price': Decimal('100.00'),
                'current_price': Decimal('105.50'),
                'total_supply': 1000,
                'available_supply': 850,
                'volatility': 0.08,
            },
            {
                'name': 'AgriFlux Water',
                'category': food_cat,
                'base_price': Decimal('80.00'),
                'current_price': Decimal('82.00'),
                'total_supply': 2000,
                'available_supply': 1500,
                'volatility': 0.05,
            },
            {
                'name': 'Aether Oxygen',
                'category': air_cat,
                'base_price': Decimal('150.00'),
                'current_price': Decimal('155.00'),
                'total_supply': 500,
                'available_supply': 450,
                'volatility': 0.12,
            },
            {
                'name': 'Aether Filters',
                'category': air_cat,
                'base_price': Decimal('200.00'),
                'current_price': Decimal('195.75'),
                'total_supply': 300,
                'available_supply': 280,
                'volatility': 0.10,
            },
            {
                'name': 'MedCore Serum',
                'category': medical_cat,
                'base_price': Decimal('500.00'),
                'current_price': Decimal('510.25'),
                'total_supply': 100,
                'available_supply': 95,
                'volatility': 0.15,
            },
            {
                'name': 'MedCore Kit',
                'category': medical_cat,
                'base_price': Decimal('1200.00'),
                'current_price': Decimal('1185.50'),
                'total_supply': 50,
                'available_supply': 48,
                'volatility': 0.20,
            },
            {
                'name': 'Volt Battery',
                'category': energy_cat,
                'base_price': Decimal('300.00'),
                'current_price': Decimal('305.75'),
                'total_supply': 750,
                'available_supply': 700,
                'volatility': 0.09,
            },
            {
                'name': 'Volt Reactor',
                'category': energy_cat,
                'base_price': Decimal('2500.00'),
                'current_price': Decimal('2450.00'),
                'total_supply': 20,
                'available_supply': 18,
                'volatility': 0.25,
            },
        ]

        for asset_data in assets_data:
            asset, created = Asset.objects.get_or_create(
                name=asset_data['name'],
                defaults=asset_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created asset: {asset.name}"))
            else:
                self.stdout.write(f"Asset already exists: {asset.name}")

        self.stdout.write(self.style.SUCCESS('Market seeding completed!'))
