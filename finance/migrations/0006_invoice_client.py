from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('finance', '0005_invoice_expense_line_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='client',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='clients.client'),
        ),
    ]
