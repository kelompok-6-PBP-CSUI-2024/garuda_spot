from django.db import migrations
from pathlib import Path
from django.conf import settings
import json

def load_news(apps, schema_editor):
    News = apps.get_model("news", "News")

    try:
        base_dir = Path(settings.BASE_DIR)
    except Exception:
        base_dir = Path(__file__).resolve().parents[3]

    dataset_path = base_dir / "static" / "data" / "dataset.json"
    if not dataset_path.exists():
        return

    try:
        data = json.loads(dataset_path.read_text(encoding="utf-8"))
    except Exception:
        return

    if News.objects.exists():
        return

    objs = []
    for x in data:
        objs.append(News(
            title=x.get("title", ""),
            category=x.get("category", "General"),
            publish_date=x.get("publish_date", ""),
            content=x.get("content", ""),
        ))
    if objs:
        News.objects.bulk_create(objs, ignore_conflicts=True)

def unload_news(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("news", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(load_news, reverse_code=unload_news),
    ]
