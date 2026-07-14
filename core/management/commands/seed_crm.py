from django.core.management.base import BaseCommand
from projects.models import Project, TaskList, Task, Tag
from documents.models import Document
from vendors.models import Vendor, VendorTag, VendorService
from finance.models import Invoice, Expense, CapitalInjection, ExpenseCategory
from accounts.models import Business
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Seeds the CRMbles database with initial project details, sample documents, and finance ledgers.'

    def handle(self, *args, **kwargs):
        # Safely clear only the specific seeded project and documents to avoid wiping custom user data
        Project.objects.filter(name="Dowitz Launch Workspace").delete()
        Document.objects.filter(title__in=["Dowitz Project Master Blueprint", "General Ideas & Brainstorming"]).delete()
        Vendor.objects.filter(name__in=["Sticker Mule", "Printify", "Namecheap", "Packlane"]).delete()
        VendorTag.objects.filter(name__in=["Stickers", "Packaging", "Apparel", "Custom Print", "Domain Host", "SSL"]).delete()
        
        # Clear all seeded financial records to avoid duplicates
        Invoice.objects.all().delete()
        Expense.objects.all().delete()
        CapitalInjection.objects.all().delete()
        
        self.stdout.write('Seeding Dowitz Project Workspace...')
        business, _ = Business.objects.get_or_create(
            name="Dowitz Workspace",
            defaults={"display_name": "Dowitz", "invoice_prefix": "DOW"}
        )
        
        # 1. Create the Dowitz Project
        dowitz = Project.objects.create(
            business=business,
            name="Dowitz Launch Workspace",
            description="Master workspace covering operations, task lists, and documentation sheets for the Dowitz project launch and business structure."
        )
        
        # Create default colored tags
        tag_marketing = Tag.objects.create(project=dowitz, name="Marketing", color="#ec4899")
        tag_technical = Tag.objects.create(project=dowitz, name="Technical", color="#0ea5e9")
        tag_admin = Tag.objects.create(project=dowitz, name="Admin", color="#f59e0b")
        tag_finance = Tag.objects.create(project=dowitz, name="Finance", color="#10b981")
        tag_urgent = Tag.objects.create(project=dowitz, name="Urgent", color="#8b5cf6")
        
        # 2. Create the list columns
        immediate_list = TaskList.objects.create(
            project=dowitz,
            name="Phase 1: Brand & Launch",
            description="High-priority steps required to get the business online."
        )
        
        finance_list = TaskList.objects.create(
            project=dowitz,
            name="Phase 2: Administrative Setup",
            description="Setting up tax filings, receipt structures, and invoices."
        )
        
        growth_list = TaskList.objects.create(
            project=dowitz,
            name="Phase 3: Sales & Growth",
            description="Outreach pipelines and client onboarding plans."
        )
        
        # 3. Populate Task list items
        # Brand tasks
        task_domain = Task.objects.create(
            list=immediate_list,
            title="Secure dowitz.com domain name",
            description="Verify availability of domain. Connect custom DNS and mailboxes.",
            priority="HIGH",
            status="TODO",
            due_date=timezone.now().date() + datetime.timedelta(days=2)
        )
        task_domain.tags.add(tag_technical, tag_urgent)
        
        task_blueprint = Task.objects.create(
            list=immediate_list,
            title="Draft initial project blueprint note",
            description="Written in markdown. Coordinated key features, goals, and modular blueprints.",
            priority="HIGH",
            status="DONE",
            due_date=timezone.now().date() - datetime.timedelta(days=1)
        )
        task_blueprint.tags.add(tag_admin, tag_marketing)
        
        task_logo = Task.objects.create(
            list=immediate_list,
            title="Design brand logo and color codes",
            description="Formulate primary visual styles (Slate background with Indigo highlights).",
            priority="MEDIUM",
            status="PROGRESS"
        )
        task_logo.tags.add(tag_marketing)
        
        # Admin tasks
        task_bank = Task.objects.create(
            list=finance_list,
            title="Open business checking account",
            description="Research local credit unions or business-focused fintech options (e.g. Mercury, Novo) for zero fee accounts.",
            priority="MEDIUM",
            status="TODO",
            due_date=timezone.now().date() + datetime.timedelta(days=7)
        )
        task_bank.tags.add(tag_finance, tag_urgent)
        
        task_receipt = Task.objects.create(
            list=finance_list,
            title="Set up digital receipt archive directory",
            description="Structure a drive or system folder to scan receipts and tax records.",
            priority="LOW",
            status="TODO"
        )
        task_receipt.tags.add(tag_finance, tag_admin)
        
        # Growth tasks
        task_clients = Task.objects.create(
            list=growth_list,
            title="Build target client list",
            description="Assemble directory of first 20 local business targets that need CRMbles custom configurations.",
            priority="MEDIUM",
            status="TODO",
            due_date=timezone.now().date() + datetime.timedelta(days=14)
        )
        task_clients.tags.add(tag_marketing, tag_urgent)
        
        self.stdout.write('Seeding Document Blueprints...')
        
        # 4. Create sample Document (Note)
        blueprint_content = """# Dowitz Project Master Blueprint

Welcome to the **Dowitz** business launch blueprint. This document compiles our strategies, operational scopes, and plans to build out our service model.

## 1. Project Overview
The Dowitz initiative aims to build a modern, visual-first client relationship and project pipeline tool. 
To facilitate rapid expansion, we're building a modular application codebase.

### Core Value Pillars
* **Strict Modularity**: Build a lightweight core dashboard first, then plug in billing and clients later.
* **Premium User Experience**: Custom dark theme, fluid list operations, and high-fidelity real-time feedback.
* **Open Source Portability**: Python, Django, and clean SQLite/Postgres options ensure seamless migrations.

---

## 2. Launch Strategy Checklist

* [x] **Scaffold Project Core**: Python virtualenv, settings config, base CSS templates.
* [x] **Implement To-Dos Module**: Drag-and-drop or interactive lists, database CRUD.
* [x] **Configure Note Space**: Server-compiled Markdown notes with side-by-side editing.
* [ ] **Add Clients App** *(Coming Soon)*: Formulate customer tracking tables.
* [ ] **Add Billing App** *(Coming Soon)*: Automated receipt matching and PDF invoices.

---

## 3. Financial Setup Notes
Setting up an elegant tracking workflow early will save massive headaches during tax seasons.

```python
# Receipt Processing Pipeline Idea
def process_receipt(file_path):
    # 1. OCR scanned invoice
    # 2. Extract tax-deductible categories
    # 3. Associate with correct client or project
    print(f"Receipt parsed successfully: {file_path}")
```

> [!TIP]
> Keep receipts grouped by quarter (Q1-Q4) and double check tax categories (Utilities, Travel, Hardware, Consulting).
"""
        
        Document.objects.create(
            business=business,
            project=dowitz,
            title="Dowitz Project Master Blueprint",
            content=blueprint_content.strip()
        )
        
        # Create a second general note
        Document.objects.create(
            business=business,
            title="General Ideas & Brainstorming",
            content="""# Ideas & Scrapbook

Use this place to scribble quick ideas that are not yet bound to a specific project.

## Receipts OCR Idea
We can plug in Python's `pytesseract` or a basic machine learning scanner to auto-extract:
- Merchant Name
- Transaction Date
- Net Total
- Tax Percentage

This will allow compiling Q4 spreadsheets automatically!
"""
        )
        
        self.stdout.write('Seeding Vendor Directory & Tags...')
        
        # Create default Vendor Tags
        vtag_stickers = VendorTag.objects.create(business=business, name="Stickers", color="#ec4899")
        vtag_packaging = VendorTag.objects.create(business=business, name="Packaging", color="#f59e0b")
        vtag_apparel = VendorTag.objects.create(business=business, name="Apparel", color="#0ea5e9")
        vtag_print = VendorTag.objects.create(business=business, name="Custom Print", color="#8b5cf6")
        vtag_host = VendorTag.objects.create(business=business, name="Domain Host", color="#10b981")
        vtag_ssl = VendorTag.objects.create(business=business, name="SSL", color="#ef4444")
        
        # Seed Vendors
        v_stickermule = Vendor.objects.create(
            business=business,
            name="Sticker Mule",
            description="Premium custom stickers, labels, and mailers.",
            website="https://stickermule.com",
            email="info@stickermule.com",
            phone="",
            notes="Fast shipping, premium quality vinyl stickers. Great customer service and weekly promos.",
            has_purchased=True
        )
        v_stickermule.tags.add(vtag_stickers, vtag_packaging, vtag_print)
        
        # Seed services for Sticker Mule
        VendorService.objects.create(
            vendor=v_stickermule,
            name="Die Cut Stickers",
            description="Premium thick vinyl stickers with a beautiful matte finish. Water-resistant and durable.",
            price="$58.00 for 50 items",
            notes="Order during weekly promos for best pricing."
        )
        VendorService.objects.create(
            vendor=v_stickermule,
            name="Custom Poly Mailers",
            description="Sturdy, lightweight shipping envelopes printed with brand styling.",
            price="$1.80 per mailer",
            notes="Bulk options reduce price to $0.85."
        )
        
        v_printify = Vendor.objects.create(
            business=business,
            name="Printify",
            description="On-demand printing for apparel, hats, and merchandise.",
            website="https://printify.com",
            email="support@printify.com",
            phone="",
            notes="Good catalog for winter hats and t-shirts. Excellent dropshipping integrations with standard pricing.",
            has_purchased=False
        )
        v_printify.tags.add(vtag_apparel, vtag_print)
        
        # Seed services for Printify
        VendorService.objects.create(
            vendor=v_printify,
            name="Winter Beanie Hat",
            description="Double-sided embroidery winter beanies, 100% acrylic.",
            price="$12.50 per unit",
            notes="Shipping averages $4.50 within US."
        )
        VendorService.objects.create(
            vendor=v_printify,
            name="Trucker Hoodie",
            description="Heavy blend cotton/poly fleece hoodie with custom print options.",
            price="$22.00 per unit",
            notes="Excellent reviews for fit and print durability."
        )
        
        v_namecheap = Vendor.objects.create(
            business=business,
            name="Namecheap",
            description="Domain registrations, DNS, and SSL security.",
            website="https://namecheap.com",
            email="sales@namecheap.com",
            phone="",
            notes="Dowitz domain registered here. Excellent renewal rates and free WHOIS privacy support.",
            has_purchased=True
        )
        v_namecheap.tags.add(vtag_host, vtag_ssl)
        
        # Seed services for Namecheap
        VendorService.objects.create(
            vendor=v_namecheap,
            name="Domain Registration",
            description=".com domain extension annual registration fee.",
            price="$8.98 / year",
            notes="Includes free lifetime WHOIS Privacy protection."
        )
        VendorService.objects.create(
            vendor=v_namecheap,
            name="PositiveSSL",
            description="Fast domain validation SSL certificate.",
            price="$5.99 / year",
            notes="Perfect for securing basic client applications."
        )
        
        v_packlane = Vendor.objects.create(
            business=business,
            name="Packlane",
            description="High-quality custom branded packaging boxes.",
            website="https://packlane.com",
            email="hello@packlane.com",
            phone="",
            notes="Great custom shipping boxes for welcome kits. High quality, premium finishes, but a bit expensive.",
            has_purchased=False
        )
        v_packlane.tags.add(vtag_packaging)
        
        self.stdout.write('Seeding Finance Ledger Records...')
        
        # 5. Clear and Seed Expense Categories
        ExpenseCategory.objects.all().delete()
        cat_materials = ExpenseCategory.objects.create(business=business, name="Manufacturing & Raw Materials", color="#ec4899")
        cat_shipping = ExpenseCategory.objects.create(business=business, name="Shipping & Fulfillment", color="#f59e0b")
        cat_marketing = ExpenseCategory.objects.create(business=business, name="Marketing & Ads", color="#8b5cf6")
        cat_software = ExpenseCategory.objects.create(business=business, name="Software & SaaS", color="#0ea5e9")
        cat_office = ExpenseCategory.objects.create(business=business, name="Office Supplies", color="#10b981")
        cat_travel = ExpenseCategory.objects.create(business=business, name="Travel & Client Meetings", color="#ef4444")
        cat_taxes = ExpenseCategory.objects.create(business=business, name="Taxes & Fees", color="#64748b")
        cat_other = ExpenseCategory.objects.create(business=business, name="Other Operations", color="#6366f1")

        # 6. Seed Invoices
        Invoice.objects.create(
            business=business,
            client_name="Acme Branding Corp",
            title="Logo Assets & Web Interface Style Guide",
            project=dowitz,
            amount=450.00,
            invoice_date=timezone.now().date() - datetime.timedelta(days=12),
            status="PAID",
            notes="Paid via bank wire transfer. Assets delivered successfully."
        )
        Invoice.objects.create(
            business=business,
            client_name="Local Pizza Parlor",
            title="Interactive Menu Web App Development",
            amount=1200.00,
            invoice_date=timezone.now().date() - datetime.timedelta(days=3),
            due_date=timezone.now().date() + datetime.timedelta(days=14),
            status="SENT",
            notes="Initial deposit invoice sent to client. Expect check or wire."
        )

        # 7. Seed Expenses
        Expense.objects.create(
            business=business,
            title="Annual Domain Registration (dowitz.com)",
            amount=8.98,
            expense_date=timezone.now().date() - datetime.timedelta(days=10),
            category=cat_software,
            status="PAID",
            vendor=v_namecheap,
            notes="Purchased .com domain and got lifetime WHOIS privacy free."
        )
        Expense.objects.create(
            business=business,
            title="Bulk Die Cut Stickers (Promo Pack)",
            amount=58.00,
            expense_date=timezone.now().date() - datetime.timedelta(days=5),
            category=cat_materials,
            status="PAID",
            vendor=v_stickermule,
            notes="Sourced matte vinyl logo stickers for launch promotion giveaway."
        )
        Expense.objects.create(
            business=business,
            title="Figma Professional Plan",
            amount=15.00,
            expense_date=timezone.now().date() - datetime.timedelta(days=8),
            category=cat_software,
            status="PAID",
            vendor_name_fallback="Figma Inc",
            notes="Interactive design drafting and wireframe blueprints subscription."
        )

        # 8. Seed Capital Injections
        CapitalInjection.objects.create(
            business=business,
            source="Personal Savings Account",
            injection_type="PERSONAL_OUT_OF_POCKET",
            amount=300.00,
            injection_date=timezone.now().date() - datetime.timedelta(days=15),
            notes="Initial bootstrapping capital transferred to business account to cover domains and initial setup."
        )
        CapitalInjection.objects.create(
            business=business,
            source="Uncle Dave",
            injection_type="LOAN",
            amount=1000.00,
            injection_date=timezone.now().date() - datetime.timedelta(days=14),
            is_repaid=False,
            notes="Friendly interest-free loan to fund initial custom material runs. Plan to repay within 6 months."
        )
        
        self.stdout.write(self.style.SUCCESS('CRMbles seeded successfully!'))
