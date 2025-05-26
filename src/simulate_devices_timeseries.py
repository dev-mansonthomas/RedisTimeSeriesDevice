import redis
import random
from datetime import datetime, timedelta, timezone
import argparse
import sys

# Types de métriques simulées
METRICS = ["temp", "volt", "current", "gaz", "alarme"]

def ms(ts):
    """Convertit un datetime en timestamp (millisecondes)"""
    return int(ts.timestamp() * 1000)

def create_series(r, device_id, retention_ms, enable_compaction: bool = False):
    """Crée les séries TS pour chaque métrique d'un device avec une rétention"""
    for metric in METRICS:
        key = f"device:{device_id}:{metric}"
        try:
            r.execute_command("TS.CREATE", key, "RETENTION", retention_ms)
        except redis.exceptions.ResponseError as e:
            if "already exists" not in str(e):
                raise
        if enable_compaction:
            for agg_name, agg_type, bucket_ms in [
                ("1h_avg", "avg", 3600000),
                ("1d_max", "max", 86400000)
            ]:
                compact_key = f"{key}:{agg_name}"
                try:
                    r.execute_command("TS.CREATE", compact_key)
                except redis.exceptions.ResponseError as e:
                    if "already exists" not in str(e):
                        raise
                r.execute_command("TS.CREATERULE", key, compact_key, "AGGREGATION", agg_type, bucket_ms)

def generate_value(metric):
    """Génère une valeur plausible en fonction du type de métrique"""
    if metric in ["gaz", "alarme"]:
        return random.choice([0, 1])
    elif metric == "temp":
        return round(random.uniform(15.0, 35.0), 2)
    elif metric == "volt":
        return round(random.uniform(220.0, 240.0), 2)
    elif metric == "current":
        return round(random.uniform(0.0, 50.0), 2)
    return 0

def add_data(r, device_id, start_ts, frequency_min, num_points, batch_size: int):
    """Ajoute des points espacés régulièrement pour un device"""
    pipe = r.pipeline()
    current_ts = start_ts
    for i in range(num_points):
        ts_millis = ms(current_ts)
        for metric in METRICS:
            key = f"device:{device_id}:{metric}"
            value = generate_value(metric)
            pipe.execute_command("TS.ADD", key, ts_millis, value, "ON_DUPLICATE", "LAST")
        current_ts += timedelta(minutes=frequency_min)
        if i % batch_size == 0:
            pipe.execute()
    pipe.execute()
    end_date_str = (current_ts - timedelta(minutes=frequency_min)).strftime("%Y-%m-%d")
    print(f"📤 device:{device_id} | date:{end_date_str} | ✅")

def delete_keys(r, num_devices):
    """Supprime les clés générées si elles existent réellement"""
    print("🧹 Vérification des clés existantes...")
    total_deleted = 0
    pipe = r.pipeline()

    for device_id in range(num_devices):
        keys = [f"device:{device_id}:{metric}" for metric in METRICS]
        # Vérifie si au moins une clé existe
        if any(r.exists(k) for k in keys):
            for key in keys:
                pipe.delete(key)
            total_deleted += len(keys)

    if total_deleted > 0:
        pipe.execute()
        print(f"✅ {total_deleted} clés supprimées.")
    else:
        print("ℹ️ Aucun device existant trouvé, rien à supprimer.")

def print_memory_info(r):
    """Affiche l'utilisation mémoire de Redis"""
    info = r.info()
    used_memory = int(info.get("used_memory", 0)) / (1024 * 1024)
    total_keys = info.get("db0", {}).get("keys", 0) if "db0" in info else 0

    print("\n📊 Redis Memory Info:")
    print(f"- Mémoire utilisée (MB) : {used_memory:.2f}")
    print(f"- Nombre total de clés  : {total_keys}")

    if "ts_stats_total_samples" in info:
        print(f"- Total TS samples      : {info['ts_stats_total_samples']}")
    if "ts_stats_total_series" in info:
        print(f"- Total TS series       : {info['ts_stats_total_series']}")

def run_simulation(
    host: str,
    port: int,
    username: str,
    password: str,
    measures_per_day: int,
    frequency_min: int,
    years: int,
    clean: bool,
    enable_compaction: bool,
    batch_size: int,
    raw_retention_days: int
):
    total_days = 365 * years
    points_per_day = 24 * 60 // frequency_min
    total_points = total_days * points_per_day
    num_devices = measures_per_day // 5
    retention_ms = raw_retention_days * 24 * 60 * 60 * 1000

    r = redis.Redis(
        host=host,
        port=port,
        username=username,
        password=password,
        decode_responses=True
    )

    if clean:
        delete_keys(r, num_devices)

    print(f"📡 Simulation de {num_devices} devices × 5 métriques sur {years} ans")
    print(f"📈 {total_points} points par métrique")

    start_time = datetime.now(timezone.utc) - timedelta(days=total_days)

    for device_id in range(num_devices):
        create_series(r, device_id, retention_ms, enable_compaction=enable_compaction)
        add_data(r, device_id, start_time, frequency_min, total_points, batch_size)

    print("✅ Insertion terminée.")
    print_memory_info(r)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Redis host")
    parser.add_argument("--port", type=int, default=6379, help="Redis port")
    parser.add_argument("--username", default=None, help="Redis username")
    parser.add_argument("--password", default=None, help="Redis password")
    parser.add_argument("--measures_per_day", type=int, required=True, help="Mesures par jour (total)")
    parser.add_argument("--frequency", type=int, required=True, help="Fréquence des mesures en minutes")
    parser.add_argument("--years", type=int, required=True, help="Nombre d'années à simuler")
    parser.add_argument("--clean", action="store_true", help="Supprimer les clés générées")
    parser.add_argument("--enable_compaction", action="store_true", help="Activer les règles de compaction (1h avg, 1d max)")
    parser.add_argument("--pipeline_batch_size", type=int, default=1000, help="Taille du pipeline Redis avant exécution")
    parser.add_argument("--raw_retention_days", type=int, default=90, help="Durée de rétention des séries brutes (en jours)")

    args = parser.parse_args()

    run_simulation(
        host=args.url,
        port=args.port,
        username=args.username,
        password=args.password,
        measures_per_day=args.measures_per_day,
        frequency_min=args.frequency,
        years=args.years,
        clean=args.clean,
        enable_compaction=args.enable_compaction,
        batch_size=args.pipeline_batch_size,
        raw_retention_days=args.raw_retention_days
    )