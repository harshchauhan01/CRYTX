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
                'name': 'Wheat Harvest',
                'category': food_cat,
                'base_price': Decimal('100.00'),
                'current_price': Decimal('105.50'),
                'supply': 1000,
                'demand': 850,
                'volatility': 0.08,
            },
            {
                'name': 'Fresh Water',
                'category': food_cat,
                'base_price': Decimal('80.00'),
                'current_price': Decimal('82.00'),
                'supply': 2000,
                'demand': 1500,
                'volatility': 0.05,
            },
            {
                'name': 'Oxygen Supply',
                'category': air_cat,
                'base_price': Decimal('150.00'),
                'current_price': Decimal('155.00'),
                'supply': 500,
                'demand': 450,
                'volatility': 0.12,
            },
            {
                'name': 'Air Purifier Cartridge',
                'category': air_cat,
                'base_price': Decimal('200.00'),
                'current_price': Decimal('195.75'),
                'supply': 300,
                'demand': 280,
                'volatility': 0.10,
            },
            {
                'name': 'Medicinal Serum',
                'category': medical_cat,
                'base_price': Decimal('500.00'),
                'current_price': Decimal('510.25'),
                'supply': 100,
                'demand': 95,
                'volatility': 0.15,
            },
            {
                'name': 'Surgical Kit',
                'category': medical_cat,
                'base_price': Decimal('1200.00'),
                'current_price': Decimal('1185.50'),
                'supply': 50,
                'demand': 48,
                'volatility': 0.20,
            },
            {
                'name': 'Solar Battery Pack',
                'category': energy_cat,
                'base_price': Decimal('300.00'),
                'current_price': Decimal('305.75'),
                'supply': 750,
                'demand': 700,
                'volatility': 0.09,
            },
            {
                'name': 'Fusion Reactor Core',
                'category': energy_cat,
                'base_price': Decimal('2500.00'),
                'current_price': Decimal('2450.00'),
                'supply': 20,
                'demand': 18,
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
