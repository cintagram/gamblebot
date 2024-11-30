#######################################################
# 모듈들 임포트
#######################################################
from flask import Flask, render_template, request, jsonify, send_file, redirect
import flask
from cryptography.hazmat.primitives import padding
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import pad, unpad
from datetime import timedelta
import secrets
import asyncio
import csv
import random
from datetime import datetime
import json
import os
import sys
from urllib.parse import urljoin, quote
from functools import partial
from discord.utils import get
import threading
import bcrypt
import sqlite3
import requests
import traceback
import time
from typing import Any, Optional, Literal, Union, Tuple
import re
import http
import pytz
import discord
from discord.ext import commands
from enum import Enum
import base64
from discord.ext import tasks, commands
from discord.ui import Button, TextInput
from discord import app_commands, Interaction, ui, ButtonStyle, SelectOption, SyncWebhook, Attachment, TextChannel
from modules import *
import sqlite3
import asyncio
import random
import math

#######################################################
# 전역변수 정의
#######################################################

class Bot(commands.AutoShardedBot):
    async def on_ready(self):
        await self.wait_until_ready()
        await self.tree.sync()
        setupsystem.bootup()
        print(f"Logged in as {self.user} !")

#intents = discord.Intents.default()
#intents.members = True
intents = discord.Intents.all()
client = Bot(intents=intents, command_prefix="!") #, shard_count=100)
app = Flask("A1 PS Connect Web")
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

BANKER_EMOJI = "<:banker:1292103841537327167>"
PLAYER_EMOJI = "<:player:1292103829785022567>"
TIE_EMOJI = "<:tie:1292103816367439968>"
MONEY_EMOJI = "💰"
CARDS_EMOJI = "🃏"

#######################################################
# 웹 루트 (필수 X)
#######################################################
@app.route("/", methods=["GET"])
async def webroot():
    return render_template('index.html')

