APP_VERSION = "0.2.4"
SUPPORT_EMAIL = "dowitzgame@gmail.com"

LATEST_UPDATE = {
    "title": "Mobile Sidebar And File Attachments",
    "date": "July 18, 2026",
    "summary": "CRMbles now has a cleaner mobile navigation shell plus file uploads and note attachments.",
    "items": [
        "Added a mobile menu button that opens and collapses the sidebar without squeezing the workspace.",
        "Added a File Library to Documents and Ideas for standalone workspace uploads.",
        "Added file attachments to follow-up notes, including support for Save Note and Save Changes.",
        "Added attached file links to note hover previews, Notes Glance, and the task note editor.",
    ],
}


FAQ_SECTIONS = [
    {
        "title": "Getting Started",
        "items": [
            {
                "question": "What is CRMbles?",
                "answer": "CRMbles is a private-first business workspace that keeps projects, tasks, documents, vendors, clients, expenses, invoices, and account access in one focused command center.",
            },
            {
                "question": "Who is CRMbles for?",
                "answer": "It is built for small businesses, internal teams, founders, operators, and solo owners who need a practical operations hub without spreading daily work across disconnected tools.",
            },
            {
                "question": "Is CRMbles public yet?",
                "answer": "Not yet. The current product is being used and refined privately first. Potential client access can be requested by email while the public onboarding flow is still being prepared.",
            },
            {
                "question": "How do I request access?",
                "answer": "Use the contact link on this page to email dowitzgame@gmail.com with your name, business, intended use, and the areas you want to test first.",
            },
            {
                "question": "Can multiple businesses use the same login?",
                "answer": "Yes. CRMbles supports business workspaces and business switching, so a user can be connected to more than one workspace when access is granted.",
            },
        ],
    },
    {
        "title": "Workspace And Accounts",
        "items": [
            {
                "question": "What does the dashboard show?",
                "answer": "The dashboard summarizes active projects, pending tasks, completed tasks, saved documents, pending invoices, and pending expenses based on the features a user can access.",
            },
            {
                "question": "Can access be limited by user?",
                "answer": "Yes. Account managers can grant or withhold access to projects, documents, vendors, clients, and finance areas for each business member.",
            },
            {
                "question": "What is an account manager?",
                "answer": "An account manager can manage users, business workspaces, and feature access. This keeps sensitive sections like finance visible only to the people who need them.",
            },
            {
                "question": "Can users update their own profile?",
                "answer": "Yes. Users can maintain profile details such as their name and photo from the profile area.",
            },
            {
                "question": "Can the app support private internal use before public launch?",
                "answer": "Yes. The current posture is private-first, with controlled users and workspaces before wider customer-facing onboarding is opened.",
            },
        ],
    },
    {
        "title": "Projects And Tasks",
        "items": [
            {
                "question": "What project tools are included?",
                "answer": "Projects can hold task lists, tasks, notes, due dates, priorities, tags, completed-task views, and pinned items for high-priority work.",
            },
            {
                "question": "Can I track pending and completed tasks separately?",
                "answer": "Yes. CRMbles includes filtered task views for pending and completed work, plus dashboard links that jump directly into those lists.",
            },
            {
                "question": "Can important tasks be pinned?",
                "answer": "Yes. Projects and tasks support pinning so the most important work stays at the top of the relevant views.",
            },
            {
                "question": "Does CRMbles replace a full project management suite?",
                "answer": "It is intentionally lighter. The goal is to keep the work visible and actionable inside the same place where documents, vendors, clients, and finance live.",
            },
        ],
    },
    {
        "title": "Documents And Notes",
        "items": [
            {
                "question": "What can documents be used for?",
                "answer": "Documents can store notes, plans, decisions, checklists, ideas, reference details, and working drafts tied to a business workspace.",
            },
            {
                "question": "Does CRMbles support Markdown?",
                "answer": "Yes. Documents use a Markdown-friendly editor with preview styling for headings, lists, code blocks, quotes, and checklists.",
            },
            {
                "question": "Can documents be pinned?",
                "answer": "Yes. Important documents can be pinned so they stay easy to find.",
            },
            {
                "question": "Can documents be filtered or searched?",
                "answer": "Document workflows are built around quick access to recent and important notes. Broader document search can be expanded as usage grows.",
            },
        ],
    },
    {
        "title": "Vendors, Clients, And Finance",
        "items": [
            {
                "question": "How are vendors connected to finance?",
                "answer": "Vendors and finance are meant to stay tied together. Vendor records can feed into expenses, invoices, services, and itemized charge workflows.",
            },
            {
                "question": "What is the Item / Service field?",
                "answer": "Item / Service describes the specific thing being bought, sold, billed, or tracked. It is separate from the accounting category.",
            },
            {
                "question": "Can invoices and expenses have multiple charges?",
                "answer": "Yes. CRMbles supports line items for invoices and expenses, so one parent record can hold multiple charges while still rolling up to a total.",
            },
            {
                "question": "Can I track clients?",
                "answer": "Yes. CRMbles has a client section that can be granted separately from vendor and finance access.",
            },
            {
                "question": "Does CRMbles move money?",
                "answer": "No. The current finance direction is recordkeeping and visibility. Future bank-linking would be read-only monitoring for incoming and outgoing money flow, not money movement.",
            },
            {
                "question": "Can I filter finance tables?",
                "answer": "Yes. Finance views include lightweight client-side filtering for invoices, expenses, and capital records.",
            },
        ],
    },
    {
        "title": "Security, Data, And Roadmap",
        "items": [
            {
                "question": "Is sensitive finance data protected by permissions?",
                "answer": "Yes. Finance is a separate feature permission, so users without finance access do not see finance dashboard links or finance metrics.",
            },
            {
                "question": "Where is CRMbles intended to run?",
                "answer": "The current deployment path targets a private subdomain first, with infrastructure files included for a VPS deployment.",
            },
            {
                "question": "What domain is planned?",
                "answer": "The future public domain target is crmbles.com. The private deployment target documented in the repo is crmbles.skulkabout.com.",
            },
            {
                "question": "Will there be subscriptions later?",
                "answer": "Possibly. The immediate goal is to use the product privately, improve it through real workflows, and only then decide how public access or subscriptions should work.",
            },
            {
                "question": "Where can I see what changed recently?",
                "answer": "Use the Latest Update link in the footer to view the current version number and the newest product changes.",
            },
        ],
    },
]
