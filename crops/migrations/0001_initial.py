# Generated by Django 5.1.7 on 2025-03-17 17:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Crop",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("local_name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("growing_season", models.CharField(max_length=50)),
                ("water_requirement", models.TextField()),
                ("soil_type", models.CharField(max_length=100)),
                ("fertilizer_requirement", models.TextField()),
                ("pest_susceptibility", models.TextField()),
                ("harvesting_time", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="CropRecommendation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("soil_type", models.CharField(max_length=100)),
                ("season", models.CharField(max_length=50)),
                ("rainfall", models.FloatField()),
                ("temperature", models.FloatField()),
                ("success_rate", models.FloatField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "crop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="crops.crop"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="PlantingSchedule",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("sowing_time", models.CharField(max_length=100)),
                ("harvesting_time", models.CharField(max_length=100)),
                ("irrigation_schedule", models.TextField()),
                ("fertilizer_schedule", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "crop",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="crops.crop"
                    ),
                ),
            ],
        ),
    ]
