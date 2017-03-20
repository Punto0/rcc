# -*- coding: utf-8 -*-

#added for onchange_product_id
import pytz
import logging

from openerp import models, fields, api, osv, _, SUPERUSER_ID
from openerp.exceptions import Warning

from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import attrgetter
from openerp.tools.safe_eval import safe_eval as eval
import openerp.addons.decimal_precision as dp
from openerp.osv.orm import browse_record_list, browse_record, browse_null
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from openerp.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)

class PurchaseCollectiveOrder(models.Model):
    _name = 'purchase_collective.order'
    _inherit = ['purchase.order',]  
    _description = 'Collective Purchases'
    
    sales_order_lines = fields.One2many('sale.order','cp_order_id','Collective Order Lines',
                                         states={'approved':[('readonly',True)],'done':[('readonly',True)]},
                                         copy=False )

    deadline_date = fields.Date(string='Order Deadline', required=True, help="End date of the order. Place your orders before this date")
    
    #amount_untaxed = fields.Float('Amount untaxed',compute='update_total',store=True)
    #amount_tax = fields.Float('Taxes',compute='update_total',store=True)
    amount_total = fields.Float('Amount Total',compute='update_total',store=True)

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', size=24)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    mobile = fields.Char('Mobile')
    qty_min = fields.Float('Minimun product quantity by single sale', required=True, help='Minimun quantity allowed by each single sale order in product quantity')
    notes = fields.Text('Description for the collective purchase', translate=True)
    progress = fields.Float('Progress on this Collective Purchase',compute='update_total',store=True)
    qty_total = fields.Float('Minimum quantity to execute the order in currency', required=True)
    CP_STATE_SELECTION = [
        ('draft', 'Open'),
        ('sent', 'Sent'),
        ('bid', 'Bid Received'),
        ('confirmed', 'Closed'),
        ('approved', 'Closed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]
    state = fields.Selection(CP_STATE_SELECTION, 'Status', readonly=True,
                                  help="The status of the collective purchase order. "
                                       "An 'Open' order accepts new single orders on it. "
                                       "A 'Closed' order does not accept new single orders."
                                       "A 'Cancelled' order is an order that it has not executed and the funds are returning to the customers.",
                                  select=True, copy=False)

    @api.multi
    def button_details(self):
       context = self.env.context.copy()
       view_id = self.env.ref(
            'sale.'
            'view_order_form').id

       context['default_is_cp'] = True 
       context['default_cp_order_id'] = self.id 
       context['supplier'] = self.partner_id
       #context['default_partner_id'] = self.partner_id.id
       context['default_pricelist_id'] = self.pricelist_id.id
       context['default_order_date'] = self.date_order
       context['default_date_planned'] = self.deadline_date
       context['view_buttons'] = True
       #context['fiscal_position'] = self.fiscal_position
       #context['state'] = self.state
       #context['parent'] = self.id

       #partial_id = self.pool.get("purchase.collective.order.line").create(context=context)

       view = {
            'name': _('Details'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': False,
            #'res_id': partial_id,
            'context': context
       }
       return view

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order').browse(cr, uid, ids, context=context):
            result[line.id] = True
        return result.keys()
    
    def create(self, cr, uid, vals, context=None):
        #logging.info("Creating order %s" %vals)  
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase_collective.order', context=context) or '/'
        if not vals.get('location_id'):
            for user_obj in self.pool.get('res.users').browse(cr, uid, [uid], context =context):
                vals['location_id'] = user_obj.partner_id.property_stock_supplier.id
                logging.info('adding location info %s' %vals.get('location_id'))
        if not vals.get('pricelist_id'):        
            for user_obj in self.pool.get('res.users').browse(cr, uid, [uid], context =context):
                vals['pricelist_id'] = user_obj.partner_id.property_product_pricelist_purchase.id
                logging.info('adding pricelist %s' %vals.get('pricelist_id'))

        context = dict(context or {}, mail_create_nolog=True)
        order =  super(PurchaseCollectiveOrder, self).create(cr, uid, vals, context=context)
        #self.message_post(cr, uid, [order], body=("RFQ created"), context=context)
        return order

    def unlink(self, cr, uid, ids, context=None):
        purchase_orders = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in purchase_orders:
            if s['state'] in ['draft','cancel']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'), _('In order to delete a purchase order, you must cancel it first.'))

        # automatically sending subflow.delete upon deletion
        self.signal_workflow(cr, uid, unlink_ids, 'purchase_cancel')

        return super(PurchaseCollectiveOrder, self).unlink(cr, uid, unlink_ids, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        # FORWARDPORT UP TO SAAS-6
        new_id = super(PurchaseCollectiveOrder, self).copy(cr, uid, id, default=default, context=context)
        for po in self.browse(cr, uid, [new_id], context=context):
            for line in po.order_line:
                vals = self.pool.get('purchase_collective.order_line').onchange_product_id(
                    cr, uid, line.id, po.pricelist_id.id, line.product_id.id, line.product_qty,
                    line.product_uom.id, po.partner_id.id, date_order=po.date_order, context=context
                )
                if vals.get('value', {}).get('date_planned'):
                    line.write({'date_planned': vals['value']['date_planned']})
        return new_id
   
    def set_order_line_status(self, cr, uid, ids, status, context=None):
        """ 
        line = self.pool.get('purchase_collective.order_line')
        order_line_ids = []
        proc_obj = self.pool.get('procurement.order')
        for order in self.browse(cr, uid, ids, context=context):
            if status in ('draft', 'cancel'):
                order_line_ids += [po_line.id for po_line in order.order_line]
            else: # Do not change the status of already cancelled lines
                order_line_ids += [po_line.id for po_line in order.order_line if po_line.state != 'cancel']
        if order_line_ids:
            line.write(cr, uid, order_line_ids, {'state': status}, context=context)
        if order_line_ids and status == 'cancel':
            procs = proc_obj.search(cr, uid, [('purchase_line_id', 'in', order_line_ids)], context=context)
            if procs:
                proc_obj.write(cr, uid, procs, {'state': 'exception'}, context=context)
        """
        return True
    
    def wkf_confirm_order(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            for line in po.sales_order_lines:
                _logger.info("line.state : %s" %line.state)       
                if line.state in ['draft','cancel']:
                    line.unlink()
            po.update_total()
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid}, context=context)
        return True

    def wkf_action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        self.set_order_line_status(cr, uid, ids, 'cancel', context=context)
        return True 

    def action_cancel(self, cr, uid, ids, context=None):
        _logger.info("cancel %s" %ids)    
        for purchase in self.browse(cr, uid, ids, context=context):
            for pick in purchase.picking_ids:
                for move in pick.move_lines:
                    if pick.state == 'done':
                        raise osv.except_osv(
                            _('Unable to cancel the purchase order %s.') % (purchase.name),
                            _('You have already received some goods for it.  '))
            self.pool.get('stock.picking').action_cancel(cr, uid, [x.id for x in purchase.picking_ids if x.state != 'cancel'], context=context)
            for inv in purchase.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise osv.except_osv(
                        _('Unable to cancel this purchase order.'),
                        _('You must first cancel all invoices related to this purchase order.'))
            self.pool.get('account.invoice') \
                .signal_workflow(cr, uid, map(attrgetter('id'), purchase.invoice_ids), 'invoice_cancel')
        self.signal_workflow(cr, uid, ids, 'purchase_cancel')
        self.wkf_action_cancel(cr, uid, ids, context=context)
        return True

    def _set_po_lines_invoiced(self, cr, uid, ids, context=None):
        """
        for po in self.browse(cr, uid, ids, context=context):
            is_invoiced = []
            if po.invoice_method == 'picking':
                # We determine the invoiced state of the PO line based on the invoiced state
                # of the associated moves. This should cover all possible cases:
                # - all moves are done and invoiced
                # - a PO line is split into multiple moves (e.g. if multiple pickings): some
                #   pickings are done, some are in progress, some are cancelled
                for po_line in po.order_line:
                    if (po_line.move_ids and
                            all(move.state in ('done', 'cancel') for move in po_line.move_ids) and
                            not all(move.state == 'cancel' for move in po_line.move_ids) and
                            all(move.invoice_state == 'invoiced' for move in po_line.move_ids if move.state == 'done')
                            and po_line.invoice_lines and all(line.invoice_id.state not in ['draft', 'cancel'] for line in po_line.invoice_lines)):
                        is_invoiced.append(po_line.id)
                    elif po_line.product_id.type == 'service':
                        is_invoiced.append(po_line.id)
            else:
                for po_line in po.order_line:
                    if (po_line.invoice_lines and 
                            all(line.invoice_id.state not in ['draft', 'cancel'] for line in po_line.invoice_lines)):
                        is_invoiced.append(po_line.id)
            if is_invoiced:
                self.pool['purchase_collective.order_line'].write(cr, uid, is_invoiced, {'invoiced': True})
            workflow.trg_write(uid, 'purchase_colective.order', po.id, cr)
         """

    def action_picking_create(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids):
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'origin': order.name
            }
            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            # esta llamada da fallo
            #self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
        return picking_id

    def _get_picking_in(self, cr, uid, context=None):
        obj_data = self.pool.get('ir.model.data')
        type_obj = self.pool.get('stock.picking.type')
        user_obj = self.pool.get('res.users')
        company_id = user_obj.browse(cr, uid, uid, context=context).company_id
        #logging.info("_get_picking_in company_id %s %s" %(company_id.id,company_id.parent_id.id))
        types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id.id)], context=context)
        if not types:
            types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', False)], context=context)
        if not types: # En fairmarket no hay definidos almacenes por compañia, usamos la madre
            types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id.parent_id.id)], context=context)
            #if not types:
                #raise osv.except_osv(_('Error!'), _("Make sure you have at least an incoming picking type defined"))
        #logging.info("Types %s" %types)
        return types[0]
    
    _defaults = {
        #'date_order': fields.datetime.now,
        #'state': 'draft',
        #'name': '/',
        #'shipped': 0,
        #'invoice_method': 'order',
        #'invoiced': 0,
        #'pricelist_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').browse(cr, uid, context['partner_id']).property_product_pricelist_purchase.id,
        #'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'purchase_collective.order', context=c),
        #'currency_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id,
        'picking_type_id': _get_picking_in,
    }

    # Actualizamos el total de la orden colectiva y subscribimos el usuario al muro
    @api.multi 
    def action_button_confirm_sale(self, partner_id=None):
        self.update_total()
        if partner_id: 
            #self.message_post(body=("Order line confirmed"))
            self.message_subscribe(partner_ids=[(partner_id)])
            #self.message_subscribe(partner_ids=[(order.partner_id.id])
        return True 

    # The update link in the cp form calls to the old api
    def update_total_oldapi(self, cr, uid, ids, context=None):
        orders = self.browse(cr, uid, ids)
        orders.update_total()
        return True

    # Esto es porque purchase esta en la vieja api y nosotros en la nueva, los campos computados han cambiado bastante 
    # y no encuentro la forma de sobreescribirlos correctamente.
    # https://github.com/odoo/odoo/issues/2693 
    def update_total(self, context=None):
        val = 0.0  
        for line in self.sales_order_lines:
            if line.state in ['done','approved','confirm','progress']: 
                  val += line.amount_total
        context = dict(context or {}, mail_create_nolog=True)
        progress= 100 * val / self.qty_total
        self.update({'amount_total':val, 'progress':progress })
        return True

###################################################
#    raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))


