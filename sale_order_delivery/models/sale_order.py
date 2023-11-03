from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    project_contract_all_ids = fields.Many2many("project.contract", string="Project", )

    def action_project_contract_all(self):
        return {
            "name": "Contract",
            "type": "ir.actions.act_window",
            "view_type": "list",
            "view_mode": "list",
            "res_model": "project.contract",
            "view": [(False, "form")],
            "target": "new",
            'domain': [{"id", "in", self.project_contract_all_ids}],
        }

    def action_view_delivery(self):
        """
        Changed the behavior of the method. All products can be divided into express delivery
        and regular delivery. If there are products with both types of delivery, then they
        will be displayed in an intermediate table. If the products have only one type of delivery,
        the intermediate table will not be displayed (standard behavior)
        """

        express_delivery = self.order_line.mapped(lambda x: x.move_ids).filtered(lambda x: x.is_express is True)
        regular_delivery = self.order_line.mapped(lambda x: x.move_ids).filtered(lambda x: x.is_express is False)
        all_delivery = self.order_line.move_ids
        if express_delivery and regular_delivery:
            if len(self.env["stock.picking"].search([("sale_id", "=", self.id)])) == 1:
                type_out = self.env.ref("stock.picking_type_out")
                self.env["stock.picking"].create({
                    "name": self.picking_ids.name + "-express",
                    "date_deadline": self.picking_ids.date_deadline,
                    "group_id": self.picking_ids.group_id.id,
                    "origin": self.picking_ids.origin,
                    "location_id": self.picking_ids.location_id.id,
                    "location_dest_id": self.picking_ids.location_dest_id.id,
                    "partner_id": self.picking_ids.partner_id.id,
                    "picking_type_id": type_out.id,
                    "move_type": self.picking_ids.move_type,
                    "state": self.picking_ids.state,
                    "sale_id": self.id,
                })

            for record in self.picking_ids:
                if 'express' in record.name:
                    record["move_ids"] = express_delivery
                else:
                    record["move_ids"] = regular_delivery

        elif len(self.picking_ids) != 1:
            for record in self.picking_ids:
                if 'express' in record.name:
                    if express_delivery:
                        record["move_ids"] = regular_delivery
                        self.env["stock.picking"].search([("name", "=", record.name)]).unlink()
                    else:
                        record["move_ids"] = express_delivery
                        self.env["stock.picking"].search([("name", "=", record.name)]).unlink()
            self.picking_ids["move_ids"] = all_delivery
        return super().action_view_delivery()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_express = fields.Boolean(string="Express delivery",
                                default=False, )


class StockMove(models.Model):
    _inherit = "stock.move"

    is_express = fields.Boolean(string="Express delivery",
                                readonly=True,
                                compute="_compute_is_express")

    @api.depends()
    def _compute_is_express(self):
        for record in self:
            stock_move_record = self.env["sale.order.line"].search([("id", "=", record.sale_line_id.id)])
            record.is_express = stock_move_record.is_express