#######################################################
# 메인 코드
#######################################################
@client.tree.command(name="가입", description="DB에 사용자를 등록합니다.")
async def register(interaction: Interaction):
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE userid = ?", (interaction.user.id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO user (userid, money, IsBlack) VALUES (?, ?, ?)", (interaction.user.id, 0, 0))
        conn.commit()
        embed = discord.Embed(title="가입 완료", description="가입이 완료되었습니다.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="가입 실패", description="이미 가입된 사용자입니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

@client.tree.command(name="잔액", description="사용자의 잔액을 확인합니다.")
async def balance(interaction: Interaction, 유저: discord.Member = None):
    if 유저 is None:
        유저 = interaction.user
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE userid = ?", (유저.id,))
    user = cursor.fetchone()
    if user:
        embed = discord.Embed(title=f"{유저.name}님의 잔액", description=f"**{user[1]}원**", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="잔액 조회 실패", description="사용자가 가입되어 있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

@client.tree.command(name="잔액수정", description="[BotAdmin] 사용자의 잔고를 수정합니다.")
async def modify_balance(interaction: Interaction, 유저: discord.Member, 금액: str):
    if not 금액.isdigit():
        embed = discord.Embed(title="잔액 수정 실패", description="금액은 숫자로만 입력해야 합니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    금액 = int(금액)
    if interaction.user.id not in config.BotSuperAdminID and 1==2:
        embed = discord.Embed(title="권한 없음", description="이 명령어를 사용할 권한이 없습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE userid = ?", (유저.id,))
    user = cursor.fetchone()
    if user:
        cursor.execute("UPDATE user SET money = ? WHERE userid = ?", (user[1] + 금액, 유저.id))
        conn.commit()
        embed = discord.Embed(title="잔액 수정", description=f"{유저.name}님의 잔액이 {금액}만큼 변경되었습니다.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="잔고 수정 실패", description="사용자가 가입되어 있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)

@client.tree.command(name="돈받기", description="돈을 받습니다.")
async def receive_money(interaction: Interaction):
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE userid = ?", (interaction.user.id,))
    user = cursor.fetchone()
    if user:
        # 마지막으로 돈을 받은 시간 확인
        cursor.execute("SELECT last_received FROM user WHERE userid = ?", (interaction.user.id,))
        last_received = cursor.fetchone()[0]
        current_time = int(time.time())
        
        if last_received is None or (current_time - last_received) >= 3600:  # 1시간 = 3600초
            cursor.execute("UPDATE user SET money = ?, last_received = ? WHERE userid = ?", (user[1] + 100000, current_time, interaction.user.id))
            conn.commit()
            embed = discord.Embed(title="돈 받기 성공", description="100,000원을 받았습니다.", color=discord.Color.green())
            await interaction.response.send_message(embed=embed)
        else:
            remaining_time = 3600 - (current_time - last_received)
            minutes, seconds = divmod(remaining_time, 60)
            embed = discord.Embed(title="돈 받기 실패", description=f"다음 돈 받기까지 {minutes}분 {seconds}초 남았습니다.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="돈 받기 실패", description="사용자가 가입되어 있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
    conn.close()

@client.tree.command(name="도박", description="돈을 걸고 도박합니다.")
async def gamble(interaction: Interaction, 금액: int):
    if 금액 < 1:
        await interaction.response.send_message("베팅 금액은 1원 이상이어야 합니다.", ephemeral=True)
        return
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE userid = ?", (interaction.user.id,))
    user = cursor.fetchone()
    
    if not user:
        embed = discord.Embed(title="도박 실패", description="사용자가 가입되어 있지 않습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        conn.close()
        return
    
    if user[1] < 금액:
        embed = discord.Embed(title="도박 실패", description="잔액이 부족합니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        conn.close()
        return
    
    await interaction.response.defer()
    
    # 금액 포맷팅 함수 추가
    def format_currency(amount):
        return f"{amount:,}₩"
    
    # 확률 생성 (정규 분포 사용)
    win_probability = min(max(random.gauss(50, 10), 10), 90) / 100
    embed = discord.Embed(title="도박 진행 중", description=f"**승리확률 : {win_probability:.2%}**\n \n **결과 : 대기중...**", color=discord.Color.gold())
    message = await interaction.followup.send(embed=embed)
    
    await asyncio.sleep(3)  # 3초 대기
    
    if random.random() < win_probability:  # 생성된 확률로 승리 여부 결정
        new_balance = user[1] + 금액
        result = "성공"
        description = f"**승리확률 : {win_probability:.2%}**\n \n **결과 :  +{format_currency(금액)}**"
        color = discord.Color.green()
    else:
        new_balance = user[1] - 금액
        result = "실패"
        description = f"**승리확률 : {win_probability:.2%}**\n \n **결과 :   -{format_currency(금액)}**"
        color = discord.Color.red()
    
    cursor.execute("UPDATE user SET money = ? WHERE userid = ?", (new_balance, interaction.user.id))
    conn.commit()
    
    embed = discord.Embed(title=f"도박에 {result}했습니다.", description=description, color=color)
    embed.set_footer(text=f"잔액 : {format_currency(new_balance)}")
    await message.edit(embed=embed)
    
    conn.close()


suits = ['♠', '♥', '♦', '♣']
ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
deck = [f"{rank}{suit}" for suit in suits for rank in ranks]

def create_deck():
    return deck.copy()

def deal_card(deck):
    return deck.pop(random.randint(0, len(deck) - 1))

def calculate_hand(hand):
    value = 0
    aces = 0
    for card in hand:
        rank = card[:-1]
        if rank in ['J', 'Q', 'K']:
            value += 10
        elif rank == 'A':
            aces += 1
        else:
            value += int(rank)
    
    for _ in range(aces):
        if value + 11 <= 21:
            value += 11
        else:
            value += 1
    
    return value

class BlackjackView(discord.ui.View):
    def __init__(self, player, player_hand, dealer_hand, deck, bet):
        super().__init__(timeout=180)  # 시간 제한을 3분으로 늘립니다
        self.player = player
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.bet = bet
        self.game_over = False
        self.insurance_bet = 0
        self.double_down = False
        self.message = None  # 메시지 객체를 저장할 변수 추가
        self.update_buttons()

    def update_buttons(self):
        for item in self.children:
            item.disabled = self.game_over
        if len(self.player_hand) > 2:
            self.double_down_button.disabled = True
        if self.dealer_hand[0][:-1] != 'A' or self.insurance_bet > 0:
            self.insurance_button.disabled = True

    @discord.ui.button(label="히트", style=ButtonStyle.primary)
    async def hit(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return

        self.player_hand.append(deal_card(self.deck))
        await self.update_game(interaction)

    @discord.ui.button(label="스탠드", style=ButtonStyle.primary)
    async def stand(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return

        self.game_over = True
        await self.update_game(interaction)

    @discord.ui.button(label="더블", style=ButtonStyle.primary)
    async def double_down_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return

        if len(self.player_hand) == 2:
            self.double_down = True
            self.bet *= 2
            self.player_hand.append(deal_card(self.deck))
            self.game_over = True
            await self.update_game(interaction)
        else:
            await interaction.response.send_message("더블 다운은 첫 두 장의 카드에서만 가능합니다.", ephemeral=True)

    @discord.ui.button(label="인슈어런스", style=ButtonStyle.secondary)
    async def insurance_button(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return

        if self.dealer_hand[0][:-1] == 'A' and self.insurance_bet == 0:
            self.insurance_bet = self.bet // 2
            await interaction.response.send_message(f"인슈어런스 베팅: {self.insurance_bet:,}원", ephemeral=True)
            await self.update_game(interaction)
        else:
            await interaction.response.send_message("인슈어런스를 할 수 없습니다.", ephemeral=True)

    async def update_game(self, interaction: Interaction):
        player_value = calculate_hand(self.player_hand)
        dealer_value = calculate_hand(self.dealer_hand)

        if player_value > 21:
            self.game_over = True
            result = "버스트! 패배"
        elif self.game_over:
            result = await self.dealer_turn(interaction)
        else:
            result = "진행 중"

        embed = self.create_game_embed(player_value, dealer_value, result)
        self.update_buttons()

        if self.game_over:
            await self.end_game(interaction, result, player_value, dealer_value)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    async def dealer_turn(self, interaction: Interaction):
        embed = self.create_game_embed(calculate_hand(self.player_hand), calculate_hand(self.dealer_hand), "딜러 턴")
        await self.message.edit(embed=embed)  # interaction 대신 self.message 사용

        while calculate_hand(self.dealer_hand) < 17:
            await asyncio.sleep(1)  # 1초 딜레이
            self.dealer_hand.append(deal_card(self.deck))
            embed = self.create_game_embed(calculate_hand(self.player_hand), calculate_hand(self.dealer_hand), "딜러 턴")
            await self.message.edit(embed=embed)  # interaction 대신 self.message 사용

        dealer_value = calculate_hand(self.dealer_hand)
        player_value = calculate_hand(self.player_hand)

        if dealer_value > 21:
            return "딜러 버스트! 승리"
        elif player_value > dealer_value:
            return "승리"
        elif player_value < dealer_value:
            return "패배"
        else:
            return "무승부"

    def create_game_embed(self, player_value, dealer_value, result):
        embed = discord.Embed(title="🃏 블랙잭", color=0x00ff00)
        
        if self.game_over:
            dealer_cards = f"```{' '.join(self.dealer_hand)}```\n**합계: {dealer_value}**"
        else:
            dealer_cards = f"```{self.dealer_hand[0]} ?```\n**합계: ?**"
        embed.add_field(name="🎩 딜러의 패", value=dealer_cards, inline=False)
        
        embed.add_field(name="👤 당신의 패", value=f"```{' '.join(self.player_hand)}```\n**합계: {player_value}**", inline=False)
        
        embed.add_field(name="💰 베팅 금액", value=f"**{self.bet:,}원**", inline=True)
        if self.insurance_bet > 0:
            embed.add_field(name="🛡️ 인슈어런스", value=f"**{self.insurance_bet:,}원**", inline=True)
        embed.add_field(name="🏆 결과", value=f"**{result}**", inline=False)
        return embed

    async def end_game(self, interaction: Interaction, result, player_value, dealer_value):
        conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
        cursor = conn.cursor()

        cursor.execute("SELECT money FROM user WHERE userid = ?", (self.player.id,))
        current_balance = cursor.fetchone()[0]

        winnings = 0
        if result == "승리" or result == "딜러 버스트! 승리":
            winnings = self.bet
        elif result == "무승부":
            winnings = 0
        else:
            winnings = -self.bet

        if self.insurance_bet > 0:
            if dealer_value == 21 and len(self.dealer_hand) == 2:
                winnings += self.insurance_bet * 2
            else:
                winnings -= self.insurance_bet

        new_balance = current_balance + winnings
        cursor.execute("UPDATE user SET money = ? WHERE userid = ?", (new_balance, self.player.id))
        conn.commit()

        embed = discord.Embed(title="🃏 블랙잭 최종 결과", color=0x00ff00)
        embed.add_field(name="🏆 최종 결과", value=f"**{result}**", inline=False)
        embed.add_field(name="🎩 딜러의 패", value=f"```{' '.join(self.dealer_hand)}```\n**합계: {dealer_value}**", inline=False)
        embed.add_field(name="👤 당신의 패", value=f"```{' '.join(self.player_hand)}```\n**합계: {player_value}**", inline=False)
        embed.add_field(name="💰 베팅 금액", value=f"**{self.bet:,}원**", inline=True)
        if self.insurance_bet > 0:
            embed.add_field(name="🛡️ 인슈어런스", value=f"**{self.insurance_bet:,}원**", inline=True)
        embed.add_field(name="💸 획득/손실 금액", value=f"**{winnings:,}원**", inline=True)
        embed.add_field(name="🏦 새로운 잔액", value=f"**{new_balance:,}원**", inline=True)

        await self.message.edit(embed=embed, view=None)  # interaction 대신 self.message 사용
        conn.close()

@client.tree.command(name="블랙잭", description="블랙잭 게임을 시작합니다.")
async def blackjack(interaction: Interaction, 베팅금액: int):
    if 베팅금액 < 1:
        await interaction.response.send_message("베팅 금액은 1원 이상이어야 합니다.", ephemeral=True)
        return
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()

    cursor.execute("SELECT money FROM user WHERE userid = ?", (interaction.user.id,))
    current_balance = cursor.fetchone()

    if current_balance is None:
        await interaction.response.send_message("먼저 가입을 해주세요.", ephemeral=True)
        conn.close()
        return

    current_balance = current_balance[0]

    if current_balance < 베팅금액:
        await interaction.response.send_message("잔액이 부족합니다.", ephemeral=True)
        conn.close()
        return

    deck = create_deck()
    player_hand = [deal_card(deck), deal_card(deck)]
    dealer_hand = [deal_card(deck), deal_card(deck)]

    view = BlackjackView(interaction.user, player_hand, dealer_hand, deck, 베팅금액)
    embed = discord.Embed(title="🃏 블랙잭", color=0x00ff00)
    embed.add_field(name="🎩 딜러의 패", value=f"```{dealer_hand[0]} ?```\n**합계: ?**", inline=False)
    embed.add_field(name="👤 당신의 패", value=f"```{' '.join(player_hand)}```\n**합계: {calculate_hand(player_hand)}**", inline=False)
    embed.add_field(name="💰 베팅 금액", value=f"**{베팅금액:,}원**", inline=False)

    message = await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()  # 메시지 객체 저장
    conn.close()


@client.tree.command(name="확률정보", description="확률정보를 보여줍니다.")
async def probability_info(interaction: Interaction):
    embed = discord.Embed(title="확률정보", description="도박들의 확률정보 입니다.", color=discord.Color.blue())
    embed.add_field(name="확률도박", value="10~90% 사이의 확률로 2배가 됩니다\n 평균이 50, 표준편차가 10인 정규분포로 확률을 생성합니다.", inline=False)
    embed.add_field(name="돈받기", value="1시간에 한번씩 확정적으로 10만원을 받을 수 있습니다.", inline=False)
    embed.add_field(name="블랙잭", value="승률이 약 45%로 딜러보다 약간 낮은 승률을 보입니다.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


class Card:
    def __init__(self, value):
        self.value = value
        self.name = self.get_name()
        self.emoji = self.get_emoji()

    def get_name(self):
        if self.value == 1:
            return 'A'
        elif self.value == 11:
            return 'J'
        elif self.value == 12:
            return 'Q'
        elif self.value == 13:
            return 'K'
        else:
            return str(self.value)

    def get_emoji(self):
        suits = ['♠️', '♥️', '♦️', '♣️']
        return f"{random.choice(suits)}{self.name}"

class HiLoGame:
    def __init__(self, bet, user_id, extreme_mode=False):
        self.deck = [Card(i) for i in range(1, 14)] * 4  # 52장의 카드
        random.shuffle(self.deck)
        self.current_card = self.draw_card()
        self.bet = bet
        self.user_id = user_id
        self.total_multiplier = 1
        self.rounds = 0
        self.card_history = [self.current_card]
        self.extreme_mode = extreme_mode
        self.min_rounds_for_cashout = 7 if extreme_mode else 0

    def can_cashout(self):
        return self.rounds >= self.min_rounds_for_cashout

    def draw_card(self):
        return self.deck.pop()

    def get_multiplier(self, choice):
        multipliers = {
            1: {'higher': 1.07, 'lower': None},
            2: {'higher': 1.07, 'lower': 6.44},
            3: {'higher': 1.17, 'lower': 4.29},
            4: {'higher': 1.29, 'lower': 3.22},
            5: {'higher': 1.43, 'lower': 2.57},
            6: {'higher': 1.61, 'lower': 2.15},
            7: {'higher': 1.84, 'lower': 1.84},
            8: {'higher': 2.15, 'lower': 1.61},
            9: {'higher': 2.57, 'lower': 1.43},
            10: {'higher': 3.22, 'lower': 1.29},
            11: {'higher': 4.29, 'lower': 1.17},
            12: {'higher': 6.44, 'lower': 1.07},
            13: {'higher': None, 'lower': 1.07}
        }
        base_multiplier = multipliers[self.current_card.value][choice]
        if base_multiplier is None:
            return None
        return base_multiplier * 1.5 if self.extreme_mode else base_multiplier

    def get_probabilities(self):
        card_value = self.current_card.value
        total_cards = 48  # 현재 카드를 제외한 남은 카드 수
        higher_prob = max((13 - card_value) * 4, 0) / total_cards * 100
        lower_prob = max((card_value - 1) * 4, 0) / total_cards * 100
        return higher_prob, lower_prob

    def play_round(self, choice):
        next_card = self.draw_card()
        self.card_history.append(next_card)
        multiplier = self.get_multiplier(choice)

        if multiplier is None:
            return False, "잘못된 선택입니다."

        result = ''
        if (choice == 'higher' and next_card.value > self.current_card.value) or \
           (choice == 'lower' and next_card.value < self.current_card.value) or \
           (next_card.value == self.current_card.value):
            result = '승리'
            self.total_multiplier *= multiplier
            self.rounds += 1
            self.current_card = next_card
            return True, f"{result}! 총 배율: {self.total_multiplier:.2f}x"
        else:
            result = '패배'
            return False, f"{result}. 게임 종료. 총 라운드: {self.rounds}, 최종 배율: {self.total_multiplier:.2f}x"
        
    def skip(self):
        self.current_card = self.draw_card()
        self.card_history.append(self.current_card)

    def cashout(self):
        winnings = int(self.bet * self.total_multiplier)
        self.update_user_balance(winnings)
        return winnings

    def update_user_balance(self, amount):
        conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
        cursor = conn.cursor()
        cursor.execute("UPDATE user SET money = money + ? WHERE userid = ?", (amount, self.user_id))
        conn.commit()
        conn.close()

class HiLoView(discord.ui.View):
    def __init__(self, game: HiLoGame):
        super().__init__()
        self.game = game
        self.update_buttons()

    def update_buttons(self):
        current_value = self.game.current_card.value
        
        if current_value == 1:  # Ace
            self.higher.label = "Higher"
            self.higher.disabled = False
            self.lower.label = "Same"
            self.lower.disabled = False
        elif current_value == 13:  # King
            self.higher.label = "Same"
            self.higher.disabled = False
            self.lower.label = "Lower"
            self.lower.disabled = False
        else:
            self.higher.label = "Higher"
            self.higher.disabled = False
            self.lower.label = "Lower"
            self.lower.disabled = False

        self.cashout.disabled = not self.game.can_cashout()
        self.skip.disabled = self.game.extreme_mode 

    @discord.ui.button(label="Higher", style=ButtonStyle.primary, emoji="⬆️")
    async def higher(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return
        if self.game.current_card.value == 13:  # King
            success, message = self.game.play_round('same')
        else:
            success, message = self.game.play_round('higher')
        await self.update_game(interaction, message, success)

    @discord.ui.button(label="Lower", style=ButtonStyle.primary, emoji="⬇️")
    async def lower(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return
        if self.game.current_card.value == 1:  # Ace
            success, message = self.game.play_round('same')
        else:
            success, message = self.game.play_round('lower')
        await self.update_game(interaction, message, success)

    @discord.ui.button(label="Skip", style=ButtonStyle.secondary, emoji="⏭️")
    async def skip(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return
        
        if self.game.extreme_mode:
            await interaction.response.send_message("Extreme 모드에서는 스킵을 사용할 수 없습니다.", ephemeral=True)
            return

        self.game.skip()
        await self.update_game(interaction, "스킵! 새로운 카드가 나왔습니다.", True)

    @discord.ui.button(label="Cashout", style=ButtonStyle.success, emoji="💰")
    async def cashout(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return
        
        if not self.game.can_cashout():
            await interaction.response.send_message(f"Extreme 모드에서는 최소 {self.game.min_rounds_for_cashout}라운드를 진행해야 캐시아웃할 수 있습니다.", ephemeral=True)
            return

        winnings = self.game.cashout()
        embed = self.create_embed(f"캐시아웃! 최종 획득 금액: {winnings:,.0f}원", discord.Color.gold())
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    async def update_game(self, interaction: Interaction, message: str, continue_game: bool):
        color = discord.Color.green() if "승리" in message else discord.Color.red() if "패배" in message else discord.Color.blue()
        embed = self.create_embed(message, color)
        self.update_buttons()
        if continue_game:
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=None)
            self.stop()

    def create_embed(self, message: str, color: discord.Color):
        embed = discord.Embed(title="🎴 하이로우", color=color)
        embed.add_field(name="카드 기록", value=" ".join([card.emoji for card in self.game.card_history]), inline=False)
        embed.add_field(name="현재 카드", value=f"**{self.game.current_card.emoji}**", inline=True)
        embed.add_field(name="베팅 금액", value=f"**{self.game.bet:,}원**", inline=True)
        embed.add_field(name="현재 배율", value=f"**{self.game.total_multiplier:.2f}x**", inline=True)
        embed.add_field(name="모드", value=f"{'Extreme' if self.game.extreme_mode else 'Normal'} (라운드: {self.game.rounds}{'/' + str(self.game.min_rounds_for_cashout) if self.game.extreme_mode else ''})", inline=True)
        
        higher_mult = self.game.get_multiplier('higher')
        lower_mult = self.game.get_multiplier('lower')
        higher_prob, lower_prob = self.game.get_probabilities()
        
        if self.game.current_card.value == 1:
            mult_info = f"Higher: {higher_mult:.2f}x (확률: {higher_prob:.1f}%)"
        elif self.game.current_card.value == 13:
            mult_info = f"Lower: {lower_mult:.2f}x (확률: {lower_prob:.1f}%)"
        else:
            mult_info = (f"Higher: {higher_mult:.2f}x (확률: {higher_prob:.1f}%)\n"
                         f"Lower: {lower_mult:.2f}x (확률: {lower_prob:.1f}%)")
        
        embed.add_field(name="다음 선택 배율 및 확률", value=mult_info, inline=False)
        
        embed.add_field(name="메시지", value=message, inline=False)
        return embed

    
    async def on_timeout(self):
        winnings = self.game.cashout()
        embed = self.create_embed(f"시간 초과! 자동 캐시아웃되었습니다. 최종 획득 금액: {winnings:,.0f}원", discord.Color.orange())
        await self.message.edit(embed=embed, view=None)

    

@client.tree.command(name="하이로우", description="하이로우 게임을 시작합니다.")
async def hilo(interaction: Interaction, 베팅금액: int, extreme: bool = False):
    response = requests.get('https://www.random.org/integers/?num=1&min=1&max=1000000000&col=1&base=10&format=plain&rnd=new')
    random_number = int(response.text)
    random.seed(random_number)
    if 베팅금액 < 1:
        await interaction.response.send_message("베팅 금액은 1원 이상이어야 합니다.", ephemeral=True)
        return
    
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()

    cursor.execute("SELECT money FROM user WHERE userid = ?", (interaction.user.id,))
    current_balance = cursor.fetchone()

    if current_balance is None:
        await interaction.response.send_message("먼저 가입을 해주세요.", ephemeral=True)
        conn.close()
        return

    current_balance = current_balance[0]

    if current_balance < 베팅금액:
        await interaction.response.send_message("잔액이 부족합니다.", ephemeral=True)
        conn.close()
        return

    # 베팅 금액 차감
    cursor.execute("UPDATE user SET money = money - ? WHERE userid = ?", (베팅금액, interaction.user.id))
    conn.commit()
    conn.close()

    game = HiLoGame(베팅금액, interaction.user.id, extreme)
    view = HiLoView(game)

    embed = view.create_embed("게임을 시작합니다. Higher 또는 Lower를 선택하세요.", discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()


class MinesGame:
    def __init__(self, bet, mines_count, user_id):
        self.board = [0] * 24
        self.bet = bet
        self.mines_count = mines_count
        self.user_id = user_id
        self.revealed = [False] * 24
        self.multiplier = 1.0
        self.game_over = False

        # 지뢰 배치
        mine_positions = random.sample(range(24), mines_count)
        for pos in mine_positions:
            self.board[pos] = 1

    def reveal(self, position):
        if self.revealed[position]:
            return False, "이미 선택한 위치입니다."
        
        self.revealed[position] = True
        if self.board[position] == 1:
            self.game_over = True
            return False, "지뢰를 밟았습니다! 게임 오버."
        
        self.update_multiplier()
        return True, f"안전! 현재 배율: {self.multiplier:.2f}x"

    def update_multiplier(self):
        revealed_count = sum(self.revealed)
        self.multiplier = 1.0 * (24 / (24 - self.mines_count)) ** revealed_count

    def cashout(self):
        if self.game_over:
            return 0
        winnings = int(self.bet * self.multiplier)
        self.update_user_balance(winnings - self.bet)  # 순수익만 추가
        return winnings

    def update_user_balance(self, amount):
        conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
        cursor = conn.cursor()
        cursor.execute("UPDATE user SET money = money + ? WHERE userid = ?", (amount, self.user_id))
        conn.commit()
        conn.close()

class MinesView(discord.ui.View):
    def __init__(self, game: MinesGame):
        super().__init__()
        self.game = game
        self.create_buttons()

    def create_buttons(self):
        for i in range(24):
            button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="?", row=i // 5, custom_id=str(i))
            button.callback = self.button_callback
            self.add_item(button)

        cashout_button = discord.ui.Button(style=discord.ButtonStyle.success, label="캐시아웃", row=4, custom_id="24")
        cashout_button.callback = self.cashout_callback
        self.add_item(cashout_button)

    async def button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return

        position = int(interaction.data["custom_id"])
        success, message = self.game.reveal(position)
        
        button = [x for x in self.children if x.custom_id == str(position)][0]
        if success:
            button.style = discord.ButtonStyle.primary
            button.label = "💎"
        else:
            button.style = discord.ButtonStyle.danger
            button.label = "💣"
        button.disabled = True

        embed = self.create_embed(message)
        
        if not success:
            self.reveal_all_tiles()
            embed.add_field(name="게임 결과", value="모든 지뢰 위치가 공개되었습니다.", inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)

        if not success:
            await interaction.followup.send("게임 오버! 베팅한 금액을 모두 잃었습니다.", ephemeral=True)

    async def cashout_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.game.user_id:
            await interaction.response.send_message("이 게임에 참여한 사람만 버튼을 누를 수 있습니다.", ephemeral=True)
            return

        winnings = self.game.cashout()
        self.reveal_all_tiles()
        embed = self.create_embed(f"캐시아웃 성공! 획득 금액: {winnings:,}원")
        embed.add_field(name="게임 결과", value="모든 지뢰 위치가 공개되었습니다.", inline=False)
        await interaction.response.edit_message(embed=embed, view=self)

    def reveal_all_tiles(self):
        for i, button in enumerate(self.children[:-1]):  # 캐시아웃 버튼 제외
            if self.game.board[i] == 1:  # 지뢰
                button.style = discord.ButtonStyle.danger
                button.label = "💣"
            else:  # 안전한 타일
                if not self.game.revealed[i]:  # 아직 공개되지 않은 타일
                    button.style = discord.ButtonStyle.secondary
                    button.label = "💎"
            button.disabled = True

    def create_embed(self, message: str):
        embed = discord.Embed(title="💣 마인즈 게임", color=discord.Color.blue())
        embed.add_field(name="베팅 금액", value=f"{self.game.bet:,}원", inline=True)
        embed.add_field(name="지뢰 개수", value=f"{self.game.mines_count}개", inline=True)
        embed.add_field(name="현재 배율", value=f"{self.game.multiplier:.2f}x", inline=True)
        embed.add_field(name="메시지", value=message, inline=False)
        return embed

@client.tree.command(name="마인즈", description="마인즈 게임을 시작합니다.")
async def mines(interaction: Interaction, 베팅금액: int, 지뢰개수: int):
    if 지뢰개수 < 1 or 지뢰개수 > 23:
        await interaction.response.send_message("지뢰 개수는 1개에서 23개 사이여야 합니다.", ephemeral=True)
        return
    
    if 베팅금액 < 1:
        await interaction.response.send_message("베팅 금액은 1원 이상이어야 합니다.", ephemeral=True)
        return

    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()

    cursor.execute("SELECT money FROM user WHERE userid = ?", (interaction.user.id,))
    current_balance = cursor.fetchone()

    if current_balance is None:
        await interaction.response.send_message("먼저 가입을 해주세요.", ephemeral=True)
        conn.close()
        return

    current_balance = current_balance[0]

    if current_balance < 베팅금액:
        embed = discord.Embed(title="마인즈 게임 실패", description="잔액이 부족합니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        conn.close()
        return

    # 베팅 금액 차감
    cursor.execute("UPDATE user SET money = money - ? WHERE userid = ?", (베팅금액, interaction.user.id))
    conn.commit()
    conn.close()

    game = MinesGame(베팅금액, 지뢰개수, interaction.user.id)
    view = MinesView(game)

    embed = view.create_embed("게임을 시작합니다. 타일을 선택하세요.")
    await interaction.response.send_message(embed=embed, view=view)

@client.tree.command(name="송금", description="송금을 합니다.")
async def 송금(interaction: Interaction, 상대방: discord.Member, 금액: int):
    if 금액 < 1:
        embed = discord.Embed(title="송금 실패", description="송금 금액은 1원 이상이어야 합니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if interaction.user.id == 상대방.id:
        embed = discord.Embed(title="송금 실패", description="자신에게는 송금할 수 없습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()

    cursor.execute("SELECT money FROM user WHERE userid = ?", (interaction.user.id,))
    current_balance = cursor.fetchone()

    if current_balance is None:
        embed = discord.Embed(title="송금 실패", description="먼저 가입을 해주세요.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        conn.close()
        return
    
    current_balance = current_balance[0]

    if current_balance < 금액:
        embed = discord.Embed(title="송금 실패", description="잔액이 부족합니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        conn.close()
        return

    # 송금 금액 차감
    cursor.execute("UPDATE user SET money = money - ? WHERE userid = ?", (금액, interaction.user.id))
    cursor.execute("UPDATE user SET money = money + ? WHERE userid = ?", (금액, 상대방.id))
    conn.commit()
    conn.close()

    embed = discord.Embed(title="송금 완료", description=f"{상대방.mention}에게 {금액:,}원을 송금했습니다.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)


# 게임 결과 저장 함수
def save_result(result):
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()
    cursor.execute("INSERT INTO baccarat_results (result) VALUES (?)", (result,))
    cursor.execute("DELETE FROM baccarat_results WHERE id NOT IN (SELECT id FROM baccarat_results ORDER BY id DESC LIMIT 20)")
    conn.commit()
    conn.close()

def get_results():
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT result FROM baccarat_results ORDER BY id DESC LIMIT 20")
    results = cursor.fetchall()
    conn.close()
    result_emojis = {
        'b': BANKER_EMOJI,
        'p': PLAYER_EMOJI,
        't': TIE_EMOJI
    }
    # 결과를 뒤집어서 최근 결과가 오른쪽에 오도록 합니다
    return ' '.join([result_emojis[r[0]] for r in reversed(results)])

class BaccaratGame:
    def __init__(self):
        self.player = []
        self.banker = []

    def deal_cards(self):
        deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 0, 0, 0, 0] * 4  # 0은 10, J, Q, K를 나타냄
        random.shuffle(deck)
        self.player = [deck.pop(), deck.pop()]
        self.banker = [deck.pop(), deck.pop()]

    def calculate_score(self, hand):
        return sum(hand) % 10

    def play_game(self):
        self.deal_cards()
        player_score = self.calculate_score(self.player)
        banker_score = self.calculate_score(self.banker)

        # 자연 8 또는 9 체크
        if player_score >= 8 or banker_score >= 8:
            return self.determine_winner()

        # 플레이어 추가 카드 규칙
        if player_score <= 5:
            self.player.append(random.randint(0, 9))
            player_score = self.calculate_score(self.player)

        # 뱅커 추가 카드 규칙
        if len(self.player) == 2:
            if banker_score <= 5:
                self.banker.append(random.randint(0, 9))
        else:
            if banker_score <= 2:
                self.banker.append(random.randint(0, 9))
            elif banker_score == 3 and self.player[2] != 8:
                self.banker.append(random.randint(0, 9))
            elif banker_score == 4 and self.player[2] in [2, 3, 4, 5, 6, 7]:
                self.banker.append(random.randint(0, 9))
            elif banker_score == 5 and self.player[2] in [4, 5, 6, 7]:
                self.banker.append(random.randint(0, 9))
            elif banker_score == 6 and self.player[2] in [6, 7]:
                self.banker.append(random.randint(0, 9))

        return self.determine_winner()

    def determine_winner(self):
        player_score = self.calculate_score(self.player)
        banker_score = self.calculate_score(self.banker)
        if player_score > banker_score:
            return "p"
        elif banker_score > player_score:
            return "b"
        else:
            return "t"

class BettingModal(ui.Modal, title="바카라 베팅"):
    bet_amount = ui.TextInput(label="베팅 금액", placeholder="베팅할 금액을 입력하세요", required=True)

    def __init__(self, bet_type):
        super().__init__()
        self.bet_type = bet_type

    async def on_submit(self, interaction: Interaction):
        try:
            amount = int(self.bet_amount.value)
            
            conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT money FROM user WHERE userid = ?", (interaction.user.id,))
            current_balance = cursor.fetchone()

            if current_balance is None or current_balance[0] < amount:
                await interaction.response.send_message(f"{MONEY_EMOJI} 잔액이 부족합니다.", ephemeral=True)
                conn.close()
                return

            # 베팅 금액 차감
            cursor.execute("UPDATE user SET money = money - ? WHERE userid = ?", (amount, interaction.user.id))
            conn.commit()

            game = BaccaratGame()
            result = game.play_game()

            # 게임 결과 저장
            save_result(result)

            win_amount = 0
            if result == 't':  # 무승부
                if self.bet_type == "tie":
                    win_amount = amount * 8
                else:
                    win_amount = amount  # 무승부 시 베팅 금액 반환
            elif result == self.bet_type[0]:  # 'p' 또는 'b'로 비교
                if self.bet_type == "banker":
                    win_amount = int(amount * 1.95)  # 5% 수수료
                else:
                    win_amount = amount * 2

            # 승리 금액 또는 반환 금액 추가
            cursor.execute("UPDATE user SET money = money + ? WHERE userid = ?", (win_amount, interaction.user.id))
            conn.commit()

            # 최종 잔액 조회
            cursor.execute("SELECT money FROM user WHERE userid = ?", (interaction.user.id,))
            final_balance = cursor.fetchone()[0]
            conn.close()

            # 금액 변동 계산
            amount_change = win_amount - amount

            # 결과에 따른 색상과 메시지 설정
            if amount_change > 0:
                result_color = discord.Color.green()
                result_message = f"🎉 승리! +{amount_change:,}원"
            elif amount_change < 0:
                result_color = discord.Color.red()
                result_message = f"😢 패배! {amount_change:,}원"
            else:
                result_color = discord.Color.gold()
                result_message = "🤝 무승부! 베팅 금액이 반환되었습니다."

            embed = discord.Embed(title=f"{CARDS_EMOJI} 바카라 게임 결과", color=result_color)
            embed.add_field(name="베팅 정보", value=f"{MONEY_EMOJI} 금액: {amount:,}원\n유형: {self.get_bet_type_emoji()}", inline=False)
            embed.add_field(name="게임 결과", value=f"승자: {self.get_result_emoji(result)}\n**{result_message}**", inline=False)
            embed.add_field(name=f"{PLAYER_EMOJI} 플레이어 카드", value=self.format_hand(game.player), inline=True)
            embed.add_field(name=f"{BANKER_EMOJI} 뱅커 카드", value=self.format_hand(game.banker), inline=True)
            embed.add_field(name="최종 잔액", value=f"{MONEY_EMOJI} {final_balance:,}원", inline=True)
            embed.add_field(name="최근 게임 결과", value=get_results(), inline=False)

            await interaction.response.send_message(embed=embed)

        except ValueError as e:
            await interaction.response.send_message(str(e), ephemeral=True)


    def get_bet_type_emoji(self):
        if self.bet_type == "player":
            return f"{PLAYER_EMOJI} 플레이어"
        elif self.bet_type == "banker":
            return f"{BANKER_EMOJI} 뱅커"
        else:
            return f"{TIE_EMOJI} 무승부"

    def get_result_emoji(self, result):
        if result == 'p':
            return f"{PLAYER_EMOJI} 플레이어"
        elif result == 'b':
            return f"{BANKER_EMOJI} 뱅커"
        else:
            return f"{TIE_EMOJI} 무승부"

    def format_hand(self, hand):
        card_emojis = {
            0: "🔟", 1: "🅰️", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣",
            6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"
        }
        return ' '.join([card_emojis[card] for card in hand])

class BaccaratView(ui.View):
    def __init__(self):
        super().__init__()

    @ui.button(label="플레이어", emoji=PLAYER_EMOJI, style=ButtonStyle.primary)
    async def player_button(self, interaction: Interaction, button: ui.Button):
        await self.handel_bet(interaction, "player")

    @ui.button(label="무승부", emoji=TIE_EMOJI, style=ButtonStyle.success)
    async def tie_button(self, interaction: Interaction, button: ui.Button):
        await self.handel_bet(interaction, "tie")

    @ui.button(label="뱅커", emoji=BANKER_EMOJI, style=ButtonStyle.danger)
    async def banker_button(self, interaction: Interaction, button: ui.Button):
        await self.handel_bet(interaction, "banker")

    async def handel_bet(self, interaction: Interaction, bet_type: str):
        modal = BettingModal(bet_type)
        await interaction.response.send_modal(modal)
        await modal.wait()

        for child in self.children:
            child.disabled = True

        await interaction.edit_original_response(view=self)

@client.tree.command(name="바카라", description="바카라 게임을 시작합니다.")
async def baccarat(interaction: Interaction):
    view = BaccaratView()
    embed = discord.Embed(title=f"{CARDS_EMOJI} 바카라", description="베팅할 곳을 선택하세요.", color=discord.Color.gold())
    embed.add_field(name="최근 게임 결과", value=get_results())
    await interaction.response.send_message(embed=embed, view=view)

def format_money(amount):
    units = ['', '만', '억', '조', '경', '해', '자', '양', '구', '간', '정', '재', '극']
    result = []
    unit_index = 0
    while amount > 0:
        part = amount % 10000
        if part > 0:
            if unit_index > 0:
                result.append(f"{part}{units[unit_index]}")
            else:
                result.append(f"{part}")
        amount //= 10000
        unit_index += 1
    return ' '.join(reversed(result)) + '원' if result else '0원'

@client.tree.command(name="순위", description="전체 금액의 순위를 1~10위까지 보여줍니다.")
async def ranking(interaction: Interaction):
    conn = sqlite3.connect(os.path.join(config.DB_Path, "db.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT userid, money FROM user ORDER BY money DESC LIMIT 10")
    top_users = cursor.fetchall()
    conn.close()

    embed = discord.Embed(title="🏆 금액 순위 (Top 10)", color=discord.Color.gold())
    
    for index, (userid, money) in enumerate(top_users, start=1):
        user = await client.fetch_user(userid)
        formatted_money = format_money(money)
        embed.add_field(name=f"{index}위: {user.name}", value=f"{formatted_money}", inline=False)

    await interaction.response.send_message(embed=embed)

#######################################################
# 봇 실행
#######################################################

def RunBot():
    client.run(config.BotToken)

if __name__ == "__main__":
    RunBot()
