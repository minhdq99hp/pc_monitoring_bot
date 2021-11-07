import logging
from django.conf import settings
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from api.models import *

class PCMonitoringBot:
    """Telegram Bot for monitoring PC"""

    def __init__(self):
        self.updater = Updater(token=settings.TELEGRAM_BOT_TOKEN)
        self.dispatcher = self.updater.dispatcher
        self.job_queue  = self.updater.job_queue

        start_handler = CommandHandler('start', self.start)
        setrole_handler = CommandHandler('set_role', self.set_role)
        list_handler = CommandHandler('list', self.list)
        status_handler = CommandHandler('status', self.status)
        turnon_handler = CommandHandler('turnon', self.turnon)
        poweroff_handler = CommandHandler('poweroff', self.poweroff)
        set_noti_hanlder = CommandHandler('set_noti', self.set_noti)
        register_handler = CommandHandler('register', self.register)
        deregister_hanlder = CommandHandler('deregister', self.deregister)
        # message_handler = MessageHandler(Filters.text & ~Filters.command, self.default_response)
        message_handler = MessageHandler(Filters.all, self.default_response)

        # ADD HANDLER
        self.dispatcher.add_handler(start_handler)
        self.dispatcher.add_handler(setrole_handler)
        self.dispatcher.add_handler(list_handler)
        self.dispatcher.add_handler(status_handler)
        self.dispatcher.add_handler(turnon_handler)
        self.dispatcher.add_handler(poweroff_handler)
        self.dispatcher.add_handler(set_noti_hanlder)
        self.dispatcher.add_handler(register_handler)
        self.dispatcher.add_handler(deregister_hanlder)
        self.dispatcher.add_handler(message_handler)
        

    @staticmethod
    def _get_message_arguments(message):
        message = message.split()

        return [] if len(message) < 2 or not message[0].startswith('/') else message[1:] 

    def start(self, update, context):
        update.message.reply_text(f"Hi, I'm PC Monitoring Bot. Your chat id is: {update.effective_user.id}")

    def status(self, update, context):

        update.message.reply_text('PC is [UNDEFINED]')
        pass

    def turnon(self, update, context):
        
        update.message.reply_text('PC has woken up.')

    def poweroff(self, update, context):

        update.message.reply_text('PC is shutting down.')
        pass
    
    def list(self, update, context):
        """List all groups and users"""

        if update.effective_chat.id >= 0:
            user = TelegramUser.objects.filter(chat_id=update.effective_chat.id)
            if not user.exists():
                update.message.reply_text("You don't have permission to perform this action.")
                return

        users = TelegramUser.objects.all()
        message = '* List of users:\n'
        for user in users:
            message += f"- {user.username} - {user.chat_id} - {user.role}\n"
        
        message += '\n\n* List of groups\n'
        groups = TelegramGroup.objects.all()
        for group in groups:
            message += f"- {group.name} - {group.chat_id} - noti: {group.receive_notification}\n"
        
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)

    def deregister(self, update, context):
        """Deregister user or group from database
        
        E.g.: /deregister
        """
        chat_user = update.effective_user
        group_chat_id = update.effective_chat.id

        if update.effective_chat.id < 0: # group
            group = TelegramGroup.objects.filter(chat_id=group_chat_id)
            if group.exists():
                group.delete()
        else: # user
            user = TelegramUser.objects.filter(chat_id=update.effective_chat.id)
            if user.exists():
                user.delete()

        update.message.reply_text('OK')

    def register(self, update, context):
        """
        Register user or group to database
        
        E.g.: /register
        """
        
        chat_user = update.effective_user
        group_chat_id = update.effective_chat.id

        if update.effective_chat.id < 0: # group
            group = TelegramGroup.objects.filter(chat_id=group_chat_id)
            if group.exists():
                update.message.reply_text('This group has already been registered.')
                return
                
            user = TelegramUser.objects.filter(chat_id=chat_user['id'], role=TelegramUser.ROLE.ADMIN)
            if not user.exists():
                update.message.reply_text(f"You don't have permission to perform this action.")
                return

            group_name = update.effective_chat.title
            
            group = TelegramGroup.objects.create(chat_id=group_chat_id, name=group_name)
        else: # user
            if chat_user['id'] != settings.TELEGRAM_MASTER_ID:
                update.message.reply_text("You don't have permission to perform this action.")
                return
            
            user = TelegramUser.objects.filter(chat_id=chat_user['id'])
            if user.exists():
                update.message.reply_text('You have already been registered.')
                return
            TelegramUser.objects.create(chat_id=settings.TELEGRAM_MASTER_ID, username=settings.TELEGRAM_MASTER_USERNAME, role=TelegramUser.ROLE.ADMIN)

        update.message.reply_text('OK')

    def set_role(self, update, context):
        """
        Set role for a user
        
        E.g: /set_role [CHAT_ID] [USERNAME] admin
        """

        chat_user = update.effective_user
        args = self._get_message_arguments(update.message.text)

        if not args:
            update.message.reply_text('Missing arguments: chat_id, username, and role.')
            return
        if len(args) != 3 or args[2] not in TelegramUser.ROLE.values or not args[0].isnumeric():
            update.message.reply_text('Invalid syntax')
            return
        
        user = TelegramUser.objects.filter(chat_id=chat_user['id'], role=TelegramUser.ROLE.ADMIN)
        if not user.exists():
            update.message.reply_text("You don't have permission to perform this action.")
            return
        
        target_user = TelegramUser.objects.filter(chat_id=args[0])
        if not target_user.exists():
            target_user = TelegramUser.objects.create(chat_id=int(args[0]), username=args[1])
        else:
            target_user = target_user.first()
        
        target_user.role = args[2]
        target_user.save()

        update.message.reply_text('OK')
        
    def set_noti(self, update, context):
        """Set notification setting for a group or an user"""

        chat_user = update.effective_user
        group_chat_id = update.effective_chat.id
        args = self._get_message_arguments(update.message.text)

        if not args:
            update.message.reply_text('Missing argument: true or false.')
            return

        if update.effective_chat.id < 0: # group
            group = TelegramGroup.objects.filter(chat_id=group_chat_id)
            if not group.exists():
                update.message.reply_text("This group has not been registered yet.")

            user = TelegramUser.objects.filter(chat_id=chat_user['id'], role=TelegramUser.ROLE.ADMIN)
            if not user.exists():
                update.message.reply_text(f"You don't have permission to perform this action.")
                return
        
            if args[0].lower() == 'true':
                group.receive_notification = True
                group.save()
            elif args[0].lower() == 'false':
                group.receive_notification = False
                group.save()
            else:
                update.message.reply_text('Invalid syntax')
                return
            
        else: # user
            user = TelegramUser.objects.filter(chat_id=chat_user['id'], role=TelegramUser.ROLE.ADMIN)
            if not user.exists():
                update.message.reply_text("You don't have permission to perform this action.")
                return
            user = user.first()
        
            if args[0].lower() == 'true':
                user.receive_notification = True
                user.save()
            elif args[0].lower() == 'false':
                user.receive_notification  = False
                user.save()
            else:
                update.message.reply_text('Invalid syntax')
                return
        
        update.message.reply_text('OK')
            
    def send_message(self, chat_id=None, message='nothing', attachment_path=''):
        '''Send message actively'''
        if not chat_id:
            chat_id = settings.TELEGRAM_MASTER_ID

        if not isinstance(message, str):
            logging.error("Can't send non-string message.")
            return
        self.updater.bot.send_message(chat_id=chat_id, text=message)

        if attachment_path.lower().endswith(('.jpg', '.png', '.gif')):
            self.updater.bot.send_chat_action(chat_id=chat_id, action="upload_photo")
            self.updater.bot.send_photo(chat_id=chat_id, photo=open(attachment_path, 'rb'))

    def default_response(self, update, context):
        update.message.reply_text("Sorry I don't understand. Please use a specific command.")

    def run(self):
        """Start polling"""

        try:
            self.send_message(message="PC Monitoring Bot has started")
        except Exception:
            logging.warning("Warning: Master has not initiate conversation with bot")

        # Start the Bot
        self.updater.start_polling()
        logging.info('PC Monitoring Bot is listening on Telegram...')

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()
        
