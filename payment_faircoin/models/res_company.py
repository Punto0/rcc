# -*- coding: utf-8 -*-

from openerp.osv import fields, osv


class ResCompany(osv.Model):
    _inherit = "res.company"

    def _get_faircoin_account(self, cr, uid, ids, name, arg, context=None):
        company = self.pool['res.users'].browse(cr, uid, uid, context=context).company_id
        return company.faircoin_account

    def _set_faircoin_account(self, cr, uid, id, name, value, arg, context=None):
        company = self.pool['res.users'].browse(cr, uid, uid, context=context).company_id
        faircoin_account = self.browse(cr, uid, id, context=context).faircoin_account
        company.write(cr, uid, company.id, {'faircoin_account': value}, context=context)
        return True

    _columns = {
        'faircoin_account': fields.char('FairCoin address'),
        #'faircoin_account': fields.function(
        #    _get_faircoin_account,
        #    fnct_inv=_set_faircoin_account,
        #     nodrop=True,
        #     type='char', string='Faircoin Account',
        #     help="Faircoin address where the FairCoins will be sent. It's not publicly avalaible"
        #),
    }
