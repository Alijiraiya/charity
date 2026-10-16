import tkinter as tk
from tkinter import ttk, messagebox
from theme import ThemeManager as TM
from widgets import create_button, create_treeview, entry_row, separator, make_scrollable
import database as db
from water_filling import WaterFillingDistribution

class DistributionsPage(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=TM.get_color("bg"))
        self.simulation_data = []
        self._build_ui()

    def _build_ui(self):
        # ── Toute la page est désormais défilante : avec le budget, le tableau
        # de simulation, l'historique ET les 2 nouvelles listes de bénéficiaires,
        # le contenu dépasse la hauteur de nombreux écrans. Sans ascenseur, le
        # bas de la page (les 2 listes) restait invisible.
        outer, wrap = make_scrollable(self)
        outer.pack(fill="both", expand=True)

        tk.Label(wrap, text="Distribution (Water-Filling) | المساعدات توزيع ",
                 font=TM.FONTS["title"], fg=TM.get_color("accent"),
                 bg=TM.get_color("bg")).pack(padx=40, pady=20)
        separator(wrap).pack(fill="x", padx=40, pady=4)

        # Budget input
        input_frame = tk.Frame(wrap, bg=TM.get_color("bg"))
        input_frame.pack(fill="x", padx=40, pady=10)
        f, self.v_budget, _ = entry_row(input_frame, "Budget total (DA) :")
        f.pack(side="right", padx=10, fill="x", expand=True)
        create_button(input_frame, "⚙️ Calculer | حساب",
                      self._run_simulation).pack(side="right")

        # Simulation results table
        self.container, self.tree = create_treeview(
            wrap, ("name","score","amount"),
            ("Famille | العائلة", "Score SVF", "Montant (DA)"),
            [250,150,200], height=8)
        self.container.pack(fill="both", expand=True, padx=40, pady=10)

        # Confirm button
        self.btn_confirm = create_button(wrap, "✅ Valider | اعتماد التوزيع",
                                         self._confirm_dist)
        self.btn_confirm.pack(pady=6)
        self.btn_confirm.config(state="disabled")

        # History
        hist_frame = tk.Frame(wrap, bg=TM.get_color("bg"))
        hist_frame.pack(fill="x", padx=40, pady=10)
        h_top = tk.Frame(hist_frame, bg=TM.get_color("bg"))
        h_top.pack(fill="x")
        tk.Label(h_top, text="Historique | التاريخي السجل ",
                 font=TM.FONTS["heading"], fg=TM.get_color("accent"),
                 bg=TM.get_color("bg")).pack(side="left", pady=5)
        tk.Button(h_top, text="🗑 Supprimer la distribution sélectionnée", font=TM.FONTS["small"],
                  bg="#e74c3c", fg="#ffffff",
                  command=self._delete_distribution).pack(side="right", pady=5)
        self.hc, self.hist_tree = create_treeview(
            hist_frame, ["id","f","amt","d"],
            ["#","Famille","Montant","Date"], [50,250,150,150], height=6)
        self.hc.pack(fill="both", expand=True)
        # (Le suivi des bénéficiaires a sa propre page : page_beneficiaries.py)

    def refresh(self):
        for r in self.hist_tree.get_children():
            self.hist_tree.delete(r)
        for r in db.get_all_distributions():
            # r: (id, head_name, amount, distribution_type, distribution_date, notes)
            self.hist_tree.insert("", "end", iid=str(r[0]),
                                  values=(r[0], r[1], f"{r[2]:,.0f} DA", r[4]))

    def _delete_distribution(self):
        sel = self.hist_tree.selection()
        if not sel:
            return messagebox.showwarning("Attention", "Sélectionnez une distribution à supprimer.")
        if messagebox.askyesno("Confirmation",
                               "Supprimer cette distribution de l'historique ?\nCette action est définitive."):
            db.delete_distribution(int(sel[0]))
            self.refresh()

    def _run_simulation(self):
        try:
            budget_str = self.v_budget.get().strip()
            if not budget_str:
                return messagebox.showerror("Erreur", "Veuillez entrer un budget.")
            budget = float(budget_str)
            families = [{'id': f[0], 'head_name': f[1], 'svf_score': f[20]}
                        for f in db.get_all_families() if f[20] > 0]
            if not families:
                return messagebox.showwarning("Attention",
                    "Aucune famille avec un score SVF > 0.")
            result = WaterFillingDistribution(budget).calculate(families)
            for item in self.tree.get_children():
                self.tree.delete(item)
            if result['success']:
                for res in result['distributions']:
                    self.tree.insert("", "end",
                        values=(res['head_name'], res['svf_score'],
                                f"{res['amount']:,.0f} DA"))
                self.simulation_data = result['distributions']
                self.btn_confirm.config(state="normal")
            else:
                messagebox.showwarning("Attention", result['message'])
                self.btn_confirm.config(state="disabled")
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide (chiffres uniquement).")

    def _confirm_dist(self):
        for res in self.simulation_data:
            db.add_distribution(res['family_id'], res['amount'],
                                "Water-Filling | خوارزمية",
                                "Automatique | توزيع تلقائي")
        self.btn_confirm.config(state="disabled")
        self.simulation_data = []
        messagebox.showinfo("Succès", "Distribution enregistrée avec succès.")
        self.refresh()