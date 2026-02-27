import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select
import os
import uuid

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

MAX_SLOT = 20
COLOR = 0x00f8ff

vip_sessions = {}


def is_admin(member: discord.Member):
    return member.guild_permissions.administrator


def get_session(message_id: int):
    if message_id not in vip_sessions:
        vip_sessions[message_id] = {
            "info": {},
            "list": []
        }
    return vip_sessions[message_id]


async def auto_delete(ctx, msg, delay=5):
    try:
        await ctx.message.delete()
    except:
        pass

    try:
        await msg.delete(delay=delay)
    except:
        pass


def make_embed(message_id: int):

    session = get_session(message_id)
    info = session["info"]
    vip_list = session["list"]

    lines = []

    lines.append("✦·┈๑⋅⋯  ⋯⋅๑┈·✦")

    title = "**💎 VIP X8 LUCK BY MYST STORE 💎**"

    if info:
        lines.append(f"* TANGGAL : {info.get('waktu','-')}")
        lines.append(f"* DURASI  : {info.get('durasi_waktu','-')}")
        lines.append(f"* HARGA   : {info.get('harga','-')}")
        lines.append(f"* PS      : {info.get('ps','-')}")

        if info.get("server"):
            lines.append(f"* SERVER   : {info.get('server')}")
    else:
        lines.append("_Belum diatur oleh admin_")

    lines.append("")
    lines.append("**──.✦ LIST SLOT**")

    index = 1
    for data in vip_list:
        line = f"{index}. {data['roblox']} — {data['mention']}"
        if data.get("paid"):
            line += " | ✅"
        lines.append(line)
        index += 1

    while index <= MAX_SLOT:
        lines.append(f"{index}.")
        index += 1

    lines.append("")
    lines.append("*Payment akan dibuka setelah semua list penuh ya guys!*")
    lines.append("*Terimakasih! —Myst MOD :3*")

    embed = discord.Embed(
        title=title,
        description="\n".join(lines),
        color=COLOR
    )

    embed.set_footer(text=f"{len(vip_list)}/{MAX_SLOT} slot")

    return embed


# ================= MODAL =================

class VipSetupModal(Modal):

    def __init__(self, message_id):
        super().__init__(title="Atur Info VIP (Admin)")
        self.message_id = message_id

        self.waktu = TextInput(label="Tanggal")
        self.durasi_waktu = TextInput(label="Durasi")
        self.harga = TextInput(label="Harga")
        self.ps = TextInput(label="PS / Host")
        self.server = TextInput(label="Server (opsional)", required=False)

        for i in (
            self.waktu,
            self.durasi_waktu,
            self.harga,
            self.ps,
            self.server
        ):
            self.add_item(i)

    async def on_submit(self, interaction: discord.Interaction):

        if not is_admin(interaction.user):
            await interaction.response.send_message("Hanya admin.", ephemeral=True)
            return

        info = get_session(self.message_id)["info"]

        info["waktu"] = self.waktu.value
        info["durasi_waktu"] = self.durasi_waktu.value
        info["harga"] = self.harga.value
        info["ps"] = self.ps.value
        info["server"] = self.server.value

        msg = await interaction.channel.fetch_message(self.message_id)

        await msg.edit(
            embed=make_embed(self.message_id),
            view=VipView(self.message_id)
        )

        await interaction.response.send_message(
            "Info diperbarui.",
            ephemeral=True
        )


class JoinModal(Modal):

    def __init__(self, message_id):
        super().__init__(title="Ikut VIP")
        self.message_id = message_id

        self.roblox = TextInput(
            label="Username Roblox",
            placeholder="Contoh : KennMyst"
        )
        self.add_item(self.roblox)

    async def on_submit(self, interaction: discord.Interaction):

        session = get_session(self.message_id)

        if len(session["list"]) >= MAX_SLOT:
            await interaction.response.send_message(
                "Slot sudah penuh.",
                ephemeral=True
            )
            return

        session["list"].append({
            "id": str(uuid.uuid4()),
            "user_id": interaction.user.id,
            "mention": interaction.user.mention,
            "roblox": self.roblox.value,
            "paid": False
        })

        msg = await interaction.channel.fetch_message(self.message_id)

        await msg.edit(
            embed=make_embed(self.message_id),
            view=VipView(self.message_id)
        )

        await interaction.response.send_message(
            "Berhasil masuk list VIP.",
            ephemeral=True
        )


