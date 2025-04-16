# generate_model.py
import random
import string
import pandas as pd


class GenerateModel:
    def __init__(self):
        self.session_id_map = {}
        self.actor_id_map = {}
        self.session_actor_map = {}

    def random_id(self, length=6):
        return ''.join(random.choices(string.digits, k=length))

    def to_iso8601_timestamp(self, value):
        try:
            dt = pd.to_datetime(value, errors='coerce')
            if pd.isnull(dt):
                return str(value)
            return dt.isoformat(timespec='seconds')
        except Exception:
            return str(value)

    def build_action(self, row, session_id=None, override_id=None, override_actor=None):
        action_id = override_id if override_id else self.random_id(6)
        raw_actor = str(row.get("Actor"))
        actor_id = override_actor if override_actor else self.actor_id_map.get(raw_actor, self.random_id(6))
        return {
            "id": action_id,
            "timestamp": self.to_iso8601_timestamp(row.get("timestamp")),
            "verb": {
                "id": f"https://w3id.org/xapi/dod-isd/verbs/{row.get('Verb', 'unknown')}"
            },
            "actor": {
                "mbox": f"mailto:{actor_id}@open.ac.uk"
            },
            "object": {
                "id": f"http://open.ac.uk/{row.get('Object', 'unknown')}"
            },
            "duration": float(row.get("Duration", 0.0))
        }

    def build_session(self, grp):
        session_id_value = grp["session_id"].iloc[0]
        if session_id_value not in self.session_id_map:
            self.session_id_map[session_id_value] = self.random_id(6)
        same_id_for_session = self.session_id_map[session_id_value]

        real_actor = grp["Actor"].iloc[0]
        if real_actor not in self.actor_id_map:
            self.actor_id_map[real_actor] = self.random_id(6)
        same_actor_for_session = self.actor_id_map[real_actor]

        actions_list = []
        for _, row in grp.iterrows():
            action_dict = self.build_action(
                row,
                session_id=session_id_value,
                override_id=same_id_for_session,
                override_actor=same_actor_for_session
            )
            actions_list.append(action_dict)
        return actions_list

    def generate(self, trained_model, num_records, users_input):
        """
        Génère des données synthétiques à partir du modèle entraîné.
        - `trained_model` : instance entraînée qui dispose d'une méthode sample().
        - `num_records` : nombre de données à générer.
        - `users_input` : chaîne représentant le nombre de unique acteurs (0 pour la génération naturelle).

        Retourne un tuple (generated_data, session_data).
        """
        # Générer un DataFrame à partir du modèle (ici on suppose que trained_model.sample renvoie un DataFrame)
        df = trained_model.sample(num_records)
        df["Actor"] = df["Actor"].astype(str)

        try:
            num_actors = int(users_input)
        except ValueError:
            num_actors = 0

        # Si un nombre spécifique d'acteurs est imposé, générer des IDs aléatoires pour l'acteur
        if num_actors > 0:
            chosen_ids = [self.random_id(6) for _ in range(num_actors)]
            base_ids = chosen_ids[:]
            remaining = len(df) - len(base_ids)
            if remaining > 0:
                import random
                base_ids += random.choices(chosen_ids, k=remaining)
            random.shuffle(base_ids)
            df["Actor"] = base_ids
            self.actor_id_map = {actor: actor for actor in set(df["Actor"])}

        # Si le DataFrame contient une colonne session_id, on regroupe par sessions
        if "session_id" in df.columns:
            df_sessions = (
                df.groupby("session_id")
                    .apply(lambda grp: self.build_session(grp))
                    .reset_index(name="actions")
            )
            df_sessions.drop("session_id", axis=1, inplace=True)
            generated_data = df_sessions
            session_data = df_sessions.copy()
        else:
            # Sinon, construire une liste d'actions
            actions = [self.build_action(row, session_id=None) for _, row in df.iterrows()]
            generated_data = actions
            session_data = pd.DataFrame(actions)
        return generated_data, session_data
