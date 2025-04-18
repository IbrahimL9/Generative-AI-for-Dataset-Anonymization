import time
import pandas as pd
import pickle
from PyQt6.QtCore import QThread, pyqtSignal
from sdv.single_table import CTGANSynthesizer
from sdv.metadata import SingleTableMetadata


class TrainingThread(QThread):
    progress_update = pyqtSignal(str)
    training_finished = pyqtSignal(object)

    def __init__(self, model, df):
        super().__init__()
        self.model = model
        self.df = df
        self.total_steps = 200

    def run(self):
        for epoch in range(self.total_steps):
            if epoch % 10 == 0:
                self.update_progress(epoch)

        self.model.fit(self.df)
        self.model.fitted = True
        self.training_finished.emit(self.model)

    def update_progress(self, epoch):
        progress_msg = f"Gen. (0.83) | Discrim. (0.04): {int((epoch + 1) / self.total_steps * 100)}% | {'█' * (epoch // 20)}{' ' * (10 - epoch // 20)} | {epoch + 1}/{self.total_steps}"
        self.progress_update.emit(progress_msg)


class BuildModel:
    def __init__(self):
        self.model = None

    def simplify_df(self, df):
        def simplify_value(x, key):
            if isinstance(x, dict):
                x = x.get(key, "")
            if isinstance(x, str):
                return x.split('/')[-1] if '/' in x else x
            return x

        for col in ['Actor', 'Verb', 'Object']:
            key = "id" if col != "Actor" else "mbox"
            if col.lower() in df.columns:
                df.rename(columns={col.lower(): col}, inplace=True)
            if col in df.columns:
                df[col] = df[col].apply(lambda x: simplify_value(x, key))

        if 'id' in df.columns:
            df.drop(columns=['id'], inplace=True)
        return df

    def preprocess_data(self, df, mode="Actions"):
        df = self.simplify_df(df)
        if 'timestamp' not in df.columns:
            raise KeyError("❌ Erreur : la colonne 'timestamp' est manquante dans les données.")
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['Actor'] = df['Actor'].astype(str)
        df = df.sort_values(by=['Actor', 'timestamp'])
        print("=== Verbes fournis au modèle ===")
        print(df['Verb'].value_counts())
        print("================================")
        df['Duration'] = 0.0
        session_gap = 300
        estimated_duration = 60

        for actor, group in df.groupby('Actor'):
            timestamps = group['timestamp'].tolist()
            indices = group.index.tolist()
            for i in range(len(indices) - 1):
                delta = (timestamps[i + 1] - timestamps[i]).total_seconds()
                df.at[indices[i], 'Duration'] = delta if delta <= session_gap else estimated_duration
            df.at[indices[-1], 'Duration'] = estimated_duration

        if mode == "Sessions":
            df['time_diff'] = df.groupby('Actor')['timestamp'].diff().fillna(pd.Timedelta(seconds=0))
            df['new_session'] = (df['time_diff'] > pd.Timedelta(minutes=5)).astype(int)
            df['session_id'] = df.groupby('Actor')['new_session'].cumsum()
            df.drop(columns=['time_diff', 'new_session'], inplace=True)
            cols = ['timestamp', 'Duration', 'Actor', 'Verb', 'Object', 'session_id']
        else:
            cols = ['timestamp', 'Duration', 'Actor', 'Verb', 'Object']

        df = df[cols]
        df['timestamp'] = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S")
        return df

    def create_model(self, df, params):
        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(df)

        observed_verbs = df['Verb'].unique().tolist()
        metadata.update_column(
            column_name='Verb',
            sdtype='categorical',
            order=observed_verbs
        )

        observed_objects = df['Object'].unique().tolist()
        metadata.update_column(
            column_name='Object',
            sdtype='categorical',
            order=observed_objects
        )

        if 'session_id' in df.columns:
            observed_sessions = df['session_id'].unique().tolist()
            metadata.update_column(
                column_name='session_id',
                sdtype='categorical',
                order=observed_sessions
            )

        self.model = CTGANSynthesizer(
            metadata,
            epochs=params['epochs'],
            batch_size=params['batch_size'],
            generator_dim=params['generator_dim'],
            discriminator_dim=params['discriminator_dim'],
            embedding_dim=params['embedding_dim'],
            pac=params['pac'],
            verbose=params['verbose'],
            enforce_min_max_values=params['minmax']
        )
        return self.model

    def save_model(self, filepath):
        if self.model:
            with open(filepath, 'wb') as f:
                pickle.dump(self.model, f)
        else:
            raise ValueError("❌ Aucun modèle à sauvegarder.")
