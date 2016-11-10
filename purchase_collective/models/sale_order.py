# -*- coding: utf-8 -*-
import random

from openerp import SUPERUSER_ID
import openerp.addons.decimal_precision as dp
from openerp.osv import osv, orm, fields
from openerp.addons.web.http import request
from openerp.tools.translate import _


class sale_order(osv.Model):
    _inherit = "sale.order"

    _columns = {
        'cp_order_id' : fields.many2one(
        'purchase_collective.order',
        string='Parent Collective Purchase',
        help='The collective purchase wich this order belongs',
        ondelete='restrict'),
        'is_cp' : fields.boolean(string="Is part of a Collective Purchase"), 
    }

