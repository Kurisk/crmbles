from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0004_industry_expense_items"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvoiceLineItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="line_items", to="finance.invoice")),
            ],
            options={
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="ExpenseLineItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expense", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="line_items", to="finance.expense")),
            ],
            options={
                "ordering": ["id"],
            },
        ),
    ]
