import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import threading
import time
from io import BytesIO
from PIL import Image, ImageTk
import json
import random

API_BASE = "https://discord.com/api/v10"


def fetch_user(token: str):
    headers = {"Authorization": token, "User-Agent": "DiscordAdminChecker/1.0"}
    url = f"{API_BASE}/users/@me"
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def fetch_guilds(token: str):
    headers = {"Authorization": token, "User-Agent": "DiscordAdminChecker/1.0"}
    url = f"{API_BASE}/users/@me/guilds"
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_guild_details(token: str, guild_id: str):
    headers = {"Authorization": token, "User-Agent": "DiscordAdminChecker/1.0"}
    url = f"{API_BASE}/guilds/{guild_id}"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def fetch_member_info(token: str, guild_id: str):
    headers = {"Authorization": token, "User-Agent": "DiscordAdminChecker/1.0"}
    url = f"{API_BASE}/guilds/{guild_id}/members/@me"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def fetch_image_tk(url, size=(96, 96)):
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert('RGBA')
        img = img.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def perms_to_names(perms):
    names = []
    try:
        p = int(perms)
    except Exception:
        return names
    FLAGS = [
        (0x00000001, "CREATE_INSTANT_INVITE"),
        (0x00000002, "KICK_MEMBERS"),
        (0x00000004, "BAN_MEMBERS"),
        (0x00000008, "ADMINISTRATOR"),
        (0x00000010, "MANAGE_CHANNELS"),
        (0x00000020, "MANAGE_GUILD"),
        (0x00000080, "VIEW_AUDIT_LOG"),
        (0x00000800, "SEND_MESSAGES"),
        (0x00002000, "MANAGE_MESSAGES"),
        (0x00010000, "READ_MESSAGE_HISTORY"),
    ]
    for bit, name in FLAGS:
        if (p & bit) != 0:
            names.append(name)
    return names


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.iconbitmap("")
        self.title("Discord Admin Checker — MistSoftworks ©")
        self.geometry("1200x720")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        main_frm = ctk.CTkFrame(self, fg_color="#0b0d0f")
        main_frm.pack(fill=tk.BOTH, expand=True)

        left_frm = ctk.CTkFrame(main_frm, fg_color="#0b0d0f")
        left_frm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        ctk.CTkLabel(left_frm, text="Discord Token (user token):", text_color="#cfe6ff").pack(anchor="w", pady=(0,6))
        self.token_var = tk.StringVar()
        token_entry = ctk.CTkEntry(left_frm, textvariable=self.token_var, show="•", width=400)
        token_entry.pack(anchor="w", pady=(0,8))
   
        btn_frm = ctk.CTkFrame(left_frm, fg_color="transparent")
        btn_frm.pack(anchor="w", pady=(0,12))
        self.check_btn = ctk.CTkButton(btn_frm, text="Check Admin Servers", command=self.on_check, width=150)
        self.check_btn.pack(side=tk.LEFT)

        self.progress_canvas = tk.Canvas(btn_frm, width=60, height=60, bg='#0b0d0f', highlightthickness=0)
        self.progress_canvas.pack(side=tk.LEFT, padx=(20,0))
        self.progress_value = 0

        self.status_var = tk.StringVar(value="Idle")
        ctk.CTkLabel(left_frm, textvariable=self.status_var, text_color="#7f8b92").pack(anchor="w", pady=(0,8))
        
        cards_lbl = ctk.CTkLabel(left_frm, text="Server Categories:", text_color="#e6eef6")
        cards_lbl.pack(anchor="w", pady=(8,4))
        self.cards_scrollable = ctk.CTkScrollableFrame(left_frm, fg_color="#121416", height=140)
        self.cards_scrollable.pack(fill=tk.BOTH, pady=(0,12))
        
        # Right panel - detailed info
        right_frm = ctk.CTkFrame(main_frm, fg_color="#0f1112", width=340)
        right_frm.pack(side=tk.RIGHT, fill=tk.BOTH, padx=12, pady=12)
        right_frm.pack_propagate(False)
    
        ctk.CTkLabel(right_frm, text="User Profile", text_color="#e6eef6", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,8))
        self.profile_name = ctk.CTkLabel(right_frm, text="(not loaded)", text_color="#cfe6ff")
        self.profile_name.pack(anchor="w")
        self.profile_avatar_lbl = ctk.CTkLabel(right_frm, text="")
        self.profile_avatar_lbl.pack(anchor="w", pady=(4,12))
        
        ctk.CTkLabel(right_frm, text="Server Details", text_color="#e6eef6", font=("Arial", 12, "bold")).pack(anchor="w", pady=(8,8))
        self.details_scrollable = ctk.CTkScrollableFrame(right_frm, fg_color="#0f1112")
        self.details_scrollable.pack(fill=tk.BOTH, expand=True)

        ctk.CTkLabel(right_frm, text="MistSoftworks ©", text_color="#6f7b84", font=("Arial", 9)).pack(side=tk.BOTTOM, pady=8)
        
        self.results = []
        self.card_images = {}

    def draw_circular_progress(self):
        """Draw a circular progress bar on canvas."""
        self.progress_canvas.delete("all")
        cx, cy = 30, 30
        radius = 25
        
        self.progress_canvas.create_oval(cx-radius, cy-radius, cx+radius, cy+radius, fill='', outline='#2a2c2f', width=3)
        
        # Progress arc
        if self.progress_value > 0:
            extent = (self.progress_value / 100) * 360
            self.progress_canvas.create_arc(cx-radius, cy-radius, cx+radius, cy+radius, 
                                           start=90, extent=-extent, fill='#3b82f6', outline='#3b82f6', width=3)

        self.progress_canvas.create_text(cx, cy, text=f"{int(self.progress_value)}%", fill='#e6eef6', font=("Arial", 10, "bold"))

    def on_check(self):
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("No token", "Please enter your Discord user token.")
            return
        self.progress_value = 0
        self.draw_circular_progress()
        self.status_var.set("Fetching... Please wait, This may take a while.")
        self.check_btn.configure(state="disabled")
        threading.Thread(target=self._check_thread, args=(token,), daemon=True).start()

    def _check_thread(self, token):
        try:
            for v in range(0, 26, 5):
                self.progress_value = v
                self.after(0, self.draw_circular_progress)
                time.sleep(0.05)
            
            user = fetch_user(token)
            self.after(0, lambda: self._set_profile(user))

            for v in range(26, 56, 5):
                self.progress_value = v
                self.after(0, self.draw_circular_progress)
                time.sleep(0.05)
            
            guilds_data = fetch_guilds(token)
            self.results = []
            
            for v in range(56, 101, 5):
                self.progress_value = v
                self.after(0, self.draw_circular_progress)
                time.sleep(0.02)

            for g in guilds_data:
                gid = g.get('id')
                guild_info = fetch_guild_details(token, gid)
                member_info = fetch_member_info(token, gid)
                
                self.results.append({
                    'id': gid,
                    'name': g.get('name'),
                    'icon': g.get('icon'),
                    'owner': g.get('owner', False),
                    'permissions': g.get('permissions'),
                    'guild_info': guild_info,
                    'member_info': member_info,
                    'joined_at': member_info.get('joined_at', 'Unknown')
                })
            
            self.after(0, self._populate_ui)
            self.progress_value = 100
            self.after(0, self.draw_circular_progress)
            self.after(0, lambda: self.status_var.set(f"Loaded {len(self.results)} servers"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.status_var.set("Error"))
        finally:
            self.after(0, lambda: self.check_btn.configure(state="normal"))

    def _set_profile(self, user):
        name = f"{user.get('username')}#{user.get('discriminator')}"
        self.profile_name.configure(text=name)
        avatar = user.get('avatar')
        if avatar:
            url = f"https://cdn.discordapp.com/avatars/{user.get('id')}/{avatar}.png?size=128"
            img = fetch_image_tk(url, size=(64, 64))
            if img:
                self.profile_avatar_lbl.configure(image=img)
                self.profile_avatar_lbl.image = img

    def _categorize_servers(self):
        """Categorize servers by admin status, ownership, and roles."""
        owned_servers = []
        admin_servers = []
        moderator_servers = []
        member_servers = []
        
        for r in self.results:
            perms = perms_to_names(r.get('permissions'))
            
            if r.get('owner'):
                owned_servers.append(r)
            elif 'ADMINISTRATOR' in perms:
                admin_servers.append(r)
            elif any(p in perms for p in ['BAN_MEMBERS', 'KICK_MEMBERS', 'MANAGE_MESSAGES', 'MANAGE_CHANNELS']):
                moderator_servers.append(r)
            else:
                member_servers.append(r)
        
        return {
            'Owned Servers': owned_servers,
            'Admin Servers': admin_servers,
            'Moderator Servers': moderator_servers,
            'Member Servers': member_servers,
        }

    def _get_overview_text(self):
        """Generate overview statistics."""
        total = len(self.results)
        categories = self._categorize_servers()
        owned = len(categories.get('Owned Servers', []))
        admin = len(categories.get('Admin Servers', []))
        mod = len(categories.get('Moderator Servers', []))
        member = len(categories.get('Member Servers', []))
        
        return f"""Total Servers: {total}
Owned: {owned}
Admin: {admin}
Moderator: {mod}
Member: {member}"""

    def _populate_ui(self):
        for w in self.cards_scrollable.winfo_children():
            w.destroy()
        for w in self.details_scrollable.winfo_children():
            w.destroy()

        overview_btn = ctk.CTkButton(
            self.cards_scrollable,
            text="📊 Overview",
            width=140,
            height=45,
            fg_color="#1a3a4d",
            hover_color="#2a4a5d",
            command=self._show_overview
        )
        overview_btn.pack(padx=4, pady=6, fill=tk.X)
        
        categories = self._categorize_servers()

        for category_name, servers in categories.items():
            count = len(servers)
            btn = ctk.CTkButton(
                self.cards_scrollable,
                text=f"{category_name}\n({count})",
                width=140,
                height=50,
                fg_color="#1f2326",
                hover_color="#2a3033",
                command=lambda cat=category_name: self._show_category(cat)
            )
            btn.pack(padx=4, pady=6, fill=tk.X)

        self._show_overview()

    def _show_category(self, category_name):
        """Show all servers in a category."""
        for w in self.details_scrollable.winfo_children():
            w.destroy()
        
        categories = self._categorize_servers()
        servers = categories.get(category_name, [])
  
        ctk.CTkLabel(self.details_scrollable, text=category_name, text_color="#e6eef6", font=("Arial", 13, "bold")).pack(anchor="w", pady=(0,8))
        
        if not servers:
            ctk.CTkLabel(self.details_scrollable, text="No servers in this category", text_color="#7f8b92").pack(anchor="w")
            return
        
        for srv in servers:
            srv_btn = ctk.CTkButton(
                self.details_scrollable,
                text=srv['name'][:30],
                width=200,
                height=32,
                fg_color="#121416",
                hover_color="#1f2326",
                command=lambda gid=srv['id']: self._show_server_details(gid)
            )
            srv_btn.pack(anchor="w", pady=3, padx=0)

    def _show_overview(self):
        """Show overview of all servers."""
        for w in self.details_scrollable.winfo_children():
            w.destroy()
 
        ctk.CTkLabel(self.details_scrollable, text="Account Overview", text_color="#e6eef6", font=("Arial", 13, "bold")).pack(anchor="w", pady=(0,12))
   
        categories = self._categorize_servers()
        owned = len(categories.get('Owned Servers', []))
        admin = len(categories.get('Admin Servers', []))
        mod = len(categories.get('Moderator Servers', []))
        member = len(categories.get('Member Servers', []))
        total = owned + admin + mod + member
        
        stats = [
            ("Total Servers", total, "#3b82f6"),
            ("Owned Servers", owned, "#4ade80"),
            ("Admin Servers", admin, "#fbbf24"),
            ("Moderator Servers", mod, "#f87171"),
            ("Member Servers", member, "#a78bfa"),
        ]
        
        for label, value, color in stats:
            frm = ctk.CTkFrame(self.details_scrollable, fg_color="#121416", corner_radius=6)
            frm.pack(anchor="w", pady=4, fill=tk.X)
            
            ctk.CTkLabel(frm, text=label, text_color=color, font=("Arial", 10, "bold")).pack(anchor="w", padx=8, pady=(4,0))
            ctk.CTkLabel(frm, text=str(value), text_color="#dbeaf7", font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=(0,4))

        ctk.CTkLabel(self.details_scrollable, text="", text_color="#0f1112").pack(pady=6)  # spacer
        ctk.CTkLabel(self.details_scrollable, text="Navigation", text_color="#cfe6ff", font=("Arial", 10, "bold")).pack(anchor="w", pady=(8,4))
        ctk.CTkLabel(self.details_scrollable, text="Click on a category above to view servers in that category.", text_color="#7f8b92", font=("Arial", 9), wraplength=300).pack(anchor="w")

    def _show_server_details(self, gid):
        """Show detailed info for a selected server."""
        for w in self.details_scrollable.winfo_children():
            w.destroy()
        
        for r in self.results:
            if r['id'] != gid:
                continue

            name_lbl = ctk.CTkLabel(self.details_scrollable, text=r['name'], text_color="#e6eef6", font=("Arial", 12, "bold"))
            name_lbl.pack(anchor="w", pady=(0,4))

            ctk.CTkLabel(self.details_scrollable, text=f"ID: {gid}", text_color="#7f8b92", font=("Arial", 8)).pack(anchor="w")

            owner_text = "✓ Owner" if r['owner'] else "Member"
            owner_color = "#4ade80" if r['owner'] else "#cfe6ff"
            ctk.CTkLabel(self.details_scrollable, text=f"Status: {owner_text}", text_color=owner_color, font=("Arial", 9, "bold")).pack(anchor="w", pady=(4,0))

            perms = perms_to_names(r.get('permissions'))
            if perms:
                ctk.CTkLabel(self.details_scrollable, text="Permissions:", text_color="#cfe6ff", font=("Arial", 10, "bold")).pack(anchor="w", pady=(8,3))
                for p in perms:
                    ctk.CTkLabel(self.details_scrollable, text=f"  • {p}", text_color="#dbeaf7", font=("Arial", 8)).pack(anchor="w")
            else:
                ctk.CTkLabel(self.details_scrollable, text="Permissions: None", text_color="#7f8b92", font=("Arial", 9)).pack(anchor="w", pady=(8,0))

            guild_info = r.get('guild_info', {})
            if guild_info:
                ctk.CTkLabel(self.details_scrollable, text="Server Info:", text_color="#cfe6ff", font=("Arial", 10, "bold")).pack(anchor="w", pady=(8,3))
                member_count = guild_info.get('member_count', 'N/A')
                owner_id = guild_info.get('owner_id', 'Unknown')
                ctk.CTkLabel(self.details_scrollable, text=f"  Members: {member_count}", text_color="#dbeaf7", font=("Arial", 8)).pack(anchor="w")
                ctk.CTkLabel(self.details_scrollable, text=f"  Owner ID: {owner_id}", text_color="#dbeaf7", font=("Arial", 8)).pack(anchor="w")
            
            member_info = r.get('member_info', {})
            if member_info:
                roles = member_info.get('roles', [])
                if roles:
                    ctk.CTkLabel(self.details_scrollable, text="Your Roles:", text_color="#cfe6ff", font=("Arial", 10, "bold")).pack(anchor="w", pady=(8,3))
                    for idx, role_id in enumerate(roles[:10]):
                        ctk.CTkLabel(self.details_scrollable, text=f"  • {role_id}", text_color="#dbeaf7", font=("Arial", 8)).pack(anchor="w")
                    if len(roles) > 10:
                        ctk.CTkLabel(self.details_scrollable, text=f"  +{len(roles)-10} more roles", text_color="#7f8b92", font=("Arial", 8)).pack(anchor="w")
            
                joined = member_info.get('joined_at', 'Unknown')
                if joined != 'Unknown':
                    joined = joined[:10]
                ctk.CTkLabel(self.details_scrollable, text=f"Joined: {joined}", text_color="#dbeaf7", font=("Arial", 9)).pack(anchor="w", pady=(4,0))
            
            break


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
