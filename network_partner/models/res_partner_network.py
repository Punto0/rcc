# -*- coding: utf-8 -*-

import logging

# V8.0
from openerp import models, fields, api, osv, _

# V7.0
"""
import openerp
from openerp import SUPERUSER_ID, models
from openerp import tools
import openerp.exceptions
from openerp import api
from openerp.osv import fields, osv, expression
from openerp.service.security import check_super
from openerp.tools.translate import _
from openerp.http import request
"""

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'
    #'users': fields.many2many('res.users', 'res_groups_users_rel', 'gid', 'uid', 'Users'),
    networks_ids = fields.Many2many('network.partner', 'res_partner_network_rel', 'nid', 'uid', 'Partners network')

class partner_network(models.Model):
    _name = 'network.partner'
    _inherits = { 'res.partner' : 'network_partner_id', }
    _inherit = 'mail.thread'
    _description = 'Partners Networks'

    #Fields
    network_partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict')
    #'groups_id': fields.many2many('res.groups', 'res_groups_users_rel', 'uid', 'gid', 'Groups'),
    member_id = fields.Many2many('res.partner', 'res_partner_network_rel', 'uid', 'nid', "Partners" )



