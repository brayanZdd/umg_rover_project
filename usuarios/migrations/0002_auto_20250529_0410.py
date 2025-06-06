# Generated by Django 3.2.19 on 2025-05-29 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coreografia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('descripcion', models.TextField()),
                ('codigo', models.TextField()),
                ('audio_file', models.CharField(max_length=100)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_modificacion', models.DateTimeField(auto_now=True)),
                ('activa', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'Coreografía',
                'verbose_name_plural': 'Coreografías',
                'db_table': 'coreografias',
                'ordering': ['nombre'],
            },
        ),
        migrations.AlterModelOptions(
            name='ingreso',
            options={'managed': False},
        ),
        migrations.AlterModelOptions(
            name='rol',
            options={'managed': False},
        ),
        migrations.AlterModelOptions(
            name='usuario',
            options={'managed': False},
        ),
    ]