# ================= DELETE (MEMBER) =================

class DeleteSelect(Select):

    def __init__(self, message_id, user_id):

        self.message_id = message_id

        session = get_session(message_id)
        vip_list = session["list"]

        options = []
        for data in vip_list:
            if data["user_id"] == user_id:
                options.append(
                    discord.SelectOption(
                        label=data["roblox"],
                        value=data["id"]
                    )
                )

        if not options:
            options.append(discord.SelectOption(label="Tidak ada slot", value="none"))

        super().__init__(
            placeholder="Pilih slot kamu",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "none":
            await interaction.response.send_message("Tidak ada slot.", ephemeral=True)
            return

        session = get_session(self.message_id)
        vip_list = session["list"]

        slot_id = self.values[0]

        for i, d in enumerate(vip_list):
            if d["id"] == slot_id:

                if d["user_id"] != interaction.user.id:
                    await interaction.response.send_message("Bukan slot kamu.", ephemeral=True)
                    return

                vip_list.pop(i)

                msg = await interaction.channel.fetch_message(self.message_id)

                await msg.edit(
                    embed=make_embed(self.message_id),
                    view=VipView(self.message_id)
                )

                await interaction.response.send_message("Slot dihapus.", ephemeral=True)
                return

        await interaction.response.send_message("Slot tidak ditemukan.", ephemeral=True)


class DeleteView(View):
    def __init__(self, message_id, user_id):
        super().__init__(timeout=60)
        self.add_item(DeleteSelect(message_id, user_id))


# ================= VIEW =================

class VipView(View):

    def __init__(self, message_id):
        super().__init__(timeout=None)
        self.message_id = message_id

    @discord.ui.button(label="+ Ikut", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: Button):

        if len(get_session(self.message_id)["list"]) >= MAX_SLOT:
            await interaction.response.send_message("Slot sudah penuh.", ephemeral=True)
            return

        await interaction.response.send_modal(
            JoinModal(self.message_id)
        )

    @discord.ui.button(label="- Hapus slot saya", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: Button):

        session = get_session(self.message_id)

        if not any(x["user_id"] == interaction.user.id for x in session["list"]):
            await interaction.response.send_message("Kamu belum punya slot.", ephemeral=True)
            return

        await interaction.response.send_message(
            "Pilih slot kamu:",
            view=DeleteView(self.message_id, interaction.user.id),
            ephemeral=True
        )

    @discord.ui.button(label="✏️ Atur Info (Admin)", style=discord.ButtonStyle.primary)
    async def setup(self, interaction: discord.Interaction, button: Button):

        if not is_admin(interaction.user):
            await interaction.response.send_message("Hanya admin.", ephemeral=True)
            return

        await interaction.response.send_modal(
            VipSetupModal(self.message_id)
        )

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(self, interaction: discord.Interaction, button: Button):

        msg = await interaction.channel.fetch_message(self.message_id)

        await msg.edit(
            embed=make_embed(self.message_id),
            view=VipView(self.message_id)
        )

        await interaction.response.send_message("Direfresh.", ephemeral=True)


# ================= ADMIN COMMAND =================

@bot.command()
@commands.has_permissions(administrator=True)
async def delete(ctx, nomor: int = None):

    if nomor is None:
        m = await ctx.send("Format:\n!delete (no slot)\nContoh: !delete 3")
        await auto_delete(ctx, m)
        return

    if not ctx.message.reference:
        m = await ctx.send("Reply pesan list VIP yang mau diubah.")
        await auto_delete(ctx, m)
        return

    message_id = ctx.message.reference.message_id

    session = vip_sessions.get(message_id)
    if not session:
        m = await ctx.send("List tidak ditemukan.")
        await auto_delete(ctx, m)
        return

    vip_list = session["list"]

    index = nomor - 1

    if index < 0 or index >= len(vip_list):
        m = await ctx.send("Nomor slot tidak valid.")
        await auto_delete(ctx, m)
        return

    vip_list.pop(index)

    msg = await ctx.channel.fetch_message(message_id)

    await msg.edit(
        embed=make_embed(message_id),
        view=VipView(message_id)
    )

    m = await ctx.send("Slot berhasil dihapus.")
    await auto_delete(ctx, m)


@bot.command()
@commands.has_permissions(administrator=True)
async def edit(ctx, nomor: int = None, roblox: str = None, member: discord.Member = None):

    if nomor is None or roblox is None or member is None:
        m = await ctx.send(
            "Format:\n!edit (no slot) (username roblox) (@tag)\n"
            "Contoh: !edit 2 KennMyst @User"
        )
        await auto_delete(ctx, m)
        return

    if not ctx.message.reference:
        m = await ctx.send("Reply pesan list VIP yang mau diubah.")
        await auto_delete(ctx, m)
        return

    message_id = ctx.message.reference.message_id

    session = vip_sessions.get(message_id)
    if not session:
        m = await ctx.send("List tidak ditemukan.")
        await auto_delete(ctx, m)
        return

    vip_list = session["list"]

    if nomor < 1 or nomor > MAX_SLOT:
        m = await ctx.send("Nomor slot tidak valid.")
        await auto_delete(ctx, m)
        return

    index = nomor - 1

    while len(vip_list) <= index:
        vip_list.append({
            "id": str(uuid.uuid4()),
            "user_id": 0,
            "mention": "-",
            "roblox": "-",
            "paid": False
        })

    vip_list[index] = {
        "id": str(uuid.uuid4()),
        "user_id": member.id,
        "mention": member.mention,
        "roblox": roblox,
        "paid": False
    }

    msg = await ctx.channel.fetch_message(message_id)

    await msg.edit(
        embed=make_embed(message_id),
        view=VipView(message_id)
    )

    m = await ctx.send("Slot berhasil diedit.")
    await auto_delete(ctx, m)


@bot.command()
@commands.has_permissions(administrator=True)
async def paid(ctx, slots: str = None):

    if slots is None:
        m = await ctx.send(
            "Format:\n!paid (no slot)\nBisa lebih dari satu.\nContoh: !paid 1,2,10"
        )
        await auto_delete(ctx, m)
        return

    if not ctx.message.reference:
        m = await ctx.send("Reply pesan list VIP yang mau diubah.")
        await auto_delete(ctx, m)
        return

    message_id = ctx.message.reference.message_id

    session = vip_sessions.get(message_id)
    if not session:
        m = await ctx.send("List tidak ditemukan.")
        await auto_delete(ctx, m)
        return

    vip_list = session["list"]

    try:
        numbers = [int(x.strip()) for x in slots.split(",")]
    except:
        m = await ctx.send("Format salah. Contoh: !paid 1,2,10")
        await auto_delete(ctx, m)
        return

    updated = 0

    for nomor in numbers:
        index = nomor - 1
        if 0 <= index < len(vip_list):
            vip_list[index]["paid"] = True
            updated += 1

    msg = await ctx.channel.fetch_message(message_id)

    await msg.edit(
        embed=make_embed(message_id),
        view=VipView(message_id)
    )

    m = await ctx.send(f"{updated} slot berhasil ditandai paid.")
    await auto_delete(ctx, m)


# ================= MAIN COMMAND =================

@bot.command()
async def vip(ctx):

    msg = await ctx.send(
        embed=discord.Embed(title="Membuat list VIP...", color=COLOR)
    )

    get_session(msg.id)

    await msg.edit(
        embed=make_embed(msg.id),
        view=VipView(msg.id)
    )

    try:
        await ctx.message.delete()
    except:
        pass


@bot.event
async def on_ready():
    print("Bot siap.")


bot.run(os.getenv("DISCORD_TOKEN"))
