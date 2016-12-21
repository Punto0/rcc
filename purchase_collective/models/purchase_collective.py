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
    
    sales_order_lines = fields.One2many('sale.order','cp_order_id','Collective Order Lines',states={'approved':[('readonly',True)],'done':[('readonly',True)]},copy=True )

    deadline_date = fields.Date(string='Order Deadline', required=True, help="End date of the order. Place your orders before this date")
    
    amount_untaxed = fields.Float('Amount untaxed',compute='onchange_order_line',store=True)
    amount_tax = fields.Float('Taxes',compute='onchange_order_line',store=True)
    amount_total = fields.Float('Amount Total',compute='onchange_order_line',store=True)

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', size=24)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    #fax = fields.Char('Fax')
    mobile = fields.Char('Mobile')

    qty_min = fields.Float('Minimun product quantity by single sale', required=True, help='Minimun quantity allowed by each single sale order in product quantity')
  
    notes = fields.Text('Description for the collective purchase', translate=True)
    # Called in the update link in the cp form and in website payment confirmation
    @api.one
    @api.onchange('sales_order_lines') 
    def onchange_order_line(self):
        #_logger.info("onchange_order_lines-- ids : %s -- args: %s" %(ids,context))
        cr, uid, context = self.env.cr, self.env.user, self.env.context
        #cur_obj=self.pool.get('res.currency')

        res = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
        }

        val = val1 = 0.0
        val_tax = 0.0
        val_untax = 0.0  

        #order = self.browse(cr, uid, ids, context=context)

        if True:
            #cur = order.pricelist_id.currency_id
            #_logger.info("order : %s " %order.sales_order_lines)
            for line in self.sales_order_lines:
                _logger.info("line %s " %line.state)
                if line.state in ['done','approved','confirm','progress']: 
                  val += line.amount_total
                  #val_tax += val.get('amount_tax',0.0)
                  #val_untax += val.get('amount_untaxed',0.0)

            res['amount_tax'] = val_tax
            res['amount_untaxed'] = val
            res['amount_total']= val

            _logger.info("Res : %s " %res)

            self.amount_untaxed = res['amount_untaxed']
            self.amount_tax = res['amount_tax']
            self.amount_total = res['amount_total'] 
        _logger.info("res : %s" %(res))
        return res
    
    @api.multi 
    def subscribe(self, partner):
        self.message_subscribe(partner_ids=[(partner.id)])
        #self.message_post(body=("Order line created by %s" %(partner.name)))
  
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
        logging.info("Creating order %s" %vals)  
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
        _logger.info("Confirmando orden : %s" %ids)       
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not any(line.state != 'cancel' for line in po.order_line):
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            #if po.invoice_method == 'picking' and not any([l.product_id and l.product_id.type in ('product', 'consu') and l.state != 'cancel' for l in po.order_line]):
            #    raise osv.except_osv(
            #        _('Error!'),
            #        _("You cannot confirm a purchase order with Invoice Control Method 'Based on incoming shipments' that doesn't contain any stockable item."))
            #for line in po.order_line:
            #    if line.state=='draft':
            #        todo.append(line.id)        
        #self.pool.get('purchase_collective.order_line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid}, context=context)
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
        logging.info("_get_picking_in company_id %s %s" %(company_id.id,company_id.parent_id.id))
        types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id.id)], context=context)
        if not types:
            types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id', '=', False)], context=context)
        if not types: # En fairmarket no hay definidos almacenes por compañia, usamos la madre
            types = type_obj.search(cr, uid, [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id.parent_id.id)], context=context)
            #if not types:
                #raise osv.except_osv(_('Error!'), _("Make sure you have at least an incoming picking type defined"))
        logging.info("Types %s" %types)
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
###################################################



