{
    'name': 'Hudson Accounting',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'A lightweight accounting module to track daily income, expenses, and P&L.',
    'description': """
        Simple Accounting Module
        ========================
        * Track daily income and expenses
        * Highlight profit/loss with Red/Green color coding
        * Powerful pivot and graph views for analytics
        * Generate custom PDF Ledgers by date range
    """,
    'author': 'Hudson Software Solutions Pvt ltd',
    'depends': ['base', 'web', 'cargo_manual_invoicing'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/simple_accounting_menus.xml',
        'views/simple_accounting_category_views.xml',
        'views/simple_accounting_transaction_views.xml',
        'report/simple_accounting_reports.xml',
        'report/simple_accounting_report_template.xml',
        'wizard/simple_accounting_report_wizard_views.xml',
        'wizard/smsa_settlement_report_wizard_views.xml',
        'report/smsa_settlement_report_template.xml',
        'data/cron_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
