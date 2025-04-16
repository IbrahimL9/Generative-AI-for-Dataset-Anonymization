# fidelity_controller.py
import matplotlib.pyplot as plt
import sns as sns

from models.fidelity_model import FidelityModel
from views.pages.fidelity_view import FidelityView
import pandas as pd


class FidelityController:
    def __init__(self, main_app, view=None):
        """
        main_app doit contenir :
           - main_app.pages["generate"].generated_data (données synthétiques)
           - main_app.pages["open"].json_data (données originales)
        """
        self.main_app = main_app
        self.model = FidelityModel()
        self.view = view if view is not None else FidelityView()
        self.connect_signals()

    def connect_signals(self):
        self.view.ksc_button.clicked.connect(self.calculate_ksc)
        self.view.tvc_button.clicked.connect(self.calculate_tvc)
        self.view.sequence_button.clicked.connect(self.calculate_verb_sequence_similarity)
        self.view.markov_button.clicked.connect(self.plot_markov_transition_matrices)
        self.view.pca_button.clicked.connect(self.perform_pca_analysis)

    def on_data_generated(self):
        # Récupérer et préparer les données
        original = self.model.ensure_dataframe(self.main_app.pages["open"].json_data)
        synthetic = self.model.ensure_dataframe(self.main_app.pages["generate"].generated_data)
        original.columns = original.columns.str.lower()
        synthetic.columns = synthetic.columns.str.lower()
        self.original_data = original
        self.synthetic_data = synthetic

    def calculate_ksc(self):
        self.on_data_generated()
        if self.original_data.empty or self.synthetic_data.empty:
            self.view.append_result("Erreur : Données non disponibles.")
            return
        categorical_columns = ['actor', 'verb', 'object']
        ksc_scores = self.model.compute_ksc(self.original_data, self.synthetic_data, categorical_columns)
        for col, score in ksc_scores.items():
            self.view.append_result(f"KS Complement Score for {col} : {score:.4f}")
        if ksc_scores:
            fig = self.model.plot_ksc_scores(ksc_scores)
            if fig:
                plt.show()

    def calculate_tvc(self):
        self.on_data_generated()
        if self.original_data.empty or self.synthetic_data.empty:
            self.view.append_result("Erreur : Données non disponibles.")
            return
        categorical_columns = ['actor', 'verb', 'object']
        tvc_scores = self.model.compute_tvc(self.original_data, self.synthetic_data, categorical_columns)
        for col, score in tvc_scores.items():
            self.view.append_result(f"TV Complement Score for {col} : {score:.4f}")
        if tvc_scores:
            # Vous pouvez ici ajouter un affichage graphique similaire si souhaité
            plt.figure(figsize=(10, 6))
            plt.bar(list(tvc_scores.keys()), list(tvc_scores.values()), color='lightcoral')
            plt.title("TV Complement Scores")
            plt.xlabel("Columns")
            plt.ylabel("Score")
            plt.ylim(0, 1)
            plt.show()

    def calculate_verb_sequence_similarity(self):
        self.on_data_generated()
        if self.original_data.empty or self.synthetic_data.empty:
            self.view.append_result("Erreur : Données non disponibles.")
            return
        top_real, top_synth, jaccard = self.model.compute_verb_sequence_similarity(self.original_data,
                                                                                   self.synthetic_data)
        self.view.append_result("\n🔎 Top 10 real bigrams (normalized):")
        total_real = sum(dict(top_real).values())
        for pair, freq in top_real:
            percent = (freq / total_real) * 100 if total_real else 0
            self.view.append_result(f"{pair} : {percent:.4f}%")
        self.view.append_result("\n🧪 Top 10 synthetic bigrams (normalized):")
        total_synth = sum(dict(top_synth).values())
        for pair, freq in top_synth:
            percent = (freq / total_synth) * 100 if total_synth else 0
            self.view.append_result(f"{pair} : {percent:.4f}%")
        self.view.append_result(f"\n✅ Jaccard similarity index (Top 10 bigrams): {jaccard:.2f}")

    def plot_markov_transition_matrices(self):
        self.on_data_generated()
        if self.original_data.empty or self.synthetic_data.empty:
            self.view.append_result("Erreur : Données non disponibles.")
            return
        required_cols = ['actor', 'verb', 'timestamp']
        for col in required_cols:
            if col not in self.original_data.columns or col not in self.synthetic_data.columns:
                self.view.append_result(f"Erreur : Colonne manquante → {col}")
                return

        df_real = self.original_data.dropna(subset=required_cols).copy()
        df_synth = self.synthetic_data.dropna(subset=required_cols).copy()
        df_real['timestamp'] = pd.to_datetime(df_real['timestamp'], errors='coerce')
        df_synth['timestamp'] = pd.to_datetime(df_synth['timestamp'], errors='coerce')
        df_real = df_real.dropna(subset=['timestamp'])
        df_synth = df_synth.dropna(subset=['timestamp'])

        real_matrix = self.model.compute_markov_transition_matrices(df_real)
        synth_matrix = self.model.compute_markov_transition_matrices(df_synth)

        verbs = sorted(set(real_matrix.index) | set(real_matrix.columns) |
                       set(synth_matrix.index) | set(synth_matrix.columns))
        real_matrix = real_matrix.reindex(index=verbs, columns=verbs, fill_value=0)
        synth_matrix = synth_matrix.reindex(index=verbs, columns=verbs, fill_value=0)

        fig, axs = plt.subplots(1, 2, figsize=(14, 6))
        sns.heatmap(real_matrix, ax=axs[0], cmap="Blues", annot=False, fmt=".2f")
        axs[0].set_title("Real Transition Matrix")
        sns.heatmap(synth_matrix, ax=axs[1], cmap="Oranges", annot=False, fmt=".2f")
        axs[1].set_title("Synthetic Transition Matrix")
        plt.tight_layout()
        plt.show()

        distance = self.model.compute_l1_divergence(real_matrix, synth_matrix)
        self.view.append_result(f"\nL1 divergence between transition matrices: {distance:.4f}")

    def perform_pca_analysis(self):
        real_df = self.model.flatten_synthetic_data(self.original_data)
        synth_df = self.model.flatten_synthetic_data(self.synthetic_data)
        self.view.append_result("\nInitial state of real data:")
        self.view.append_result(str(real_df.head()))
        self.view.append_result("\nInitial state of synthetic data:")
        self.view.append_result(str(synth_df.head()))
        if real_df.empty or synth_df.empty:
            self.view.append_result("Erreur : Données non disponibles pour PCA.")
            return

        # Convertir les colonnes
        columns = ['verb', 'actor', 'object', 'duration']
        real_df = self.model.convert_column_types(real_df, columns)
        synth_df = self.model.convert_column_types(synth_df, columns)

        self.view.append_result("\nState after column type conversion (real):")
        self.view.append_result(str(real_df.head()))
        self.view.append_result("\nState after column type conversion (synthetic):")
        self.view.append_result(str(synth_df.head()))

        real_df, _ = self.model.encode_categorical(real_df, ['verb', 'actor', 'object'])
        synth_df, _ = self.model.encode_categorical(synth_df, ['verb', 'actor', 'object'])
        self.view.append_result("\nState after categorical encoding (real):")
        self.view.append_result(str(real_df.head()))
        self.view.append_result("\nState after categorical encoding (synthetic):")
        self.view.append_result(str(synth_df.head()))

        real_df['dataset'] = 'original'
        synth_df['dataset'] = 'synthetic'
        combined_df = pd.concat([real_df, synth_df], ignore_index=True).dropna(subset=columns)

        X = combined_df[columns].copy()
        y = combined_df['dataset']
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        fig, var_info = self.model.perform_pca(real_df, synth_df)
        if fig is not None:
            plt.show()
        self.view.append_result(
            f"\n📊 Explained variance:\n→ 2 dimensions: {var_info['cumulative_2D']:.2%}\n→ 5 dimensions: {var_info['cumulative_5D']:.2%}"
        )
        if var_info['cumulative_2D'] >= 0.45:
            self.view.append_result("✅ 2D projection is sufficient.")
        else:
            self.view.append_result(
                "⚠️ 2D projection loses too much information, consider more dimensions for better comparison.")
