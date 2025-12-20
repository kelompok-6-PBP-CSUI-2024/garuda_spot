from django.db import migrations, models
import re

MONTH_MAP = {
    "jan":1,"januari":1,
    "feb":2,"februari":2,
    "mar":3,"maret":3,
    "apr":4,"april":4,
    "mei":5,"may":5,
    "jun":6,"juni":6,
    "jul":7,"juli":7,
    "agu":8,"agustus":8,"aug":8,"august":8,
    "sep":9,"september":9,
    "okt":10,"oct":10,"oktober":10,"october":10,
    "nov":11,"november":11,
    "des":12,"dec":12,"desember":12,"december":12,
}

def parse_month(s: str):
    if not s: return None
    m = re.search(r"\b([A-Za-zÀ-ÿ\.]+)\b\s+20\d{2}", s)
    if not m:
        m = re.search(r"\d{1,2}\s+([A-Za-zÀ-ÿ\.]+)\s+20\d{2}", s)
    if not m: return None
    token = m.group(1).lower().strip(".")
    return MONTH_MAP.get(token)

def forwards(apps, schema_editor):
    News = apps.get_model("news", "News")
    for n in News.objects.all().only("id", "publish_date"):
        mon = parse_month(n.publish_date or "")
        if mon:
            News.objects.filter(id=n.id).update(published_month=mon)

def backwards(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [("news", "0002_seed_news_from_dataset")]
    operations = [
        migrations.AddField(
            model_name="news",
            name="published_month",
            field=models.PositiveSmallIntegerField(null=True, db_index=True),
        ),
        migrations.RunPython(forwards, backwards),
    ]
