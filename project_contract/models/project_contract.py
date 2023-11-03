import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectContract(models.Model):
    _name = "project.contract"
    _inherit = ["mail.thread", ]
    _description = "Projects"

    name = fields.Char(string="Project name",
                       required=True,
                       help="Name of your project.",
                       tracking=True)
    contract_ids = fields.One2many(comodel_name="contract.contract",
                                   inverse_name="project_id",
                                   string="Contract",
                                   required=True,
                                   domain="[('project_id', '=', None), ('status', '=', 'confirm')]",
                                   tracking=True)

    def action_show_contracts(self):
        """
        Shows the contracts belonging to the project
        """

        return {
            "name": "Contract",
            "type": "ir.actions.act_window",
            "view_type": "list",
            "view_mode": "list",
            "res_model": "contract.contract",
            "view": [(False, "form")],
            "target": "new",
            "domain": [("id", "in", self.contract_ids.ids)],
        }

    @api.constrains("contract_ids")
    def _check_exist_active_contract(self):
        """
        The method raises an error if you add more than one active contract to the project
        """

        exist_active_contract = list(self.mapped("contract_ids").filtered(lambda x: x.status == "confirm"))
        if len(exist_active_contract) != 1:
            raise UserError(_("There must be one active contract in the project!"))

    def project_info_button(self):
        """
        The chat displays information about the project with its contracts
        """

        lst_contracts = []
        contract_number = 1

        for contract in self.contract_ids:
            contract_info = (f"{contract_number}. <b>Contract name:</b> {contract.name}; "
                             f"<b>Contract status:</b> {contract.status}. <br>")
            lst_contracts.append(contract_info)
            contract_number += 1

        result = " ".join(lst_contracts)

        self.message_post(body=f"""<div><em>Project information:</em></div>
                                    <div><b>Project name:</b> {self.name}</div>
                                    <br>
                                    <div>The project has the following contracts:</div>
                                    <div>{result}</div>
                                    <br>
                                """)


class Contract(models.Model):
    _name = "contract.contract"
    _description = "Contracts"

    name = fields.Char(string="Contract name",
                       required=True,
                       help="The name of your contract.")
    date_sign = fields.Datetime(string="Date of signing",
                                default=None,
                                readonly=True,
                                help="Date when the contract received the status: confirmed")
    project_id = fields.Many2one(comodel_name="project.contract",
                                 string="Project",
                                 readonly=True,
                                 index=True)
    status = fields.Selection([
        ("draft", "Draft"),
        ("confirm", "Confirmed"),
        ("completed", "Completed"),
    ], string="Contract status", default=None, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """
        The method creates a contract and assigns the draft status to the contract
        """

        for vals in vals_list:
            vals["status"] = "draft"
        contract = super().create(vals_list)

        return contract

    def action_confirm_contract(self):
        """
        The method changes the status of the contract: draft -> confirm
        """

        for record in self:
            record.status = "confirm"
            record.date_sign = datetime.datetime.now()
        return True

    def action_complete_contract(self):
        """
        This method changes the status of the contract to: Completed
        """

        for record in self:
            record.status = "completed"
        return True

    def edit_contract_name(self):
        """
        Contract renaming method
        """

        self.ensure_one()
        return {
            "name": "Contract",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "edit.name.contract",
            "view": [(False, "form")],
            "target": "new",
            'context': {
                'contract_id': self.id,
                'default_new_name': self.name,
            }
        }
