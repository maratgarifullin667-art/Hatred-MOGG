import discord
from discord.ext import commands
from discord.ui import Modal, View, Button, Select
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import json
import os
import re
from typing import Optional, List

# ===== НАСТРОЙКИ БОТА =====
EMBED_CHANNEL_ID = 0  # ID канала для эмбиенда
LOGS_CHANNEL_ID =  0  # ID канала для логов
VOICE_CHANNEL_ID =  0  # ID голосового канала для обзвона
CATEGORY_ID =  0  # ID категории для создания каналов
ADMIN_ROLE_ID =  0  # ID роли администрации
MODERATOR_ROLE_ID =  0  # ID роли модераторов
FARM_ROLE_ID =  0  # ID роли для Farm
APRENTICE_ROLE_ID =  0  # ID роли для Aprentice
DEPMODERATORE_ID = 0
MENTION_ROLE_IDS = [ADMIN_ROLE_ID, MODERATOR_ROLE_ID]

# ===== НАСТРОЙКИ ЛИЧНЫХ КАБИНЕТОВ =====
CABINET_CHANNEL_ID = 1563485002446938233     # ID канала для эмбиенда ЛК (0 = использовать EMBED_CHANNEL_ID)
CABINET_CATEGORY_ID = 1563484496093904937    # ID категории для ЛК (0 = использовать CATEGORY_ID)
CABINETS_FILE = 'cabinets.json'

# ===== НАСТРОЙКИ СИСТЕМЫ СБОРОВ =====
TIER_S_ROLE_ID = 1562467779032907786        # ID роли Tier S
TIER_1_ROLE_ID = 1562182232234524782        # ID роли Tier 1
TIER_2_ROLE_ID = 1562202327958683668        # ID роли Tier 2
TIER_3_ROLE_ID = 1562202554883121252        # ID роли Tier 3
GATHERING_MANAGE_ROLE_IDS = [ADMIN_ROLE_ID, MODERATOR_ROLE_ID]
GATHERINGS_FILE = 'gatherings.json'

TIER_ORDER = {'Tier S': 0, 'Tier 1': 1, 'Tier 2': 2, 'Tier 3': 3, 'Без тира': 4}
TIER_EMOJI = {'Tier S': '👑', 'Tier 1': '🥇', 'Tier 2': '🥈', 'Tier 3': '🥉', 'Без тира': '🟢'}

EMBED_IMAGE_URL = "https://media.discordapp.net/attachments/1545810377273516032/1545819519845670985/5tpw4fu8ieqox2gv.png?ex=6a9d881d&is=6a9c369d&hm=efc876ad3838259e3e6c686c3f4a67c9d1d4c44d94103315ec2d277529b34b43&=&format=webp&quality=lossless&width=384&height=256"

EMBED_TITLE = "**НАБОР В СЕМЬЮ HIKARU**"
EMBED_DESCRIPTION = "**Принимаем заявки на две роли Farm/Aprentice**\n\nХочешь проверить себя в деле?\nЗаявка открыта ровно до того момента, пока мы не наберём полный состав.\n**Докажи, что ты достоин носить нашу фамилию.**"
EMBED_FOOTER = "Выберите тип заявки ниже 👇"

FARM_BUTTON_LABEL = "123"
APRENTICE_BUTTON_LABEL = "RP Hatred"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

APPLICATIONS_FILE = 'applications.json'
CONFIG_FILE = 'bot_config.json'
STATS_FILE = 'stats.json'


