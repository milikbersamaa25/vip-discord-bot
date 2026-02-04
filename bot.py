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

vip_info = {}
vip_list = []


def is_admin(member: discord.Member):
    return member.guild_permissions.administrator


def make_embed():
    lines = []
    title = "💎VIP X8 LUCK BY MYST STORE💎"

    start = 1

    if vip_info:
        lines.append(f"🗓️ Waktu : {vip_info.get('waktu', '-')}")
        lines.append(f"💰 Harga : {vip_info.get('harga', '-')}")
        lines.append(f"👤 PS : {vip_info.get('ps', '-')}")
        if vip_info.get("server"):
            lines.append(f"🌐 Server : {vip_info.get('server')}")
        lines.append("")

        lines.append(f"1. {vip_info.get('slot1', '-')}")
        start = 2

    index = start
    for data in vip_list:
        lines.append(f"{index}. {data['roblox']} — {data['mention']}")
        index += 1

    while index <= MAX_SLOT:
        lines.append(f"{index}.")
        index += 1

    lines.append("")
    lines.append("*Payment akan dibuka setelah semua list penuh ya guys!*")
    lines.append("*Terimakasih! —Myst MOD :3*")

    used = len(vip_list) + (1 if vip_info else 0)

    embed = discord.Embed(
        title=title,
        description="\n".join(lines),
        color=COLOR
    )
    embed.set_footer(text=f"{used}/{MAX_SLOT} slot")

    return embed


class VipSetupModal(Modal, title="Atur Info VIP (Admin)"):

    waktu = TextInput(label="Waktu pelaksanaan", max_length=100)
    harga = TextInput(label="Harga per slot", max_length=50)
    ps = TextInput(label="Nama akun Roblox (slot 1)", max_length=50)
    server = TextInput(label="Server (opsional)", required=False, max_length=50)

    async def on_submit(self, interaction: discord.Interaction):

        if not is_admin(interaction.user):
            await interaction.response.send_message(
                "Hanya admin yang boleh mengatur info VIP.",
                ephemeral=True
            )
            return

        vip_info["waktu"] = self.waktu.value
        vip_info["harga"] = self.harga.value
        vip_info["ps"] = self.ps.value
        vip_info["slot1"] = self.ps.value
        vip_info["server"] = self.server.value

        await interaction.message.edit(
            embed=make_embed(),
            view=VipView(admin=is_admin(interaction.user))
        )

        await interaction.response.send_message(
            "Info VIP diperbarui.",
            ephemeral=True
        )


class JoinModal(Modal, title="Ikut VIP"):

    roblox = TextInput(
        label="Username Roblox",
        placeholder="Contoh : KennMyst",
        max_length=50
    )

    async def on_submit(self, interaction: discord.Interaction):

        used = len(vip_list) + (1 if vip_info else 0)

        if used >= MAX_SLOT:
            await interaction.response.send_message(
                "Slot sudah penuh.",
                ephemeral=True
            )
            return

        vip_list.append({
            "id": str(uuid.uuid4()),
            "user_id": interaction.user.id,
            "mention": interaction.user.mention,
            "roblox": self.roblox.value
        })

        await interaction.message.edit(
            embed=make_embed(),
            view=VipView(admin=is_admin(interaction.user))
        )

        await interaction.response.send_message(
            "Berhasil masuk list VIP.",
            ephemeral=True
        )


class DeleteSelect(Select):

    def __init__(self, user_id: int):

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
            options.append(
                discord.SelectOption(label="Tidak ada slot", value="none")
            )

        super().__init__(
            placeholder="Pilih slot kamu yang ingin dihapus",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):

        if self.values[0] == "none":
            await interaction.response.send_message(
                "Kamu belum memiliki slot.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        slot_id = self.values[0]

        index = None
        removed_name = None

        for i, data in enumerate(vip_list):
            if data["id"] == slot_id:
                index = i
                removed_name = data["roblox"]
                break

        if index is None:
            await interaction.followup.send(
                "Slot sudah tidak tersedia.",
                ephemeral=True
            )
            return

        if vip_list[index]["user_id"] != interaction.user.id:
            await interaction.followup.send(
                "Ini bukan slot milik kamu.",
                ephemeral=True
            )
            return

        vip_list.pop(index)

        try:
            await interaction.message.edit(
                embed=make_embed(),
                view=VipView(admin=is_admin(interaction.user))
            )
        except:
            pass

        await interaction.followup.send(
            f"Slot ({removed_name}) telah dihapus.",
            ephemeral=True
        )


class DeleteView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(DeleteSelect(user_id))


class VipView(View):

    def __init__(self, admin=False):
        super().__init__(timeout=None)
        self.admin = admin

        if not self.admin:
            self.remove_item(self.setup_button)

    @discord.ui.button(label="+ Ikut", style=discord.ButtonStyle.success)
    async def join_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(JoinModal())

    @discord.ui.button(label="- Hapus slot saya", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: Button):

        my_slots = [x for x in vip_list if x["user_id"] == interaction.user.id]

        if not my_slots:
            await interaction.response.send_message(
                "Kamu belum punya slot.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Pilih slot kamu yang ingin dihapus:",
            view=DeleteView(interaction.user.id),
            ephemeral=True
        )

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary)
    async def refresh_button(self, interaction: discord.Interaction, button: Button):

        await interaction.message.edit(
            embed=make_embed(),
            view=VipView(admin=is_admin(interaction.user))
        )

        await interaction.response.send_message(
            "List diperbarui.",
            ephemeral=True
        )

    @discord.ui.button(label="✏️ Atur Info (Admin)", style=discord.ButtonStyle.primary)
    async def setup_button(self, interaction: discord.Interaction, button: Button):

        if not is_admin(interaction.user):
            await interaction.response.send_message(
                "Hanya admin yang boleh mengatur info.",
                ephemeral=True
            )
            return

        await interaction.response.send_modal(VipSetupModal())


@bot.command()
async def vip(ctx):
    global vip_list, vip_info

    vip_list = []
    vip_info = {}

    await ctx.send(
        embed=make_embed(),
        view=VipView(admin=is_admin(ctx.author))
    )

    try:
        await ctx.message.delete()
    except:
        pass


@bot.event
async def on_ready():
    print("Bot siap.")


bot.run(os.getenv("DISCORD_TOKEN"))