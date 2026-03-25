import os
import json
import queue
import re
import threading
import tkinter as tk
from collections import Counter
from tkinter import filedialog, messagebox, scrolledtext
from urllib import error, request


class DeepGameScanner:
    REVIEW_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1486151919998206154/VSILeBAmFhDB5YIx2Hno-VBQWhgQ2trf0wJ5nep4xFPVtyOP8Vr0MM2iZktrCqxuZyuI"
    SCAN_EXTENSIONS = (
        ".dll",
        ".exe",
        ".cs",
        ".unitypackage",
        ".asset",
        ".dat",
        ".json",
        ".sys",
        ".txt",
        ".cfg",
        ".ini",
        ".xml",
    )

    def __init__(self, root):
        self.root = root
        self.root.title("Anti Findr")
        self.root.geometry("1120x760")
        self.root.minsize(980, 700)
        self.root.configure(bg="#07111f")

        self.all_signatures = [
            "DeviceCheck",
            "Anti",
            "BadBilly",
            "AnnoyModders",
            "Lemon scripts",
            "TrollModders",
            "spoopy",
            "yummy",
            "VersionChecker",
            "QuestTriggers",
            "QuestSenstinelProtect",
            "QuestLink",
            "Change Photon",
            "Playfab Settings",
            "GorillaObjectCheck",
            "Oxgspersonalanticheat",
            "FrameworkSession",
            "VectorMathUtility",
            "RuntimeUtility",
            "JJFiT",
            "Encryption",
            "AntiNoclip",
            "AntiPhoton",
            "CheatUpdate",
            "CloudScriptRevision",
            "dumbasstheanticheatsaresomewhereelse",
            "OPANTICHEAT",
            "ACHIDER",
            "CokesAntiCheat",
            "HydrasBasicAntiCheat",
            "MonsterBugFix",
            "moveon",
            "NoLemonScript",
            "Playfabchecker",
            "RENAMETHIS",
            "UnitysAntiCheat",
            "XRToolkitCS",
            "ChangePhotonSettings",
            "QuestSentinelProtect",
            "ALOOKITSAFUCKINGMODDER",
        ]

        self.anticheat_signatures = [
            "DeviceCheck",
            "QuestSenstinelProtect",
            "Oxgspersonalanticheat",
            "AntiNoclip",
            "AntiPhoton",
            "dumbasstheanticheatsaresomewhereelse",
            "OPANTICHEAT",
            "ACHIDER",
            "CokesAntiCheat",
            "HydrasBasicAntiCheat",
            "UnitysAntiCheat",
            "QuestSentinelProtect",
            "ALOOKITSAFUCKINGMODDER",
        ]

        self.signatures = list(self.anticheat_signatures)
        self.signature_map = {
            signature: self.normalize_for_compare(signature)
            for signature in self.signatures
        }
        self.scan_in_progress = False
        self.event_queue = queue.Queue()
        self.stats = Counter()
        self.current_folder = ""
        self.reported_hits = set()

        self.build_ui()
        self.root.after(75, self.process_queue)

    def build_ui(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        shell = tk.Frame(self.root, bg="#07111f")
        shell.grid(sticky="nsew", padx=22, pady=22)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(2, weight=1)

        header = tk.Frame(shell, bg="#0d1b2e", highlightbackground="#26f0c7", highlightthickness=1)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="ANTI FINDR",
            font=("Bahnschrift", 28, "bold"),
            fg="#e8fff9",
            bg="#0d1b2e",
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 0))

        tk.Label(
            header,
            text="Scanning only anti-cheat category entries from your list across names and readable content.",
            font=("Segoe UI", 11),
            fg="#8ed9ca",
            bg="#0d1b2e",
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(6, 18))

        controls = tk.Frame(shell, bg="#07111f")
        controls.grid(row=1, column=0, sticky="ew", pady=(18, 14))
        controls.grid_columnconfigure(3, weight=1)

        self.scan_button = tk.Button(
            controls,
            text="Select Game Folder",
            command=self.start_scan_thread,
            font=("Segoe UI", 12, "bold"),
            bg="#26f0c7",
            fg="#06211b",
            activebackground="#74ffe0",
            activeforeground="#041511",
            relief="flat",
            padx=18,
            pady=12,
            cursor="hand2",
        )
        self.scan_button.grid(row=0, column=0, sticky="w")

        self.review_button = tk.Button(
            controls,
            text="Review / Feedback",
            command=self.open_review_window,
            font=("Segoe UI", 11, "bold"),
            bg="#1c314e",
            fg="#dff8ff",
            activebackground="#2d4d77",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=12,
            cursor="hand2",
        )
        self.review_button.grid(row=0, column=1, sticky="w", padx=(12, 0))

        self.folder_label = tk.Label(
            controls,
            text="No folder selected",
            font=("Consolas", 10),
            fg="#7fb0c8",
            bg="#07111f",
        )
        self.folder_label.grid(row=0, column=2, sticky="w", padx=(16, 0))

        self.status = tk.Label(
            controls,
            text="Status: Ready",
            font=("Segoe UI Semibold", 11),
            fg="#b9c9d6",
            bg="#07111f",
        )
        self.status.grid(row=0, column=3, sticky="e")

        body = tk.Frame(shell, bg="#07111f")
        body.grid(row=2, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        console_frame = tk.Frame(body, bg="#08111b", highlightbackground="#1b3652", highlightthickness=1)
        console_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(1, weight=1)

        tk.Label(
            console_frame,
            text="Live Scan Feed",
            font=("Segoe UI", 12, "bold"),
            fg="#d7fffb",
            bg="#08111b",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(12, 8))

        self.result_area = scrolledtext.ScrolledText(
            console_frame,
            wrap="word",
            bg="#02070d",
            fg="#7df9d4",
            insertbackground="#7df9d4",
            selectbackground="#26f0c7",
            selectforeground="#00110d",
            relief="flat",
            font=("Consolas", 10),
            padx=12,
            pady=12,
        )
        self.result_area.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        sidebar = tk.Frame(body, bg="#0b1523", highlightbackground="#24507a", highlightthickness=1)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(2, weight=1)

        tk.Label(
            sidebar,
            text="Detection Summary",
            font=("Segoe UI", 12, "bold"),
            fg="#e9f7ff",
            bg="#0b1523",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        self.summary_total = tk.Label(
            sidebar,
            text="0 total hits",
            font=("Bahnschrift", 20, "bold"),
            fg="#26f0c7",
            bg="#0b1523",
        )
        self.summary_total.grid(row=1, column=0, sticky="w", padx=16)

        self.summary_area = scrolledtext.ScrolledText(
            sidebar,
            wrap="word",
            bg="#08101b",
            fg="#d5e7f3",
            relief="flat",
            state="disabled",
            font=("Consolas", 10),
            padx=12,
            pady=12,
            height=20,
        )
        self.summary_area.grid(row=2, column=0, sticky="nsew", padx=16, pady=(10, 16))

        tk.Label(
            shell,
            text="Copyright (c) 2026 Maxplayztv Studios",
            font=("Segoe UI", 9),
            fg="#5f89a3",
            bg="#07111f",
        ).grid(row=3, column=0, sticky="e", pady=(10, 0))

        self.log("Ready. Pick a folder to scan for anti-cheat category signatures only.")

    @staticmethod
    def normalize_for_compare(text):
        return re.sub(r"[^a-z0-9]+", "", text.casefold())

    @staticmethod
    def normalize_webhook_url(url):
        return url.replace("https://discordapp.com/api/webhooks/", "https://discord.com/api/webhooks/")

    def update_summary(self):
        total_hits = sum(self.stats.values())
        self.summary_total.config(text=f"{total_hits} total hit{'s' if total_hits != 1 else ''}")

        lines = []
        if self.stats:
            for signature, count in self.stats.most_common():
                lines.append(f"{count:>3}x  {signature}")
        else:
            lines.append("No detections yet.")

        self.summary_area.config(state="normal")
        self.summary_area.delete("1.0", tk.END)
        self.summary_area.insert(tk.END, "\n".join(lines))
        self.summary_area.config(state="disabled")

    def log(self, text):
        self.result_area.insert(tk.END, text + "\n")
        self.result_area.see(tk.END)

    def queue_log(self, text):
        self.event_queue.put(("log", text))

    def queue_status(self, text):
        self.event_queue.put(("status", text))

    def queue_hit(self, signature, message):
        self.event_queue.put(("hit", signature, message))

    def queue_done(self):
        self.event_queue.put(("done",))

    def queue_review_result(self, success, message):
        self.event_queue.put(("review_result", success, message))

    def record_hit(self, signature, category, source_path):
        hit_key = (signature, category, source_path)
        if hit_key in self.reported_hits:
            return

        self.reported_hits.add(hit_key)
        self.queue_hit(signature, f"[{category}] {signature} matched in {source_path}")

    def process_queue(self):
        try:
            while True:
                item = self.event_queue.get_nowait()
                kind = item[0]

                if kind == "log":
                    self.log(item[1])
                elif kind == "status":
                    self.status.config(text=item[1])
                elif kind == "hit":
                    signature, message = item[1], item[2]
                    self.stats[signature] += 1
                    self.log(message)
                    self.update_summary()
                elif kind == "done":
                    total_hits = sum(self.stats.values())
                    self.status.config(text="Status: Scan complete")
                    self.scan_button.config(state="normal", text="Scan Another Folder")
                    self.update_summary()
                    self.scan_in_progress = False
                    messagebox.showinfo("Scan Complete", f"Found {total_hits} total matches.")
                elif kind == "review_result":
                    success, message = item[1], item[2]
                    if success:
                        messagebox.showinfo("Review Sent", message)
                    else:
                        messagebox.showerror("Send Failed", message)
        except queue.Empty:
            pass

        self.root.after(75, self.process_queue)

    def start_scan_thread(self):
        if self.scan_in_progress:
            return

        path = filedialog.askdirectory(title="Select game folder")
        if not path:
            return

        self.scan_in_progress = True
        self.current_folder = path
        self.stats.clear()
        self.reported_hits.clear()
        self.result_area.delete("1.0", tk.END)
        self.update_summary()
        self.folder_label.config(text=path)
        self.status.config(text="Status: Preparing scan...")
        self.scan_button.config(state="disabled", text="Scanning...")
        self.log(f"Starting scan in: {path}")
        self.log(f"Loaded {len(self.signatures)} anti-cheat signatures.")

        threading.Thread(target=self.scan, args=(path,), daemon=True).start()

    def open_review_window(self):
        review_window = tk.Toplevel(self.root)
        review_window.title("Send Review")
        review_window.geometry("540x520")
        review_window.configure(bg="#0b1523")
        review_window.resizable(False, False)
        review_window.grid_columnconfigure(0, weight=1)
        review_window.grid_rowconfigure(5, weight=1)

        tk.Label(
            review_window,
            text="Review and Feedback",
            font=("Bahnschrift", 22, "bold"),
            fg="#e8fff9",
            bg="#0b1523",
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(18, 6))

        tk.Label(
            review_window,
            text="Send product feedback directly to your Discord review server.",
            font=("Segoe UI", 10),
            fg="#8ed9ca",
            bg="#0b1523",
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 12))

        tk.Label(
            review_window,
            text="Name",
            font=("Segoe UI", 10, "bold"),
            fg="#dff8ff",
            bg="#0b1523",
        ).grid(row=2, column=0, sticky="w", padx=18)

        name_entry = tk.Entry(
            review_window,
            font=("Segoe UI", 11),
            bg="#08101b",
            fg="#e9f7ff",
            insertbackground="#e9f7ff",
            relief="flat",
        )
        name_entry.grid(row=3, column=0, sticky="ew", padx=18, pady=(6, 12))

        options_frame = tk.Frame(review_window, bg="#0b1523")
        options_frame.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 12))
        options_frame.grid_columnconfigure(1, weight=1)

        tk.Label(
            options_frame,
            text="Rating (1-5)",
            font=("Segoe UI", 10, "bold"),
            fg="#dff8ff",
            bg="#0b1523",
        ).grid(row=0, column=0, sticky="w")

        rating_var = tk.StringVar(value="5")
        rating_menu = tk.OptionMenu(options_frame, rating_var, "5", "4", "3", "2", "1")
        rating_menu.config(
            font=("Segoe UI", 10),
            bg="#1c314e",
            fg="#dff8ff",
            activebackground="#2d4d77",
            activeforeground="#ffffff",
            relief="flat",
            highlightthickness=0,
        )
        rating_menu["menu"].config(
            bg="#1c314e",
            fg="#dff8ff",
            activebackground="#2d4d77",
            activeforeground="#ffffff",
        )
        rating_menu.grid(row=0, column=1, sticky="w", padx=(12, 0))

        feedback_frame = tk.Frame(review_window, bg="#0b1523")
        feedback_frame.grid(row=5, column=0, sticky="nsew", padx=18, pady=(0, 16))
        feedback_frame.grid_columnconfigure(0, weight=1)
        feedback_frame.grid_rowconfigure(1, weight=1)

        tk.Label(
            feedback_frame,
            text="Feedback",
            font=("Segoe UI", 10, "bold"),
            fg="#dff8ff",
            bg="#0b1523",
        ).grid(row=0, column=0, sticky="w")

        feedback_box = scrolledtext.ScrolledText(
            feedback_frame,
            wrap="word",
            height=9,
            font=("Segoe UI", 10),
            bg="#08101b",
            fg="#e9f7ff",
            insertbackground="#e9f7ff",
            relief="flat",
            padx=10,
            pady=10,
        )
        feedback_box.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        footer = tk.Frame(review_window, bg="#0b1523")
        footer.grid(row=6, column=0, sticky="ew", padx=18, pady=(0, 18))
        footer.grid_columnconfigure(0, weight=1)

        send_button = tk.Button(
            footer,
            text="Send Review",
            font=("Segoe UI", 11, "bold"),
            bg="#26f0c7",
            fg="#06211b",
            activebackground="#74ffe0",
            activeforeground="#041511",
            relief="flat",
            padx=18,
            pady=10,
            cursor="hand2",
        )
        send_button.grid(row=0, column=1, sticky="e")

        def submit_review():
            reviewer_name = name_entry.get().strip() or "Anonymous"
            rating = rating_var.get().strip()
            feedback = feedback_box.get("1.0", tk.END).strip()

            if not feedback:
                messagebox.showwarning("Missing Feedback", "Please enter feedback before sending.")
                return

            send_button.config(state="disabled", text="Sending...")
            threading.Thread(
                target=self.send_review_to_discord,
                args=(reviewer_name, rating, feedback, review_window, send_button),
                daemon=True,
            ).start()

        send_button.config(command=submit_review)

    def scan(self, game_path):
        try:
            for root_dir, dirs, files in os.walk(game_path):
                self.queue_status(f"Status: Scanning {root_dir[-70:]}")

                for directory_name in dirs:
                    full_path = os.path.join(root_dir, directory_name)
                    self.match_text(directory_name, "FOLDER", full_path)

                for file_name in files:
                    full_path = os.path.join(root_dir, file_name)
                    self.match_text(file_name, "NAME", full_path)

                    if file_name.lower().endswith(self.SCAN_EXTENSIONS):
                        self.scan_file(full_path, file_name)
        finally:
            self.queue_done()

    def find_matches(self, text):
        normalized_text = self.normalize_for_compare(text)
        if not normalized_text:
            return []

        matches = []
        for signature, normalized_signature in self.signature_map.items():
            if normalized_signature and normalized_signature in normalized_text:
                matches.append(signature)
        return matches

    def match_text(self, text, label, source_path):
        for signature in self.find_matches(text):
            self.record_hit(signature, label, source_path)

    def scan_file(self, path, filename):
        try:
            previous_tail = b""
            with open(path, "rb") as file_handle:
                while True:
                    chunk = file_handle.read(65536)
                    if not chunk:
                        break

                    combined = previous_tail + chunk
                    previous_tail = combined[-512:]

                    readable_text = combined.decode("utf-8", errors="ignore")
                    for signature in self.find_matches(readable_text):
                        self.record_hit(signature, "CONTENT", path)

                    lowered_bytes = combined.lower()
                    for signature in self.signatures:
                        if signature.lower().encode("utf-8") in lowered_bytes:
                            self.record_hit(signature, "BINARY", path)
        except OSError as exc:
            self.queue_log(f"[SKIP] Could not read {filename}: {exc}")

    def send_review_to_discord(self, reviewer_name, rating, feedback, review_window, send_button):
        payload = {
            "username": "Anti Findr Reviews",
            "content": (
                "**New Anti Findr Review**\n"
                f"**Name:** {reviewer_name}\n"
                f"**Rating:** {rating}/5\n"
                f"**Feedback:**\n{feedback}"
            ),
        }

        data = json.dumps(payload).encode("utf-8")
        webhook_url = self.normalize_webhook_url(self.REVIEW_WEBHOOK_URL)
        discord_request = request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "AntiFindrReviewClient/1.0",
            },
            method="POST",
        )

        try:
            with request.urlopen(discord_request, timeout=10) as response:
                if response.status not in (200, 204):
                    raise RuntimeError(f"Discord returned status {response.status}")

            self.root.after(0, review_window.destroy)
            self.queue_review_result(True, "Your review was sent to Discord successfully.")
        except error.HTTPError as exc:
            try:
                details = exc.read().decode("utf-8", errors="ignore").strip()
            except Exception:
                details = ""

            extra = f" Details: {details}" if details else ""
            self.root.after(0, lambda: send_button.config(state="normal", text="Send Review"))
            self.queue_review_result(False, f"Could not send the review: HTTP {exc.code}.{extra}")
        except (error.URLError, RuntimeError) as exc:
            self.root.after(0, lambda: send_button.config(state="normal", text="Send Review"))
            self.queue_review_result(False, f"Could not send the review: {exc}")


if __name__ == "__main__":
    root = tk.Tk()
    app = DeepGameScanner(root)
    app.update_summary()
    root.mainloop()
