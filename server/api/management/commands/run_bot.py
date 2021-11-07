import logging
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from api.logic import PCMonitoringBot
from api.models import TelegramUser

class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

        # create admin user if not exist
        user = TelegramUser.objects.filter(chat_id=settings.TELEGRAM_MASTER_ID)
        if not user.exists():
            TelegramUser.objects.create(
                chat_id=settings.TELEGRAM_MASTER_ID,
                username=settings.TELEGRAM_MASTER_USERNAME,
                role=TelegramUser.ROLE.ADMIN,
                receive_notification=True
            )

        bot = PCMonitoringBot()
        bot.run()


