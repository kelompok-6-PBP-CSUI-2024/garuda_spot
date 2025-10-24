from django.db import models
from datetime import date

# ==== pilihan posisi ====
POS_CHOICES = [
    ("", "—"),  # boleh kosong
    ("GK","GK"), ("LWB","LWB"), ("LB","LB"), ("CB","CB"), ("RB","RB"), ("RWB","RWB"),
    ("LM","LM"), ("CM","CM"), ("CDM","CDM"), ("CAM","CAM"), ("RM","RM"),
    ("LW","LW"), ("ST","ST"), ("RW","RW"),
]

class Player(models.Model):
    name = models.CharField(max_length=100)
    photo_url = models.URLField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    club = models.CharField(max_length=100, blank=True)
    height_cm = models.PositiveIntegerField(null=True, blank=True)

    # ==== NEW: tiga posisi ====
    position1 = models.CharField(max_length=4, choices=POS_CHOICES, blank=True, default="")
    position2 = models.CharField(max_length=4, choices=POS_CHOICES, blank=True, default="")
    position3 = models.CharField(max_length=4, choices=POS_CHOICES, blank=True, default="")

    # statistik
    caps = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def age(self):
        if not self.birth_date:
            return None
        t = date.today()
        return t.year - self.birth_date.year - ((t.month, t.day) < (self.birth_date.month, self.birth_date.day))

    @property
    def fname(self):
        return (self.name or "").split()[0] if self.name else ""

    @property
    def lname(self):
        parts = (self.name or "").split()
        return " ".join(parts[1:]) if len(parts) > 1 else ""

    # gabungkan posisi untuk tampilan overlay
    @property
    def positions_list(self):
        return [p for p in [self.position1, self.position2, self.position3] if p]

    @property
    def positions_display(self):
        return ", ".join(self.positions_list) if self.positions_list else ""

    # role untuk filter → ikut Position 1
    @property
    def role_tag(self):
        p = (self.position1 or "").upper()
        if p == "GK":
            return "GOALKEEPER"
        if p in {"LWB","LB","CB","RB","RWB"}:
            return "DEFENDER"
        if p in {"LM","CM","CDM","CAM","RM"}:
            return "MIDFIELDER"
        if p in {"LW","ST","RW"}:
            return "ATTACKER"
        return "MIDFIELDER"
    
    @property
    def positions_list(self):
        return [x for x in [self.position1, self.position2, self.position3] if x]

    def __str__(self): return self.name