class ApplicationSystem:
    def __init__(self):
        self.applications = {}
        self.load_applications()

    def load_applications(self):
        if os.path.exists(APPLICATIONS_FILE):
            try:
                with open(APPLICATIONS_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.applications = json.loads(content)
                    else:
                        self.applications = {}
            except:
                self.applications = {}
        else:
            self.applications = {}

    def save_applications(self):
        try:
            with open(APPLICATIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.applications, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения заявок: {e}")

    def add_application(self, user_id, app_type, data, channel_id=None):
        app_id = str(len(self.applications) + 1)
        self.applications[app_id] = {
            'user_id': user_id,
            'type': app_type,
            'data': data,
            'status': 'pending',
            'timestamp': datetime.now().isoformat(),
            'reviewed_by': None,
            'review_date': None,
            'rejection_reason': None,
            'interview_called': False,
            'channel_id': channel_id,
            'taken_by': None,
            'taken_at': None,
            'interview_by': None,
            'interview_at': None,
            'private_message_id': None,
            'log_message_id': None,
            'is_new_user': True,
            'accepted_by': None,
            'accepted_at': None
        }
        self.save_applications()
        return app_id

    def get_user_applications(self, user_id):
        return [app for app in self.applications.values()
                if app['user_id'] == user_id and app['status'] in ['pending', 'under_review', 'interview']]

    def has_previous_accepted_except(self, user_id, current_app_id):
        return any(
            app['user_id'] == user_id and
            app['status'] == 'accepted' and
            app_id != current_app_id
            for app_id, app in self.applications.items()
        )

    def update_status(self, app_id, status, reviewer_id=None, reason=None):
        if app_id in self.applications:
            self.applications[app_id]['status'] = status
            if reviewer_id:
                self.applications[app_id]['reviewed_by'] = reviewer_id
            if reason:
                self.applications[app_id]['rejection_reason'] = reason
            self.applications[app_id]['review_date'] = datetime.now().isoformat()

            if status == 'accepted' and reviewer_id:
                self.applications[app_id]['accepted_by'] = reviewer_id
                self.applications[app_id]['accepted_at'] = datetime.now().isoformat()
                user_id = self.applications[app_id]['user_id']
                if self.has_previous_accepted_except(user_id, app_id):
                    self.applications[app_id]['is_new_user'] = False
                else:
                    self.applications[app_id]['is_new_user'] = True

            self.save_applications()
            return True
        return False

    def take_application(self, app_id, reviewer_id):
        if app_id in self.applications:
            self.applications[app_id]['status'] = 'under_review'
            self.applications[app_id]['taken_by'] = reviewer_id
            self.applications[app_id]['taken_at'] = datetime.now().isoformat()
            self.save_applications()
            return True
        return False

    def mark_interview_called(self, app_id, reviewer_id):
        if app_id in self.applications:
            self.applications[app_id]['interview_called'] = True
            self.applications[app_id]['interview_by'] = reviewer_id
            self.applications[app_id]['interview_at'] = datetime.now().isoformat()
            self.save_applications()
            return True
        return False

    def set_private_message_id(self, app_id, message_id):
        if app_id in self.applications:
            self.applications[app_id]['private_message_id'] = message_id
            self.save_applications()
            return True
        return False

    def set_log_message_id(self, app_id, message_id):
        if app_id in self.applications:
            self.applications[app_id]['log_message_id'] = message_id
            self.save_applications()
            return True
        return False


class StatsSystem:
    def __init__(self):
        self.stats = {}
        self.load_stats()

    def load_stats(self):
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.stats = json.loads(content)
                    else:
                        self.stats = {}
            except:
                self.stats = {}
        else:
            self.stats = {}

    def save_stats(self):
        try:
            with open(STATS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения статистики: {e}")

    def add_accepted(self, reviewer_id, user_id, app_id, app_type):
        reviewer_id = str(reviewer_id)
        if reviewer_id not in self.stats:
            self.stats[reviewer_id] = {
                'accepted_users': [],
                'total_accepted': 0,
                'new_users_accepted': 0
            }

        for entry in self.stats[reviewer_id]['accepted_users']:
            if entry['user_id'] == user_id:
                entry['app_id'] = app_id
                entry['app_type'] = app_type
                entry['accepted_at'] = datetime.now().isoformat()
                entry['is_new'] = False
                self.save_stats()
                return

        self.stats[reviewer_id]['accepted_users'].append({
            'user_id': user_id,
            'app_id': app_id,
            'app_type': app_type,
            'accepted_at': datetime.now().isoformat(),
            'is_new': True
        })
        self.stats[reviewer_id]['total_accepted'] += 1
        self.stats[reviewer_id]['new_users_accepted'] += 1
        self.save_stats()

    def get_stats(self, reviewer_id, start_date=None, end_date=None):
        reviewer_id = str(reviewer_id)
        if reviewer_id not in self.stats:
            return {'new_users': 0, 'total': 0, 'users': []}

        users = []
        new_users = 0

        for entry in self.stats[reviewer_id]['accepted_users']:
            accepted_at = datetime.fromisoformat(entry['accepted_at'])
            if start_date and accepted_at < start_date:
                continue
            if end_date and accepted_at > end_date:
                continue

            users.append(entry)
            if entry.get('is_new', False):
                new_users += 1

        return {'new_users': new_users, 'total': len(users), 'users': users}


class BotConfig:
    def __init__(self):
        self.config = {}
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.config = json.loads(content)
                    else:
                        self.config = {}
            except:
                self.config = {}
        else:
            self.config = {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")

    def get_embed_message_id(self):
        return self.config.get('embed_message_id')

    def set_embed_message_id(self, message_id):
        self.config['embed_message_id'] = message_id
        self.save_config()

    def get_cabinet_embed_message_id(self):
        return self.config.get('cabinet_embed_message_id')

    def set_cabinet_embed_message_id(self, message_id):
        self.config['cabinet_embed_message_id'] = message_id
        self.save_config()


# ===== СИСТЕМА ЛИЧНЫХ КАБИНЕТОВ =====
class CabinetSystem:
    def __init__(self):
        self.cabinets = {}
        self.load()

    def load(self):
        if os.path.exists(CABINETS_FILE):
            try:
                with open(CABINETS_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    self.cabinets = json.loads(content) if content else {}
            except Exception as e:
                print(f"Ошибка загрузки кабинетов: {e}")
                self.cabinets = {}
        else:
            self.cabinets = {}

    def save(self):
        try:
            with open(CABINETS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cabinets, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения кабинетов: {e}")

    def has_cabinet(self, user_id):
        return str(user_id) in self.cabinets

    def get_cabinet(self, user_id):
        return self.cabinets.get(str(user_id))

    def add_cabinet(self, user_id, nick, static, channel_id):
        self.cabinets[str(user_id)] = {
            'nick': nick,
            'static': static,
            'channel_id': channel_id,
            'created_at': datetime.now().isoformat()
        }
        self.save()

    def remove_cabinet(self, user_id):
        if str(user_id) in self.cabinets:
            del self.cabinets[str(user_id)]
            self.save()
            return True
        return False


app_system = ApplicationSystem()
bot_config = BotConfig()
stats_system = StatsSystem()
cabinet_system = CabinetSystem()


class RejectionModal(Modal):
    def __init__(self, app_id):
        super().__init__(title="Причина отказа")
        self.app_id = app_id

        self.reason = discord.ui.TextInput(
            label="Причина отказа",
            placeholder="Введите причину отказа...",
            required=True,
            max_length=500,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        await self.process_rejection(interaction, self.reason.value)

    async def process_rejection(self, interaction, reason):
        app_data = app_system.applications.get(self.app_id)
        if not app_data:
            await interaction.response.send_message("❌ Заявка не найдена!", ephemeral=True)
            return

        app_system.update_status(self.app_id, 'rejected', interaction.user.id, reason)

        user = await bot.fetch_user(app_data['user_id'])
        if user:
            try:
                embed = discord.Embed(
                    title="❌ Заявка отклонена",
                    description=f"К сожалению, ваша заявка #{self.app_id} на роль {app_data['type']} была отклонена.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Причина отказа", value=reason, inline=False)
                await user.send(embed=embed)
            except:
                pass

        await update_log(app_data, 'rejected', interaction.user, reason)
        await update_private_channel(app_data, 'rejected', interaction.user, reason)
        await delete_application_channel(app_data)

        await interaction.response.send_message(f"✅ Заявка #{self.app_id} отклонена!", ephemeral=True)


class ApplicationModal(Modal):
    def __init__(self, app_type):
        if app_type == "Farm":
            super().__init__(title="Заявка - Farm")
        else:
            super().__init__(title="Заявка - Aprentice")
        self.app_type = app_type

        if app_type == "Farm":
            self.nickname_static = discord.ui.TextInput(
                label="Ваш игровой никнейм и статик",
                placeholder="Например: Nickname #123",
                required=True,
                max_length=100
            )
            self.add_item(self.nickname_static)
        else:
            self.nickname = discord.ui.TextInput(
                label="Ваш ник в игре",
                placeholder="Введите ваш игровой ник",
                required=True,
                max_length=100
            )
            self.add_item(self.nickname)

            self.static = discord.ui.TextInput(
                label="Статик #",
                placeholder="Введите номер статика",
                required=True,
                max_length=50
            )
            self.add_item(self.static)

            self.age_occ = discord.ui.TextInput(
                label="Имя, Возраст OCC",
                placeholder="Например: Иван, 18",
                required=True,
                max_length=100
            )
            self.add_item(self.age_occ)

            self.goal = discord.ui.TextInput(
                label="Цель вступления",
                placeholder="Опишите вашу цель вступления...",
                required=True,
                max_length=500,
                style=discord.TextStyle.paragraph
            )
            self.add_item(self.goal)

            self.how_known = discord.ui.TextInput(
                label="Как узнали о семье",
                placeholder="Расскажите, как вы узнали о нас...",
                required=True,
                max_length=500,
                style=discord.TextStyle.paragraph
            )
            self.add_item(self.how_known)

    async def on_submit(self, interaction: discord.Interaction):
        if self.app_type == "Aprentice":
            try:
                age_text = self.age_occ.value
                age_matches = re.findall(r'\d+', age_text)
                if age_matches:
                    age = int(age_matches[0])
                    if age < 16:
                        embed = discord.Embed(
                            title="❌ Заявка отклонена",
                            description="К сожалению, ваша заявка была автоматически отклонена.",
                            color=discord.Color.red(),
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="Причина",
                                        value="Возрастное ограничение: принимаются заявки только от 16 лет.",
                                        inline=False)

                        try:
                            await interaction.user.send(embed=embed)
                        except:
                            pass

                        await interaction.response.send_message(
                            "❌ **Заявка отклонена**: Принимаются заявки только от 16 лет!",
                            ephemeral=True
                        )
                        return
            except:
                pass

        existing_apps = app_system.get_user_applications(interaction.user.id)
        if existing_apps:
            await interaction.response.send_message(
                "❌ **Ошибка**: У вас уже есть активная заявка!",
                ephemeral=True
            )
            return

        category = discord.utils.get(interaction.guild.categories, id=CATEGORY_ID)
        if category:
            channel_name = f"заявка-{interaction.user.name}"
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
            mod_role = interaction.guild.get_role(MODERATOR_ROLE_ID)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            if mod_role:
                overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            try:
                channel = await interaction.guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites
                )
            except Exception as e:
                channel = None
                print(f"Ошибка создания канала: {e}")
        else:
            channel = None

        data = {}
        if self.app_type == "Farm":
            data['nickname_static'] = self.nickname_static.value
        else:
            data['nickname'] = self.nickname.value
            data['static'] = self.static.value
            data['age_occ'] = self.age_occ.value
            data['goal'] = self.goal.value
            data['how_known'] = self.how_known.value

        channel_id = channel.id if channel else None
        app_id = app_system.add_application(interaction.user.id, self.app_type, data, channel_id)

        mentions = []
        for role_id in MENTION_ROLE_IDS:
            role = interaction.guild.get_role(role_id)
            if role:
                mentions.append(role.mention)

        mentions_text = " ".join(mentions) if mentions else ""

        if channel:
            embed = create_private_embed(app_id, self.app_type, data, 'pending', interaction.user)
            view = PrivateChannelView(app_id)

            content_parts = []
            content_parts.append(f"**Заявитель:** {interaction.user.mention}")
            if mentions_text:
                content_parts.append(f"**Модерация:** {mentions_text}")

            content = "\n".join(content_parts)

            private_message = await channel.send(content, embed=embed, view=view)

            app_system.set_private_message_id(app_id, private_message.id)

        await create_log(app_system.applications[app_id], 'created', interaction.user)

        await interaction.response.send_message(
            f"✅ **Заявка #{app_id} успешно отправлена!**\n"
            "Ожидайте рассмотрения. Ответ придёт в личные сообщения.",
            ephemeral=True
        )


def create_private_embed(app_id, app_type, data, status, user=None, reason=None):
    embed = discord.Embed(
        title=f"📋 Заявка #{app_id}",
        description=f"**Тип**: {app_type}",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    if user:
        embed.add_field(name="Заявитель", value=user.mention, inline=True)
        embed.add_field(name="ID", value=str(user.id), inline=True)

    embed.add_field(name="Статус", value=get_status_emoji(status), inline=True)

    if status == 'pending':
        embed.add_field(name="Взял в работу", value="Никто", inline=True)
    elif status == 'under_review' and user:
        embed.add_field(name="Взял в работу", value=user.mention, inline=True)
    elif status == 'interview' and user:
        embed.add_field(name="Кто вызвал", value=user.mention, inline=True)
    elif status == 'accepted' and user:
        embed.add_field(name="Кто принял", value=user.mention, inline=True)
    elif status == 'rejected' and user:
        embed.color = discord.Color.red()
        embed.add_field(name="Кто отклонил", value=user.mention, inline=True)
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)

    if app_type == "Farm":
        embed.add_field(name="Никнейм и статик", value=data['nickname_static'], inline=False)
    else:
        embed.add_field(name="Ник в игре", value=data['nickname'], inline=True)
        embed.add_field(name="Статик #", value=data['static'], inline=True)
        embed.add_field(name="Имя, Возраст OCC", value=data['age_occ'], inline=False)
        embed.add_field(name="Цель вступления", value=data['goal'], inline=False)
        embed.add_field(name="Как узнали о семье", value=data['how_known'], inline=False)

    return embed


def get_status_emoji(status):
    status_map = {
        'pending': '🕐 Ожидает рассмотрения',
        'under_review': '📋 В рассмотрении',
        'interview': '📞 Вызван на обзвон',
        'accepted': '✅ Принята',
        'rejected': '❌ Отклонена'
    }
    return status_map.get(status, '❓ Неизвестно')


class PrivateChannelView(View):
    def __init__(self, app_id):
        super().__init__(timeout=None)
        self.app_id = app_id

    @discord.ui.button(label="📋 Взять на рассмотрение", style=discord.ButtonStyle.primary,
                       custom_id="pc_take_review_btn")
    async def take_review_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_take_review(interaction)

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.green, custom_id="pc_accept_btn")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_accept(interaction)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.red, custom_id="pc_reject_btn")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_reject(interaction)

    async def handle_take_review(self, interaction):
        if not self.check_permissions(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

        app_data = app_system.applications.get(self.app_id)
        if not app_data:
            await interaction.response.send_message("❌ Заявка не найдена!", ephemeral=True)
            return

        if app_data['status'] == 'under_review':
            await interaction.response.send_message("❌ Эта заявка уже взята в работу!", ephemeral=True)
            return

        app_system.take_application(self.app_id, interaction.user.id)

        if interaction.message:
            embed = create_private_embed(
                self.app_id,
                app_data['type'],
                app_data['data'],
                'under_review',
                interaction.user
            )
            new_view = PrivateUnderReviewView(self.app_id)
            await interaction.message.edit(embed=embed, view=new_view)

        await update_log(app_data, 'under_review', interaction.user)

        user = await bot.fetch_user(app_data['user_id'])
        if user:
            try:
                embed = discord.Embed(
                    title="📋 Заявка взята в работу",
                    description=f"Ваша заявка #{self.app_id} взята в работу.",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed.add_field(name="Взял в работу", value=interaction.user.mention, inline=False)
                await user.send(embed=embed)
            except:
                pass

        await interaction.response.send_message(f"✅ Заявка #{self.app_id} взята в работу!", ephemeral=True)

    async def handle_accept(self, interaction):
        if not self.check_permissions(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

        await self.accept_application(interaction)

    async def handle_reject(self, interaction):
        if not self.check_permissions(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

        modal = RejectionModal(self.app_id)
        await interaction.response.send_modal(modal)

    async def accept_application(self, interaction):
        app_data = app_system.applications.get(self.app_id)
        if not app_data:
            await interaction.response.send_message("❌ Заявка не найдена!", ephemeral=True)
            return

        is_new_user = not app_system.has_previous_accepted_except(app_data['user_id'], self.app_id)

        app_system.update_status(self.app_id, 'accepted', interaction.user.id)

        role_given = await give_role(interaction.guild, app_data)

        if is_new_user:
            stats_system.add_accepted(interaction.user.id, app_data['user_id'], self.app_id, app_data['type'])

        user = await bot.fetch_user(app_data['user_id'])
        if user:
            try:
                embed = discord.Embed(
                    title="✅ Заявка принята!",
                    description=f"Поздравляем! Ваша заявка #{self.app_id} на роль {app_data['type']} была одобрена!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                if role_given:
                    embed.add_field(name="Роль выдана", value="✅ Роль успешно выдана", inline=False)
                embed.add_field(name="Дальнейшие действия",
                                value="С вами свяжется администрация для дальнейших инструкций.")
                await user.send(embed=embed)
            except:
                pass

        if interaction.message:
            embed = create_private_embed(
                self.app_id,
                app_data['type'],
                app_data['data'],
                'accepted',
                interaction.user
            )
            if role_given:
                embed.add_field(name="Роль", value="✅ Выдана", inline=True)
            await interaction.message.edit(embed=embed, view=None)

        await update_log(app_data, 'accepted', interaction.user)
        await delete_application_channel(app_data)

        await interaction.response.send_message(f"✅ Заявка #{self.app_id} принята!", ephemeral=True)

    def check_permissions(self, user):
        if not user.guild_permissions.administrator:
            admin_role = discord.utils.get(user.roles, id=ADMIN_ROLE_ID)
            mod_role = discord.utils.get(user.roles, id=MODERATOR_ROLE_ID)
            return admin_role is not None or mod_role is not None
        return True


class PrivateUnderReviewView(View):
    def __init__(self, app_id):
        super().__init__(timeout=None)
        self.app_id = app_id

    @discord.ui.button(label="📞 Вызвать на обзвон", style=discord.ButtonStyle.blurple,
                       custom_id="pcur_call_interview_btn")
    async def call_interview_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_call_interview(interaction)

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.green, custom_id="pcur_accept_btn")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_accept(interaction)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.red, custom_id="pcur_reject_btn")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_reject(interaction)

    async def handle_call_interview(self, interaction):
        if not self.check_permissions(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

        app_data = app_system.applications.get(self.app_id)
        if not app_data:
            await interaction.response.send_message("❌ Заявка не найдена!", ephemeral=True)
            return

        app_system.mark_interview_called(self.app_id, interaction.user.id)
        app_system.update_status(self.app_id, 'interview')

        voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
        user = await bot.fetch_user(app_data['user_id'])

        if voice_channel and user:
            try:
                invite = await voice_channel.create_invite(max_age=3600, max_uses=1)
                await user.send(f"🔊 Вы приглашены на обзвон по заявке #{self.app_id}!\nСсылка: {invite.url}")

                embed = create_private_embed(
                    self.app_id,
                    app_data['type'],
                    app_data['data'],
                    'interview',
                    interaction.user
                )
                new_view = PrivateDecisionView(self.app_id)
                await interaction.message.edit(embed=embed, view=new_view)

                await update_log(app_data, 'interview', interaction.user)

                await interaction.response.send_message(f"✅ Пользователь вызван на обзвон!", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Ошибка: не найден голосовой канал или пользователь!",
                                                    ephemeral=True)

    async def handle_accept(self, interaction):
        if not self.check_permissions(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

        await self.accept_application(interaction)

    async def handle_reject(self, interaction):
        if not self.check_permissions(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

        modal = RejectionModal(self.app_id)
        await interaction.response.send_modal(modal)

    async def accept_application(self, interaction):
        app_data = app_system.applications.get(self.app_id)
        if not app_data:
            await interaction.response.send_message("❌ Заявка не найдена!", ephemeral=True)
            return

        is_new_user = not app_system.has_previous_accepted_except(app_data['user_id'], self.app_id)

        app_system.update_status(self.app_id, 'accepted', interaction.user.id)

        role_given = await give_role(interaction.guild, app_data)

        if is_new_user:
            stats_system.add_accepted(interaction.user.id, app_data['user_id'], self.app_id, app_data['type'])

        user = await bot.fetch_user(app_data['user_id'])
        if user:
            try:
                embed = discord.Embed(
                    title="✅ Заявка принята!",
                    description=f"Поздравляем! Ваша заявка #{self.app_id} на роль {app_data['type']} была одобрена!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                if role_given:
                    embed.add_field(name="Роль выдана", value="✅ Роль успешно выдана", inline=False)
                embed.add_field(name="Дальнейшие действия",
                                value="С вами свяжется администрация для дальнейших инструкций.")
                await user.send(embed=embed)
            except:
                pass

        if interaction.message:
            embed = create_private_embed(
                self.app_id,
                app_data['type'],
                app_data['data'],
                'accepted',
                interaction.user
            )
            if role_given:
                embed.add_field(name="Роль", value="✅ Выдана", inline=True)
            await interaction.message.edit(embed=embed, view=None)

        await update_log(app_data, 'accepted', interaction.user)
        await delete_application_channel(app_data)

        await interaction.response.send_message(f"✅ Заявка #{self.app_id} принята!", ephemeral=True)

    def check_permissions(self, user):
        if not user.guild_permissions.administrator:
            admin_role = discord.utils.get(user.roles, id=ADMIN_ROLE_ID)
            mod_role = discord.utils.get(user.roles, id=MODERATOR_ROLE_ID)
            return admin_role is not None or mod_role is not None
        return True


class PrivateDecisionView(View):
    def __init__(self, app_id):
        super().__init__(timeout=None)
        self.app_id = app_id

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.green, custom_id="pcd_accept_btn")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_accept(interaction)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.red, custom_id="pcd_reject_btn")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_reject(interaction)

    async def handle_accept(self, interaction):
        if not self.check_permissions(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

        await self.accept_application(interaction)

    async def handle_reject(self, interaction):
        if not self.check_permissions(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

        modal = RejectionModal(self.app_id)
        await interaction.response.send_modal(modal)

    async def accept_application(self, interaction):
        app_data = app_system.applications.get(self.app_id)
        if not app_data:
            await interaction.response.send_message("❌ Заявка не найдена!", ephemeral=True)
            return

        is_new_user = not app_system.has_previous_accepted_except(app_data['user_id'], self.app_id)

        app_system.update_status(self.app_id, 'accepted', interaction.user.id)

        role_given = await give_role(interaction.guild, app_data)

        if is_new_user:
            stats_system.add_accepted(interaction.user.id, app_data['user_id'], self.app_id, app_data['type'])

        user = await bot.fetch_user(app_data['user_id'])
        if user:
            try:
                embed = discord.Embed(
                    title="✅ Заявка принята!",
                    description=f"Поздравляем! Ваша заявка #{self.app_id} на роль {app_data['type']} была одобрена!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                if role_given:
                    embed.add_field(name="Роль выдана", value="✅ Роль успешно выдана", inline=False)
                embed.add_field(name="Дальнейшие действия",
                                value="С вами свяжется администрация для дальнейших инструкций.")
                await user.send(embed=embed)
            except:
                pass

        if interaction.message:
            embed = create_private_embed(
                self.app_id,
                app_data['type'],
                app_data['data'],
                'accepted',
                interaction.user
            )
            if role_given:
                embed.add_field(name="Роль", value="✅ Выдана", inline=True)
            await interaction.message.edit(embed=embed, view=None)

        await update_log(app_data, 'accepted', interaction.user)
        await delete_application_channel(app_data)

        await interaction.response.send_message(f"✅ Заявка #{self.app_id} принята!", ephemeral=True)

    def check_permissions(self, user):
        if not user.guild_permissions.administrator:
            admin_role = discord.utils.get(user.roles, id=ADMIN_ROLE_ID)
            mod_role = discord.utils.get(user.roles, id=MODERATOR_ROLE_ID)
            return admin_role is not None or mod_role is not None
        return True


async def update_private_channel(app_data, status, user, reason=None):
    if 'channel_id' not in app_data or not app_data['channel_id']:
        return

    channel = bot.get_channel(app_data['channel_id'])
    if not channel:
        return

    embed = create_private_embed_from_data(app_data, status, user, reason)

    if 'private_message_id' in app_data and app_data['private_message_id']:
        try:
            message = await channel.fetch_message(app_data['private_message_id'])
            await message.edit(embed=embed)
            return
        except:
            pass

    message = await channel.send(embed=embed)
    for app_id, app in app_system.applications.items():
        if app.get('channel_id') == app_data.get('channel_id'):
            app_system.set_private_message_id(app_id, message.id)
            break


def create_private_embed_from_data(app_data, status, user=None, reason=None):
    app_id = None
    for aid, app in app_system.applications.items():
        if app.get('channel_id') == app_data.get('channel_id'):
            app_id = aid
            break

    embed = discord.Embed(
        title=f"📋 Заявка #{app_id or 'Неизвестно'}",
        description=f"Тип: {app_data.get('type', 'Неизвестно')}",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    if 'user_id' in app_data:
        embed.add_field(name="Заявитель", value=f"<@{app_data['user_id']}>", inline=True)
        embed.add_field(name="ID", value=str(app_data['user_id']), inline=True)

    embed.add_field(name="Статус", value=get_status_emoji(status), inline=True)

    if status == 'under_review' and user:
        embed.add_field(name="Взял в работу", value=user.mention, inline=True)
    elif status == 'interview' and user:
        embed.add_field(name="Кто вызвал", value=user.mention, inline=True)
    elif status == 'accepted' and user:
        embed.add_field(name="Кто принял", value=user.mention, inline=True)
    elif status == 'rejected' and user:
        embed.color = discord.Color.red()
        embed.add_field(name="Кто отклонил", value=user.mention, inline=True)
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
    else:
        embed.add_field(name="Взял в работу", value="Никто", inline=True)

    if 'data' in app_data and app_data['data']:
        if 'nickname_static' in app_data['data']:
            embed.add_field(name="Никнейм и статик", value=app_data['data']['nickname_static'], inline=False)
        elif 'nickname' in app_data['data']:
            embed.add_field(name="Ник в игре", value=app_data['data']['nickname'], inline=True)
            embed.add_field(name="Статик #", value=app_data['data']['static'], inline=True)
            if 'age_occ' in app_data['data']:
                embed.add_field(name="Имя, Возраст OCC", value=app_data['data']['age_occ'], inline=False)
            if 'goal' in app_data['data']:
                embed.add_field(name="Цель вступления", value=app_data['data']['goal'], inline=False)
            if 'how_known' in app_data['data']:
                embed.add_field(name="Как узнали о семье", value=app_data['data']['how_known'], inline=False)

    return embed


async def create_log(app_data, action, user, reason=None):
    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if logs_channel:
        embed = create_log_embed(app_data, action, user, reason)
        message = await logs_channel.send(embed=embed)

        for app_id, app in app_system.applications.items():
            if app.get('user_id') == app_data.get('user_id') and app.get('type') == app_data.get('type'):
                app_system.set_log_message_id(app_id, message.id)
                break


async def update_log(app_data, action, user, reason=None):
    logs_channel = bot.get_channel(LOGS_CHANNEL_ID)
    if not logs_channel:
        return

    app_id = None
    for aid, app in app_system.applications.items():
        if app.get('user_id') == app_data.get('user_id') and app.get('type') == app_data.get('type'):
            app_id = aid
            break

    if app_id and 'log_message_id' in app_system.applications[app_id] and app_system.applications[app_id][
        'log_message_id']:
        try:
            message = await logs_channel.fetch_message(app_system.applications[app_id]['log_message_id'])
            embed = create_log_embed(app_data, action, user, reason)
            await message.edit(embed=embed)
            return
        except:
            pass

    embed = create_log_embed(app_data, action, user, reason)
    message = await logs_channel.send(embed=embed)

    if app_id:
        app_system.set_log_message_id(app_id, message.id)


def create_log_embed(app_data, action, user, reason=None):
    embed = discord.Embed(
        title="📝 Лог заявки",
        color=discord.Color.greyple(),
        timestamp=datetime.now()
    )

    action_map = {
        'created': '📋 Заявка создана',
        'auto_rejected_age': '❌ Автоматически отклонена (возраст)',
        'under_review': '📋 Взята в работу',
        'interview': '📞 Вызван на обзвон',
        'accepted': '✅ Принята',
        'rejected': '❌ Отклонена'
    }

    embed.add_field(name="Действие", value=action_map.get(action, action), inline=False)
    embed.add_field(name="Инициатор", value=user.mention if hasattr(user, 'mention') else str(user), inline=True)
    embed.add_field(name="Тип заявки", value=app_data.get('type', 'Неизвестно'), inline=True)

    if 'user_id' in app_data:
        embed.add_field(name="Заявитель", value=f"<@{app_data['user_id']}>", inline=True)
        embed.add_field(name="ID заявителя", value=str(app_data['user_id']), inline=True)

    if 'data' in app_data and app_data['data']:
        if 'nickname_static' in app_data['data']:
            embed.add_field(name="Никнейм и статик", value=app_data['data']['nickname_static'], inline=False)
        elif 'nickname' in app_data['data']:
            embed.add_field(name="Ник в игре", value=app_data['data']['nickname'], inline=True)
            embed.add_field(name="Статик #", value=app_data['data']['static'], inline=True)
            if 'age_occ' in app_data['data']:
                embed.add_field(name="Имя, Возраст OCC", value=app_data['data']['age_occ'], inline=False)

    if 'timestamp' in app_data:
        embed.add_field(name="Создана", value=app_data['timestamp'][:19].replace('T', ' '), inline=True)
    if 'review_date' in app_data and app_data['review_date']:
        embed.add_field(name="Обработана", value=app_data['review_date'][:19].replace('T', ' '), inline=True)

    if 'taken_by' in app_data and app_data['taken_by']:
        embed.add_field(name="Взял в работу", value=f"<@{app_data['taken_by']}>", inline=True)
    if 'interview_by' in app_data and app_data['interview_by']:
        embed.add_field(name="Кто вызвал на обзвон", value=f"<@{app_data['interview_by']}>", inline=True)
    if 'accepted_by' in app_data and app_data['accepted_by']:
        embed.add_field(name="Кто принял", value=f"<@{app_data['accepted_by']}>", inline=True)

    if reason:
        embed.add_field(name="Причина", value=reason, inline=False)

    return embed


async def give_role(guild, app_data):
    try:
        user_id = app_data['user_id']
        member = guild.get_member(user_id)

        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except:
                return False

        if app_data['type'] == 'Farm':
            role_id = FARM_ROLE_ID
        elif app_data['type'] == 'Aprentice':
            role_id = APRENTICE_ROLE_ID
        else:
            return False

        role = guild.get_role(role_id)
        if role and member:
            await member.add_roles(role)
            print(f"Роль {role.name} выдана пользователю {member.name}")
            return True
        else:
            print(f"Ошибка: роль с ID {role_id} не найдена или пользователь не найден")
            return False
    except Exception as e:
        print(f"Ошибка выдачи роли: {e}")
        return False


class ApplicationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label=FARM_BUTTON_LABEL, style=discord.ButtonStyle.gray, custom_id="app_farm_btn")
    async def farm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ApplicationModal("Farm")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label=APRENTICE_BUTTON_LABEL, style=discord.ButtonStyle.gray, custom_id="app_aprentice_btn")
    async def aprentice_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ApplicationModal("Aprentice")
        await interaction.response.send_modal(modal)


# ===== ЛИЧНЫЕ КАБИНЕТЫ — VIEW / MODAL =====
class CabinetModal(Modal):
    def __init__(self):
        super().__init__(title="Создание личного кабинета")

        self.nick = discord.ui.TextInput(
            label="Ваш игровой ник",
            placeholder="Например: Axess Swagov",
            required=True,
            max_length=40
        )
        self.add_item(self.nick)

        self.static = discord.ui.TextInput(
            label="Ваш статик",
            placeholder="Например: 110897",
            required=True,
            max_length=15
        )
        self.add_item(self.static)

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user

        if cabinet_system.has_cabinet(user.id):
            cab = cabinet_system.get_cabinet(user.id)
            existing = interaction.guild.get_channel(cab['channel_id']) if cab else None
            if existing:
                await interaction.response.send_message(
                    f"❌ У вас уже есть личный кабинет: {existing.mention}",
                    ephemeral=True
                )
                return
            cabinet_system.remove_cabinet(user.id)

        cat_id = CABINET_CATEGORY_ID if CABINET_CATEGORY_ID else CATEGORY_ID
        category = discord.utils.get(interaction.guild.categories, id=cat_id)

        raw_name = f"{self.nick.value} | {self.static.value}"
        channel_name = re.sub(r'[^\w\s\|\-]', '', raw_name).strip()[:95] or f"cabinet-{user.name}"

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True,
                use_external_emojis=True
            ),
            interaction.guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True
            )
        }
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        mod_role = interaction.guild.get_role(MODERATOR_ROLE_ID)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if mod_role:
            overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"ЛК {user.name} | Ник: {self.nick.value} | Статик: {self.static.value}"
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Ошибка создания канала: `{e}`", ephemeral=True
            )
            return

        cabinet_system.add_cabinet(user.id, self.nick.value, self.static.value, channel.id)

        embed = discord.Embed(
            title="📁 Личный кабинет",
            description=f"Это приватный канал {user.mention}. Здесь вас видят только вы и администрация.",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="👤 Владелец", value=user.mention, inline=True)
        embed.add_field(name="🎮 Ник", value=self.nick.value, inline=True)
        embed.add_field(name="🔢 Статик", value=self.static.value, inline=True)
        embed.set_footer(text="Кабинет виден только вам и администрации")

        await channel.send(content=user.mention, embed=embed, view=CabinetControlView(user.id))

        await interaction.response.send_message(
            f"✅ Личный кабинет создан: {channel.mention}", ephemeral=True
        )


class CabinetControlView(View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="🗑️ Удалить кабинет", style=discord.ButtonStyle.red,
                       custom_id="cabinet_delete_btn")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        is_admin_perm = interaction.user.guild_permissions.administrator
        has_admin_role = discord.utils.get(interaction.user.roles, id=ADMIN_ROLE_ID) is not None
        has_mod_role = discord.utils.get(interaction.user.roles, id=MODERATOR_ROLE_ID) is not None

        if not (is_admin_perm or has_admin_role or has_mod_role):
            await interaction.response.send_message(
                "❌ Удалить кабинет может только администрация.",
                ephemeral=True
            )
            return

        cabinet_system.remove_cabinet(self.owner_id)
        await interaction.response.send_message("🗑️ Кабинет удаляется...", ephemeral=True)
        try:
            await interaction.channel.delete()
        except Exception as e:
            print(f"Ошибка удаления кабинета: {e}")


class CabinetView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📁 Создать личный кабинет",
                       style=discord.ButtonStyle.primary,
                       custom_id="cabinet_create_btn")
    async def create_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CabinetModal())


async def delete_application_channel(app_data):
    if 'channel_id' in app_data and app_data['channel_id']:
        try:
            channel = bot.get_channel(app_data['channel_id'])
            if channel:
                await channel.delete()
        except Exception as e:
            print(f"Ошибка удаления канала: {e}")


async def restore_application_views():
    for app_id, app_data in app_system.applications.items():
        if app_data['status'] in ['pending', 'under_review', 'interview']:
            channel_id = app_data.get('channel_id')
            if channel_id:
                channel = bot.get_channel(channel_id)
                if channel:
                    message_id = app_data.get('private_message_id')
                    if message_id:
                        try:
                            message = await channel.fetch_message(message_id)

                            if app_data['status'] == 'pending':
                                view = PrivateChannelView(app_id)
                            elif app_data['status'] == 'under_review':
                                view = PrivateUnderReviewView(app_id)
                            elif app_data['status'] == 'interview':
                                view = PrivateDecisionView(app_id)
                            else:
                                continue

                            await message.edit(view=view)
                            print(f"✅ View восстановлен для заявки #{app_id}")
                        except discord.NotFound:
                            print(f"⚠️ Сообщение для заявки #{app_id} не найдено")
                        except Exception as e:
                            print(f"Ошибка восстановления view для заявки #{app_id}: {e}")


# ==========================================================
# ===== СИСТЕМА СБОРОВ =====================================
# ==========================================================
def get_user_tier(member, guild):
    if not member:
        return 'Без тира'
    for name, rid in (('Tier S', TIER_S_ROLE_ID), ('Tier 1', TIER_1_ROLE_ID),
                      ('Tier 2', TIER_2_ROLE_ID), ('Tier 3', TIER_3_ROLE_ID)):
        if rid:
            role = guild.get_role(rid)
            if role and role in member.roles:
                return name
    return 'Без тира'


def check_gathering_perms(user):
    if user.guild_permissions.administrator:
        return True
    for rid in GATHERING_MANAGE_ROLE_IDS:
        if rid and discord.utils.get(user.roles, id=rid):
            return True
    return False


def chunk_lines(lines, limit=1000):
    chunks, cur, size = [], [], 0
    for line in lines:
        if size + len(line) + 1 > limit:
            chunks.append(cur)
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    if cur:
        chunks.append(cur)
    return chunks


class GatheringSystem:
    def __init__(self):
        self.gatherings = {}
        self.load()

    def load(self):
        if os.path.exists(GATHERINGS_FILE):
            try:
                with open(GATHERINGS_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    self.gatherings = json.loads(content) if content else {}
            except Exception as e:
                print(f"Ошибка загрузки сборов: {e}")
                self.gatherings = {}

    def save(self):
        try:
            with open(GATHERINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.gatherings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения сборов: {e}")

    def new_id(self):
        if not self.gatherings:
            return "1"
        return str(max(int(k) for k in self.gatherings.keys()) + 1)

    def create(self, name, minutes, limit, creator_id, channel_id):
        gid = self.new_id()
        now = datetime.now()
        self.gatherings[gid] = {
            'id': gid,
            'name': name,
            'start_time': (now + timedelta(minutes=minutes)).isoformat(),
            'limit': limit,
            'creator_id': creator_id,
            'channel_id': channel_id,
            'message_id': None,
            'thread_id': None,
            'participants': [],
            'reserve': [],
            'closed': False,
            'created_at': now.isoformat(),
        }
        self.save()
        return gid

    def get(self, gid):
        return self.gatherings.get(str(gid))

    def join(self, gid, uid):
        g = self.get(gid)
        if not g:
            return 'not_found'
        if g['closed']:
            return 'closed'
        if uid in g['participants'] or uid in g['reserve']:
            return 'already'
        if len(g['participants']) < g['limit']:
            g['participants'].append(uid)
            self.save()
            return 'joined'
        g['reserve'].append(uid)
        self.save()
        return 'reserve'

    def leave(self, gid, uid):
        g = self.get(gid)
        if not g:
            return None
        if uid in g['participants']:
            g['participants'].remove(uid)
            promoted = None
            if g['reserve']:
                promoted = g['reserve'].pop(0)
                g['participants'].append(promoted)
            self.save()
            return ('left', promoted)
        if uid in g['reserve']:
            g['reserve'].remove(uid)
            self.save()
            return ('left_reserve', None)
        return 'not_in'

    def add_time(self, gid, minutes):
        g = self.get(gid)
        if not g:
            return False
        st = datetime.fromisoformat(g['start_time'])
        g['start_time'] = (st + timedelta(minutes=minutes)).isoformat()
        self.save()
        return True

    def close(self, gid):
        g = self.get(gid)
        if not g:
            return False
        g['closed'] = True
        self.save()
        return True

    def set_message(self, gid, mid):
        g = self.get(gid)
        if g:
            g['message_id'] = mid
            self.save()

    def set_thread(self, gid, tid):
        g = self.get(gid)
        if g:
            g['thread_id'] = tid
            self.save()


gathering_system = GatheringSystem()


def build_gathering_embed(gid, guild):
    g = gathering_system.get(gid)
    if not g:
        return None

    color = discord.Color.greyple() if g['closed'] else discord.Color.blue()
    embed = discord.Embed(title=f"⚔️ СБОР: {g['name']}", color=color, timestamp=datetime.now())

    if g['closed']:
        embed.add_field(name="📊 Статус", value="🔴 Закрыт", inline=True)
    else:
        st = datetime.fromisoformat(g['start_time'])
        embed.add_field(name="⏰ До начала", value=f"<t:{int(st.timestamp())}:R>", inline=True)

    embed.add_field(name="👥 Участники", value=f"**{len(g['participants'])}/{g['limit']}**", inline=True)
    embed.add_field(name="📋 Резерв", value=f"**{len(g['reserve'])}**", inline=True)

    if g['participants']:
        def sort_key(uid):
            m = guild.get_member(uid)
            return TIER_ORDER.get(get_user_tier(m, guild), 99)

        lines = []
        for uid in sorted(g['participants'], key=sort_key):
            m = guild.get_member(uid)
            if m:
                t = get_user_tier(m, guild)
                lines.append(f"{TIER_EMOJI[t]} {m.mention} — `{t}`")
            else:
                lines.append(f"⚪ <@{uid}> — `Неизвестно`")

        for i, chunk in enumerate(chunk_lines(lines)):
            name = "👥 Присоединились" if i == 0 else "👥 Присоединились (продолжение)"
            embed.add_field(name=name, value="\n".join(chunk), inline=False)
    else:
        embed.add_field(name="👥 Присоединились", value="*Пока никого*", inline=False)

    if g['reserve']:
        lines = []
        for uid in g['reserve']:
            m = guild.get_member(uid)
            if m:
                t = get_user_tier(m, guild)
                lines.append(f"{TIER_EMOJI[t]} {m.mention} — `{t}` *(резерв)*")
            else:
                lines.append(f"⚪ <@{uid}> *(резерв)*")
        for i, chunk in enumerate(chunk_lines(lines)):
            name = "📋 Резерв" if i == 0 else "📋 Резерв (продолжение)"
            embed.add_field(name=name, value="\n".join(chunk), inline=False)

    embed.set_footer(text=f"Сбор #{gid} | Лимит: {g['limit']} чел.")
    return embed


async def send_gathering_log(gid, guild, text):
    g = gathering_system.get(gid)
    if not g or not g.get('thread_id'):
        return
    try:
        thread = guild.get_thread(g['thread_id'])
        if thread:
            await thread.send(text)
    except Exception as e:
        print(f"Ошибка лога сбора: {e}")


async def refresh_gathering_message(gid):
    g = gathering_system.get(gid)
    if not g or not g.get('message_id'):
        return
    try:
        channel = bot.get_channel(g['channel_id'])
        if not channel:
            return
        msg = await channel.fetch_message(g['message_id'])
        embed = build_gathering_embed(gid, channel.guild)
        view = None if g['closed'] else GatheringView(gid)
        await msg.edit(embed=embed, view=view)
    except Exception as e:
        print(f"Ошибка обновления сбора {gid}: {e}")


class GatheringView(View):
    def __init__(self, gid):
        super().__init__(timeout=None)
        self.gid = str(gid)
        # делаем custom_id уникальными для каждого сбора
        buttons = [c for c in self.children if isinstance(c, discord.ui.Button)]
        if len(buttons) >= 3:
            buttons[0].custom_id = f"gathering_join_{self.gid}"
            buttons[1].custom_id = f"gathering_leave_{self.gid}"
            buttons[2].custom_id = f"gathering_manage_{self.gid}"

    @discord.ui.button(label="✅ Присоединиться", style=discord.ButtonStyle.green)
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = gathering_system.join(self.gid, interaction.user.id)

        if result == 'closed':
            await interaction.response.send_message("❌ Сбор закрыт!", ephemeral=True)
            return
        if result == 'already':
            await interaction.response.send_message("❌ Вы уже в списке!", ephemeral=True)
            return
        if result == 'joined':
            await interaction.response.send_message("✅ Вы присоединились к сбору!", ephemeral=True)
            tier = get_user_tier(interaction.user, interaction.guild)
            await send_gathering_log(self.gid, interaction.guild,
                f"➕ {interaction.user.mention} (`{tier}`) присоединился к сбору.")
        elif result == 'reserve':
            await interaction.response.send_message("⏳ Мест нет — вы в резерве.", ephemeral=True)
            tier = get_user_tier(interaction.user, interaction.guild)
            await send_gathering_log(self.gid, interaction.guild,
                f"⏳ {interaction.user.mention} (`{tier}`) добавлен в **резерв**.")

        await refresh_gathering_message(self.gid)

    @discord.ui.button(label="❌ Выйти", style=discord.ButtonStyle.red)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        result = gathering_system.leave(self.gid, interaction.user.id)
        if not result or result == 'not_in':
            await interaction.response.send_message("❌ Вас нет в списке!", ephemeral=True)
            return

        status, promoted = result if isinstance(result, tuple) else ('left', None)

        if status == 'left_reserve':
            await interaction.response.send_message("✅ Вы убраны из резерва.", ephemeral=True)
            await send_gathering_log(self.gid, interaction.guild,
                f"➖ {interaction.user.mention} покинул резерв.")
        else:
            msg = "✅ Вы вышли из сбора."
            log = f"➖ {interaction.user.mention} покинул сбор."
            if promoted:
                p = interaction.guild.get_member(promoted)
                if p:
                    msg += f"\n🎉 {p.mention} перенесён из резерва в участники."
                    log += f"\n🎉 {p.mention} перенесён из резерва."
            await interaction.response.send_message(msg, ephemeral=True)
            await send_gathering_log(self.gid, interaction.guild, log)

        await refresh_gathering_message(self.gid)

    @discord.ui.button(label="⚙️ Управление", style=discord.ButtonStyle.secondary)
    async def manage_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not check_gathering_perms(interaction.user):
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return
        g = gathering_system.get(self.gid)
        if not g or g['closed']:
            await interaction.response.send_message("❌ Сбор уже закрыт.", ephemeral=True)
            return
        await interaction.response.send_message(
            "⚙️ **Управление сбором:**",
            view=GatheringManageView(self.gid),
            ephemeral=True
        )


class GatheringManageView(View):
    def __init__(self, gid):
        super().__init__(timeout=300)
        self.gid = str(gid)

    def _ok(self, user):
        return check_gathering_perms(user)

    @discord.ui.button(label="➕ +5 мин", style=discord.ButtonStyle.primary)
    async def add5(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._ok(interaction.user):
            await interaction.response.send_message("❌", ephemeral=True); return
        gathering_system.add_time(self.gid, 5)
        await interaction.response.send_message("✅ +5 минут добавлено.", ephemeral=True)
        await send_gathering_log(self.gid, interaction.guild,
            f"⏰ {interaction.user.mention} добавил **+5 минут**.")
        await refresh_gathering_message(self.gid)

    @discord.ui.button(label="➕ +10 мин", style=discord.ButtonStyle.primary)
    async def add10(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._ok(interaction.user):
            await interaction.response.send_message("❌", ephemeral=True); return
        gathering_system.add_time(self.gid, 10)
        await interaction.response.send_message("✅ +10 минут добавлено.", ephemeral=True)
        await send_gathering_log(self.gid, interaction.guild,
            f"⏰ {interaction.user.mention} добавил **+10 минут**.")
        await refresh_gathering_message(self.gid)

    @discord.ui.button(label="➕ +15 мин", style=discord.ButtonStyle.primary)
    async def add15(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._ok(interaction.user):
            await interaction.response.send_message("❌", ephemeral=True); return
        gathering_system.add_time(self.gid, 15)
        await interaction.response.send_message("✅ +15 минут добавлено.", ephemeral=True)
        await send_gathering_log(self.gid, interaction.guild,
            f"⏰ {interaction.user.mention} добавил **+15 минут**.")
        await refresh_gathering_message(self.gid)

    @discord.ui.button(label="🔒 Закрыть сбор", style=discord.ButtonStyle.danger)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._ok(interaction.user):
            await interaction.response.send_message("❌", ephemeral=True); return
        gathering_system.close(self.gid)
        await interaction.response.send_message("🔒 Сбор закрыт.", ephemeral=True)
        await send_gathering_log(self.gid, interaction.guild,
            f"🔒 {interaction.user.mention} **закрыл сбор**.")
        await refresh_gathering_message(self.gid)

    @discord.ui.button(label="🎤 Проверка войса", style=discord.ButtonStyle.blurple)
    async def voice_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._ok(interaction.user):
            await interaction.response.send_message("❌", ephemeral=True); return

        voice_channels = list(interaction.guild.voice_channels)
        if not voice_channels:
            await interaction.response.send_message("❌ Нет голосовых каналов.", ephemeral=True); return

        options = [discord.SelectOption(label=vc.name[:100], value=str(vc.id))
                   for vc in voice_channels[:25]]
        select = discord.ui.Select(placeholder="Выберите голосовой канал", options=options)
        gid = self.gid

        async def callback(inter: discord.Interaction):
            g = gathering_system.get(gid)
            vc = inter.guild.get_channel(int(select.values[0]))
            if not vc:
                await inter.response.send_message("❌ Канал не найден.", ephemeral=True); return

            in_v, not_in_v = [], []
            for uid in g['participants']:
                m = inter.guild.get_member(uid)
                if m and m.voice and m.voice.channel and m.voice.channel.id == vc.id:
                    in_v.append(m)
                else:
                    not_in_v.append(uid)

            e = discord.Embed(
                title=f"🎤 Проверка войса: {vc.name}",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            e.add_field(
                name=f"✅ В канале ({len(in_v)})",
                value="\n".join(m.mention for m in in_v) if in_v else "*никого*",
                inline=False
            )
            if not_in_v:
                e.add_field(
                    name=f"❌ Отсутствуют ({len(not_in_v)})",
                    value="\n".join(f"<@{u}>" for u in not_in_v),
                    inline=False
                )
            e.set_footer(text=f"В канале: {len(in_v)}/{len(g['participants'])}")
            await inter.response.send_message(embed=e, ephemeral=True)

        select.callback = callback
        view = View(timeout=120)
        view.add_item(select)
        await interaction.response.send_message("Выберите канал для проверки:", view=view, ephemeral=True)


async def restore_gathering_views():
    count = 0
    for gid, g in gathering_system.gatherings.items():
        if g.get('closed'):
            continue
        if not g.get('message_id'):
            continue
        try:
            bot.add_view(GatheringView(gid))
            count += 1
        except Exception as e:
            print(f"Ошибка восстановления view сбора {gid}: {e}")
    print(f"✅ Восстановлено {count} views сборов")


# ==========================================================
# ===== СОБЫТИЯ И КОМАНДЫ ==================================
# ==========================================================
@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')

    bot.add_view(ApplicationView())
    bot.add_view(CabinetView())

    await setup_embed()
    await setup_cabinet_embed()
    await restore_application_views()
    await restore_gathering_views()

    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано {len(synced)} команд")
    except Exception as e:
        print(f"Ошибка синхронизации команд: {e}")

    print("✅ Все view восстановлены")


async def setup_embed():
    channel = bot.get_channel(EMBED_CHANNEL_ID)
    if not channel:
        print("❌ Канал для эмбиенда не найден!")
        return

    message_id = bot_config.get_embed_message_id()

    if message_id:
        try:
            message = await channel.fetch_message(message_id)
            embed = create_embed()
            view = ApplicationView()
            await message.edit(embed=embed, view=view)
            print("✅ Эмбиенд обновлен (существующее сообщение)")
            return
        except discord.NotFound:
            print("⚠️ Старое сообщение не найдено, создаю новое")
            bot_config.set_embed_message_id(None)
        except Exception as e:
            print(f"Ошибка при поиске сообщения: {e}")

    embed = create_embed()
    view = ApplicationView()
    message = await channel.send(embed=embed, view=view)

    bot_config.set_embed_message_id(message.id)
    print(f"✅ Эмбиенд создан (ID: {message.id})")


def create_embed():
    embed = discord.Embed(
        title=EMBED_TITLE,
        description=EMBED_DESCRIPTION,
        color=discord.Color.light_grey(),
        timestamp=datetime.now()
    )

    embed.set_image(url=EMBED_IMAGE_URL)
    embed.set_footer(text=EMBED_FOOTER)

    return embed


def create_cabinet_embed():
    embed = discord.Embed(
        title="**ЛИЧНЫЕ КАБИНЕТЫ**",
        description=(
            "**Нажми на кнопку ниже, чтобы создать свой личный кабинет.**\n\n"
            "📌 **Что это?**\n"
            "Приватный текстовый канал, который виден **только вам** и администрации.\n\n"
            "📌 **Что нужно указать?**\n"
            "• Ваш игровой **ник**\n"
            "• Ваш **статик**\n\n"
            "Название канала будет в формате: `ник | статик`"
        ),
        color=discord.Color.light_grey(),
        timestamp=datetime.now()
    )
    embed.set_footer(text="Нажмите на кнопку ниже 👇")
    return embed


async def setup_cabinet_embed():
    channel_id = CABINET_CHANNEL_ID if CABINET_CHANNEL_ID else EMBED_CHANNEL_ID
    channel = bot.get_channel(channel_id)
    if not channel:
        print("❌ Канал для эмбиенда ЛК не найден!")
        return

    old_id = bot_config.get_cabinet_embed_message_id()
    if old_id:
        try:
            old = await channel.fetch_message(old_id)
            await old.edit(embed=create_cabinet_embed(), view=CabinetView())
            print("✅ Эмбиенд ЛК обновлён")
            return
        except Exception:
            pass

    message = await channel.send(embed=create_cabinet_embed(), view=CabinetView())
    bot_config.set_cabinet_embed_message_id(message.id)
    print(f"✅ Эмбиенд ЛК создан (ID: {message.id})")


@bot.tree.command(name="devprofile", description="Показать статистику модератора/администратора")
@app_commands.describe(
    user="Пользователь для просмотра статистики (по умолчанию - вы)",
    period="Период: day (день), week (неделя), month (месяц), all (всё время)"
)
@app_commands.choices(period=[
    app_commands.Choice(name="День", value="day"),
    app_commands.Choice(name="Неделя", value="week"),
    app_commands.Choice(name="Месяц", value="month"),
    app_commands.Choice(name="Всё время", value="all")
])
async def devprofile(interaction: discord.Interaction, user: discord.Member = None, period: str = "all"):
    if not user:
        user = interaction.user

    if not interaction.user.guild_permissions.administrator:
        admin_role = discord.utils.get(interaction.user.roles, id=ADMIN_ROLE_ID)
        mod_role = discord.utils.get(interaction.user.roles, id=MODERATOR_ROLE_ID)
        if not admin_role and not mod_role:
            await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
            return

    start_date = None
    end_date = datetime.now()

    if period == "day":
        start_date = end_date - timedelta(days=1)
    elif period == "week":
        start_date = end_date - timedelta(weeks=1)
    elif period == "month":
        start_date = end_date - timedelta(days=30)

    stats = stats_system.get_stats(user.id, start_date, end_date)

    embed = discord.Embed(
        title=f"📊 Статистика: {user.name}",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )

    period_names = {
        "day": "За день",
        "week": "За неделю",
        "month": "За месяц",
        "all": "За всё время"
    }

    embed.add_field(name="Период", value=period_names.get(period, "Всё время"), inline=False)
    embed.add_field(name="Принято новых пользователей", value=stats['new_users'], inline=True)
    embed.add_field(name="Всего принято", value=stats['total'], inline=True)

    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)

    view = AcceptedUsersView(user.id, start_date, end_date)

    await interaction.response.send_message(embed=embed, view=view)


class AcceptedUsersView(View):
    def __init__(self, reviewer_id, start_date=None, end_date=None):
        super().__init__(timeout=300)
        self.reviewer_id = reviewer_id
        self.start_date = start_date
        self.end_date = end_date
        self.page = 0
        self.per_page = 10

    @discord.ui.button(label="👥 Показать принятых", style=discord.ButtonStyle.primary, custom_id="show_accepted_btn")
    async def show_accepted_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        stats = stats_system.get_stats(self.reviewer_id, self.start_date, self.end_date)
        users = stats['users']

        if not users:
            await interaction.response.send_message("❌ Нет принятых пользователей за этот период!", ephemeral=True)
            return

        embed = discord.Embed(
            title="👥 Принятые пользователи",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )

        start_idx = self.page * self.per_page
        end_idx = min(start_idx + self.per_page, len(users))

        for i in range(start_idx, end_idx):
            entry = users[i]
            user = await bot.fetch_user(entry['user_id'])
            user_name = user.name if user else f"ID: {entry['user_id']}"
            is_new = "🆕" if entry.get('is_new', False) else "🔄"
            accepted_at = entry['accepted_at'][:19].replace('T', ' ')

            embed.add_field(
                name=f"{is_new} {user_name}",
                value=f"Тип: {entry['app_type']}\nПринят: {accepted_at}",
                inline=False
            )

        total_pages = (len(users) + self.per_page - 1) // self.per_page
        embed.set_footer(text=f"Страница {self.page + 1} из {total_pages} | Всего: {len(users)}")

        nav_view = AcceptedUsersNavigationView(self.reviewer_id, self.start_date, self.end_date, self.page)

        await interaction.response.send_message(embed=embed, view=nav_view, ephemeral=True)


class AcceptedUsersNavigationView(View):
    def __init__(self, reviewer_id, start_date=None, end_date=None, page=0):
        super().__init__(timeout=300)
        self.reviewer_id = reviewer_id
        self.start_date = start_date
        self.end_date = end_date
        self.page = page
        self.per_page = 10

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, custom_id="prev_page_btn")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary, custom_id="next_page_btn")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        stats = stats_system.get_stats(self.reviewer_id, self.start_date, self.end_date)
        total_pages = (len(stats['users']) + self.per_page - 1) // self.per_page

        if self.page < total_pages - 1:
            self.page += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    async def update_message(self, interaction):
        stats = stats_system.get_stats(self.reviewer_id, self.start_date, self.end_date)
        users = stats['users']

        embed = discord.Embed(
            title="👥 Принятые пользователи",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )

        start_idx = self.page * self.per_page
        end_idx = min(start_idx + self.per_page, len(users))

        for i in range(start_idx, end_idx):
            entry = users[i]
            user = await bot.fetch_user(entry['user_id'])
            user_name = user.name if user else f"ID: {entry['user_id']}"
            is_new = "🆕" if entry.get('is_new', False) else "🔄"
            accepted_at = entry['accepted_at'][:19].replace('T', ' ')

            embed.add_field(
                name=f"{is_new} {user_name}",
                value=f"Тип: {entry['app_type']}\nПринят: {accepted_at}",
                inline=False
            )

        total_pages = (len(users) + self.per_page - 1) // self.per_page
        embed.set_footer(text=f"Страница {self.page + 1} из {total_pages} | Всего: {len(users)}")

        self.prev_button.disabled = (self.page == 0)
        self.next_button.disabled = (self.page >= total_pages - 1)

        await interaction.response.edit_message(embed=embed, view=self)


@bot.command(name='setup')
@commands.has_permissions(administrator=True)
async def setup_command(ctx):
    await ctx.message.delete()

    message_id = bot_config.get_embed_message_id()
    if message_id:
        channel = bot.get_channel(EMBED_CHANNEL_ID)
        if channel:
            try:
                old_message = await channel.fetch_message(message_id)
                await old_message.delete()
            except:
                pass

    bot_config.set_embed_message_id(None)
    await setup_embed()
    await ctx.send("✅ Эмбиенд успешно обновлен!", delete_after=5)


@bot.command(name='setupcabinet')
@commands.has_permissions(administrator=True)
async def setupcabinet_command(ctx):
    await ctx.message.delete()
    await setup_cabinet_embed()
    await ctx.send("✅ Эмбиенд личных кабинетов обновлён!", delete_after=5)


# ===== СЛЭШ-КОМАНДА СОЗДАНИЯ СБОРА =====
@bot.tree.command(name="капт", description="Создать сбор")
@app_commands.describe(
    название="Название сбора",
    через="Через сколько минут начнётся",
    огран="Ограничение по количеству участников"
)
async def kapt_cmd(interaction: discord.Interaction,
                   название: str, через: int, огран: int):
    if not check_gathering_perms(interaction.user):
        await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        return
    if через < 0:
        await interaction.response.send_message("❌ Время не может быть отрицательным.", ephemeral=True)
        return
    if огран < 1:
        await interaction.response.send_message("❌ Лимит должен быть ≥ 1.", ephemeral=True)
        return
    if not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message("❌ Команда доступна только в текстовых каналах.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    gid = gathering_system.create(название, через, огран, interaction.user.id, interaction.channel.id)

    embed = build_gathering_embed(gid, interaction.guild)
    view = GatheringView(gid)
    message = await interaction.channel.send(embed=embed, view=view)

    gathering_system.set_message(gid, message.id)
    g = gathering_system.get(gid)

    # Ветка для логов
    try:
        thread = await message.create_thread(
            name=f"📋 Логи — {название[:50]}",
            auto_archive_duration=1440
        )
        gathering_system.set_thread(gid, thread.id)
        st = datetime.fromisoformat(g['start_time'])
        await thread.send(
            f"📋 **Логи сбора #{gid} — {название}**\n"
            f"👤 Создатель: {interaction.user.mention}\n"
            f"👥 Лимит: **{огран}**\n"
            f"⏰ Старт: <t:{int(st.timestamp())}:R>"
        )
    except Exception as e:
        print(f"Ошибка создания треда сбора: {e}")

    await interaction.followup.send(
        f"✅ Сбор **#{gid}** создан: {message.jump_url}",
        ephemeral=True
    )


# Запуск бота
if __name__ == "__main__":
    bot.run('TOKEN')
