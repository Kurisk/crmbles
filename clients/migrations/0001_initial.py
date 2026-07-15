from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0004_business_pins'),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('color', models.CharField(default='#0ea5e9', max_length=7)),
                ('business', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='client_tags', to='accounts.business')),
            ],
            options={
                'ordering': ['name'],
                'unique_together': {('name', 'business')},
            },
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('company', models.CharField(blank=True, max_length=160)),
                ('contact_name', models.CharField(blank=True, max_length=120)),
                ('website', models.URLField(blank=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('status', models.CharField(choices=[('LEAD', 'Lead'), ('ACTIVE', 'Active Client'), ('PAST', 'Past Client'), ('INACTIVE', 'Inactive')], default='LEAD', max_length=20)),
                ('source', models.CharField(blank=True, help_text='Where this client or lead came from.', max_length=120)),
                ('notes', models.TextField(blank=True)),
                ('is_pinned', models.BooleanField(default=False)),
                ('pinned_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='clients', to='accounts.business')),
                ('tags', models.ManyToManyField(blank=True, related_name='clients', to='clients.clienttag')),
            ],
            options={
                'ordering': ['-is_pinned', '-pinned_at', 'name'],
            },
        ),
        migrations.CreateModel(
            name='ClientOpportunity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=140)),
                ('description', models.TextField(blank=True)),
                ('estimate', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('WON', 'Won'), ('PAUSED', 'Paused'), ('LOST', 'Lost')], default='OPEN', max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opportunities', to='clients.client')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
