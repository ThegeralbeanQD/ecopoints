# Generated by Django 2.1.5 on 2025-03-26 14:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ecopoints', '0014_userprofile_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='LikedCategory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ecopoints.Task')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='liked_categories',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='picture',
        ),
    ]
