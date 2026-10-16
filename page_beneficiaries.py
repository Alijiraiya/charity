import tkinter as tk
from theme import ThemeManager as TM
from widgets import create_button, create_treeview, separator
import database as db


class BeneficiariesPage(tk.Frame):
    """Page « Bénéficiaires » : suivi de l'aide reçue par les familles.

    - À gauche : familles ayant déjà bénéficié d'au moins une distribution
      (nombre de fois + montant total), triées par montant décroissant.
    - À droite : familles actives n'ayant JAMAIS reçu d'aide, triées par
      score SVF décroissant (les plus vulnérables d'abord).
    Les deux listes se remplissent automatiquement à chaque ouverture de la page.
    """

    def __init__(self, parent):
        super().__init__(parent, bg=TM.get_color("bg"))
        self._build_ui()

    def _build_ui(self):
        bg = TM.get_color("bg")

        # ── En-tête ──────────────────────────────────────────────────────
        head = tk.Frame(self, bg=bg)
        head.pack(fill="x", padx=40, pady=(20, 4))
        tk.Label(head, text="Bénéficiaires de l'aide | المستفيدون من المساعدات",
                 font=TM.FONTS["title"], fg=TM.get_color("accent"),
                 bg=bg).pack(side="left")
        create_button(head, "🔄 Actualiser | تحديث", self.refresh).pack(side="right")

        self.lbl_summary = tk.Label(self, text="", font=TM.FONTS["body"],
                                    fg=TM.get_color("text_muted"), bg=bg, anchor="w")
        self.lbl_summary.pack(fill="x", padx=40, pady=(0, 4))
        separator(self).pack(fill="x", padx=40, pady=4)

        # ── Les deux listes, côte à côte (visibles sans défilement) ─────
        body = tk.Frame(self, bg=bg)
        body.pack(fill="both", expand=True, padx=40, pady=(8, 20))
        body.columnconfigure(0, weight=1, uniform="lists")
        body.columnconfigure(1, weight=1, uniform="lists")
        body.rowconfigure(0, weight=1)

        left = tk.LabelFrame(body, text=" Familles bénéficiaires | العائلات المستفيدة ",
                             font=TM.FONTS["body_b"], fg=TM.get_color("text"),
                             bg=bg, padx=8, pady=8)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.benef_c, self.benef_tree = create_treeview(
            left, ["name", "count", "total"],
            ["Famille | العائلة", "Nb. de fois", "Montant total"],
            [200, 90, 130], height=15)
        self.benef_c.pack(fill="both", expand=True)

        right = tk.LabelFrame(body, text=" Familles jamais bénéficiaires | لم تستفد أبداً ",
                              font=TM.FONTS["body_b"], fg=TM.get_color("text"),
                              bg=bg, padx=8, pady=8)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.nobenef_c, self.nobenef_tree = create_treeview(
            right, ["name", "phone", "score"],
            ["Famille | العائلة", "Téléphone", "Score SVF"],
            [200, 110, 90], height=15)
        self.nobenef_c.pack(fill="both", expand=True)

    def refresh(self):
        for tree in (self.benef_tree, self.nobenef_tree):
            for r in tree.get_children():
                tree.delete(r)

        with_help = db.get_families_with_distributions_summary()
        without_help = db.get_families_without_distributions()

        for fid, name, count, total in with_help:
            self.benef_tree.insert("", "end", iid=f"b{fid}",
                                   values=(name, count, f"{total:,.0f} DA"))
        for fid, name, phone, score in without_help:
            self.nobenef_tree.insert("", "end", iid=f"n{fid}",
                                     values=(name, phone or "---", f"{(score or 0)}%"))

        total_given = sum(r[3] for r in with_help)
        self.lbl_summary.config(
            text=f"{len(with_help)} famille(s) aidée(s) — {total_given:,.0f} DA distribués"
                 f"   |   {len(without_help)} famille(s) jamais aidée(s)")
