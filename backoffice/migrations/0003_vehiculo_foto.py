# Generated by Django 4.2.7 on 2025-01-30 00:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0002_transportista_ubicacion_vehiculo_traslado'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiculo',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='fotos_vehiculos/'),
        ),
    ]
