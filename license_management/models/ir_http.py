from odoo import models, exceptions, _

class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _authenticate(cls, endpoint):
        res = super()._authenticate(endpoint)
        
        # Check license before allowing any request
        # If expired and user is not admin → raise AccessDenied
        from odoo.http import request
        if request and request.env:
            ICP = request.env['ir.config_parameter'].sudo()
            status = ICP.get_param('license.status', 'draft')
            mode = ICP.get_param('license.mode', 'block')
            admin_uid_str = ICP.get_param('license.admin_uid', '2')
            try:
                admin_uid = int(admin_uid_str)
            except ValueError:
                admin_uid = 2
                
            if status in ['expired', 'suspended', 'invalid'] and mode == 'block':
                if request.env.user.id != admin_uid and request.env.user.id != 1:
                    # Allow access to web.login and our expired page
                    if request.httprequest.path not in ['/web/login', '/license/expired', '/web/session/logout']:
                        raise exceptions.AccessDenied(_('License expired. Access blocked.'))
        return res
