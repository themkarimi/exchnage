from django.core.management.base import BaseCommand
from wallet.models.token import Token


class Command(BaseCommand):
    help = 'Create initial tokens for the exchange'

    def handle(self, *args, **kwargs):
        tokens = [
            {'name': 'bitcoin', 'symbol': 'BTC', 'actual_price': 50000.00},
            {'name': 'ethereum', 'symbol': 'ETH', 'actual_price': 3000.00},
            {'name': 'tether', 'symbol': 'USDT', 'actual_price': 1.00},
            {'name': 'binancecoin', 'symbol': 'BNB', 'actual_price': 400.00},
            {'name': 'solana', 'symbol': 'SOL', 'actual_price': 100.00},
            {'name': 'cardano', 'symbol': 'ADA', 'actual_price': 0.50},
        ]

        for token_data in tokens:
            token, created = Token.objects.get_or_create(
                name=token_data['name'],
                defaults={
                    'symbol': token_data['symbol'],
                    'actual_price': token_data['actual_price']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created token: {token.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Token already exists: {token.name}'))
