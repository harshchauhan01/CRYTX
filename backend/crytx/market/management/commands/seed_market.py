"""
CRYTX — Seed Market Data
Creates 6 sectors with 2 Crytal cards each.
"""

from django.core.management.base import BaseCommand
from market.models import AssetCategory, Asset


SECTORS = [
    {
        'name': 'AgriFlux', 'icon': '🌾', 'color': '#39ff14',
        'description': 'Controls the post-apocalyptic food supply chain.',
        'assets': [
            {'name': 'AgriFlux Wheat', 'ticker': 'AGF-WHEAT', 'base_price': 45.00, 'volatility': 0.04},
            {'name': 'AgriFlux Water', 'ticker': 'AGF-WATER', 'base_price': 78.50, 'volatility': 0.03},
        ]
    },
    {
        'name': 'MedCore', 'icon': '💊', 'color': '#ff00ff',
        'description': 'Monopoly on medical resources and biotech.',
        'assets': [
            {'name': 'MedCore Serum', 'ticker': 'MED-SERUM', 'base_price': 120.00, 'volatility': 0.06},
            {'name': 'MedCore Kit', 'ticker': 'MED-KIT', 'base_price': 65.00, 'volatility': 0.04},
        ]
    },
    {
        'name': 'Volt', 'icon': '⚡', 'color': '#ffd700',
        'description': 'Energy syndicate controlling power infrastructure.',
        'assets': [
            {'name': 'Volt Battery', 'ticker': 'VLT-BATT', 'base_price': 95.00, 'volatility': 0.05},
            {'name': 'Volt Reactor', 'ticker': 'VLT-REACT', 'base_price': 250.00, 'volatility': 0.07},
        ]
    },
    {
        'name': 'Arsenal', 'icon': '🔫', 'color': '#ff3333',
        'description': 'Military-industrial complex. Weapons and defense.',
        'assets': [
            {'name': 'Arsenal Ammo', 'ticker': 'ARS-AMMO', 'base_price': 35.00, 'volatility': 0.08},
            {'name': 'Arsenal Shield', 'ticker': 'ARS-SHLD', 'base_price': 180.00, 'volatility': 0.06},
        ]
    },
    {
        'name': 'NexaTech', 'icon': '🔧', 'color': '#00f5e4',
        'description': 'Advanced technology and quantum computing.',
        'assets': [
            {'name': 'NexaTech Chip', 'ticker': 'NXT-CHIP', 'base_price': 200.00, 'volatility': 0.07},
            {'name': 'NexaTech AI Core', 'ticker': 'NXT-AICR', 'base_price': 450.00, 'volatility': 0.09},
        ]
    },
    {
        'name': 'Ironworks', 'icon': '🏗️', 'color': '#b44aff',
        'description': 'Infrastructure builders. Steel, concrete, nanomesh.',
        'assets': [
            {'name': 'Ironworks Steel', 'ticker': 'IRN-STEE', 'base_price': 55.00, 'volatility': 0.04},
            {'name': 'Ironworks Nanomesh', 'ticker': 'IRN-NANO', 'base_price': 320.00, 'volatility': 0.06},
        ]
    },
]


class Command(BaseCommand):
    help = 'Seed the CRYTX market with 6 sectors and 12 Crytal cards.'

    def handle(self, *args, **options):
        for sector in SECTORS:
            cat, created = AssetCategory.objects.get_or_create(
                name=sector['name'],
                defaults={
                    'icon': sector['icon'],
                    'color': sector['color'],
                    'description': sector['description'],
                }
            )
            action = 'Created' if created else 'Exists'
            self.stdout.write(f"  {action}: {cat}")

            for asset_data in sector['assets']:
                asset, created = Asset.objects.get_or_create(
                    ticker=asset_data['ticker'],
                    defaults={
                        'name': asset_data['name'],
                        'category': cat,
                        'base_price': asset_data['base_price'],
                        'current_price': asset_data['base_price'],
                        'volatility': asset_data['volatility'],
                    }
                )
                action = 'Created' if created else 'Exists'
                self.stdout.write(f"    {action}: {asset}")

        self.stdout.write(self.style.SUCCESS('\n✅ Market seeding complete! 6 sectors, 12 cards.'))
